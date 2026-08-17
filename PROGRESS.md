# Progress

Last updated: 2026-08-15

| Phase | Status | Notes |
|-------|--------|-------|
| Research docs (nawab v2) | done | PR #2 |
| P0 — Agnostic core | done | PR #3 merged |
| P1 — LangGraph adapter | done | this PR |
| P2 — Lang ecosystem + other stacks | specified | [docs/p2-ecosystem.md](docs/p2-ecosystem.md) |

## P1 commit matrix

| # | Commit | Status |
|---|--------|--------|
| 1 | nawab contract | done |
| 2 | lazy registry + extra | done |
| 3 | `--adapter` exit 2 | done |
| 4 | mapper + fixtures | done |
| 5 | `scaffold` | done |
| 6 | usage docs | done |
| 7 | import grep tests | done |
| 8 | validate + LEARNING | this commit |

## P1 done when

- [x] extras-free `python -m pytest -q` green (23 passed before extra install)
- [x] `--adapter langgraph` without extra → exit 2
- [x] both graph shapes + retriever quirk mapped
- [x] `scaffold` write-only; ABSTAIN has no patch
- [x] no LangChain import outside `adapters/langgraph.py`
- [x] extras-on: 21 passed, 2 skipped; `--adapter langgraph` maps `model` + `lookup_order`
- [x] draft P1 PR
