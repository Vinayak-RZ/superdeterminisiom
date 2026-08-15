# Progress

Last updated: 2026-08-15

| Phase | Status | Notes |
|-------|--------|-------|
| Research docs (nawab v2) | done | PR #2 |
| P0 — Agnostic core | done | PR #3 merged |
| P1 — LangGraph adapter | in progress | nawab contract; this branch |
| P2 — Lang ecosystem + other stacks | specified | [docs/p2-ecosystem.md](docs/p2-ecosystem.md) |

## P1 commit matrix

| # | Commit | Status |
|---|--------|--------|
| 1 | nawab contract | this commit |
| 2 | lazy registry + extra | pending |
| 3 | `--adapter` exit 2 | pending |
| 4 | mapper + fixtures | pending |
| 5 | `scaffold` | pending |
| 6 | usage docs | pending |
| 7 | import grep tests | pending |
| 8 | validate + LEARNING | pending |

## P1 done when

- [ ] extras-free `python -m pytest -q` green
- [ ] `--adapter langgraph` without extra → exit 2
- [ ] both graph shapes + retriever quirk mapped
- [ ] `scaffold` write-only; ABSTAIN has no patch
- [ ] no LangChain import outside `adapters/langgraph.py`
- [ ] draft P1 PR
