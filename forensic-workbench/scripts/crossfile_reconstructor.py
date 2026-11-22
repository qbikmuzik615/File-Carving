#!/usr/bin/env python3
"""Wyze recovery hypothesis engine: no source modification, no invented media.

Tests whether MOV/MP4 metadata (`moov`) in one recovered file matches an
`mdat` payload beginning in another by *exact sum of stsz sample sizes*.
It also checks the first AVC sample's length prefix, identifies intrinsic
MP4 creation stamps, and can create visibly labelled partial test containers
when the original mdat is truncated or mixed with other file fragments.

This does NOT establish original recording time or reconstruct the missing
part of a card. Best used with a bit-for-bit raw card image and verified
same-device reference clips. All candidate outputs are derivatives.

Usage:
 python3 crossfile_reconstructor.py --out REPORTS /path/to/copied_mp4_files
 python3 crossfile_reconstructor.py --out REPORTS --extract /path/to/copied_mp4_files
"""
import argparse,hashlib,json,mmap,os,re,shutil,struct,subprocess
from datetime import datetime,timedelta,timezone
from pathlib import Path

ROOTTYPES={b'ftyp',b'mdat',b'moov'}
NESTED={b'moov',b'trak',b'mdia',b'minf',b'stbl',b'edts',b'dinf',b'udta',b'meta',b'ilst',b'moof',b'traf'}
VIDEO_TYPES={'avc1','avc3','hvc1','hev1'}
SUFFIXES={'.mp4','.mov','.m4v','.3gp','.dat','.bin','.raw'}

def sha256(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for x in iter(lambda:f.read(8*1024*1024),b''):h.update(x)
 return h.hexdigest()

def u32(b):return int.from_bytes(b,'big')
def u64(b):return int.from_bytes(b,'big')

def box(mm,at,end):
 if at<0 or at+8>end:return None
 n=u32(mm[at:at+4]);t=mm[at+4:at+8];head=8
 if n==1:
  if at+16>end:return None
  n=u64(mm[at+8:at+16]);head=16
 if n==0:n=end-at
 if n<head or not all(32<=v<=126 for v in t):return None
 return {'offset':at,'size':n,'type':t.decode('ascii'),'head':head,'end':at+n,'valid_extent':at+n<=end}

def children(mm,start,end,depth=0):
 if depth>12:return
 p=start
 for _ in range(100000):
  b=box(mm,p,end)
  if not b or not b['valid_extent'] or b['end']>end:break
  yield b
  if b['type'].encode() in NESTED:
   nested=p+b['head']+(4 if b['type']=='meta' else 0)
   yield from children(mm,nested,b['end'],depth+1)
  p=b['end']
  if p>=end:break

def creation_time(mm,moov):
 data=list(children(mm,moov['offset']+moov['head'],moov['end']))
 h=next((x for x in data if x['type']=='mvhd'),None)
 if not h:return None
 p=h['offset']+h['head'];version=mm[p]
 if version==1:
  if p+32>h['end']:return None
  a,b=u64(mm[p+4:p+12]),u64(mm[p+12:p+20]);ts=u32(mm[p+20:p+24]);dur=u64(mm[p+24:p+32])
 else:
  if p+20>h['end']:return None
  a,b=u32(mm[p+4:p+8]),u32(mm[p+8:p+12]);ts=u32(mm[p+12:p+16]);dur=u32(mm[p+16:p+20])
 epoch=datetime(1904,1,1,tzinfo=timezone.utc)
 def dt(v):
  try:return (epoch+timedelta(seconds=v)).isoformat()
  except OverflowError:return None
 return {'creation_datetime_as_utc':dt(a),'modification_datetime_as_utc':dt(b),'duration_seconds':round(dur/ts,3) if ts else None,'source_clock_timezone_unverified':True,'timescale':ts}

def parse_moov(mm,b):
 if not b['valid_extent'] or b['size']>5_000_000:return None
 nodes=list(children(mm,b['offset']+b['head'],b['end']))
 sizes=[];desc=[];offsets=[]
 for c in nodes:
  pos=c['offset']+c['head'];type_=c['type']
  if type_=='stsz':
   if pos+12>c['end']:return None
   default,count=u32(mm[pos+4:pos+8]),u32(mm[pos+8:pos+12]);
   if count>200_000 or (default==0 and pos+12+count*4>c['end']):return None
   total=default*count if default else sum(u32(mm[x:x+4]) for x in range(pos+12,pos+12+count*4,4))
   first=default if default else (u32(mm[pos+12:pos+16]) if count else 0)
   sizes.append({'default_sample_size':default,'sample_count':count,'first_sample_size':first,'sum_sample_bytes':total})
  if type_=='stsd' and pos+16<=c['end']:
   count=u32(mm[pos+4:pos+8]);d=pos+8
   if count and d+8<=c['end']:
    x=box(mm,d,c['end'])
    if x:desc.append(x['type'])
  if type_ in ('stco','co64') and pos+12<=c['end']:
   count=u32(mm[pos+4:pos+8]);first=u64(mm[pos+8:pos+16]) if type_=='co64' and pos+16<=c['end'] else u32(mm[pos+8:pos+12]);offsets.append({'type':type_,'count':count,'first_chunk_offset':first})
 if not sizes or len(sizes)<2:return None
 total=sum(z['sum_sample_bytes'] for z in sizes)
 if total<100_000 or total>100_000_000:return None
 dur=creation_time(mm,b)
 return {'box_offset':b['offset'],'box_size':b['size'],'total_media_sample_bytes':total,'tracks':sizes,'codec_entries':desc,'chunk_offsets':offsets,'movie_header':dur}

def scan_one(p,max_hits=300):
 found={'name':p.name,'full_path':str(p.resolve()),'size_bytes':p.stat().st_size,'sha256':sha256(p),'moov':[],'mdat':[],'ftyp':[]}
 if not p.stat().st_size:return found
 with p.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
  length=len(mm)
  for name in (b'ftyp', b'moov', b'mdat'):  # deterministic: collect ftyp anchors before mdat evidence
   pos=0;count=0
   while count<max_hits:
    at=mm.find(name,pos)
    if at<0:break
    pos=at+1;count+=1
    b=box(mm,at-4,length)
    if not b or b['type'].encode()!=name:continue
    if name==b'moov':
     d=parse_moov(mm,b)
     if d:found['moov'].append(d)
    if name==b'ftyp' and b['valid_extent'] and b['size'] in (16,20,24,28,32):found['ftyp'].append({'offset':b['offset'],'size':b['size']})
    if name==b'mdat' and b['size']>=128 and b['size']<=100_000_000:
     meta={'offset':b['offset'],'declared_size':b['size'],'declared_payload_bytes':b['size']-b['head'],'extends_beyond_current_file':not b['valid_extent']}
     ftyp=next((x for x in found['ftyp'] if x['offset']+160==b['offset']),None)
     # Detection is order-dependent, ftyp processed before mdat.
     if ftyp:
      meta['ftyp_offset']=ftyp['offset']; meta['mdat_original_relative_offset']=160
      st=b['offset']+b['head']
      if st+5<=length:
       meta['first_prefix_be32']=u32(mm[st:st+4]);meta['first_nal_type']=mm[st+4]&31
     found['mdat'].append(meta)
 return found

def make_derivative(src,moovsrc,mdata,mdata_record,moov,output):
 srco=mdata_record.get('ftyp_offset');mdato=mdata_record['offset']
 if srco is None:raise ValueError('No nearby ftyp')
 with src.open('rb') as sf,moovsrc.open('rb') as mf:
  sf.seek(srco); prefix=sf.read(160)
  if len(prefix)!=160 or prefix[4:8]!=b'ftyp' or prefix[28:32]!=b'free':raise ValueError('Unexpected header layout')
  # Use contiguous bytes only; stop before the next independently validated ftyp.
  first=mdato+8;remaining=src.stat().st_size-first
  with src.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
   pos=first;boundary=src.stat().st_size
   while True:
    at=mm.find(b'ftyp',pos)
    if at<0:break
    candidate=box(mm,at-4,len(mm))
    if candidate and candidate['type']=='ftyp' and candidate['size']==24 and candidate['valid_extent']:
     boundary=at-4;break
    pos=at+1
  contiguous=max(0,min(remaining,boundary-first,mdata_record['declared_payload_bytes']))
  if contiguous<=0:raise ValueError('No mdat payload bytes available')
  if contiguous+8 >=2**32:raise ValueError('Requires 64-bit size')
  mf.seek(moov['box_offset']);moov_bytes=mf.read(moov['box_size'])
  if len(moov_bytes)!=moov['box_size']:raise ValueError('Incomplete moov')
  # Guard source hash remains externally auditable; do not modify input.
  with output.open('xb') as dest:
   dest.write(prefix);dest.write(struct.pack('>I',contiguous+8)+b'mdat')
   sf.seek(first)
   for _ in range((contiguous+1024*1024-1)//(1024*1024)):
    chunk=sf.read(min(1024*1024,contiguous-(dest.tell()-168)))
    if not chunk:break
    dest.write(chunk)
   dest.write(moov_bytes)
 return {'source_mdat_offset':mdato,'source_ftyp_offset':srco,'source_moov_offset':moov['box_offset'],
  'source_mdat_declared_payload_bytes':mdata_record['declared_payload_bytes'],
  'contiguous_payload_bytes_available':contiguous,'bytes_missing_vs_declaration':max(0,mdata_record['declared_payload_bytes']-contiguous),
  'patched_four_bytes':'mdat.size (little intervention solely to make truncated candidate parseable)',
  'media_bytes_all_original':True,'missing_bytes_not_fabricated':True,'derivative_sha256':sha256(output)}

def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('inputs',nargs='+',help='Recovered MP4 file(s) and/or directory')
 ap.add_argument('--out',required=True)
 ap.add_argument('--extract',action='store_true',help='Create partial hypothesis MP4 files (never overwrite evidence)')
 ap.add_argument('--limit-matches',type=int,default=100)
 arg=ap.parse_args();out=Path(arg.out).resolve();inputs=[]
 for x in arg.inputs:
  p=Path(x).resolve();inputs.extend(p.rglob('*') if p.is_dir() else [p])
 files=sorted({f for f in inputs if f.is_file() and f.suffix.lower() in SUFFIXES})
 if not files:ap.error('No input files found')
 for f in files:
  if f==out or out in f.parents:ap.error('Output overlaps source')
 out.mkdir(exist_ok=True,parents=True)
 catalog=[scan_one(f) for f in files]
 # Only compare exact numeric content totals, not superficially identical codecs.
 matches=[]
 for ix,a in enumerate(catalog):
  for m in a['moov']:
   for j,b in enumerate(catalog):
    for d in b['mdat']:
     if m['total_media_sample_bytes']!=d['declared_payload_bytes']:continue
     v=next((t for t in m['tracks'] if t['default_sample_size']==0),None)
     framecheck=bool(v and d.get('first_prefix_be32') is not None and v['first_sample_size']>=4 and v['first_sample_size']-4==d['first_prefix_be32'] and d.get('first_nal_type') in (1,5))
     matches.append({'moov_filename':a['name'],'moov_source_sha256':a['sha256'],'moov_offset':m['box_offset'],'moov_size':m['box_size'],'mdat_filename':b['name'],'mdat_source_sha256':b['sha256'],'mdat_offset':d['offset'],'mdat_declared_payload_bytes':d['declared_payload_bytes'],'exact_sample_byte_match':True,'first_h264_sample_length_and_nal_match':framecheck,'recorded_movie_time':m['movie_header'],'codec_entries':m['codec_entries'],'moov_input_index':ix,'mdat_input_index':j})
 matches.sort(key=lambda x:(not x['first_h264_sample_length_and_nal_match'],x['moov_filename'],x['mdat_filename']))
 if arg.extract:
  cdir=out/'derived_partial_candidates';cdir.mkdir(exist_ok=True)
  for k,m in enumerate(matches[:arg.limit_matches]):
   a=catalog[m['moov_input_index']];b=catalog[m['mdat_input_index']];origmoov=next(x for x in a['moov'] if x['box_offset']==m['moov_offset']);origmdat=next(x for x in b['mdat'] if x['offset']==m['mdat_offset']);
   if 'ftyp_offset' not in origmdat:continue
   name=f'{k:03d}_mdat_{b["name"].replace(".","_")}_{m["mdat_offset"]}_moov_{a["name"].replace(".","_")}_{m["moov_offset"]}_PARTIAL.mp4'
   candidate=cdir/name
   try:
    result=make_derivative(Path(b['full_path']),Path(a['full_path']),b,origmdat,origmoov,candidate)
    m['test_derivative']=name;m['test_provenance']=result
    if shutil.which('ffprobe'):
     p=subprocess.run(['ffprobe','-v','error','-show_error','-show_format','-show_streams','-of','json',str(candidate)],capture_output=True,text=True,timeout=30)
     m['test_ffprobe_returncode']=p.returncode
     (candidate.with_suffix('.ffprobe.json')).write_text(p.stdout)
     (candidate.with_suffix('.ffprobe.stderr')).write_text(p.stderr)
   except Exception as e:m['extract_error']=str(e)
 (out/'crossfile_moov_mdat_matches.json').write_text(json.dumps(matches,indent=2,ensure_ascii=False))
 (out/'all_embedded_structures.json').write_text(json.dumps(catalog,indent=2,ensure_ascii=False))
 summary={'input_count':len(files),'moov_count':sum(len(x['moov']) for x in catalog),'mdat_count':sum(len(x['mdat']) for x in catalog),'exact_content_matches':len(matches),'double_verified_avc_first_sample':sum(x['first_h264_sample_length_and_nal_match'] for x in matches),'warning':'MP4 creation stamps may be camera-local time despite 1904 epoch UTC encoding; metadata may belong to a different recording than the enclosing recovered filename. Decoding and visual authentication remain separate tests.'}
 (out/'SUMMARY.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
 for m in matches: print(m['moov_filename'],m['moov_offset'],'->',m['mdat_filename'],m['mdat_offset'],'bytes',m['mdat_declared_payload_bytes'],'AVC first',m['first_h264_sample_length_and_nal_match'])
if __name__=='__main__':main()