#!/usr/bin/env python3
"""Append a redacted cross-agent handoff. Does not push unless explicitly directed."""
import argparse
import datetime
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_LOG = ROOT / "agents" / "turn-log.jsonl"

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--turn-id", required=True)
    parser.add_argument("--agent", choices=["ChatGPT","Codex","Gemini","Claude","Human"], required=True)
    parser.add_argument("--status", choices=["VERIFIED","TESTED","INFERENCE","HYPOTHESIS","BLOCKED","NOT_RUN"], required=True)
    parser.add_argument("--summary", required=True, help="PUBLIC-SAFE redacted summary; not a raw chat transcript")
    parser.add_argument("--test", action="append", default=[])
    parser.add_argument("--next", action="append", default=[])
    parser.add_argument("--parent-commit", default="")
    parser.add_argument("--publish", action="store_true", help="git commit and push, requires --public-safe-confirmed")
    parser.add_argument("--public-safe-confirmed", action="store_true")
    args = parser.parse_args()
    if args.publish and not args.public_safe_confirmed:
        parser.error("--publish requires --public-safe-confirmed after reviewing for private evidence")
    if any(c in args.summary for c in ("\x00", "\r", "\n")):
        parser.error("Summary must be one line; no raw chat transcripts")
    entry = {
        "turn_id": args.turn_id, "agent": args.agent,
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": args.status, "summary": args.summary,
        "tests": args.test, "next_actions": args.next,
        "parent_commit": args.parent_commit
    }
    PUBLIC_LOG.parent.mkdir(parents=True, exist_ok=True)
    with PUBLIC_LOG.open("a", encoding="utf-8") as out:
        out.write(json.dumps(entry, sort_keys=True) + "\n")
    print("Appended redacted agent record:", PUBLIC_LOG)
    if args.publish:
        repo = ROOT.parent
        rel = PUBLIC_LOG.relative_to(repo)
        subprocess.run(["git", "-C", str(repo), "add", str(rel)], check=True)
        subprocess.run(["git", "-C", str(repo), "commit", "-m", "docs(agents): log " + args.turn_id], check=True)
        subprocess.run(["git", "-C", str(repo), "push"], check=True)
        print("Git push succeeded")

if __name__ == "__main__":
    main()
