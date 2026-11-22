# Forensic Audio Restoration SOP — Ring, Wyze and Cross-Device Audio
Version 1.0 | Public-safe

## Primary audio objective
Recover actual recorded sound and improve listening intelligibility for the target historical camera recordings, especially two adjacent Ring clip candidates. Maintain independent branches for original, losslessly decoded reference, deterministic DSP derivatives, neural enhancement experiments and possible speaker-separation outputs. Never represent a guessed phoneme as verified speech.

## Acoustics / provenance hierarchy
`A: archived original bytes` → `B: bitstream-copied elementary audio in .m4a/.ulaw` → `C: PCM lossless decode` → `D: deterministic DSP derivative` → `E: neural masking/enhancement derivative` → `F: generative bandwidth extension or speech recreation (illustrative only)`.

Use the best-preserved stream copy, not the loudest export. A re-encoded gain-boosted audio may clip, lose AAC quality, shift timing or create false detail. Store both if they might contain unique content. An AAC stream-copy .m4a changes the container but not the AAC packets; the PCM .wav is a decoded derivative. MP3/other lossy export is not a valid lossless source.

## Phase A: Establish reference
1. Identify original file by private source hash, custody, original acquisition and codec/container metadata (not just filesize).
2. `ffprobe -v error -show_format -show_streams -of json INPUT.mp4`. Save raw stdout, stderr and version.
3. `ffmpeg -nostdin -i INPUT.mp4 -map 0:a:0 -c:a copy -vn AUDIO_STREAM.m4a` for AAC; for G.711 ensure correct codec mapping and preserve known parameters.
4. Decode a reference PCM at native sample rate, e.g. `ffmpeg -nostdin -i INPUT.mp4 -map 0:a:0 -c:a pcm_f32le REFERENCE_f32.wav`; hash every output.
5. Preserve baseline listen, peak/RMS, clipping, DC offset, spectral floor, tone/harmonic peaks, and time-frequency activity plot. If two versions exist, use lagged correlation and residual analysis to distinguish gain, offset and different content.
6. Keep Ring AAC typically 48 kHz candidates distinct from model-specific Wyze G.711 μ-law sources (e.g. 8 kHz bandwidth). Resampling does NOT create original missing frequencies.

## Phase B: Signal inventory
Inspect STFT/wavelet spectrograms, RMS/loudness, crest factor, clipping, packet dropouts, reverberation, hum/tonal impulses, speech versus transients. For steady periodic buzz, measure spectrum at 50/60 Hz and harmonics. Use narrow Q notches only after finding a measurable component; adaptive hum filters can suppress voiced harmonics. Identify speech candidate regions with human audition. Document every crop's time origin and relation to recording start.

## Phase C: Classical DSP comparator
Run and preserve separate mild highpass, conditional lowpass, bandpass, measured notch, spectral subtraction, Wiener/soft spectral gate and dynamic-EQ versions. Require documented commands and checksums. Default gentle baseline can use `highpass=f=70,lowpass=f=12000` with a separate cautiously denoised `afftdn=nr=6:nf=-55` test if appropriate. These values are not evidence-specific optimal values; they must be benchmarked and should never be destructively chained over the source.

## Phase D: Neural model arms (each a separate derivative)
- DeepFilterNet3: low-complexity deep filtering, compare spectral and voice consonant integrity; site https://github.com/Rikorose/DeepFilterNet .
- MP-SENet: magnitude+phase denoising; https://github.com/yxlu-0102/MP-SENet .
- SEMamba: Mamba-based speech enhancement; https://github.com/RoyChao19477/SEMamba .
- Mamba-SEUNet: later Mamba U-Net variant; https://github.com/MyParadise21/Mamba-SEUNet .
- GTCRN: lightweight enhancement comparison; https://github.com/Xiaobin-Rong/gtcrn .
- ClearerVoice-Studio with MossFormer2 / FRCRN: https://github.com/modelscope/ClearerVoice-Studio .
- Optional trained vocal/source-separation models: compare only if overlapping speakers/noises justify this model task. Separation does not prove which real person spoke.
- Generative bandwidth extension, AudioSR, voice cloning or reconstructed speech: illustrative/non-evidentiary research arm only; cannot infer lost words or restore missing original 8-kHz bandwidth.
For each arm log exact model file/hash, version, Python/CUDA/FFmpeg versions, sample-rate conversions, device, runtime, parameters, sample peak/loudness, references, output hash, reviewer evaluation, limitations, and model license. No cloud uploads by default.

## Phase E: Controlled listening and verification
First make independent transcripts from ORIGINAL PCM and gentle DSP, marking `[inaudible]` with onset/offset. Ask separate blind reviewers to label confidence and exact source time. ASR may suggest words for review but must never authoritatively settle a contested word; prompting AI with an expected story can bias listening and hallucinate syllables. A model must not receive the desired quote in advance. Compare acoustic consonants/formants/transitions against baseline spectrogram and alternate camera recordings.

Recommended comparisons: blind same-loudness ABX, paired original/enhanced audio, residual `original - time-aligned processed`, objective PESQ/STOI where a matched clean reference exists (usually not for historical evidence), nonintrusive DNSMOS only as exploratory signal-quality rating. Human intelligibility with transcript consistency and audio authenticity controls matters more than perceptual prettiness.

## Phase F: Synchronization and deliverable
Use independently corroborated clock anchors from Ring and Wyze. Correlate shared transients and estimate lag/drift, not filenames alone. Deliver original, stream copy, PCM, each enhancement, parameters, plots, expert annotations, derived timestamp mapping and plain-language caveats, never one unlabelled 'cleaned evidence.wav'.

## Scientific basis
- SWGDE Best Practices for Enhancement of Digital Audio (2025): https://www.swgde.org/documents/published-complete-listing/20-a-001-2/
- SWGDE Best Practices for Forensic Audio: https://www.swgde.org/documents/published-complete-listing/08-a-001-swgde-best-practices-for-forensic-audio/
- SWGDE Technical Notes on FFmpeg for Forensic Audio Examination (2025): https://www.swgde.org/documents/published-complete-listing/23-a-001-technical-notes-on-ffmpeg-for-forensic-audio-examination/
- AES Audio Forensics Technical Committee: https://aes.org/community/technical-council/aes-technical-committee-audio-forensics/
- 2026 PASE hallucination study: https://doi.org/10.1609/aaai.v40i39.40562
