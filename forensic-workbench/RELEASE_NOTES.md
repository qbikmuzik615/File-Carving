# Release 0.3.0 — Integrated forensic recovery application

- Automated CLI + localhost browser UI.
- Read-only source SHA-256 acquisition inventory and after-run integrity check.
- Original source may be: media **directory**, **ZIP backup** (temporary safe extraction), or uncompressed RAW/DD/IMG sector image.
- Full metadata: ISOBMFF structures, embedded atoms, hex and block-level entropy, FFprobe, optional MediaInfo/MediaTrace, MediaConch, ExifTool, GPAC, Bento4.
- Deterministic cross-file moov–mdat matching; fixed unordered signature scan; tested with multiple hash seeds.
- Six FFmpeg experimental profiles per derived partial candidate, with error logs, outputs, SHA-256 hashes.
- Sector-level read-only signature scan; optional TSK mmls/fsstat/fls for partition and deleted-entry context; rejects compressed E01 as linear raw image.
- Optional consent-gated Gemini/OpenAI metadata-only technical review, not automatic API spending or fabricated evidence.
- Eight automated tests including ZIP backup handling, malicious ZIP path protection, image-only workflow and no source changes.
- No original user evidence is included in this software distribution or public GitHub branch.

**Current incident result:** Two structural cross-file matches, zero fully validated complete video recoveries. An original 32 GB physical image has not been identified in connected Drive.