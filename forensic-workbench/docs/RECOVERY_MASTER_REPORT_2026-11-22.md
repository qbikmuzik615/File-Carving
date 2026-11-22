# Comprehensive Forensic Recovery Project Report
Date: 2026-11-22 | Public-safe summary | Version 1.0

## Executive finding
The greatest near-term prospect for reliable audible information is **already readable audio in two existing time-adjacent Ring recordings**. Separately, the Wyze material remains a significant but harder H.264/MP4 fragment-recovery problem; exported metadata and one valid AVC opening packet do not show a fully reconstructable continuous scene. Technical work must divide source bytes, processing derivatives and generative experiments into separate evidentiary classes.

## Evidence availability and quality
- Two archive folders each contain 42 Ring video files, with overlapping event labels and separate export histories. Their file labels include the two priority times; clock and source-originality are not independently authenticated.
- Two candidate H.264 exports encode 20 fps video and AAC-LC mono at 48 kHz and ~69 kb/s audio. Two corresponding apparently processed exports are MPEG-4 Part 2 video with AAC mono at 48 kHz and ~64 kb/s.
- The louder audio variants show roughly +11.35 dB and +8.65 dB relative RMS over the less-processed candidates, while sample peak excursions and counted near-clipped samples increase. Preliminary 1-kHz downsampled first-60s normalized cross-correlation after lag search reaches ~0.86 and ~0.89 with ~44-ms lag. These correlations support relationship, not identical bitstreams, original authenticity or proven same performance of every instant.
- AAC and decoded PCM have been extracted privately from the H.264 versions; gentle non-neural processing and time-frequency spectrograms generated as labeled derivatives.
- Earlier private Wyze analysis found six cross-file metadata/media candidate pairs with equal declared sample sums, six first valid length-prefixed AVC envelopes and six failed second video packets. No full surviving tail confirmed under tentative zero-gap assumption.
- 34 exported files show 16 KiB length quantization (33 regular files) with 19 aligned at 32 KiB, final 160-byte fragment. None of 33 adjacent exports is an exact 16 or 32 KiB suffix continuation; shared-wall byte-identical sliding-window model failed. No source FAT32 cluster size established.
- The private physical SD-card image and a fully authenticated Ring original acquisition are not yet confirmed; forensic reports must not imply they exist.

## Decision: prioritized audio workflow
1. Source-better-variant selection based on original acquisition provenance, codec, lossy history, clipping and residual content—never loudness alone.
2. Lossless remux (AAC packet copy) + native-rate PCM reference; spectrogram and clipping diagnosis.
3. Analyze speech activity regions by human listening and sound event evidence, mark uncertainty. Segment aligned, reproducible 5–15 second regions for specialized filters.
4. Build clean signal-preserving processing controls: HP/LP, bandpass, limited spectral gate, measured hum notch, independent Wiener and STFT mask.
5. Evaluate open models as separate benchmark arms: DeepFilterNet3, MP-SENet, SEMamba, Mamba-SEUNet, ClearerVoice-Studio/MossFormer2, GTCRN. Match input sample rates, model provenance and tool license. Explicitly log model-induced syllable/artifact changes.
6. Evaluate voice isolation only if more than one source/speaker or substantial interfering noise. Diarization and ASR are investigative suggestions, not confirmed identification/testimony. Any super-resolution/voice reconstruction is illustrative.
7. Blind paired-listening comparison with source reference and residual checking; annotate acoustic support for specific disputed phonemes, retain `[inaudible]` where not independently heard.
8. Align Ring tracks to Wyze acoustic transients and external known-time data; preserve drift and offset uncertainty.

## Decision: video repair workflow
Verify physical FAT, preserve original source, carve H.264 from identified raw byte runs and use known-good camera codec references. Parse ISO-BMFF bounds and all sample table relationships, run strict bitstream decoders and alternative sample-index reconstruction. Maintain an offset join map, test against false donors, reject invented frames and disclose decoder concealment. Tools to evaluate: untrunc, FFmpeg, recover-mp4, basinski, Bento4, GPAC, Sleuth Kit, PhotoRec, ddrescue. Their github claims are NOT validation on this evidence.

## Team workflow
GitHub = transparent public code and technical findings; private vault = raw audiovisual evidence, acquisition identifiers, hashes and exact-content reports. Every agent receives a single governed master prompt, a task, relevant code revision, and latest handoff; every completed turn yields tests, a review, redacted JSONL record, and revision commit. The offline synthetic CI runs on each feature push. Optional Gemini, Claude and Codex API jobs require explicit provider configuration and budget bounds, never private media access. Perplexity is a web-literature review agent with full cited source links, not a forensic fact witness.

## Automation architecture
- Continuous: GitHub CI unit tests, compile, public-evidence leak scan on shared branch pushes.
- Weekly (after default-branch activation): GitHub release/commit radar for pinned open-source recovery/audio model repositories, producing dated public technical delta JSON.
- On-demand: opted-in independent model reviews and expensive/private audio or disk-image tests only after security/budget/consent check.
- Every session: human/agent generates a redacted turn log and updates handoff; automatic chat-to-GitHub cross-platform synchronization is NOT built into the chat providers.
- Every accepted result: an automated hash manifest, provenance record, and review summary are attached to the correct private artifact.

## Key uncertainty/risk register
- **Cloud retention**: Ring's usual temporary recording retention is up to 180 days; historical 2022 video is unlikely to remain available from ordinary current cloud history. Existing archives and exports are critical.
- **Evidentiary contamination**: neural enhancement can hallucinate linguistic or acoustic details. Do not adjudicate speech from AI output alone.
- **Source confusion**: two files of the same nominal name may be separately transcoded; require full private path and SHA-256.
- **False media association**: a valid first packet or consistent sizes can coexist with invalid subsequent samples.
- **Clock confidence**: device timezones, metadata, audio lag, and trim offsets require independent alignment.
- **Code automation risk**: public CI and untrusted PR code must not receive evidence-vault access or provider secrets.
- **Provider/model cost**: evaluate zero-cost deterministic baseline before API inference; no spend without configured limits.

## Scientific/technical authorities
- SWGDE, Best Practices for Enhancement of Digital Audio (2025): https://www.swgde.org/documents/published-complete-listing/20-a-001-2/
- SWGDE, Best Practices for Forensic Audio: https://www.swgde.org/documents/published-complete-listing/08-a-001-swgde-best-practices-for-forensic-audio/
- SWGDE, Technical Notes on FFmpeg for Forensic Audio Examination: https://www.swgde.org/documents/published-complete-listing/23-a-001-technical-notes-on-ffmpeg-for-forensic-audio-examination/
- NIST OSAC Registry: https://www.nist.gov/osac/registry
- AES Technical Committee Audio Forensics: https://aes.org/community/technical-council/aes-technical-committee-audio-forensics/
- Ring video retention: https://ring.com/support/articles/6shp7/managing-your-ring-videos
- PASE 2026 paper re neural speech hallucination: https://doi.org/10.1609/aaai.v40i39.40562
- Research tool registry: ../research/TOOLS_AND_SCIENCE.md

## Deliverable checklist
A private source/derivative inventory and complete log; reproducible script/release versions; original Ring AAC and decoded PCM reference, diagnostic plots and audio branches; Wyze offset mapping and playable valid segments only; clock reconstruction; review consensus and dissent; final report distinguishing verified signal, derived enhanced presentation and unresolved content.

This PUBLIC report deliberately excludes source IDs, recorded voices, specific event allegations, private source paths, excerpts, and raw media.
