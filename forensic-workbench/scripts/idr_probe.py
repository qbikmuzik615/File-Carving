#!/usr/bin/env python3
"""Read-only AVCC-to-AnnexB IDR validation for carved MP4 beginnings.

Outputs only derived .h264 streams, local JSON and logs; keeps original inputs
unchanged. A decoder failure is not automatically a physical cluster boundary.
All byte offsets are absolute in the input file. Requires installed ffmpeg.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from phase_invariant_audit import atom_report


def extract_avcc(reference: bytes, offset=None):
    starts=[]
    if offset is None:
        pos=0
        while (idx:=reference.find(b'avcC',pos))>=0:
            starts.append(idx-4)
            pos=idx+4
    else:
        starts=[offset]
    for s in starts:
        if s<0 or s+13>len(reference):
            continue
        size=int.from_bytes(reference[s:s+4],'big')
        if not 16<=size<=4096 or reference[s+4:s+8]!=b'avcC' or s+size>len(reference):
            continue
        p=reference[s+8:s+size]
        if p[0]!=1:
            continue
        width=(p[4]&3)+1
        n_sps=p[5]&31
        q=6
        sps=[]
        try:
            for _ in range(n_sps):
                n=int.from_bytes(p[q:q+2],'big');q+=2
                if n<1 or q+n>len(p):raise ValueError
                sps.append(p[q:q+n]);q+=n
            n_pps=p[q];q+=1
            pps=[]
            for _ in range(n_pps):
                n=int.from_bytes(p[q:q+2],'big');q+=2
                if n<1 or q+n>len(p):raise ValueError
                pps.append(p[q:q+n]);q+=n
            if sps and pps and q==len(p):
                return {'avcc_offset':s,'nal_length_size':width,'sps':sps,'pps':pps}
        except (ValueError,IndexError):
            pass
    raise ValueError('No valid avcC atom with SPS/PPS found at specified offset')


def probe_file(file:Path, avcc, out_dir:Path):
    d=file.read_bytes()
    results=[]
    for n, hit in enumerate(atom_report(d)):
        box=hit['mdat_start']
        if box is None:
            continue
        payload=box+8
        n_width=avcc['nal_length_size']
        if payload+n_width>len(d):
            continue
        nal_len=int.from_bytes(d[payload:payload+n_width],'big')
        nal_start=payload+n_width
        nal_end=nal_start+nal_len
        entry={'file':str(file),'ftyp_start':hit['ftyp_start'],
               'mdat_start':box,'first_nal_length':nal_len,
               'first_nal_header':d[nal_start:nal_start+4].hex(),
               'first_nal_type':d[nal_start]&31 if nal_start<len(d) else None,
               'sample_fits_export':nal_end<=len(d),
               'sample_end':nal_end,
               'predicted_next_16k_boundary':hit['ftyp_start']+16384,
               'predicted_next_32k_boundary':hit['ftyp_start']+32768}
        if not 0<nal_len<=10_000_000 or nal_end>len(d):
            entry['status']='sample_outside_export'
            results.append(entry)
            continue
        safe_prefix=f'{file.parent.name}_{file.stem}_{n}_off{hit["ftyp_start"]}'
        stream=out_dir/(safe_prefix+'.h264')
        stream.write_bytes(b''.join(b'\0\0\0\1'+x for x in avcc['sps']+avcc['pps']+[d[nal_start:nal_end]]))
        entry['derived_annexb_sha256']=hashlib.sha256(stream.read_bytes()).hexdigest()
        args=['ffmpeg','-hide_banner','-nostdin','-loglevel','debug','-ec','0',
              '-err_detect','explode','-xerror','-f','h264','-i',str(stream),
              '-frames:v','1','-f','null','-']
        completed=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                 text=True,errors='replace',check=False)
        log=out_dir/(safe_prefix+'.decoder.log')
        log.write_text(completed.stderr)
        entry['decoder_exit_code']=completed.returncode
        entry['decoder_log_file']=str(log)
        entry['decoder_errors']=[s for s in completed.stderr.splitlines()
                                 if re.search(r'error while decoding MB|invalid data|frames decoded|decode errors|corrupt decoded frame',s,re.I)][-8:]
        entry['status']='no_strict_decoder_error_observed' if completed.returncode==0 else 'strict_decode_failed'
        results.append(entry)
    return results


def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--reference',type=Path,required=True)
    a.add_argument('--avcc-offset',type=int,default=None,help='absolute avcC box start in reference')
    a.add_argument('--output-dir',type=Path,required=True)
    a.add_argument('inputs',nargs='+',type=Path)
    args=a.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    avcc=extract_avcc(args.reference.read_bytes(),args.avcc_offset)
    sources=[]
    for x in args.inputs:
        if x.is_dir():sources.extend(sorted(y for y in x.iterdir() if y.suffix.lower() in ('.mp4','.mov')))
        else:sources.append(x)
    reports=[]
    for p in sources:
        reports.extend(probe_file(p,avcc,args.output_dir))
    r={'avcc_offset':avcc['avcc_offset'],
       'reference_file_sha256':hashlib.sha256(args.reference.read_bytes()).hexdigest(),
       'sps_hex':[x.hex() for x in avcc['sps']], 'pps_hex':[x.hex() for x in avcc['pps']],
       'nal_prefix_bytes':avcc['nal_length_size'],'probes':reports}
    (args.output_dir/'idr_probe_report.json').write_text(json.dumps(r,indent=2)+'\n')
    for entry in reports:
        print(Path(entry['file']).name,entry['ftyp_start'],entry['first_nal_length'],entry['status'])
        for msg in entry.get('decoder_errors',[]):print(' ',msg)
    print('Wrote local JSON report with input SHA-256 and decoder logs')


if __name__=='__main__':
    main()
