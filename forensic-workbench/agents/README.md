# Multi-model GitHub coordination

**Current repository:** https://github.com/qbikmuzik615/File-Carving/tree/feature/forensic-recovery-workbench

GitHub is the durable, reviewable coordination substrate, not a claim that three chatbots are presently running simultaneously.

## Roles
- **ChatGPT / Codex — Integrator:** selects experiments, implements parsers, checks evidence provenance, compares model opinions, updates handoff and issue state.
- **Gemini — Independent reviewer:** independently challenges MP4 box interpretation, FAT32 layout assumptions, statistical assertions and sample-table indexing.
- **Claude — Code reviewer:** evaluates parser correctness, failure paths, tests, CI safety, efficiency and forensic defensibility.
- **Human reviewer:** approves any original-evidence access, paid API usage, privacy-boundary changes, or proposed evidentiary conclusions.

Each model works via its own authenticated environment with explicit GitHub access. Merely naming a model here does NOT connect or launch it.

## Zero-cost baseline
Use ordinary git branches, issues, PRs, JSONL handoffs, unittest, and local scripts. No AI API keys required. The automated GitHub workflow runs only deterministic synthetic-data tests.

## Optional official hosted agents (not configured or started)
- Gemini: https://github.com/google-github-actions/run-gemini-cli — requires a supported current auth path. Free use and quotas may change.
- Claude: https://github.com/anthropics/claude-code-action — requires supported auth (API / OAuth / cloud federation). Costs depend on plan/configuration.
- OpenAI Codex: https://github.com/openai/codex-action — requires an API key/provider credentials and can incur costs.

Add providers via opt-in `workflow_dispatch` and locked-down GitHub secrets, with per-run budget/cost limits, minimum scopes, commit-pinned dependencies, and no automatic access to private evidence. Do not commit secrets or paste them in issue comments.

## Handoff cycle
Read AGENTS.md -> HANDOFF.md -> recent turn-log -> examine tests -> work on issue -> produce PR and test report -> append one JSONL turn record -> update HANDOFF.md. Cite parent commit, branch, test output and limitations.

Conversation-to-GitHub publication is not automatic. A chat client must invoke its GitHub connector/API after each turn (or use an external authenticated webhook agent). No GitHub Action can see private chat turns on its own.

## Turn log schema
Required: `turn_id`, `agent`, `utc`, `status`, `summary`, `tests`, `next_actions`, `parent_commit`. No private case facts in this public log. Put detailed, source-referenced trace in the private vault.

## Branch protocol
Keep this isolated forensic feature branch as shared integration. Each agent makes a topic branch and PR; review before merging. Avoid force pushes to shared branches.
