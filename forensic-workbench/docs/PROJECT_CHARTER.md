# Forensic Media Recovery Lab — Project Charter
Version 1.0 | 2026-11-22 | Public-safe engineering charter

## The prize: genuine recoverable information
Recover and validate the greatest possible portion of the target historical security-camera recordings and their original recorded sound. The primary workstreams are (A) corrupted/deleted Wyze microSD MP4/mdat media and (B) two time-adjacent Ring video/audio clips. Deliver an authenticated original-source inventory, structurally reconstructed candidates, separate speech-intelligibility derivatives, an independent peer-review trail, and a technical report that clearly distinguishes what exists in the underlying encoded recording from what any algorithm hypothesizes.

**Do not substitute a convincing-looking video or intelligible-sounding AI-generated words for recovered evidence.** Neither target event, speaker identity, nor recording time is established merely by a filename, model output, or media metadata field.

## Definition of done
- Every input registered privately by source URI, source class, acquisition procedure, exact size, SHA-256, and copy-to-copy integrity checks.
- Physical imaging/cluster geometry documented from the filesystem boot sector if the original card/bitstream becomes available; otherwise marked unavailable.
- For every purported recovered video segment: provenance offsets, codec/SPS/PPS, continuous AVC access-unit parsing, actual strict decoder result, audio continuity and independent review.
- For every audio candidate: source AAC/ulaw and bit-perfect stream-copy derivative, decoded PCM reference, analysis parameters, controlled DSP results, neural comparison branches with model/checkpoint versions, intelligibility annotations, and acknowledged uncertainty.
- Video/audio clock synchronization with independently checked time anchors, sample-accurate media timeline, and uncertainty bounds.
- Human verification of all proposed audible words using source and alternative, non-generative signal-processing versions. Blind listening when feasible.
- Court-oriented packet: evidence ledger, method SOP, exact commands, tool versions, hashes, non-destructive derivative tree, known limitations, opposing-expert challenge log and presentation-quality clips identified as enhancements rather than originals.

## Guardrails
- PUBLIC GitHub hosts implementation, synthetic fixtures, redacted statistics, research links, decisions, discussions and actions.
- PRIVATE encrypted vault hosts actual Ring/Wyze media, hashes linked to Drive identifiers, extraction outputs, recovered video/audio, spectrograms, transcription drafts and case facts.
- Development branches are not private if the repository is public.
- Original evidence must never be modified or served to a public GitHub runner.
- Cloud model calls use only public-safe technical metadata unless separately authorized. Never upload real audio/frames to third-party APIs by default.
- Model suggestions are hypotheses; no neural generated content is evidentiary support without independent source corroboration.

## Four outcome levels
1. **Verified recovered original encoded bytes**: exact hash/physical provenance and decoded source-consistent AV units.
2. **Defensible reconstruction**: binary joins and container repairs with explicit offsets, confidence and decoding tests.
3. **Interpretive enhancement**: original-derived audio/video under reversible, documented DSP; not an original.
4. **Illustrative AI reconstruction**: potentially generative artifacts for experimentation; barred from evidentiary assertion.

## Critical dependency
The original physical SD-card image remains unavailable. Analysis of exported filenames/lengths must not be confused with source FAT32 cluster allocation. See `VIDEO_RECOVERY_PROTOCOL.md`.

## Work ownership
Integration: ChatGPT/Codex; independent technical challenge: Gemini; parser/test/security review: Claude; live web and scholarly discovery: Perplexity or other research models using documented citations; human examination/approval: evidence custodian.

## Milestones, not time estimates
**M0** inventory and integrity -> **M1** verify Ring audio source variants -> **M2** automate classical DSP baseline -> **M3** benchmark neural speech enhancement against source -> **M4** recover Wyze bitstreams and audio -> **M5** synchronize devices -> **M6** independent repeatability review -> **M7** locked evidentiary report.

See `ROADMAP.md`, `MASTER_AGENT_PROMPT.md`, `AUDIO_FORENSIC_PROTOCOL.md`, `VIDEO_RECOVERY_PROTOCOL.md`.
