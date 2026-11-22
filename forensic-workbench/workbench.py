#!/usr/bin/env python3
"""Forensic Recovery Workbench — deterministic local-first orchestrator.

Source evidence is never written, opened for modification or committed to a repository.
This tool does not infer footage which is not present in source bytes.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, os, re, shutil, subprocess, sys, threading, time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

ROOT=Path(__file__).resolve().parent
EXTENSIONS={'.mp4','.mov','.m4v','.h264','.264','.avi','.mts','.m2ts','.mkv'}
TIMEOUT=210

def now():return datetime.now(timezone.utc).isoformat()
def sha256(path:Path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def invoke(argv:list[str],stdout_path:Path,timeout=TIMEOUT)->dict:
 try:
  with stdout_path.open('w',encoding='utf8',errors='replace') as log:
   p=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,
                    timeout=timeout,check=False,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
  return {'argv':argv,'returncode':p.returncode,'log':stdout_path.name}
 except (OSError,subprocess.TimeoutExpired) as e:
  with stdout_path.open('a',encoding='utf8') as f:f.write('\nERROR: '+str(e)+'\n')
  return {'argv':argv,'returncode':None,'error':str(e),'log':stdout_path.name}

def sources(path:Path):
 if path.is_file():return [path]
 return sorted(f for f in path.rglob('*') if f.is_file() and f.suffix.lower() in EXTENSIONS)

def parse_datetime(label:str):
 try:return datetime.strptime(label,'%Y-%m-%d')
 except Exception:return None

def rank_candidate(filename:Path,limit_sec=90)->dict:
 """Decode and score content integrity: not a judgment of footage authenticity.

 No FFmpeg error-concealment or AI interpolation is used. Includes raw error counts.
 """
 score={'candidate':filename.name,'source_sha256':sha256(filename),'bytes':filename.stat().st_size,
        'non_authentic_derivative':True,'assurance':'NOT AUTHENTICATED'}
 if not shutil.which('ffprobe') or not shutil.which('ffmpeg'):
  score['status']='skipped: ffprobe/ffmpeg unavailable';return score
 try:
  p=subprocess.run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(filename)],
     capture_output=True,text=True,timeout=25,check=False)
  score['ffprobe_returncode']=p.returncode
  if p.returncode==0:
   detail=json.loads(p.stdout);score['streams']=[{'codec_type':s.get('codec_type'),'codec_name':s.get('codec_name'),
     'width':s.get('width'),'height':s.get('height'),'duration':s.get('duration')} for s in detail.get('streams',[])]
 except Exception as e:score['ffprobe_error']=str(e)
 try:
  q=subprocess.run(['ffmpeg','-nostdin','-hide_banner','-v','warning','-xerror','-i',str(filename),
    '-map','0:v:0?','-an','-t',str(limit_sec),'-f','null','-'],capture_output=True,text=True,timeout=50,check=False)
  logs=q.stderr[-30000:];score['decode_returncode']=q.returncode;score['decode_message_excerpt']=logs[-2000:]
  score['h264_error_lines']=sum(bool(re.search(r'error|corrupt|invalid|missing|conceal|unspecified',ln,re.I)) for ln in logs.splitlines())
  score['validation']='decoder_pass' if q.returncode==0 and score['h264_error_lines']==0 else 'decoding_errors'
 except Exception as e:score['decode_error']=str(e);score['validation']='not_checked'
 # This is hypothesis prioritization only. High rank does not prove source time or identity.
 score['triage_score']=max(0,100-(35 if score.get('ffprobe_returncode')!=0 else 0)
   -(45 if score.get('decode_returncode')!=0 else 0)-min(20,score.get('h264_error_lines',0)))
 return score

@dataclass
class Job:
 id:str
 source:str
 output:str
 status:str='queued'
 started:str|None=None
 finished:str|None=None
 step:str='waiting'
 history:list=field(default_factory=list)
 error:str|None=None
 results:dict=field(default_factory=dict)
 def view(self):return vars(self).copy()

class Engine:
 def __init__(self):self.jobs:dict[str,Job]={};self.lock=threading.Lock()
 def create(self,source:str,output:str,target_date='2022-06-21',before=30,after=30,disk_image=None,extract=True):
  s=Path(source).expanduser().resolve(strict=True)
  if not (s.is_file() or s.is_dir()):raise ValueError('Source must be file or directory')
  output_path=Path(output).expanduser().resolve()
  if output_path==s or (s.is_dir() and s in output_path.parents):raise ValueError('Reports must be outside the source evidence tree')
  if (s.is_dir() and output_path in s.parents):raise ValueError('Source is inside reports folder')
  stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
  # No user-controlled path traversal in the unique job name.
  jobid=f'wb-{stamp}'
  report=output_path/jobid
  image=Path(disk_image).expanduser().resolve(strict=True) if disk_image else None
  if image and (not image.is_file() or image in [s,report]):raise ValueError('Disk image must be a separate readable file')
  j=Job(jobid,str(s),str(report))
  with self.lock:self.jobs[jobid]=j
  params={'target_date':target_date,'before':max(0,min(365,before)),'after':max(0,min(365,after)),
          'disk_image':str(image) if image else None,'extract':bool(extract)}
  th=threading.Thread(target=self._run,args=(j,params),daemon=True);th.start();return j
 def _run(self,j:Job,opts:dict):
  try:self._analyze(j,opts)
  except Exception as e:
   j.status='failed';j.error=f'{type(e).__name__}: {e}';j.finished=now()
   try:(Path(j.output)/'job_state.json').write_text(json.dumps(j.view(),indent=2,default=str))
   except Exception:pass
 def _mark(self,j,name,details=None):
  j.step=name;j.history.append({'time_utc':now(),'stage':name,'details':details or {}})
  (Path(j.output)/'job_state.json').write_text(json.dumps(j.view(),indent=2,default=str))
 def _analyze(self,j:Job,o:dict):
  j.started=now();j.status='running';dest=Path(j.output);dest.mkdir(parents=True,exist_ok=False)
  src=Path(j.source);files=sources(src)
  self._mark(j,'01_acquisition_manifest',{'number_of_source_files':len(files)})
  if not files:raise ValueError('No supported media files found')
  evidence=[]
  for f in files:
   st=f.stat(); evidence.append({'source_path':str(f),'path_relative_to_source':str(f.relative_to(src)) if src.is_dir() else f.name,
     'sha256':sha256(f),'bytes':st.st_size,'filesystem_mtime_utc':datetime.fromtimestamp(st.st_mtime,timezone.utc).isoformat(),
     'filesystem_mtime_is_not_camera_recording_time':True})
  (dest/'source_manifest.json').write_text(json.dumps({'created_utc':now(),'originals_read_only':True,'files':evidence},indent=2))
  j.results['source_count']=len(files);j.results['total_source_bytes']=sum(x['bytes'] for x in evidence)
  (dest/'logs').mkdir()
  self._mark(j,'02_full_binary_metadata')
  r=invoke([sys.executable,str(ROOT/'scripts/forensic_metadata.py'),str(src),'--out',str(dest/'metadata')],dest/'logs/02_metadata.log',timeout=max(210,len(files)*25))
  if r['returncode']!=0:raise RuntimeError('Metadata stage failed; inspect '+r['log'])
  self._mark(j,'03_moov_mdat_cross_matching')
  cmd=[sys.executable,str(ROOT/'scripts/crossfile_reconstructor.py'),str(src),'--out',str(dest/'reconstruction')]
  if o['extract']:cmd.append('--extract')
  r=invoke(cmd,dest/'logs/03_crossmatching.log',timeout=max(210,len(files)*25))
  if r['returncode']!=0:raise RuntimeError('Cross-file stage failed; inspect '+r['log'])
  summary=json.loads((dest/'reconstruction/SUMMARY.json').read_text());j.results['matches']=summary
  self._mark(j,'04_candidate_decoder_validation')
  derivatives=sorted((dest/'reconstruction/derived_partial_candidates').glob('*.mp4')) if (dest/'reconstruction/derived_partial_candidates').exists() else []
  quality=[rank_candidate(p) for p in derivatives]
  quality.sort(key=lambda x:-x.get('triage_score',0));(dest/'candidate_scores.json').write_text(json.dumps(quality,indent=2))
  j.results['candidate_count']=len(quality);j.results['candidate_decoder_passes']=sum(x.get('validation')=='decoder_pass' for x in quality)
  self._mark(j,'05_surrounding_date_inventory')
  if src.is_dir() or src.suffix.lower()=='.zip':
   invoke([sys.executable,str(ROOT/'scripts/sdcard_timeline.py'),str(src),'--out',str(dest/'timeline'),
     '--target-date',o['target_date'],'--days-before',str(o['before']),'--days-after',str(o['after'])],dest/'logs/05_timeline.log',timeout=210)
   timeline_path=dest/'timeline/summary.json'
   if timeline_path.exists():j.results['timeline']=json.loads(timeline_path.read_text())
  if o['disk_image']:
   self._mark(j,'06_sector_image_signature_carving')
   invoke([sys.executable,str(ROOT/'scripts/image_scan.py'),o['disk_image'],'--out',str(dest/'image_scan'),
       '--extract','--limit',str(40)],dest/'logs/06_image_scan.log',timeout=2400)
   summary_image=dest/'image_scan/summary.json'
   if summary_image.exists():j.results['image']=json.loads(summary_image.read_text())
  self._mark(j,'07_source_integrity_recheck')
  changes=[str(f) for f,rec in zip(files,evidence) if sha256(f)!=rec['sha256']]
  j.results['source_hash_changed']=changes
  if changes:raise RuntimeError('Source changed while analysis was running: '+str(changes))
  self._mark(j,'08_report_generation')
  (dest/'REPORT.md').write_text(report_md(j,quality,opts=o),encoding='utf8')
  j.status='completed';j.finished=now();self._mark(j,'complete')

def report_md(j:Job,quality:list,opts:dict)->str:
 return '\n'.join([
 '# Forensic Recovery Workbench — Run Report','',
 f'**Run:** `{j.id}`',f'**Source:** `{j.source}`',f'**UTC start:** {j.started}',
 f'**Files:** {j.results.get("source_count")}, total bytes {j.results.get("total_source_bytes")}',
 f'**Matching structures:** {j.results.get("matches",{}).get("exact_content_matches")}',
 f'**Cross-file candidates:** {len(quality)}',
 f'**Decoder-clean candidates:** {sum(x.get("validation")=="decoder_pass" for x in quality)}',
 f'**Source hash changed:** {j.results.get("source_hash_changed",[])}','',
 '## Interpretation','',
 'These results are preliminary structural and decoding hypotheses, **not authenticated video**.',
 'Timestamp paths, MP4 creation fields, and file modification metadata must be independently corroborated.',
 'A high hypothesis score does not imply the footage depicts the target time or event.','',
 '## Workflow and complete reproducibility','',
 'See source_manifest.json, metadata/manifest.json, reconstruction/all_embedded_structures.json,',
 'reconstruction/crossfile_moov_mdat_matches.json, candidate_scores.json and logs/.','',
 '## Constraints','',
 'Absent unallocated image sectors cannot be recovered from copied file bytes.',
 'Do not perform AI video interpolation or synthetic speech as forensic reconstruction.',
 'Tools only operate on local files. No model invocation or network transfer is performed by a normal analysis run.',
 '',f'**Options:** `{json.dumps(opts)}`',''])

def main():
 a=argparse.ArgumentParser(description=__doc__)
 a.add_argument('--source',required=True,help='Read-only evidence directory, MP4 file or ZIP for timeline (use directory for media)')
 a.add_argument('--output',default=str(Path.home()/'ForensicWorkbenchReports'))
 a.add_argument('--disk-image',help='Optional RAW/DD/IMG sector image. SHA and scan; no writes')
 a.add_argument('--target-date',default='2022-06-21');a.add_argument('--days-before',type=int,default=30);a.add_argument('--days-after',type=int,default=30)
 a.add_argument('--no-extract',action='store_true')
 p=a.parse_args(); e=Engine();job=e.create(p.source,p.output,p.target_date,p.days_before,p.days_after,p.disk_image,not p.no_extract)
 print('Job ID:',job.id,'Output:',job.output,flush=True)
 while job.status in ('queued','running'):
  print('STAGE:',job.step,flush=True);time.sleep(1)
 print('Status:',job.status,'Summary:',json.dumps(job.results,indent=2),flush=True)
 if job.error:print('ERROR:',job.error,file=sys.stderr)
 return 0 if job.status=='completed' else 1
if __name__=='__main__':sys.exit(main())