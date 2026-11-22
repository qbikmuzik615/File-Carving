# Read-Only Audio Triage Tool

`python3 scripts/audio_triage.py /private/source/clip.mp4 --output /private/reports/job_001 --label clip_001 --dsp --spectrogram`

The tool **requires FFmpeg and FFprobe**; Python standard library only. Never point `--output` to the directory of the original source. This is a separate, new private output directory, never committed into the public Git repository. The tool reads a source hash before and after; emits `ffprobe`-based audio stream facts, packet-copied AAC `.m4a` (or other codec in `.mka` where muxer supports it), decoded float32 WAV at the native sample rate, and optionally two deliberately mild non-neural comparison branches and source spectrogram. Every output is rehashed and every FFmpeg command recorded in `audio_triage_private_report.json`.

This does **not** automatically identify real speakers, speech content, missing words, physical original recording dates, hum, packet duplication or acoustic authenticity. The 70 Hz highpass and 12 kHz (or 40% of sample rate) lowpass are provisional gentle comparators, not universally optimal filters. The `afftdn=nr=6:nf=-55` branch is a reproducible low-intensity test; do not compound denoisers on the previous branch. Use source AAC and original PCM as auditory reference. Human approval is required for every proposed transcript.

For historical `ulaw` Wyze files, validate the codec and recorded sample rate from healthy camera references; a missing track or damaged metadata is not repaired by this tool.
