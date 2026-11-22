# Recovery Roadmap — Results Over Tool Collection

## P0 — Immediate audio recoverability
- [x] Locate candidate time-adjacent Ring MP4s in a connected archive (two collections; no public case filenames).
- [x] Download four distinct variants (two timestamps × two collections) into a local private working vault.
- [x] Confirm two H.264/AAC copies and two MPEG-4 Part 2/AAC copies. Distinguish source-candidate from already boosted derivatives.
- [x] Read-only extract AAC stream copies and PCM decoded working copies for the H.264 candidates.
- [x] Generate two non-neural DSP comparison sets and full-clip spectrograms privately.
- [ ] Establish exact edit history, recorder native export metadata, true time anchors, alternate channel sources.
- [ ] Segment 5–15 s regions on which human reviewers detect possible speech, recording both speech and noise baseline segments.
- [ ] Blind A/B/C (original, gently filtered, controlled AI) review of candidate speech with transcription disagreement log.
- [ ] Match time windows across Ring cameras, Wyze clips and other independent audio.

## P1 — Wyze clip/data repair
- [x] Prior six moov/mdat candidates and second-sample failures documented in redacted reports.
- [x] 34-file cluster-length staircase falsified as exact 16/32 KiB adjacent sliding export at tested offsets.
- [ ] Obtain original physical disk-image or recovery utility's original sector map, verify BPB_BytsPerSec/BPB_SecPerClus.
- [ ] Search whole private evidence store for H.264 NAL and G.711/G.726/AAC compatible runs; deduplicate *content* without presuming identical physical clusters.
- [ ] Rebuild sample/track sequence with multiple independent decoders and explicit interleaving offsets.
- [ ] Benchmark `untrunc`, `recover_mp4`, `basinski`, Bento4 and GPAC against synthetic FAT fragment models before applying to working copies.
- [ ] Extract only verified media sections; flag ambiguity, holes, black/green/concealed frames and missing audio rather than synthesize.
- [ ] Validate against healthy original clips from the same model, firmware and encoding settings.

## P2 — Audio DSP and model benchmarking
- [x] Decode two priority Ring AAC streams losslessly into float PCM analysis working copies.
- [ ] Stationary noise estimate based on independently reviewed noise-only regions (not a guessed first second).
- [ ] Measured hum identification: check 50/60 Hz and harmonics before adaptive notch; verify residual distortion and harmonics.
- [ ] Classical baseline: high-pass/low-pass/EQ, STFT spectral subtraction/wiener, attenuated spectral gating, dynamics only when measured.
- [ ] Model arm: DeepFilterNet3, MP-SENet, SEMamba, ClearerVoice/MossFormer2, GTCRN, and independent non-generative baseline; benchmark by source characteristics and local model licensing.
- [ ] Multi-speaker overlap: optional speech/source separation if acoustic evidence and model applicability support it.
- [ ] Cautiously test speech super-resolution as **illustrative only**; hallucinated bandwidth cannot recover recorded physical frequencies.
- [ ] Independent ASR proposals plus human source-audition; record uncertainty/no-speech when ambiguous.

## P3 — Collaboration and repeatable reports
- [x] Shared `AGENTS.md`, `GEMINI.md`, `CLAUDE.md`, handoffs, turn log and offline CI.
- [ ] Gemini independent data/codec review completed.
- [ ] Claude independent code and DSP-benchmark validation completed.
- [ ] Perplexity literature review with source links completed.
- [ ] Research radar scheduled from GitHub default branch; no paid inference required.
- [ ] Dedicated private evidence vault provisioned and verified for write access.
- [ ] Implement a private `evidence-import` flow with offline manifests/hashes.
- [ ] Documented human review with versioned signed report.

## Priorities and exit gates
Audio work is not blocked by damaged Wyze `moov`: the Ring audio tracks are already decodable. No proposed testimony enters a final report solely because a model generated it. Model benchmark gates: intelligibility improvement without invented words, preserved event timing, sufficient residual and artifact disclosure. Release gates: code CI green, reproducible hash manifests, independent review, uncertainties stated.
