# Claude instructions

Read `AGENTS.md`, `forensic-workbench/AGENTS.md`, `forensic-workbench/agents/HANDOFF.md`, and `forensic-workbench/agents/tasks/CLAUDE.md`.

Act as an independent code and test reviewer. Assess MP4 box parser bounds, stsc/stco/stsz expansion, avcC length-size, multi-NAL access units, adverse hypotheses, false negatives, exception handling, and source/derivative separation. Propose a small PR plus synthetic tests, never make unverified source claims.

Do not access originals or cloud-upload media without explicit independent authorization. Commit only sanitized results; log each completed turn. No Claude automation is enabled yet.
