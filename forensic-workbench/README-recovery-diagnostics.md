# Read-only phase-invariant MP4 recovery diagnostics

Two source-independent digital-forensic tools. This public repository contains **no evidence, source video, credentials, case-specific results or legal assertions**.

## Scripts
- \`forensic-workbench/scripts/phase_invariant_audit.py\`: embedded \`ftyp/free/mdat\` byte-structure and SHA-256 manifest audit; deterministic cross-file exact-byte overlap testing. A local rolling 64-byte k-gram hash with a 193-position winnowing window selects at least one common fingerprint in every identical substring of length >= 256 bytes, regardless of offsets. Direct byte comparison eliminates hash-collision false positives. This is not a codec-level similarity detector.
- \`forensic-workbench/scripts/idr_probe.py\`: extract SPS/PPS from an existing \`avcC\` atom, construct one derived Annex B IDR stream, run strict FFmpeg diagnosis, and write local logs. A decoder failure does not independently establish physical disk allocation geometry.

## Local, private usage
\`\`\`bash
python3 forensic-workbench/scripts/phase_invariant_audit.py /private/source/files --json-out /private/results/audit.json
python3 forensic-workbench/scripts/idr_probe.py --reference /private/reference.mp4 --output-dir /private/results/idr /private/source/files
python3 -m unittest discover -s forensic-workbench/tests -p 'test_*.py' -v
\`\`\`

**Do not commit input videos, original forensic images, derived H.264 streams, logs, or results.** The synthetic unit tests need neither original videos nor secrets. The new GitHub Action has read-only contents permission, no external API keys, and a pinned checkout revision.

## Scope of conclusions
- Report a zero-overlap result only for fully completed exact-match scans of the specified input corpus and >=256-byte **unchanged** substrings.
- Transcoding, encryption, bit changes, missing files, and the physical microSD layout are outside that guarantee.
- MP4 signature recurrence and common 512-byte phases alone do not prove a FAT32 FirstDataSector error.
- Always retain source acquisition provenance and an independently recorded SHA-256 manifest.

## References
- Schleimer, Wilkerson & Aiken, *Winnowing: Local Algorithms for Document Fingerprinting*, SIGMOD 2003: https://theory.stanford.edu/~aiken/publications/papers/sigmod03.pdf
- FFmpeg decoding options: https://www.ffmpeg.org/ffmpeg-all.html
- Microsoft FAT32 specification: https://academy.cba.mit.edu/classes/networking_communications/SD/FAT.pdf
- NIST Digital Evidence Preservation: https://www.nist.gov/itl/csd/secure-systems-and-applications/computer-forensics-tool-testing-program-cftt/digital
