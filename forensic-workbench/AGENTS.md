# Forensic Recovery Workbench — Shared Agent Contract

**Applies to ChatGPT/Codex, Gemini, Claude, and human reviewers.** Read this file, `agents/HANDOFF.md`, and the newest `agents/turn-log.jsonl` entries before modifying anything.

## Mission
Recover and verify existing Wyze microSD media bytes by deterministic means. Build reproducible code and tests. Never invent missing frames, voices, source locations, timestamps, or probabilities.

## Required collaboration cycle
1. Start from the newest branch and read the handoff, open tasks and existing reports.
2. Declare exactly which source hash, input path, tool version and source/derivative status were used (in the private vault when sensitive).
3. Make a small branch or PR with executable code, **synthetic** tests, concise findings, and reproducible commands.
4. Run tests and distinguish PASS, FAIL, BLOCKED, NOT RUN, and INCONCLUSIVE. Cite the test's output artifact and commit SHA.
5. Append a structured agent-log entry and update `agents/HANDOFF.md`. State what another model should independently challenge.
6. Do not merge incompatible findings. Preserve contradictory hypotheses and supporting data; request independent replication.

## Privacy and integrity — mandatory
- This repository is PUBLIC. Do not commit source recordings, repaired recordings, frames, audio, physical card images, email text, individual names, location-sensitive paths, Drive file IDs, API tokens, provider keys, raw user chat, or unredacted case details.
- Place copied evidence in an access-controlled, read-only local vault or **dedicated private** repository. Sharing a branch in a public repo does NOT make it private.
- Case manifests containing Drive IDs, SHA-256 hashes, and original relative paths are private; share only anonymized statistics here.
- Use SHA-256 provenance in private reports. Never modify authoritative evidence; derived media must be visibly labeled.
- Never run untrusted PR scripts on self-hosted evidence runners. Keep public CI synthetic-only.
- Never send audiovisual bytes or detailed event records to cloud models unless a separate explicit consent decision is recorded.

## Factual claim labels
VERIFIED_BYTES (reproduced from source), TEST_OUTPUT (machine output), INFERENCE (interpretation), HYPOTHESIS, NOT_RUN, and BLOCKED.

## Runtime and costs
Pure Python and offline test suite are the default. Provider-powered GitHub Actions require separately configured API authentication and may incur charges; opt-in dispatch only. No provider call is implicit in pushing a commit.

## State locations
`agents/HANDOFF.md` — next agent's entrypoint; `agents/turn-log.jsonl` — chronological append-only summaries; `agents/README.md` — orchestration; `results/public/` — redacted reproducible outputs; `evidence/README.md` — private vault layout.
