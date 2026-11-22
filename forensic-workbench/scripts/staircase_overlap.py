#!/usr/bin/env python3
"""Read-only fragment overlap and allocation-size audit. stdlib only.
Results may contain sensitive source paths/hashes: keep generated JSON PRIVATE.
"""
import argparse
import hashlib
import json
from pathlib import Path

def _sha(data):
    return hashlib.sha256(data).hexdigest()

def analyze(directory, shifts=(16384, 32768), sector=512):
    folder = Path(directory)
    files = sorted((p for p in folder.glob("*.mp4") if p.stem.isdigit()),
                   key=lambda p: int(p.stem))
    if not files:
        raise ValueError("No numbered .mp4 files in directory")
    data = [(p, p.read_bytes()) for p in files]
    out = {
        "folder": str(folder), "file_count": len(data),
        "files": [], "adjacent_pairs": [], "alignment": {},
        "duplicate_aligned_sector_blocks": [], "terminal_fragment_hits": []
    }
    seen = {}
    for p, b in data:
        out["files"].append({
            "name": p.name, "size": len(b), "sha256": _sha(b),
            "mod_16384": len(b) % 16384,
            "mod_32768": len(b) % 32768,
            "signatures": {t.decode("ascii"): b.count(t)
                          for t in (b"ftyp", b"mdat", b"moov", b"avcC", b"mvhd")}
        })
        for pos in range(0, len(b) - sector + 1, sector):
            digest = _sha(b[pos:pos + sector])
            if digest in seen:
                out["duplicate_aligned_sector_blocks"].append({
                    "a": seen[digest], "b": [p.name, pos], "sha256": digest
                })
            else:
                seen[digest] = [p.name, pos]
    for (pa, a), (pb, b) in zip(data, data[1:]):
        row = {"from": pa.name, "to": pb.name,
               "size_delta": len(b) - len(a)}
        for shift in shifts:
            row["exact_suffix_shift_" + str(shift)] = (
                len(a) >= shift and a[shift:] == b)
            row["first4k_shift_" + str(shift)] = (
                len(a) >= shift + 4096 and len(b) >= 4096
                and a[shift:shift+4096] == b[:4096])
        out["adjacent_pairs"].append(row)
    last = data[-1][1]
    if last:
        for p, b in data[:-1]:
            offset = b.find(last)
            if offset >= 0:
                out["terminal_fragment_hits"].append({
                    "file": p.name, "offset": offset
                })
    out["alignment"] = {
        str(n): sum(len(b) % n == 0 for _, b in data)
        for n in (512, 4096, 8192, 16384, 32768, 65536)
    }
    out["total_exported_bytes"] = sum(len(b) for _, b in data)
    return out

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("folder", help="Private working COPY of a recovered folder")
    ap.add_argument("--output", required=True,
                    help="PRIVATE JSON output path outside public git tree")
    args = ap.parse_args()
    result = analyze(args.folder)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("file_count=", result["file_count"],
          "exact_16k=", sum(r["exact_suffix_shift_16384"] for r in result["adjacent_pairs"]),
          "exact_32k=", sum(r["exact_suffix_shift_32768"] for r in result["adjacent_pairs"]),
          "duplicate_512b=", len(result["duplicate_aligned_sector_blocks"]),
          "terminal_fragment_hits=", len(result["terminal_fragment_hits"]))
    print("PRIVATE report:", output)

if __name__ == "__main__":
    main()
