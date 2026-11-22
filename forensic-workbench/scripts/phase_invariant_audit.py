#!/usr/bin/env python3
"""Read-only MP4 signature audit and deterministic phase-invariant byte-overlap test.

Uses local winnowing of rolling 64-byte k-gram hashes with a 193-position
window. Every exact matching run of length >= 64+193-1 = 256 bytes contains
one common fingerprint (independent of its byte offsets). All candidates are
verified by direct byte comparison and expanded to maximal identical runs.
No contents are transmitted, altered, or included in reports.
"""
from __future__ import annotations
import argparse
from collections import defaultdict, deque
import hashlib
import json
from pathlib import Path

K = 64
W = 193
MIN_RUN = K + W - 1
BASE = 257
MASK = (1 << 64) - 1
POWER = pow(BASE, K - 1, 1 << 64)


def fingerprints(buf: bytes):
    """Yield (64-bit fingerprint, byte offset) with deterministic leftmost tie."""
    n = len(buf)
    if n < MIN_RUN:
        return
    h = 0
    for b in buf[:K]:
        h = (h * BASE + b + 1) & MASK
    minima = deque()
    last = -1
    for pos in range(n - K + 1):
        if pos:
            h = ((h - (buf[pos - 1] + 1) * POWER) * BASE + buf[pos + K - 1] + 1) & MASK
        while minima and minima[-1][0] > h:
            minima.pop()
        minima.append((h, pos))
        while minima and minima[0][1] <= pos - W:
            minima.popleft()
        if pos >= W - 1:
            v, at = minima[0]
            if at != last:
                yield v, at
                last = at


def expand(a: bytes, ia: int, b: bytes, ib: int):
    """Return maximal matching source intervals (start_a, start_b, len)."""
    left = 0
    while ia > left and ib > left and a[ia - left - 1] == b[ib - left - 1]:
        left += 1
    right = K
    while ia + right < len(a) and ib + right < len(b) and a[ia + right] == b[ib + right]:
        right += 1
    return ia - left, ib - left, left + right


def atom_report(data: bytes):
    hits = []
    pos = 0
    while (idx := data.find(b'ftyp', pos)) >= 0:
        pos = idx + 4
        start = idx - 4
        if start < 0 or start + 168 > len(data):
            continue
        size = int.from_bytes(data[start:start+4], 'big')
        if not 8 <= size <= 4096:
            continue
        if data[start+8:start+12] != b'mp42':
            continue
        free_start = start + size
        free_size = int.from_bytes(data[free_start:free_start+4], 'big')
        free_valid = (data[free_start+4:free_start+8] == b'free' and free_size >= 8)
        mdat_start = free_start + free_size if free_valid else -1
        mdat_valid = (mdat_start + 8 <= len(data) and data[mdat_start+4:mdat_start+8] == b'mdat')
        hits.append({
            'ftyp_start':start, 'mod_512':start % 512,
            'mod_16384':start % 16384, 'ftyp_size':size,
            'free_size':free_size if free_valid else None,
            'mdat_start':mdat_start if mdat_valid else None,
            'mdat_size':int.from_bytes(data[mdat_start:mdat_start+4], 'big') if mdat_valid else None,
            'header_sha256':hashlib.sha256(data[start:mdat_start]).hexdigest() if mdat_valid else None,
            'free_zero_padding':(not any(data[free_start+8:mdat_start])) if mdat_valid else None,
        })
    return hits


def audit(paths, min_run=MIN_RUN):
    if min_run < MIN_RUN:
        raise ValueError(f'Minimum guarantee threshold is {MIN_RUN} bytes')
    inputs = [Path(p) for p in paths]
    if len(set(x.resolve() for x in inputs)) != len(inputs):
        raise ValueError('Duplicate inputs must be removed')
    blobs = {}
    records = []
    anchors = defaultdict(list)
    for path in sorted(inputs):
        b = path.read_bytes()
        key = str(path)
        blobs[key] = b
        records.append({
            'file':key, 'size':len(b),
            'sha256':hashlib.sha256(b).hexdigest(),
            'ftyp_at_zero':len(b)>=8 and b[4:8]==b'ftyp',
            'ftyp_hits':atom_report(b),
        })
        for hash64, at in fingerprints(b):
            anchors[hash64].append((key, at))
    detected = {}
    candidates = 0
    for group in anchors.values():
        if len(group) < 2:
            continue
        for i, (p1, o1) in enumerate(group):
            for p2, o2 in group[i+1:]:
                if p1 == p2:
                    continue
                candidates += 1
                if p1 > p2:
                    a, ia, b, ib = p2, o2, p1, o1
                else:
                    a, ia, b, ib = p1, o1, p2, o2
                if blobs[a][ia:ia+K] != blobs[b][ib:ib+K]:
                    continue
                delta = ib - ia
                covered = False
                for xa, xb, ln in detected.get((a,b,delta), ()):
                    if xa <= ia < xa + ln and xb <= ib < xb + ln:
                        covered = True
                        break
                if covered:
                    continue
                sa,sb,ln = expand(blobs[a],ia,blobs[b],ib)
                if ln >= min_run:
                    detected.setdefault((a,b,delta), []).append((sa,sb,ln))
    found = []
    for (a,b,delta),runs in detected.items():
        for x,y,ln in runs:
            found.append({'file_a':a,'offset_a':x,'file_b':b,
                          'offset_b':y,'length':ln,'delta_b_minus_a':delta,
                          'delta_mod_512':delta%512,'delta_mod_16384':delta%16384})
    found.sort(key=lambda x:(-x['length'],x['file_a'],x['file_b'],x['offset_a']))
    return {'method':'winnowing-leftmost-minimum-64-bit-polynomial+exact-byte-verification',
            'k_bytes':K,'window_kgrams':W,'exact_match_guarantee_bytes':MIN_RUN,
            'min_report_length':min_run,'status':'complete',
            'files':records,'total_bytes':sum(len(x) for x in blobs.values()),
            'fingerprint_key_count':len(anchors),'candidate_pairs':candidates,
            'match_count':len(found),'matches':found}


def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('paths',nargs='+',help='input directories or individual recovered files')
    a.add_argument('--min-run',type=int,default=MIN_RUN)
    a.add_argument('--json-out',type=Path,help='local report (keep private; never auto-publish)')
    args=a.parse_args()
    paths=[]
    for s in args.paths:
        p=Path(s)
        if p.is_dir():
            paths.extend(sorted(x for x in p.iterdir() if x.suffix.lower() in ('.mp4','.mov')))
        elif p.is_file():
            paths.append(p)
        else:
            a.error(f'Not a file or directory: {p}')
    out=audit(paths,args.min_run)
    brief={k:v for k,v in out.items() if k not in ('files','matches')}
    print(json.dumps(brief,indent=2))
    print('Candidate matches (max first):')
    for r in out['matches'][:25]:
        print(f"{Path(r['file_a']).name}@{r['offset_a']} = {Path(r['file_b']).name}@{r['offset_b']} len={r['length']} delta={r['delta_b_minus_a']}")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True,exist_ok=True)
        args.json_out.write_text(json.dumps(out,indent=2)+'\n')


if __name__=='__main__':
    main()
