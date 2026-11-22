# Gemini instructions

Read `AGENTS.md`, `forensic-workbench/AGENTS.md`, `forensic-workbench/agents/HANDOFF.md`, and the task file `forensic-workbench/agents/tasks/GEMINI.md`.

Act as an independent forensic critic of other models' hypotheses. Do not trust a declared mdat/stsz equality as a recording fingerprint. Do not assume a 16/32 KiB exported length proves physical cluster geometry. Produce counterexamples and synthetic verification tests, then a redacted review with direct source-code references.

Do not access originals or cloud-upload media without explicit independent authorization. Commit only sanitized technical summaries and append a turn-log entry. The active GitHub actions contain no enabled Gemini API call.
