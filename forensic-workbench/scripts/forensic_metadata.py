#!/usr/bin/env python3
"""Read-only multimedia forensics: hashing, complete binary box mapping, JSON tool sidecars.

Usage: python3 forensic_metadata.py --out /SEPARATE/OUTPUT_DIR /path/MP4s
Requires Python 3.9+. Optional: ffprobe, file, MediaInfo CLI, ExifTool, Bento4 mp4dump,
GPAC MP4Box. NEVER overwrites/reconstructs source bytes. Reports are not authentication.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, mmap, os, re, shutil, struct, subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

RECOGNIZED=(b'ftyp',b'moov',b'mdat',b'moof',b'mvhd',b'trak',b'mdia',b'minf',b'stbl',b'stsd',b'stts',b'stsc',b'stsz',b'stco',b'co64',b'stss',b'ctts',b'avcC',b'esds',b'mp4a',b'hvcC',b'free',b'wide',b'uuid',b'skip',b'mfra',b'traf',b'udta',b'hand',b'hdlr',b'mdhd',b'tkhd',b'tfhd',b'trun',b'tfdt')
CONTAINERS={b'moov',b'trak',b'mdia',b'minf',b'stbl',b'edts',b'dinf',b'udta',b'meta',b'ilst',b'moof',b'traf',b'mvex',b'mfra',b'sinf',b'schi',b'tref'}
SUFFIX={'.mp4','.m4v','.mov','.3gp','.264','.h264','.h265','.aac','.raw','.bin','.dat','.tmp'}

def now(): return datetime.now(timezone.utc).isoformat()
def bhex(b: bytes): return b.hex(' ',4)
def ascii_safe(b:bytes): return ''.join(chr(x) if 32<=x<127 else '.' for x in b)
def be32(b): return struct.unpack('>I',b)[0]
def be64(b): return struct.unpack('>Q',b)[0]

def box_header(mm,off,end):
    if off<0 or off+8>end: return None
    typ=mm[off+4:off+8]
    if typ not in RECOGNIZED and typ not in CONTAINERS and not all(32<=c<127 for c in typ): return None
    size=be32(mm[off:off+4]); header=8
    if size==1:
        if off+16>end:return None
        size=be64(mm[off+8:off+16]);header=16
    if size==0:
        return {'offset':off,'type':typ.decode('latin1'),'size':end-off,'header_size':header,'extends_to_eof':True,'valid_extent':True}
    if size<header:return None
    return {'offset':off,'type':typ.decode('latin1'),'size':size,'header_size':header,'ends':off+size,'valid_extent':off+size<=end}

def walk_boxes(mm,start,end,depth=0,max_boxes=4000):
    boxes=[];off=start;count=0
    while off+8<=end and count<max_boxes:
        head=box_header(mm,off,end)
        if not head: break
        boxes.append(head);count+=1
        if not head['valid_extent']: break
        payload=off+head['header_size'];t=head['type'].encode()
        if t==b'ftyp' and payload+8<=off+head['size']:
            head['major_brand']=ascii_safe(mm[payload:payload+4]);head['minor_version']=be32(mm[payload+4:payload+8])
            head['compatible_brands']=[ascii_safe(mm[p: p+4]) for p in range(payload+8,min(off+head['size'],payload+56)-3,4)]
        elif t in (b'stsz', b'stts', b'stsc', b'stco', b'co64', b'ctts', b'stss') and payload+8<=off+head['size']:
            head['version_flags_hex']=mm[payload:payload+4].hex()
            if t==b'stsz' and payload+12<=off+head['size']:
                head['default_sample_size']=be32(mm[payload+4:payload+8]);head['sample_count']=be32(mm[payload+8:payload+12])
            else:head['entry_count']=be32(mm[payload+4:payload+8])
        elif t==b'stsd' and payload+8<=off+head['size']:
            head['description_count']=be32(mm[payload+4:payload+8]); entries=[];ep=payload+8
            for _ in range(min(head['description_count'],10)):
                if ep+8>off+head['size']:break
                en=be32(mm[ep:ep+4]);etype=ascii_safe(mm[ep+4:ep+8]);item={'codec_sample_entry_fourcc':etype,'size':en}
                if en<8 or ep+en>off+head['size']: item['truncated']=True;entries.append(item);break
                if etype in ('avc1','avc3','hvc1','hev1','mp4v') and en>=40:
                    item['width_px']=int.from_bytes(mm[ep+32:ep+34],'big');item['height_px']=int.from_bytes(mm[ep+34:ep+36],'big')
                if etype in ('alaw','ulaw','mp4a','sowt','twos','lpcm') and en>=36:
                    item['channels']=int.from_bytes(mm[ep+24:ep+26],'big');item['sample_bits']=int.from_bytes(mm[ep+26:ep+28],'big')
                    item['sample_rate_hz']=be32(mm[ep+32:ep+36])>>16
                entries.append(item);ep+=en
            head['sample_descriptions']=entries
        elif t==b'hdlr' and payload+12<=off+head['size']:
            head['handler_type']=ascii_safe(mm[payload+8:payload+12])
        elif t==b'mdhd' and payload+20<=off+head['size']:
            version=mm[payload];head['version']=version;idx=payload+(20 if version==1 else 12)
            if idx+4<=off+head['size']:
                head['timescale']=be32(mm[idx:idx+4]);
        elif t==b'mvhd' and payload+20<=off+head['size']:
            version=mm[payload];head['version']=version
            idx=payload+(20 if version==1 else 12)
            try:
                head['timescale']=be32(mm[idx:idx+4]);head['duration_ticks']=be64(mm[idx+4:idx+12]) if version==1 else be32(mm[idx+4:idx+8]);
                head['duration_seconds']=round(head['duration_ticks']/head['timescale'],4) if head['timescale'] else None
            except Exception: pass
        if t in CONTAINERS and depth<12:
            child=payload+(4 if t==b'meta' else 0)
            if child+8<=off+head['size']:
                head['children']=walk_boxes(mm,child,off+head['size'],depth+1,max_boxes)
                if head['children']:
                    consumed=head['children'][-1]['offset']+head['children'][-1]['size']
                    if consumed<off+head['size']:head['child_parse_unparsed_tail_bytes']=(off+head['size'])-consumed
                else:head['child_parse_unparsed_tail_bytes']=(off+head['size'])-child
        off+=head['size']
    return boxes

def signatures(mm,out_base):
    sz=len(mm);hits={};allbox=[]
    dumpdir=out_base/'binary_fragments';dumpdir.mkdir(exist_ok=True,parents=True)
    for typ in RECOGNIZED:
        name=typ.decode('ascii'); pos=0;arr=[]
        while len(arr)<1000:
            idx=mm.find(typ,pos); 
            if idx<0:break
            off=idx-4;entry={'type_offset':idx,'box_offset':off}
            head=box_header(mm,off,sz)
            if head and head['type']==name:
                entry.update(head)
                if head['valid_extent'] and typ in (b'ftyp',b'moov',b'free',b'wide') and head['size']<=10*1024*1024:
                    # Carved *unaltered box bytes* for expert use; fragments aren't repaired playable videos.
                    dst=dumpdir/f'{off:010d}_{name}.bin'
                    dst.write_bytes(mm[off:off+head['size']])
                    entry['carved_box_path']=str(dst.relative_to(out_base))
                if head['valid_extent'] and typ in (b'moov',b'ftyp'):
                    entry['parsed_tree']=walk_boxes(mm,off,off+head['size'])
                allbox.append(entry)
            else:entry['plausible_box_header']=False
            arr.append(entry);pos=idx+1
        if arr:hits[name]=arr
    return hits,allbox

def sha(path):
    sh1=hashlib.sha256(); sh2=hashlib.sha512();sh3=hashlib.md5()
    with path.open('rb') as f:
        for c in iter(lambda:f.read(8*1024*1024),b''):
            sh1.update(c);sh2.update(c);sh3.update(c)
    return {'sha256':sh1.hexdigest(),'sha512':sh2.hexdigest(),'md5_legacy':sh3.hexdigest()}

def entropy(b):
    if not b:return 0.0
    n=len(b);counts=Counter(b)
    return round(-sum((c/n)*math.log2(c/n) for c in counts.values()),5)

def binary_blocks(mm,p,out_dir,blocksz=16384):
    blocks=[]
    for off in range(0,len(mm),blocksz):
        d=mm[off:off+blocksz];n=len(d)
        blocks.append({'offset':off,'size':n,'sha256':hashlib.sha256(d).hexdigest(),
                       'entropy':entropy(d),'zero_byte_fraction':round(d.count(0)/n,6),
                       'ff_byte_fraction':round(d.count(255)/n,6)})
    (out_dir/'block_statistics.json').write_text(json.dumps(blocks,indent=2))
    return blocks

def cli(name,argv,stem,dirpath,timeout=90):
    tool=shutil.which(name)
    if not tool:return {'available':False,'command_template':' '.join([name]+argv),'reason':'binary not installed'}
    try:
        proc=subprocess.run([tool]+argv,capture_output=True,timeout=timeout)
        (dirpath/f'{stem}.stdout').write_bytes(proc.stdout)
        (dirpath/f'{stem}.stderr').write_bytes(proc.stderr)
        return {'available':True,'exit_code':proc.returncode,'stdout_file':f'{stem}.stdout',
                'stderr_file':f'{stem}.stderr','stderr_excerpt':proc.stderr.decode('utf-8','replace')[-800:]}
    except (OSError,subprocess.TimeoutExpired) as e:return {'available':True,'error':str(e)}

def collect(args):
    p=[]
    for x in args:
        f=Path(x).resolve()
        if f.is_file():p.append(f)
        elif f.is_dir():p.extend(y.resolve() for y in f.rglob('*') if y.is_file() and y.suffix.lower() in SUFFIX)
    return list(dict.fromkeys(p))

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('inputs',nargs='+')
    a.add_argument('--out',required=True,help='Output outside all source input directories')
    a.add_argument('--deep-ffprobe',action='store_true',help='Also request packet and frame records from FFprobe')
    a.add_argument('--run-mediaconch',action='store_true',help='Optional MediaConch informational probe (not an MP4 integrity verdict)')
    opts=a.parse_args();out=Path(opts.out).resolve();files=collect(opts.inputs)
    if not files:a.error('No accessible matching inputs')
    for raw in opts.inputs:
        original=Path(raw).resolve()
        if original.is_dir() and (original==out or original in out.parents):a.error('Output must NOT be inside a source directory')
    out.mkdir(parents=True,exist_ok=True)
    catalog=[];shared=defaultdict(list)
    for path in files:
        sub=out/f'{len(catalog):04d}_{re.sub(r"[^a-zA-Z0-9._-]","_",path.name)}';sub.mkdir(exist_ok=True)
        size=path.stat().st_size
        report={'file':str(path),'size_bytes':size,'local_copy_mtime_utc':datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat(),
                'file_hashes':sha(path),'inspection_utc':now(),'tools':{}}
        if size:
            with path.open('rb') as f, mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
                report['head_4096_hex']=bhex(mm[:min(4096,size)])
                report['tail_4096_hex']=bhex(mm[max(0,size-4096):])
                report['first_64_bytes_ascii']=ascii_safe(mm[:64]);report['global_entropy']=entropy(mm[:min(size,16*1024*1024)])
                hits,valid=signatures(mm,sub)
                report['bmff_signature_hits']=hits
                report['validated_candidate_boxes']=[{k:v for k,v in b.items() if k!='parsed_tree'} for b in valid]
                report['top_level_boxes_at_zero']=walk_boxes(mm,0,size)
                report['internal_structures']= [v for v in valid if v['type'] in ('ftyp','moov','mdat')]
                blocks=binary_blocks(mm,path,sub)
                for b in blocks:shared[b['sha256']].append({'file':str(path),'offset':b['offset'],'size':b['size']})
                report['block_count']=len(blocks)
        report['tools']['file']=cli('file',['-k',str(path)],'file_identification',sub)
        ffp=['-hide_banner','-v','error','-show_error','-show_format','-show_streams','-show_chapters','-of','json',str(path)]
        report['tools']['ffprobe']=cli('ffprobe',ffp,'ffprobe_full',sub)
        if opts.deep_ffprobe:
            report['tools']['ffprobe_packets_frames']=cli('ffprobe',['-hide_banner','-v','error','-show_error','-show_packets','-show_frames','-of','json',str(path)],'ffprobe_packets_frames',sub)
        report['tools']['mediainfo_json']=cli('mediainfo',['--Full','--Output=JSON',str(path)],'mediainfo_full_json',sub)
        report['tools']['mediainfo_xml']=cli('mediainfo',['--Full','--Output=XML',str(path)],'mediainfo_full_xml',sub)
        report['tools']['exiftool']=cli('exiftool',['-G1','-a','-s','-ee','-j',str(path)],'exiftool_full',sub)
        report['tools']['bento4_mp4dump']=cli('mp4dump',['--verbosity','3',str(path)],'bento4_mp4dump',sub)
        report['tools']['gpac_mp4box']=cli('MP4Box',['-diso',str(path)],'gpac_mp4box_diso',sub)
        if opts.run_mediaconch:
            report['tools']['mediaconch']=cli('mediaconch',[str(path)],'mediaconch_info',sub)
        (sub/'file_report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False,default=str))
        simple={'filename':path.name,'size_bytes':size,**report['file_hashes'],
                'recognized_ftyp':len([b for b in report.get('internal_structures',[]) if b['type']=='ftyp']),
                'recognized_moov':len([b for b in report.get('internal_structures',[]) if b['type']=='moov']),
                'recognized_mdat':len([b for b in report.get('internal_structures',[]) if b['type']=='mdat']),
                'ffprobe_exit':report['tools']['ffprobe'].get('exit_code'),
                'ffprobe_error':report['tools']['ffprobe'].get('stderr_excerpt',''),
                'analysis_dir':sub.name}
        catalog.append(simple)
        print(path.name, 'size',size,'valid structures',[(b['type'],b['offset']) for b in report.get('internal_structures',[])],flush=True)
    with (out/'manifest.csv').open('w',newline='',encoding='utf8') as o:
        w=csv.DictWriter(o,fieldnames=list(catalog[0]));w.writeheader();w.writerows(catalog)
    duplicates=[{'block_sha256':h,'locations':v} for h,v in shared.items() if len(set(t['file'] for t in v))>1]
    (out/'cross_file_identical_blocks.json').write_text(json.dumps(duplicates,indent=2))
    (out/'manifest.json').write_text(json.dumps({'created_utc':now(),'files':catalog,'shared_block_digest_occurrences':duplicates,
      'notes':['Read-only analysis; extracted atom data are byte-for-byte copies and not repaired movies',
       'MP4 atom presence can be incidental or relate to another recording; validate audio/video linkage before conclusions',
       'FFprobe/MediaInfo failures do not prove deliberate tampering or establish deleted cluster ordering',
       'No unallocated SD sectors or FAT/exFAT allocation maps exist in ordinary copied MP4 files']},indent=2))

if __name__=='__main__':main()