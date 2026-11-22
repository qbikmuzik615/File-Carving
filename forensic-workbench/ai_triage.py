"""Optional explicit opt-in LLM review. No raw audiovisual data or secrets transmitted.

Use a narrowly bounded technical metadata summary. No imaginary recovered evidence.
"""
import json,os,requests
from pathlib import Path

def metadata_summary(run:Path):
 doc=json.loads((run/'job_state.json').read_text());m=doc.get('results',{})
 scores=json.loads((run/'candidate_scores.json').read_text()) if (run/'candidate_scores.json').exists() else []
 return {'pipeline':'Forensic Recovery Workbench','file_count':m.get('source_count'),
     'matching_structures':m.get('matches',{}),'candidate_scores':[
       {k:v for k,v in c.items() if k in ('candidate','bytes','triage_score','validation','h264_error_lines','streams','decode_returncode')}
       for c in scores[:20]],
     'restrictions':'No media bytes, full paths or personal data are included; missing footage is unknown.'}

def review(run:Path,provider='gemini',model=None,explicit_consent=False):
 if not explicit_consent:raise PermissionError('AI review requires deliberate user authorization')
 prompt=('You are a digital-video-forensics technical assistant. Review only the machine-measured metadata below. '
  'Return JSON with {observations:[...], next_experiments:[{test,method,acceptance_criteria}], '
  'limitations:[...], caution:[...]}. Give exact falsifiable steps. Never claim that corrupted or absent '
  'footage exists, or that anyone deleted evidence. Never infer human identities/events from metadata. '
  'Never propose hallucinating frames/audio. Include priority for SD image and reliable timestamp.\n'+
  json.dumps(metadata_summary(run),sort_keys=True)[:20000])
 if provider=='gemini':
  k=os.environ.get('GEMINI_API_KEY')
  if not k:raise RuntimeError('Set GEMINI_API_KEY in environment (never paste it in project files)')
  model=model or 'gemini-2.5-flash-lite'
  # User expressly authorizes the metadata-only network request by clicking the control.
  url=f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
  r=requests.post(url,params={'key':k},json={'contents':[{'role':'user','parts':[{'text':prompt}]}],
    'generationConfig':{'responseMimeType':'application/json','temperature':0.1}},timeout=90)
  r.raise_for_status();body=r.json();raw='\n'.join(p.get('text','') for c in body.get('candidates',[]) for p in c.get('content',{}).get('parts',[]))
 elif provider=='openai':
  k=os.environ.get('OPENAI_API_KEY')
  if not k:raise RuntimeError('Set OPENAI_API_KEY in environment')
  model=model or 'gpt-4.1-mini'
  r=requests.post('https://api.openai.com/v1/chat/completions',headers={'Authorization':f'Bearer {k}'},json={
    'model':model,'temperature':0.1,'response_format':{'type':'json_object'},'messages':[{'role':'user','content':prompt}]},timeout=90)
  r.raise_for_status();raw=r.json()['choices'][0]['message']['content']
 else:raise ValueError('provider must be gemini or openai')
 try:structured=json.loads(raw)
 except Exception:structured={'unparsed_response':raw}
 p=run/'ai_review_OPT_IN.json';p.write_text(json.dumps({'provider':provider,'model':model,'review':structured,
      'notice':'Model interpretation, not independent forensic evidence'},indent=2))
 return structured