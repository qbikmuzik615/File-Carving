#!/usr/bin/env python3
"""Read-only ISOBMFF/AVC forward/backward candidate auditor. Stdlib Python 3.9+.

THIS DOES NOT REPAIR OR AUTHENTICATE RECOVERED MEDIA. An embedded moov and mdat
may be unrelated, and moov adjacency must be independently established.

Usage:
    python3 wyze_bidirectional_audit.py MOOV_DONOR MP4_MDAT_DONOR --out ./audit

Only classic (non-fragmented) sample-table MP4 is supported. Unsupported formats
are explicitly rejected/flagged instead of silently applying a 4-byte NAL rule.
"""
import argparse
import csv
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import struct
import sys

CLUSTERS = (4096, 8192, 16384, 32768, 65536)
MAX_BOX_ENTRIES = 2_000_000
EPOCH = datetime(1904, 1, 1, tzinfo=timezone.utc)

class ParseError(Exception):
    pass

def u32(data, p):
    if p < 0 or p + 4 > len(data): raise ParseError('truncated u32 at %d' % p)
    return struct.unpack_from('>I', data, p)[0]

def u64(data, p):
    if p < 0 or p + 8 > len(data): raise ParseError('truncated u64 at %d' % p)
    return struct.unpack_from('>Q', data, p)[0]

def boxes(buf, start, end):
    p = start
    while p + 8 <= end:
        n, tag = struct.unpack_from('>I4s', buf, p)
        header = 8
        if n == 1:
            if p + 16 > end: raise ParseError('truncated 64-bit box at %d' % p)
            n, header = u64(buf, p+8), 16
        elif n == 0: n = end-p
        if n < header or p + n > end:
            raise ParseError('box %s invalid at %d, size=%d, limit=%d' % (tag, p, n, end))
        yield {'tag': tag, 'start': p, 'body': p+header, 'end': p+n, 'header':header}
        p += n
    if p != end:
        # trailing bytes in boxes are not necessarily valid and should be reported
        raise ParseError('box stream has %d orphan trailing bytes at %d' % (end-p,p))

def children_named(buf, start, end, tag):
    return [b for b in boxes(buf,start,end) if b['tag']==tag]

def hash_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as fp:
        for block in iter(lambda:fp.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def find_candidate_boxes(buf, tag):
    hits=[]
    at=0
    while True:
        i=buf.find(tag, at)
        if i<0:break
        at=i+1
        p=i-4
        if p<0:continue
        n=u32(buf,p);hdr=8
        if n==1:
            if i+12>len(buf): continue
            n=u64(buf,i+4);hdr=16
        if n==0:continue  # zero-sized embedded box cannot be located without topology
        if n<hdr or n>max(len(buf),128*1024*1024):continue
        end=p+n
        if tag==b'moov' and end>len(buf):continue
        if tag==b'moov':
            try:
                ch=list(boxes(buf,p+hdr,end))
                if not (any(c['tag']==b'trak' for c in ch) and any(c['tag']==b'mvhd' for c in ch)):
                    continue
            except ParseError: continue
        hits.append({'tag':tag.decode('ascii'),'start':p,'body':p+hdr,'size':n,
                     'end_declared':end,'present_end':min(len(buf),end),'header':hdr,
                     'complete':end<=len(buf)})
    return hits

def parse_mvhd(buf, box):
    p,e=box['body'],box['end']
    if p+4>e:raise ParseError('short mvhd')
    version=buf[p]
    if version==0:
        if p+20>e:raise ParseError('short mvhd v0')
        ct,mt,ts,dur=struct.unpack_from('>IIII',buf,p+4)
    elif version==1:
        if p+32>e:raise ParseError('short mvhd v1')
        ct,mt,ts,dur=struct.unpack_from('>QQIQ',buf,p+4)
    else:raise ParseError('unsupported mvhd version')
    return {'raw_creation_seconds_since_1904':ct,
            'nominal_utc':(EPOCH+timedelta(seconds=ct)).isoformat(),
            'timescale':ts,'duration_seconds':dur/ts if ts else None,
            'time_caveat':'Uncalibrated camera clock/timezone'}

def parse_array_table(buf,b,record_width):
    p,e=b['body'],b['end']
    if p+8>e: raise ParseError('truncated table header')
    count=u32(buf,p+4)
    if count>MAX_BOX_ENTRIES:raise ParseError('excessive table count')
    if p+8+count*record_width>e:raise ParseError('table array extends beyond box')
    return count,p+8

def find_avcc_in_entry(buf, entry_start, entry_end):
    at=entry_start+8
    while True:
        i=buf.find(b'avcC',at,entry_end)
        if i<0: return None
        p=i-4
        if p>=entry_start+8:
            n=u32(buf,p)
            if n>=14 and p+n<=entry_end:
                record=p+8
                if buf[record]==1:
                    val=(buf[record+4]&3)+1
                    if val in (1,2,4):
                        return {'prefix_bytes':val,'box_offset':p,
                                'avcc_sha256':hashlib.sha256(buf[record:p+n]).hexdigest()}
        at=i+4

def parse_stsd(buf,b):
    count,p=parse_array_table(buf,b,0)
    entries={}
    for i in range(1,count+1):
        if p+8>b['end']:raise ParseError('stsd entry truncated')
        sz=u32(buf,p)
        if sz<8 or p+sz>b['end']:raise ParseError('invalid stsd entry')
        codec=buf[p+4:p+8].decode('latin1')
        v={'codec':codec,'size':sz}
        if codec in ('avc1','avc3','encv'):
            v.update(find_avcc_in_entry(buf,p,p+sz) or {})
        entries[i]=v
        p+=sz
    return entries

def parse_track(buf, trak, number):
    track={'track':number,'handler':'unknown','stsz':None,'stco':None,'stsc':None,
           'stsd':{},'stts_count':None,'notices':[]}
    def descend(start,end):
        for b in boxes(buf,start,end):
            typ=b['tag']
            if typ in (b'mdia',b'minf',b'stbl'):
                descend(b['body'],b['end'])
            elif typ==b'hdlr':
                if b['body']+12<=b['end']:
                    track['handler']=buf[b['body']+8:b['body']+12].decode('latin1')
            elif typ==b'stsz':
                p=b['body'];e=b['end']
                if p+12>e:raise ParseError('stsz too short')
                fixed,count=struct.unpack_from('>II',buf,p+4)
                if count>MAX_BOX_ENTRIES:raise ParseError('stsz too many samples')
                if fixed:
                    track['stsz']=[fixed]*count
                else:
                    if p+12+4*count>e:raise ParseError('stsz sizes truncated')
                    track['stsz']=list(struct.unpack_from('>%dI'%count,buf,p+12))
            elif typ in (b'stco',b'co64'):
                count,p=parse_array_table(buf,b,4 if typ==b'stco' else 8)
                track['stco']=[u32(buf,p+4*i) if typ==b'stco' else u64(buf,p+8*i)
                                 for i in range(count)]
                track['chunk_offset_type']=typ.decode()
            elif typ==b'stsc':
                count,p=parse_array_table(buf,b,12)
                track['stsc']=[struct.unpack_from('>III',buf,p+i*12) for i in range(count)]
            elif typ==b'stsd':track['stsd']=parse_stsd(buf,b)
            elif typ==b'stts':
                count,p=parse_array_table(buf,b,8)
                track['stts_count']=sum(u32(buf,p+8*i) for i in range(count))
            elif typ==b'stz2':track['notices'].append('stz2 unsupported')
    descend(trak['body'],trak['end'])
    for key in ('stsz','stco','stsc'):
        if track[key] is None:raise ParseError('missing %s in track %d'%(key,number))
    if track['stts_count'] is not None and track['stts_count']!=len(track['stsz']):
        track['notices'].append('stts sample count differs from stsz')
    return track

def parse_moov(buf, moov):
    end=moov['end_declared'];body=moov['body']; mvhd=None;trks=[]
    for b in boxes(buf,body,end):
        if b['tag']==b'mvhd':mvhd=parse_mvhd(buf,b)
        if b['tag']==b'trak':trks.append(parse_track(buf,b,len(trks)+1))
    if not trks:raise ParseError('no trak')
    return {'moov_offset':moov['start'],'moov_size':moov['size'],
            'mvhd':mvhd,'tracks':trks}

def sample_map(tracks):
    samples=[];track_summaries=[]
    for tr in tracks:
        sizes=tr['stsz'];offsets=tr['stco'];entries=tr['stsc']
        if not entries and sizes:raise ParseError('nonempty stsz but empty stsc')
        if entries and entries[0][0]!=1:raise ParseError('stsc must begin with first_chunk 1')
        if any(fc<1 or spc<1 or desc<1 for fc,spc,desc in entries):raise ParseError('invalid stsc entry')
        if any(entries[i+1][0]<=entries[i][0] for i in range(len(entries)-1)):
            raise ParseError('stsc not strictly sorted')
        idx=0
        for j,(fc,spc,desc) in enumerate(entries):
            next_fc=entries[j+1][0] if j+1<len(entries) else len(offsets)+1
            if next_fc>len(offsets)+1:raise ParseError('stsc exceeds chunk count')
            for chunk_number in range(fc,next_fc):
                p=offsets[chunk_number-1]
                for _ in range(spc):
                    if idx>=len(sizes):raise ParseError('stsc maps MORE samples than stsz')
                    sample_size=sizes[idx]
                    if sample_size<=0:raise ParseError('zero size sample %d'%idx)
                    descinfo=tr['stsd'].get(desc,{})
                    samples.append({'orig_offset':p,'size':sample_size,'track':tr['track'],
                                    'handler':tr['handler'],'sample_index':idx,
                                    'chunk':chunk_number,'description_index':desc,
                                    'codec':descinfo.get('codec'),
                                    'nal_prefix_bytes':descinfo.get('prefix_bytes')})
                    p+=sample_size;idx+=1
        if idx!=len(sizes):raise ParseError('stsc maps FEWER samples than stsz (%s of %s)'%(idx,len(sizes)))
        track_summaries.append({'track':tr['track'],'handler':tr['handler'],
                                'samples':len(sizes),'chunks':len(offsets),
                                'sum_sample_bytes':sum(sizes),'descriptions':tr['stsd'],
                                'notices':tr['notices'],'chunk_offset_type':tr.get('chunk_offset_type')})
    samples.sort(key=lambda x:(x['orig_offset'],x['track'],x['sample_index']))
    if not samples:raise ParseError('no samples')
    for a,b in zip(samples,samples[1:]):
        if b['orig_offset']<a['orig_offset']+a['size']:
            raise ParseError('overlapping samples at original file offsets %d/%d'%(a['orig_offset'],b['orig_offset']))
    return samples,track_summaries

def validate_video(buf,pos,sz,prefix):
    """AVCC envelope validation, NOT an H.264 entropy/slice decode."""
    if prefix not in (1,2,4):return ('unsupported_prefix',None,None)
    if pos<0 or pos+sz>len(buf):return ('sample_out_of_bounds',None,None)
    if sz<prefix+1:return ('short_sample',None,None)
    q=0;types=[]
    while q<sz:
        if sz-q<prefix:return ('partial_prefix',pos+q,types)
        n=int.from_bytes(buf[pos+q:pos+q+prefix],'big')
        if n<1 or n>sz-q-prefix:return ('bad_nal_length',pos+q,types)
        h=buf[pos+q+prefix]
        if h&0x80:return ('h264_forbidden_bit',pos+q+prefix,types)
        typ=h&0x1F
        if typ==0 or typ>23:return ('invalid_nal_type',pos+q+prefix,types)
        types.append(typ);q+=prefix+n
    return ('valid_avcc',None,types)

def anchor_mods(file_offset):
    return {'file_mod_%s'%c:file_offset%c if file_offset is not None else None for c in CLUSTERS}

def inspect_pair(meta,mdat_info,moov_data,mdat_data,tail_gap):
    samples,tracks=sample_map(meta['tracks'])
    first=min(s['orig_offset'] for s in samples)
    last=max(s['orig_offset']+s['size'] for s in samples)
    total=sum(s['size'] for s in samples)
    span=last-first
    declared=mdat_info['size']-mdat_info['header']
    actual_avail=max(0,min(len(mdat_data),mdat_info['end_declared'])-mdat_info['body'])
    vids=[s for s in samples if s['handler']=='vide']
    video_count=len(vids)
    res=[]
    for s in samples:
        relative=s['orig_offset']-first
        fpos=mdat_info['body']+relative
        # Tail alignment is a TESTABLE HYPOTHESIS; it is not intrinsic to moov.
        bpos=meta['moov_offset']-tail_gap-(last-s['orig_offset'])
        fstat,ffail,ftypes=validate_video(mdat_data,fpos,s['size'],s['nal_prefix_bytes']) if s['handler']=='vide' else ('not_video',None,None)
        bstat,bfail,btypes=validate_video(moov_data,bpos,s['size'],s['nal_prefix_bytes']) if s['handler']=='vide' else ('not_video',None,None)
        res.append({**s,'relative_offset':relative,'forward_pos':fpos,'backward_pos':bpos,
                    'forward_status':fstat,'forward_invalid_byte':ffail,
                    'backward_status':bstat,'backward_invalid_byte':bfail,
                    'forward_nal_types':ftypes,'backward_nal_types':btypes})
    vs=[s for s in res if s['handler']=='vide']
    prefix=0
    for s in vs:
        if s['forward_status']=='valid_avcc':prefix+=1
        else:break
    suffix=0
    for s in reversed(vs):
        if s['backward_status']=='valid_avcc':suffix+=1
        else:break
    first_video=vs[0] if vs else None
    first_failed=vs[prefix] if prefix<len(vs) else None
    last_failed=vs[len(vs)-suffix-1] if suffix<len(vs) else None
    return {'moov_offset':meta['moov_offset'],'moov_size':meta['moov_size'],
            'mdat_offset':mdat_info['start'],'mdat_payload_offset':mdat_info['body'],
            'mdat_declared_payload_bytes':declared,
            'mdat_current_file_available_bytes':actual_avail,
            'sum_all_track_sample_bytes':total,'sample_extent_bytes':span,
            'unmapped_gap_bytes':span-total,
            'stsz_equals_mdat_payload':total==declared,
            'span_equals_mdat_payload':span==declared,
            'first_sample_original_offset':first,'last_sample_original_end':last,
            'video_samples':video_count,'forward_initial_video_run':prefix,
            'backward_terminal_video_run_HYPOTHETICAL':suffix,
            'forward_valid_all_indices':sum(s['forward_status']=='valid_avcc' for s in vs),
            'backward_valid_all_indices_HYPOTHETICAL':sum(s['backward_status']=='valid_avcc' for s in vs),
            'first_video_sample':first_video,'first_forward_failure':first_failed,
            'first_reverse_failure':last_failed,
            'moov_is_embedded_in_export':meta['moov_offset']>0,
            'moov_before_mdat_in_separate_donors':None,
            'backward_anchor_warning': 'NOT AUTHENTICATED: adjacency to original mdat EOF not established; compare original raw card layout.',
            'offset_mods_first_failure':anchor_mods(first_failed['forward_pos'] if first_failed else None),
            'offset_mods_backward_failure':anchor_mods(last_failed['backward_pos'] if last_failed else None),
            'audio_samples':sum(s['handler']=='soun' for s in samples),
            'mvhd':meta['mvhd'],'tracks':tracks,'rows':res}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('moov_donor')
    ap.add_argument('mdat_donor')
    ap.add_argument('--out',required=True,help='Output directory; originals NEVER modified')
    ap.add_argument('--tail-gap',type=int,default=0,help='Hypothetical bytes between last mapped sample and moov (default 0; unproven)')
    ap.add_argument('--moov-offset',type=int,default=None,help='Restrict to exact embedded moov start')
    ap.add_argument('--mdat-offset',type=int,default=None,help='Restrict to exact embedded mdat start')
    args=ap.parse_args()
    md=Path(args.moov_donor).read_bytes();dd=Path(args.mdat_donor).read_bytes()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    moovs=find_candidate_boxes(md,b'moov')
    mdats=find_candidate_boxes(dd,b'mdat')
    if args.moov_offset is not None:moovs=[x for x in moovs if x['start']==args.moov_offset]
    if args.mdat_offset is not None:mdats=[x for x in mdats if x['start']==args.mdat_offset]
    results=[];errors=[];all_rows=[]
    for moov in moovs:
        try:meta=parse_moov(md,moov)
        except (ParseError,IndexError,ValueError) as e:
            errors.append({'moov_at':moov['start'],'error':str(e)});continue
        for mdat in mdats:
            try:r=inspect_pair(meta,mdat,md,dd,args.tail_gap)
            except (ParseError,IndexError,ValueError) as e:
                errors.append({'moov_at':moov['start'],'mdat_at':mdat['start'],'error':str(e)});continue
            all_rows.extend([{'moov_start':r['moov_offset'],'mdat_start':r['mdat_offset'],**s}
                             for s in r.pop('rows')])
            results.append(r)
    results.sort(key=lambda x:(not x['stsz_equals_mdat_payload'],
                               not x['span_equals_mdat_payload'],
                               -x['forward_initial_video_run'],
                               -x['backward_terminal_video_run_HYPOTHETICAL']))
    data={'tool':'wyze_bidirectional_audit.py','schema':'audit_v1','explanation':'Read-only heuristic. No reconstruction is authenticated.',
          'source_moov':{'file':str(Path(args.moov_donor).resolve()),'size':len(md),'sha256':hash_file(args.moov_donor)},
          'source_mdat':{'file':str(Path(args.mdat_donor).resolve()),'size':len(dd),'sha256':hash_file(args.mdat_donor)},
          'candidate_moov_boxes':moovs,'candidate_mdat_boxes':mdats,
          'tail_gap_assumption':args.tail_gap,'candidate_pair_results':results,'parse_errors':errors}
    (out/'audit.json').write_text(json.dumps(data,indent=2)+'\n')
    if all_rows:
        fields=list(all_rows[0])
        with (out/'samples.csv').open('w',newline='') as fp:
            w=csv.DictWriter(fp,fieldnames=fields);w.writeheader();w.writerows(all_rows)
    print('Sources SHA256:',data['source_moov']['sha256'],data['source_mdat']['sha256'])
    print('Embedded moov candidates:',[(a['start'],a['size']) for a in moovs]);
    print('Embedded mdat candidates:',[(a['start'],a['size'],a['complete']) for a in mdats])
    for i,x in enumerate(results):
        f=x['first_forward_failure'];b=x['first_reverse_failure'];s=x['first_video_sample']
        print('PAIR %d moov@%d mdat@%d stsz=%d declared=%d span=%d gaps=%d fullF=%d/%d backHYP=%d/%d allF=%d'%
              (i,x['moov_offset'],x['mdat_offset'],x['sum_all_track_sample_bytes'],
               x['mdat_declared_payload_bytes'],x['sample_extent_bytes'],x['unmapped_gap_bytes'],
               x['forward_initial_video_run'],x['video_samples'],
               x['backward_terminal_video_run_HYPOTHETICAL'],x['video_samples'],x['forward_valid_all_indices']))
        if s:print('  video[0]: orig=%d size=%d fpos=%d fstatus=%s bstatus=%s'
                   %(s['orig_offset'],s['size'],s['forward_pos'],s['forward_status'],s['backward_status']))
        if f:print('  first forward failure: VIDEO[%d] @export=%d status=%s invalidbyte=%s'
                   %(f['sample_index'],f['forward_pos'],f['forward_status'],f['forward_invalid_byte']))
        if b:print('  first backward failure: VIDEO[%d] @export=%d status=%s'
                   %(b['sample_index'],b['backward_pos'],b['backward_status']))
    print('Output:',(out/'audit.json').resolve())
    return 0 if results else 2

if __name__=='__main__':sys.exit(main())