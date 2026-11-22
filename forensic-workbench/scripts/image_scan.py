#!/usr/bin/env python3
"""Read-only bounded physical-image MP4 signature scanner + cautious sector carving.

Candidates are labelled partial/unverified. Does not reassemble fragmented FAT chains.
"""
import argparse,hashlib,json,os,struct,subprocess,shutil
from pathlib import Path
from datetime import datetime,timezone
SIGS={b'ftyp',b'moov',b'mdat',b'free',b'moof'}
def digest(f):
 h=hashlib.sha256()
 with f.open('rb') as inp:
  for b in iter(lambda:inp.read(8<<20),b''):h.update(b)
 return h.hexdigest()
def scan(p:Path,limit=100000,step=4<<20):
 seen=set();count=0;carry=b''
 with p.open('rb') as f:
  while True:
   block=f.read(step)
   if not block:break
   start=f.tell()-len(block);chunk=carry+block;base=start-len(carry)
   for token in SIGS:
    pos=0
    while count<limit:
     j=chunk.find(token,pos)
     if j<0:break
     pos=j+1;offset=base+j-4
     if offset<0 or offset in seen or j<4:continue
     size=struct.unpack('>I',chunk[j-4:j])[0]
     if not(8<=size<=256*1024*1024):continue
     # Reject unlikely container sizes; address is physical offset in source image.
     seen.add(offset);count+=1
     yield {'offset':offset,'type':token.decode(),'declared_size':size,'aligned_to_512':offset%512==0,
            'aligned_to_16384':offset%16384==0,'box_end':offset+size,'image_contiguity_not_verified':True}
   carry=chunk[-64:]

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('image');p.add_argument('--out',required=True);p.add_argument('--limit',type=int,default=1000);p.add_argument('--extract',action='store_true');p.add_argument('--max-bytes-per-carve',type=int,default=16*1024*1024)
 a=p.parse_args();image=Path(a.image).resolve(strict=True);out=Path(a.out).resolve()
 if out==image or image in out.parents: p.error('Output path must differ from image')
 out.mkdir(parents=True,exist_ok=True)
 fullhash=digest(image)
 hits=sorted(scan(image,max(40000,a.limit*200)),key=lambda x:x['offset'])
 (out/'signature_offsets.json').write_text(json.dumps(hits,indent=2))
 candidates=[]
 if a.extract:
  candidate_dir=out/'UNVERIFIED_carved_fragments';candidate_dir.mkdir(exist_ok=True)
  for j,h in enumerate(x for x in hits if x['type']=='ftyp'):
   if len(candidates)>=a.limit:break
   # Carve bounded contiguous bytes only; not an authenticated movie or complete clip.
   next_ftyp=next((z['offset'] for z in hits if z['type']=='ftyp' and z['offset']>h['offset']),image.stat().st_size)
   n=min(a.max_bytes_per_carve,next_ftyp-h['offset'],image.stat().st_size-h['offset'])
   if n<64:continue
   path=candidate_dir/f'UNVERIFIED_phys_{h["offset"]:012x}.bin'
   with image.open('rb') as raw,path.open('xb') as o:
    raw.seek(h['offset']);left=n
    while left>0:
     b=raw.read(min(left,4<<20))
     if not b:break
     o.write(b);left-=len(b)
   candidates.append({'offset':h['offset'],'bytes_copied':n,'filename':str(path.name),'sha256':digest(path),
     'partial_unverified':True,'source_image_sha256':fullhash,'cannot_presume_fat_cluster_contiguity':True})
 (out/'carve_manifest.json').write_text(json.dumps(candidates,indent=2))
 info={'utc':datetime.now(timezone.utc).isoformat(),'source':str(image),'image_sha256':fullhash,'image_size_bytes':image.stat().st_size,
       'signature_count':len(hits),'ftyp_count':sum(x['type']=='ftyp' for x in hits),
       'carve_count':len(candidates),'warning':'Raw signatures do not prove clip validity. Deleted FAT/exFAT cluster chains may be non-contiguous.'}
 (out/'summary.json').write_text(json.dumps(info,indent=2));print(json.dumps(info,indent=2))
 if shutil.which('mmls'):
  q=subprocess.run(['mmls',str(image)],capture_output=True,text=True,timeout=45)
  (out/'mmls_partition_map.txt').write_text(q.stdout+'\n'+q.stderr)
 if shutil.which('fsstat'):
  q=subprocess.run(['fsstat',str(image)],capture_output=True,text=True,timeout=45)
  (out/'fsstat_filesystem.txt').write_text(q.stdout+'\n'+q.stderr)
if __name__=='__main__':main()