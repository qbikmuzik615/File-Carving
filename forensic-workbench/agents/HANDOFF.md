# Active handoff — updated 2026-11-22

**State:** Public developer collaboration initialized; source evidence stays private. Branch: `feature/forensic-recovery-workbench`.

## Verified / previously reproduced public-safe facts
- Eleven recovered directories are indexed in the connected evidence set, with 633 entries totaling 2,093,794,069 bytes of exported lengths. This total is NOT distinct allocated physical bytes.
- One anonymized 34-file folder contains 33 exports with lengths divisible by 16,384 bytes and a final 160-byte fragment. 19/33 are divisible by 32,768.
- No adjacent full-file 16 KiB or 32 KiB exact suffix identity in the 34-file group. No aligned 512-byte duplicate blocks within this group. The terminal 160 bytes do not occur as an exact substring in the preceding 33 files.
- Six proposed metadata/media candidate pairings matched sample-size sum and first AVCC envelope, but failed next video sample; reverse-tail assertions depend on unproven anchor assumptions. This is NOT authenticated media recovery.
- The simplest fixed-wall, byte-identical adjacent sliding-window hypothesis is falsified for the examined exports. Physical FAT32 cluster size is NOT established from exported lengths.

## Highest priority open work
1. Obtain a PRIVATE, authenticated physical card image and record BPB sector bytes, FAT type, bytes/sector and sectors/cluster; do not expose it in this repository.
2. Search for displaced byte runs with source-to-derivative offset mapping, full AVCC samples and H.264 slice continuity. No source mutation.
3. Replicate file-pair tests independently and examine possible stco rebase, chunk interleaving, media-declaration and close-time errors.
4. Add a private evidence vault and perform hash verification after source transfer.
5. Independent Gemini review of statistical/format claims; independent Claude review of parser and public CI. Both are OPEN, not running.

## What has NOT been proven
Original SD geometry; recording times solely from recovered folder names; provenance of fragments from a specific camera; recoverability of the original event; truthful audio content; original recording contiguous tails.

## Commands
    python3 forensic-workbench/scripts/staircase_overlap.py /path/to/PRIVATE_WORKING_COPY --output /path/to/PRIVATE_REPORT.json
    python3 -m unittest discover -s forensic-workbench/tests -p 'test_*.py' -v

Machine outputs with original source filenames, hashes or full paths go to the private evidence vault, not the public repository.

## Collaboration update
GitHub deterministic CI passed on the published code (runs 45014810068 and 45014904782). Public agent entrypoints and pending task files are committed; GitHub Issues currently disabled. `GET /api/collaboration` reports agent configuration without implying Gemini/Claude are running. An access-controlled local 46-file evidence ZIP exists separately; not stored on public GitHub.
