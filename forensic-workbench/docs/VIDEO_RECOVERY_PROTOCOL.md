# Wyze / MP4 Reconstruction SOP (Working Copies Only)

## Stage 1: Imaging and acquisition
Prefer read-only bit-for-bit sector image of the complete original microSD card plus second independently verified hash. Preserve the device and image; do not mount read/write, run filesystem repair, write to the card, or recursively alter timestamps. If an archive contains only exported recovered files, call them exported artifacts—not raw filesystem sectors. Record tool, version, original card capacity and physical geometry.

Verify FAT32 from actual boot sector before declaring any 32 KiB cluster unit. Export sizes may be 16 KiB/32 KiB quantized independently of native cluster size; exact 32,768-byte steps do not prove allocation.

## Stage 2: Reference corpus
Use healthy clips from the exact camera generation/firmware: video `avc1` profile/level and SPS/PPS, length-prefixed NAL size `avcC`; audio `ulaw` (G.711 μ-law) or AAC *per observed healthy reference*, sample rate, channel layout and interleaving. Cameras/models may differ; don't assume all footage uses one codec.

## Stage 3: Atom/sample-table forensics
- Parse ISO-BMFF atom sizes (32-bit, 64-bit `largesize`, size=0 only when legal), nesting bounds, `moov/trak/mdia/minf/stbl/stsd/stts/ctts/stsc/stsz/stco/co64/stss`.
- Compute every media sample's absolute byte offsets from `stsc`, `stsz` and `stco/co64`; validate mapped interleaved audio/video sample ranges.
- Validate NAL length prefixes and boundaries, forbidden_zero_bit, type, SPS/PPS/slice presence. **AVCC envelope passing alone does not prove the H.264 slice entropy is decodable**.
- Independently run FFmpeg strict decoder diagnostics, ffprobe, and at least one alternative parser; use only the requested clean derivative output directory.
- Distinguish declared `mdat` payload size equivalence from matching actual donor bytes. Cross-file pairs with only first video sample valid remain tentative.
- Annotate every join as `(sourceID, sourceOffset, length, expectedTimeline, validation)`; provide a jump/gap table and disagreement log.

## Stage 4: Fragment carving
Scan in windows with overlap adequate for signatures and robust bounds. Check shift offsets over sector, 16 KiB and 32 KiB grids without assuming those are physical cluster boundaries. Test reverse hypotheses only after justifying `moov` adjacency; a zero-gap anchor is not evidence. Detect repetitive/export-overlap by exact full-byte comparisons and exact block hash matches; repeated blocks can arise legitimately and do not themselves prove original physical sectors shared.

Tools to evaluate: FFmpeg/ffprobe; `ponchio/untrunc`; Bento4/GPAC; `ntrnghia/recover-mp4`; `zetlen/basinski`; Sleuth Kit; PhotoRec; GNU ddrescue. Read model/release/license and test support for G.711 and device-specific interleaving before claims. New libraries are candidate tools until run on synthetic cases.

## Stage 5: Media and time validation
For a candidate, count audio/video samples and compare to expected frame duration; document FPS and audio clock drift. Check IDR continuity and actual decoded image output; measure concealment. Corroborate recorded local time against unaffected original sources and daylight-saving offset; don't equate `mvhd` date or recovered folder labels with event time. Cross-reference independently captured Ring audio when possible.

## Excluded forensic shortcuts
No FFmpeg re-encode of an original that overwrites it. No AI video interpolation/deblurring as proof of a previously unrecorded detail. No untrunc output called original. No non-source transcript accepted without independent acoustic verification.

## Completion
Produce a read-only source ledger, source-hash-backed candidate and offset mapping, decoder logs, reconstruction code revision, human review, and a report of irrecoverable spans.
