# 6th Sense — Architecture

**Status:** placeholder — no code exists yet. This file documents module boundaries once Phase 1 produces real code. **Do not fill in module diagrams or interfaces speculatively;** that just becomes debt to unwind later.

## Intent
Once Phase 1 (MVP software loop) exists, this file will define the boundaries between:

- **Audio capture module** — mic input on the Pixel 10 Fold, format/sample rate, wake handling (if any).
- **Gemini client module** — request-response or streaming, auth handling, retry/error behavior.
- **BLE control module** — abstraction over droid commands, so the body (BB-8 now, custom hardware later) can be swapped without touching the orchestration logic above it.

## Modularity Requirement
Per the operating contract: components (sensors, LLM backend, physical body) must be swappable without refactoring the whole system. This file is where that boundary gets enforced in writing — if a future change requires touching more than one module to swap a component, that's a flagged architecture violation, not a quick fix.

## Update Rule
This file gets its first real content the moment Phase 1 code is written. Until then it stays a placeholder — do not backfill it with assumed structure.
