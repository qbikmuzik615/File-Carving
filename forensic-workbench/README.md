# Forensic Recovery Workbench

Local-first forensic workflow and experimental MP4/Wyze file-carving laboratory. Fully runnable without AI/API credentials. **Source evidence is read only**; all changes are independently stored derivatives and audit records.

## One-click Mac setup

Requires Python 3.10+, plus FFmpeg/FFprobe. Best with optional MediaInfo, MediaConch, ExifTool, Sleuth Kit, GPAC and Bento4.

```bash
brew install python ffmpeg mediainfo exiftool sleuthkit
```

Then double-click `launch_mac.command` (if macOS blocks it, use `zsh launch_mac.command` in Terminal). It runs on **http://127.0.0.1:8765** only by default.

Enter an evidence **folder**, a **ZIP of a full card-copy directory tree**, or an **uncompressed RAW/IMG/DD sector image**, and optionally a separate raw bit-for-bit SD-card image. ZIP files are unpacked to temporary scratch for analysis and cleaned up afterward; scratch disk space must be sufficient. The app autonomously runs each stage, displays progress, ranks the structural matches, and offers an evidence-free ZIP report download. **The original source files are never moved or written.**

Run from a terminal without the graphical interface:

```bash
python3 workbench.py --source /Volumes/WORKING_COPY/recovered --output ~/ForensicWorkbenchReports
python3 workbench.py --source /Volumes/WORKING_COPY/recovered --disk-image /Volumes/WORKING_COPY/card_32GB.dd --output ~/ForensicWorkbenchReports
```

To use the browser interface without the Mac launcher:

```bash
python3 -m pip install -r requirements.txt
python3 app.py
```

## Automation stages

1. Input manifest: SHA-256 every media file and preserve source path, size, filesystem timestamps.
2. Read-only byte analysis: 4 KB hex heads/tails, ISO BMFF structures, block hashes/entropy, FFprobe, optional MediaInfo/MediaTrace, MediaConch, ExifTool, GPAC, Bento4.
3. Structural association: search across all inputs for embedded `moov` and `mdat` boxes; pair exact sample-size sums with media payload declarations; check first AVC sample length and NAL type.
4. Candidate generation: test hypotheses as **new, clearly labelled partial files**, never mutate originals. A few modified container bytes are explicitly reported.
5. Decoder validation: real FFmpeg decoding, diagnostics, structural/decoder-based prioritization. Never conflate parsable metadata with valid image content.
6. Timeline inventory: surrounding dates in `record/YYYYMMDD/HH/MM.mp4`, or archived ZIP; records directory evidence, not confirmed footage time.
7. Optional sector image scan: read-only signature scan of RAW/IMG/DD physical media, anchored byte offsets, cautious bounded extraction, optional `mmls`, `fsstat` and `fls` including deleted directory entries.
8. Rehash sources and write final reproducibility report.
9. Optional **explicitly consented AI review**: Gemini or OpenAI analyzes only compact technical metrics, NEVER audiovisual bytes or source paths. Not run automatically.

## AI provider setup (optional)

The application works offline. If explicitly requested, set `GEMINI_API_KEY` or `OPENAI_API_KEY` in the **local environment** and click the provider review button with consent. Model outputs are engineering hypotheses, never evidence. The app does not promise free API inference; billing depends on your provider.

## Evidence integrity and scope limitations

* Reports go outside source trees; no transcode or deletion of original evidence.
* Candidate media may show gray/decoder-concealed frames or misleading timestamps, and **must not be represented as authenticated footage**.
* Identifying `avc1`/`ulaw` or matching `moov`/`mdat` **does not** establish recorded time, incident or provenance.
* A missing/overwritten cluster cannot be reconstructed from non-existent bytes using AI; seek original physical image or card.
* A copied SD folder does not contain unallocated/deleted sectors; locating the original RAW/DD/IMG/E01 is priority.
* Disk image signature extraction assumes contiguous physical bytes and is only an investigative aid; FAT/exFAT chains may be fragmented.
* Camera local time offset and daylight saving must be corroborated against known intact adjacent videos.
* External `ffmpeg` outputs may attempt error concealment by default. Decoder-assisted frames are not untouched original evidence.
* No GitHub repository should contain original audiovisual evidence or forensic case identifiers unless expressly authorized.

## Source code and dependencies

The bundled `scripts/*.py` are Python standard-library analysis tools. The UI requires FastAPI, Uvicorn and Requests. The audio/video engines are FFmpeg and optionally MediaInfo, MediaConch, Bento4, GPAC and Sleuth Kit. `image_scan.py` processes large images in 4 MiB streaming blocks, not in RAM. Existing carving heuristics are deterministic; the optional AI only generates technical next-test suggestions.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

**Privacy:** `127.0.0.1` binding is intentional; do not host the web service openly on the internet. Treat the reports as sensitive if they include full filesystem paths or forensic details.

**E01 / EWF / AFF4 images:** compressed forensic containers require a read-only raw stream exported by a specialist tool (e.g., `ewfexport`) before running the byte-address scanner. Do not scan compressed E01 bytes as a linear disk image.
## GitHub cross-agent review (v0.3.1)

`/api/collaboration` and the local UI show latest PUBLIC-SAFE agent handoffs, review task status, and whether Gemini/Claude are actually configured. GitHub receives redacted code, findings and synthetic tests; original surveillance media stays in an access-controlled private vault. Agent task files live at `agents/tasks/` because repository Issues are currently disabled. To publish one reviewed and redacted turn, use `scripts/log_agent_turn.py` with `--publish --public-safe-confirmed` in an authenticated git checkout; a chat conversation by itself does not automatically push commits.
