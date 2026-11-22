# Perplexity research review — 2026-11-22

Agent: Perplexity (research agent). Status: RESEARCH_ONLY. Code changed: none. Tests run: none (NOT_RUN). No media, identifiers, transcripts or credentials were accessed or used.

Labels: EXTERNAL_LITERATURE = seen in a web source this session; NOT_VERIFIED = not confirmed against the primary paper/code; HYPOTHESIS = proposed test, not a finding.

## 1. Standards and literature seen (EXTERNAL_LITERATURE)
- SWGDE, Best Practices for Enhancement of Digital Audio (page dated 2025-09-02): https://www.swgde.org/documents/published-complete-listing/20-a-001-2/ . Full text NOT_VERIFIED; requirements must be extracted by a reviewer.
- SWGDE, Best Practices for Forensic Audio v2.5 (2022-06-09): https://www.swgde.org/wp-content/uploads/2023/11/2022-06-09-SWGDE-Best-Practices-for-Forensic-Audio_v2.5.pdf . Full text NOT_VERIFIED.
- Interspeech 2024, 'Are Recent Deep Learning-Based Speech Enhancement Methods ...' (Mawalim et al.): https://www.isca-archive.org/interspeech_2024/mawalim24_interspeech.pdf . Snippet states ASR-based approaches may induce critical hallucination effects. Conditions and conclusions NOT_VERIFIED.
- SEMamba: https://arxiv.org/html/2405.06573v1 (2024-05-10). Results NOT_VERIFIED for 8 kHz / codec-degraded surveillance audio.
- ClearerVoice-Studio: https://arxiv.org/html/2506.19398v1 ; code https://github.com/modelscope/ClearerVoice-Studio ; MossFormer2_SE_48K checkpoint listed Apache-2.0: https://huggingface.co/alibabasglab/MossFormer2_SE_48K . Code and weight licences must be confirmed by a reviewer.
- AAC double-compression detection: https://www.mdpi.com/2078-2489/9/7/161 . MPEG-4 double-compression detection (DHNet): https://arxiv.org/html/2107.08939v2 . Review: https://www.sciencedirect.com/science/article/abs/pii/S0925231225016558 . Domain mismatch with the target files is NOT_VERIFIED.
- Cascade benchmark (DeepFilterNet3 + VAD + faster-whisper) in a human-robot setting: https://www.mdpi.com/2076-3417/16/22/11262 . Not a surveillance-audio study.
- untrunc (anthwlock fork): https://github.com/anthwlock/untrunc . A practitioner post reports it learns frame layout from a healthy same-device file (unrated source, HYPOTHESIS only): https://xslabs.dev/articles/recorder-deleted-interrupted-recordings/ .
- Not reached this session: primary pages for MP-SENet, DeepFilterNet3, GTCRN (fetches truncated). Latest versions and update dates NOT_VERIFIED for all candidate tools.

## 2. Per-technology table (fields still open are NOT_VERIFIED)
| Tech | Primary source | Open items |
|---|---|---|
| DeepFilterNet3 | https://github.com/Rikorose/DeepFilterNet | paper DOI, version, licence, 8 kHz behaviour, hallucination test |
| MP-SENet | https://github.com/yxlu-0102/MP-SENet | magnitude+phase estimation per its title; weights, licence, sample rate |
| SEMamba | arXiv 2405.06573 | code/weights, licence |
| MossFormer2 / ClearerVoice | see above | 48 kHz model on codec-degraded input |
| GTCRN | not fetched | everything |
| untrunc | github.com/anthwlock/untrunc | needs healthy same-firmware reference; synthetic FAT-fragment benchmark first |

## 3. Falsifiable tests (HYPOTHESIS; none executed)
1. Lineage: after lag and gain alignment, residual between the louder export and the H.264 export should contain no speech-band information absent from the H.264 audio. Large residual or distinct content falsifies simple gain-adjusted transcode.
2. Clipping audit: fraction of clipped/near-full-scale samples per variant; report per variant before any processing.
3. Hallucination control: run each model on synthetic speech at known SNR and on noise-only and silence inputs. Any phoneme-like or ASR-transcribable output on noise-only input disqualifies that model for evidentiary use.
4. ASR as hypothesis generator only: run on unenhanced audio and each branch; retain only words that blind human listeners confirm on the unenhanced signal.
5. Hum: measure 50/60 Hz harmonic energy before any notch.

## 4. Ranked experiments
1. Offline lag/gain/residual and clipping audit of the four Ring variants (private vault, local only).
2. Classical DSP baseline with fixed logged parameters.
3. Synthetic hallucination benchmark for DeepFilterNet3, MP-SENet, MossFormer2 (public CI-safe synthetic inputs).
4. Blind A/B/C human audition protocol with disagreement log (human custodian required).
5. untrunc/recover_mp4/Bento4 benchmark on synthetic FAT-fragment models; blocked on the physical card image for real data.

Costs: 1-3 local CPU/GPU, no paid inference. Risks: domain mismatch, model-introduced content, overclaiming from web snippets. Human review required before any finding.

## 5. What another model should challenge
Verify every NOT_VERIFIED item against primary papers and code; extract concrete requirements from the SWGDE texts; independently assess whether double-compression detectors apply to AAC re-encodes of this kind.
