#!/usr/bin/env python3
"""Reproducible, multi-profile FFmpeg hypothesis tests of recovered VIDEO/AUDIO.

Not a source recovery algorithm. Profiles intentionally alter handling of malformed
container bytes; ALL outputs are derivative and unauthenticated.
"""
from __future__ import annotations
import argparse,hashlib,json,re,shutil,subprocess
from pathlib import Path
from datetime import datetime,timezone

def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()

def profile_cmd(profile,source,output,seconds):
 base=['ffmpeg','-nostdin','-hide_banner','-loglevel','warning','-y']
 if profile=='strict':return base+['-xerror','-err_detect','explode','-i',str(source),'-map','0:v:0?','-an','-t',str(seconds),'-f','null','-']
 if profile=='tolerant':return base+['-err_detect','ignore_err','-fflags','+genpts+discardcorrupt','-i',str(source),'-map','0:v:0?','-an','-t',str(seconds),'-f','null','-']
 if profile=='keyframes':return base+['-skip_frame','nokey','-i',str(source),'-map','0:v:0?','-an','-t',str(seconds),'-f','null','-']
 if profile=='audio_wav':return base+['-err_detect','ignore_err','-i',str(source),'-map','0:a:0?','-vn','-t',str(seconds),'-ar','8000','-ac','1','-c:a','pcm_s16le',str(output)]
 if profile=='annexb':return base+['-i',str(source),'-map','0:v:0?','-an','-c:v','copy','-bsf:v','h264_mp4toannexb',str(output)]
 if profile=='remux':return base+['-fflags','+genpts','-err_detect','ignore_err','-i',str(source),'-map','0','-c','copy','-t',str(seconds),str(output)]
 raise ValueError(profile)

def run(candidates:Path,out:Path,seconds=15,max_candidates=20):
 if not shutil.which('ffmpeg'):raise RuntimeError('ffmpeg not installed')
 if out==candidates or candidates in out.parents:raise ValueError('Outputs must not be under input folder')
 out.mkdir(parents=True,exist_ok=True)
 profiles=['strict','tolerant','keyframes','audio_wav','annexb','remux']
 recs=[]
 for src in sorted(p for p in candidates.rglob('*.mp4') if p.is_file())[:max_candidates]:
  stem=re.sub('[^a-zA-Z0-9_-]+','_',src.stem)
  for profile in profiles:
   f=out/(stem+'__'+profile+{'audio_wav':'.wav','annexb':'.h264','remux':'.mp4'}.get(profile,'.log'))
   cmd=profile_cmd(profile,src,f,seconds)
   try:
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=45,check=False)
    errors=[x for x in p.stderr.splitlines() if re.search(r'invalid|corrupt|error|missing|conceal|unspec',x,re.I)]
    rec={'source':src.name,'source_sha256':digest(src),'profile':profile,'command':cmd,
         'exit_code':p.returncode,'diagnostic_error_lines':len(errors),'error_excerpt':'\n'.join(errors[-15:])[-5000:],
         'output':f.name if f.is_file() else None,'output_bytes':f.stat().st_size if f.is_file() else None,
         'output_sha256':digest(f) if f.is_file() else None,'non_original_derivative':True,'not_authenticated':True}
   except Exception as e:rec={'source':src.name,'profile':profile,'error':str(e),'not_authenticated':True}
   recs.append(rec)
 with (out/'experiment_matrix.json').open('w') as f:json.dump(recs,f,indent=2)
 summary={'utc':datetime.now(timezone.utc).isoformat(),'input_candidates':len(set(x['source'] for x in recs)),
   'experiment_count':len(recs),'by_profile':{},'warning':'No experiment proves source authenticity; tolerant decoding is not evidence of real missing frames.'}
 for p in profiles:
  subset=[x for x in recs if x['profile']==p]
  summary['by_profile'][p]={'ran':len(subset),'exit_clean':sum(x.get('exit_code')==0 for x in subset),'derivative_files_created':sum(bool(x.get('output')) for x in subset)}
 (out/'SUMMARY.json').write_text(json.dumps(summary,indent=2));return summary

if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('candidates');a.add_argument('--out',required=True);a.add_argument('--seconds',type=int,default=15);a.add_argument('--max-candidates',type=int,default=20)
 o=a.parse_args();print(json.dumps(run(Path(o.candidates).resolve(),Path(o.out).resolve(),o.seconds,o.max_candidates),indent=2))