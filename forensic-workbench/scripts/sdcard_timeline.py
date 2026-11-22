#!/usr/bin/env python3
"""Read-only Wyze microSD recording tree / ZIP inventory for dates around incident.

Does NOT modify files, recover deleted sectors, or presume missing minute means tampering.
Use --days-before 30 --days-after 30 to inspect an approximately 61-day window.
Usage: python3 sdcard_timeline.py --out /separate/output --target-date 2022-06-21 /source/card_copy
Optional input: ZIP file holding record/YYYYMMDD/HH/MM.mp4, no extraction required.
"""
import argparse,csv,datetime,hashlib,json,re,sys,zipfile
from collections import defaultdict
from pathlib import Path,PurePosixPath

PAT=re.compile(r'(?i)(?:^|/)(?:record/)?(20\d{6})/(\d\d)/(\d\d)\.mp4$')

def entries(path):
    if path.is_dir():
        for f in path.rglob('*'):
            if f.is_file():
                try: yield f.relative_to(path).as_posix(),f.stat().st_size,str(f), 'filesystem copy'
                except OSError:continue
    elif path.is_file() and zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as a:
            for info in a.infolist():
                if not info.is_dir(): yield info.filename,info.file_size,f'{path}::{info.filename}', 'zip entry'
    elif path.is_file(): yield path.name,path.stat().st_size,str(path), 'single file'

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('sources',nargs='+')
    ap.add_argument('--out',required=True)
    ap.add_argument('--target-date',default='2022-06-21')
    ap.add_argument('--days-before',type=int,default=30)
    ap.add_argument('--days-after',type=int,default=30)
    args=ap.parse_args()
    out=Path(args.out).resolve()
    for src in args.sources:
        p=Path(src).resolve()
        if p.is_dir() and (out==p or p in out.parents):ap.error('Output cannot be under a scanned source directory')
    out.mkdir(parents=True,exist_ok=True)
    date=datetime.date.fromisoformat(args.target_date)
    rows=[];unrecognized=[];seen_keys=defaultdict(list)
    for source in args.sources:
        p=Path(source).resolve()
        for rel,sz,locator,typ in entries(p):
            match=PAT.search(rel.replace('\\','/'))
            if match:
                datestr,hh,mm=match.groups()
                try:dt=datetime.datetime.strptime(datestr,'%Y%m%d').date()
                except ValueError:continue
                h=int(hh);m=int(mm)
                if not 0<=h<=23 or not 0<=m<=59:continue
                if not(date-datetime.timedelta(days=args.days_before)<=dt<=date+datetime.timedelta(days=args.days_after)):continue
                r={'recorded_date_from_path':str(dt),'hour_from_path':f'{h:02d}','minute_from_path':f'{m:02d}',
                   'relative_path':rel,'bytes':sz,'locator':locator,'source_name':str(p),'source_type':typ}
                rows.append(r);seen_keys[(dt,h,m)].append(r)
            elif len(unrecognized)<2000:unrecognized.append({'path':rel,'bytes':sz,'source':str(p)})
    rows.sort(key=lambda r:(r['recorded_date_from_path'],r['hour_from_path'],r['minute_from_path'],r['locator']))
    fields=['recorded_date_from_path','hour_from_path','minute_from_path','relative_path','bytes','locator','source_name','source_type']
    with (out/'card_clip_catalog.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    counts=defaultdict(lambda:{'files':0,'bytes':0,'minutes':set(),'hours':set()})
    for r in rows:
        item=counts[r['recorded_date_from_path']];item['files']+=1;item['bytes']+=r['bytes'];item['minutes'].add((r['hour_from_path'],r['minute_from_path']));item['hours'].add(r['hour_from_path'])
    daily=[]
    for d in (date+datetime.timedelta(days=x) for x in range(-args.days_before,args.days_after+1)):
        z=counts[str(d)];daily.append({'date':str(d),'present':bool(z['files']),'clips_count':z['files'],
            'unique_minutes':len(z['minutes']),'hours_observed':','.join(sorted(z['hours'])),'total_bytes':z['bytes']})
    with (out/'daily_coverage.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(daily[0]));w.writeheader();w.writerows(daily)
    dup=[{'date':str(dt),'hour':h,'minute':m,'count':len(recs),'paths':[r['locator'] for r in recs]} for (dt,h,m),recs in seen_keys.items() if len(recs)>1]
    (out/'duplicate_minute_paths.json').write_text(json.dumps(dup,indent=2))
    (out/'nonstandard_paths_sample.json').write_text(json.dumps(unrecognized,indent=2))
    (out/'summary.json').write_text(json.dumps({'target_date':str(date),'days_before':args.days_before,'days_after':args.days_after,
        'source_paths':args.sources,'number_matched':len(rows),'days_with_video':sum(bool(v['files']) for v in counts.values()),
        'days_with_video_actual':sorted(k for k,v in counts.items() if v['files']),
        'duplicate_minute_slots':len(dup),'notes':['Filenames only; not proof of recording time',
        'Missing minutes may reflect motion-only mode, camera downtime, overwritten circular buffer, erased data, or incomplete copied tree',
        'ZIP directory inventory cannot recover deleted/unallocated sectors','File mtime and camera timezone must be corroborated independently']},indent=2))
    print('Found',len(rows),'clips; days present:', ', '.join(sorted(k for k,v in counts.items() if v['files'])) or 'none')

if __name__=='__main__':main()