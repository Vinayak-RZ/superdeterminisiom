# Progress

Last updated: 2026-08-15

| Phase | Status | Notes |
|-------|--------|-------|
| Research docs (nawab v2) | done | PR #2 |
| P0 — Agnostic core | done | PR #3 merged |
| P1 — LangGraph adapter | done | PR #4 (open) |
| P2 — Lang ecosystem + other stacks | done | this PR |

## P2 commit matrix

| # | Commit | Status |
|---|--------|--------|
| 1 | nawab contract | done |
| 2 | Protocol + extra-optional resolve | done |
| 3 | custom adapter example | done |
| 4 | `--traces-dir` | done |
| 5 | Langfuse mapper | done |
| 6 | MLflow docs | done |
| 7 | MAF refuse on langgraph | done |
| 8 | CrewAI kickoff→workflow | done |
| 9 | `--opt-in-l1` | done |
| 10 | planted fixtures | done |
| 11 | usage docs | done |
| 12 | validate + LEARNING | this commit |

## P2 done when

- [x] `--adapter custom` from contract + example
- [x] Non-Lang adapter fixtures (custom, CrewAI, MAF)
- [x] Langfuse fixture tested; MLflow gaps documented
- [x] `--traces-dir` → one JSON
- [x] langgraph refuses MAF
- [x] `--opt-in-l1` omitted never calls a model
- [x] extras-free pytest: 35 passed, 2 skipped
- [x] draft P2 PR
