# Research Registry: Scientific Audio & Video Recovery
Updated 2026-11-22. Candidate discovery and independent evaluation; no tool listed here has been validated on the private source merely by appearing in this document.

## Standards/professional sources to follow
- SWGDE audio methods (Aug 2025 v2): https://www.swgde.org/documents/published-complete-listing/20-a-001-2/
- SWGDE forensic audio: https://www.swgde.org/documents/published-complete-listing/08-a-001-swgde-best-practices-for-forensic-audio/
- SWGDE forensic FFmpeg audio (2025): https://www.swgde.org/documents/published-complete-listing/23-a-001-technical-notes-on-ffmpeg-for-forensic-audio-examination/
- NIST OSAC Registry: https://www.nist.gov/osac/registry
- AES Audio Forensics committee: https://aes.org/community/technical-council/aes-technical-committee-audio-forensics/
- International Association for Forensic Phonetics and Acoustics research: https://www.iafpa.net/
- Academic proceedings: https://www.isca-archive.org/ , https://ieeexplore.ieee.org/ , https://asa.scitation.org/ , https://www.aes.org/e-lib/
- Ring native export and video retention: https://ring.com/support/articles/6shp7/managing-your-ring-videos

## Verified research starting points (read primary text)
- DeepFilterNet3 implementation and paper: https://github.com/Rikorose/DeepFilterNet ; https://arxiv.org/abs/2305.08227 .
- MP-SENet original author implementation: https://github.com/yxlu-0102/MP-SENet ; Interspeech 2023.
- SEMamba original author: https://github.com/RoyChao19477/SEMamba ; IEEE SLT 2024.
- Mamba-SEUNet ICASSP 2025: https://github.com/MyParadise21/Mamba-SEUNet .
- GTCRN ICASSP 2024: https://github.com/Xiaobin-Rong/gtcrn .
- ClearerVoice-Studio 2025 (FRCRN/MossFormer2): https://github.com/modelscope/ClearerVoice-Studio and https://www.isca-archive.org/interspeech_2025/zhao25f_interspeech.pdf .
- PASE 2026 warns generative enhancement can hallucinate linguistic and speaker content: https://doi.org/10.1609/aaai.v40i39.40562 .
- NIST and SWGDE require documenting processing, testing and original/derived evidence separation; review the standards, not only snippets.
- Comparative open MP4 carving candidates: https://github.com/ponchio/untrunc ; https://github.com/ntrnghia/recover-mp4 ; https://github.com/zetlen/basinski ; https://github.com/repairmyvideo/mp4inspect .
- Filesystem tools: https://github.com/sleuthkit/sleuthkit ; https://www.cgsecurity.org/wiki/PhotoRec ; https://www.gnu.org/software/ddrescue/ddrescue.html .
- ISO BMFF analysis: https://github.com/axiomatic-systems/Bento4 ; https://github.com/gpac/gpac ; https://ffmpeg.org/documentation.html .

## Selection rubric
Score candidate tools on verified input codec/profile, applicability to 8 kHz μlaw versus 48 kHz AAC, chunk/scatter assumptions, official release and commit maintenance, independent evidence, measured intelligibility improvement, absence of artificial speech, cost, GPU, OS availability, license and reproducibility. Record `experimental` unless tested on synthetic and then an authorized working copy.

## Community sources
Specialist audio practitioner workshops, SWGDE / AES technical sessions, IAFPA proceedings, VideoHelp forums (https://forum.videohelp.com/), forensicfocus (https://www.forensicfocus.com/forums/) and relevant GitHub issues/Discussions may suggest recovery heuristics. Such posts are not independently verified science or source byte authentication. Research entries must link the particular discussion and a reproduction attempt; no scraping private user accounts.

## Automation
`scripts/research_radar.py` checks public GitHub project metadata for the 15 repository candidates listed in `sources.json`. It does not run downloaded code, download AI weights, upload media or call any paid model. GitHub `schedule` requires workflow installed on default branch; see `docs/MULTI_AGENT_AUTOMATION.md`.
