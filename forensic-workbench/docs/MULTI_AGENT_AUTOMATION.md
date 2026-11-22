# Multi-Agent Orchestration & Automation Plan
Status: Working instructions and deterministic CI deployed; provider API reviews not yet connected.

## Workspaces
1. Public developer repository and feature integration branch.
2. Separate encrypted private evidence vault with read-only originals, manifest, derived clips and waveform results.
3. Review agents use individual feature branches/PRs or review-specific files, and common `agents/HANDOFF.md` state.
4. Public research radar and untrusted-text citation registry.
5. Human gate controlling any source access, real-world identifications, model inference spend and evidentiary publication.

## Cheap-by-default automation
- On every push/PR touching workbench: synthetic unit tests, public privacy guard, compile; fail closed.
- Weekly source radar: query official public GitHub metadata for selected repositories; save dated JSON deltas and monitor change; no LLM required.
- Every research review: explicit source URL, date, claim, tested hardware/audio conditions, limitation, code license status.
- Every chat-model session: locally generate reviewed public-safe summary, push through its authenticated GitHub connector or `scripts/log_agent_turn.py --publish --public-safe-confirmed`. Chat providers do not automatically share conversation turns just by reading AGENTS.
- On-demand paid inference: `workflow_dispatch` only, provider secret with strict permission, maximum output tokens and event budget. No original media in provider prompt.
- Private compute: local tools and native on-device models preferred. No public GitHub-hosted runner gets private original footage.
- Human gate before integrating any neural output as evidence or speaker/transcript assessment.

## Scheduling caveat
GitHub scheduled workflows run from the repository default branch (`master`), not simply by placing a `schedule` YAML in feature branch. A default-branch scheduler must be installed before weekly unattended radar runs. Scheduled GitHub Actions execute at best-effort times, not a guaranteed second.

## Agent setup
**Claude**: install/enable Claude Code GitHub integration or use Claude app to open repository branch; paste the master prompt and `agents/tasks/CLAUDE.md`. Submit PR on independent review branch.
**Gemini**: use Gemini CLI/Google AI Studio or Gemini app with GitHub source access; paste master prompt + `agents/tasks/GEMINI.md`; push review notes/test PR. Use free-tier supported model only if available.
**Perplexity**: paste master prompt + `agents/tasks/PERPLEXITY.md`; request source-backed literature with primary-source verification. Publish via user-approved GitHub connector or copy returned Markdown to review PR.
**ChatGPT/Codex**: follow AGENTS protocol, inspect and implement code, run tests and update handoff. Do not invent future automatic agent collaboration.

## Security posture
Use fine-grained provider secrets in GitHub only; repo default `GITHUB_TOKEN` reads unless a scheduled trusted job needs `contents:write`. Avoid `pull_request_target` code checkout and third-party actions with unfixed tags for high-trust environments. Restrict PR edits to reviewed code; secrets never printed or uploaded.
