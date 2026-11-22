# File and Folder Contract

```text
File-Carving/                      # PUBLIC only
  AGENTS.md                        # universal repo instructions
  GEMINI.md                        # Gemini entrypoint
  CLAUDE.md                        # Claude entrypoint
  .github/workflows/               # CI, research radar, opt-in model dispatch
  forensic-workbench/
    app.py, workbench.py, ai_triage.py, static/
    docs/
      PROJECT_CHARTER.md
      ROADMAP.md
      MASTER_AGENT_PROMPT.md
      RECOVERY_MASTER_REPORT_2026-11-22.md
      MULTI_AGENT_AUTOMATION.md
      VIDEO_RECOVERY_PROTOCOL.md
      AUDIO_FORENSIC_PROTOCOL.md
    agents/
      HANDOFF.md
      turn-log.jsonl
      tasks/{GEMINI,CLAUDE,PERPLEXITY,PRIVATE-EVIDENCE}.md
      reviews/                        # redacted model reviews
    research/
      TOOLS_AND_SCIENCE.md
      radar/                          # dated public snapshots
    scripts/
      staircase_overlap.py
      wyze_bidirectional_audit.py
      audio_triage.py                 # read-only private working-copy analysis
      research_radar.py               # PUBLIC metadata only
      log_agent_turn.py
    tests/                            # synthetic inputs only
    results/public/                   # redacted counts only
    evidence/README.md                # metadata about private vault, NO MEDIA
```

```text
PRIVATE ENCRYPTED VAULT/             # NOT GitHub public and not part of code checkout
  originals/
    ring/{candidate_source,boosted_derivative,other_device}/
    wyze/{exported,physical_image_if_found,reference_clips}/
  manifests/
    evidence_ledger.jsonl
    sha256.csv
    source_to_drive_id.csv
  derived/
    audio/{aac_packet_copies,pcm_refs,dsp,neural,speech_segments,spectrograms}/
    video/{carved,rebuilt,decoder_logs}/
  analysis/
    audio/{waveform_stats,crosscorrelation,ASR_hypotheses,blind_reviews}/
    video/{moov_mdat,recovered_samples,physical_extents}/
  custody/
    acquisitions.jsonl
    decisions.jsonl
    examiner_reviews/
  final/
    authenticated_sources/
    clearly_labeled_enhancements/
    verified_timeline/
    expert_packet/
```

In code, never assume a private path, source media size or origin. Use explicit parameters and checksum the source. Never check original media into a PUBLIC branch. A GitHub Project board is a separate optional planning interface; the file-based task board works even though Issues are disabled in this repository.
