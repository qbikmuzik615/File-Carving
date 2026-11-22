#!/usr/bin/env python3
"""Public GitHub project metadata radar; no AI, downloads or evidence access.
Reads a checked-in source list and writes one dated snapshot. Uses standard library.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

HERE=Path(__file__).resolve().parent.parent
SOURCES=HERE/"research"/"sources.json"
OUTPUT=HERE/"research"/"radar"
REPO_RE=re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

def sanitize(entry):
    repo=entry.get("repo","")
    if not isinstance(repo,str) or not REPO_RE.fullmatch(repo) or ".." in repo:
        raise ValueError("Invalid GitHub repository path")
    return repo

def github_json(path,token=None):
    if not path.startswith("/repos/"):
        raise ValueError("Only public repository metadata endpoints permitted")
    req=Request("https://api.github.com"+path,headers={
        "Accept":"application/vnd.github+json",
        "User-Agent":"public-forensic-research-radar/1.0",
        **({"Authorization":"Bearer "+token} if token else {}),
    })
    with urlopen(req,timeout=15) as response:
        return json.load(response)

def snapshot(entries,fetch=github_json,token=None):
    out=[]
    for item in entries:
        name=sanitize(item)
        try:
            repo=fetch("/repos/"+name,token)
            if repo.get("private"):
                out.append({"repo":name,"status":"skipped_nonpublic"})
                continue
            out.append({
                "repo":name,"domain":item.get("domain"),
                "status":"ok",
                "html_url":repo.get("html_url"),
                "description":str(repo.get("description") or "")[:240],
                "default_branch":repo.get("default_branch"),
                "pushed_at":repo.get("pushed_at"),
                "updated_at":repo.get("updated_at"),
                "stars":repo.get("stargazers_count"),
                "open_issues_count":repo.get("open_issues_count"),
                "license_spdx":(repo.get("license") or {}).get("spdx_id"),
                "archived":bool(repo.get("archived")),
            })
        except (HTTPError,URLError,ValueError,KeyError,TypeError) as error:
            out.append({"repo":name,"status":"unavailable","reason":type(error).__name__})
    return out

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sources",type=Path,default=SOURCES)
    ap.add_argument("--output-dir",type=Path,default=OUTPUT)
    args=ap.parse_args()
    data=json.loads(args.sources.read_text(encoding="utf8"))
    entries=data["repositories"]
    now=dt.datetime.now(dt.timezone.utc)
    data={
        "generated_at_utc":now.isoformat(),
        "observation_only":"Public GitHub repository metadata; not proof of recovery or audio quality",
        "repositories":snapshot(entries,token=os.environ.get("GITHUB_TOKEN")),
        "notes":["No private case media sent or received","Tool commits and licenses must be pinned/validated before installation"],
    }
    args.output_dir.mkdir(parents=True,exist_ok=True)
    path=args.output_dir/(now.strftime("%Y%m%dT%H%M%SZ")+".json")
    path.write_text(json.dumps(data,indent=2,sort_keys=True)+"\n",encoding="utf8")
    errors=sum(e["status"]!="ok" for e in data["repositories"])
    print("Public research snapshot:",path,"repos:",len(entries),"unavailable:",errors)
    if errors:
        print("Some source metadata unavailable; review snapshot before interpreting.",file=sys.stderr)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
