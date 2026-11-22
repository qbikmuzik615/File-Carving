#!/usr/bin/env python3
"""Local browser interface for forensic workbench; localhost by default."""
from __future__ import annotations
import json,os,threading,zipfile
from datetime import datetime,timezone
from pathlib import Path
from fastapi import FastAPI,HTTPException,Query
from fastapi.responses import HTMLResponse,JSONResponse,FileResponse
from pydantic import BaseModel,Field
from workbench import Engine
from ai_triage import review

app=FastAPI(title='Forensic Recovery Workbench',version='0.2.0',docs_url='/api/docs')
ENGINE=Engine()
REPORTS=Path(os.getenv('FORENSIC_REPORTS',str(Path.home()/'ForensicWorkbenchReports'))).expanduser().resolve()
REPORTS.mkdir(parents=True,exist_ok=True)

class StartRequest(BaseModel):
 source:str=Field(min_length=1)
 target_date:str='2022-06-21'
 days_before:int=Field(30,ge=0,le=365)
 days_after:int=Field(30,ge=0,le=365)
 disk_image:str|None=None
 extract:bool=True

class AIRequest(BaseModel):
 provider:str='gemini'
 model:str|None=None
 confirm_metadata_only_upload:bool=False

def path_for(job_id:str)->Path:
 if not job_id.startswith('wb-') or not job_id[3:].replace('T','').replace('Z','').isdigit():
  raise HTTPException(400,'Invalid run ID')
 d=(REPORTS/job_id).resolve()
 if REPORTS not in d.parents:raise HTTPException(403,'Invalid path')
 if not d.is_dir():raise HTTPException(404,'Run not found')
 return d

@app.get('/',response_class=HTMLResponse)
def page():return (Path(__file__).parent/'static/index.html').read_text(encoding='utf8')

@app.get('/api/status')
def status():return {'status':'ready','reports_root':str(REPORTS),'local_only':True,
 'tools':{a:bool(__import__('shutil').which(a)) for a in ('ffmpeg','ffprobe','mediainfo','mediaconch','exiftool','mp4dump','MP4Box','mmls','fsstat','photorec')},
 'ai_key_available':{'gemini':bool(os.getenv('GEMINI_API_KEY')),'openai':bool(os.getenv('OPENAI_API_KEY'))}}

@app.post('/api/runs')
def create(p:StartRequest):
 try:
  datetime.fromisoformat(p.target_date)
  j=ENGINE.create(p.source,str(REPORTS),p.target_date,p.days_before,p.days_after,p.disk_image,p.extract)
  return j.view()
 except Exception as e:raise HTTPException(400,str(e)) from e

@app.get('/api/runs')
def runs():
 disk=[]
 for p in sorted(REPORTS.glob('wb-*/job_state.json'),reverse=True)[:50]:
  try:disk.append(json.loads(p.read_text()))
  except Exception:pass
 return disk

@app.get('/api/runs/{job_id}')
def run_detail(job_id:str):
 if job_id in ENGINE.jobs:return ENGINE.jobs[job_id].view()
 p=path_for(job_id)/'job_state.json'
 if not p.exists():raise HTTPException(404,'Run not found')
 return json.loads(p.read_text())

@app.get('/api/runs/{job_id}/files')
def file_manifest(job_id:str):
 p=path_for(job_id)/'source_manifest.json'
 if not p.exists():raise HTTPException(404,'Not ready')
 return json.loads(p.read_text())

@app.get('/api/runs/{job_id}/candidates')
def candidate_scores(job_id:str):
 p=path_for(job_id)/'candidate_scores.json'
 return json.loads(p.read_text()) if p.exists() else []

@app.get('/api/runs/{job_id}/matches')
def matches(job_id:str):
 p=path_for(job_id)/'reconstruction/crossfile_moov_mdat_matches.json'
 return json.loads(p.read_text()) if p.exists() else []

@app.get('/api/runs/{job_id}/report')
def report(job_id:str):
 p=path_for(job_id)/'REPORT.md'
 if not p.exists():raise HTTPException(404,'Not ready')
 return {'markdown':p.read_text()}

@app.post('/api/runs/{job_id}/ai')
def ai(job_id:str,p:AIRequest):
 if not p.confirm_metadata_only_upload:raise HTTPException(400,'Confirm consent to upload METADATA ONLY')
 root=path_for(job_id)
 try:return review(root,p.provider,p.model,True)
 except Exception as e:raise HTTPException(400,str(e)) from e

@app.get('/api/runs/{job_id}/download')
def download(job_id:str):
 root=path_for(job_id)
 if not (root/'REPORT.md').exists():raise HTTPException(404,'Run not complete')
 p=root/'analysis_report.zip'
 if not p.exists():
  with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
   for f in sorted(root.rglob('*')):
    if f.is_file() and f!=p and not f.name.endswith('.mp4') and not f.name.endswith('.bin') and f.stat().st_size<35_000_000:
     z.write(f,f.relative_to(root))
 return FileResponse(p,filename=f'{job_id}_forensic_reports.zip',media_type='application/zip')

if __name__=='__main__':
 import uvicorn
 uvicorn.run(app,host=os.getenv('FORENSIC_HOST','127.0.0.1'),port=int(os.getenv('FORENSIC_PORT','8765')))