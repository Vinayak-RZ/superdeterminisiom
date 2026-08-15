# Leftover polish + README — nawab execution contract

Approved feature-mode plan. User: plan first, then implement; do not wait. Authority for product behaviour stays in the research docs and ADRs. This slice closes leftover P2 deliverables and rewrites the front door.

---

## §0 Plan metadata

| Field | Value |
|-------|-------|
| **Mode** | feature |
| **Stack** | Python 3.10+, stdlib core, pytest via `[dev]` |
| **Base branch** | `cursor/p2-ecosystem-329f` (P2 tip; P2 PR still open) |
| **Feature branch** | `cursor/oss-polish-readme-329f` |
| **Authority docs** | [docs/p2-ecosystem.md](docs/p2-ecosystem.md), [docs/methodology.md](docs/methodology.md), [docs/refactor.md](docs/refactor.md), [ADR 0003](docs/decisions/0003-no-auto-apply.md), [extensive-readme](.cursor/skills/extensive-readme/SKILL.md) |
| **Estimated commits** | 5 |
| **Lead agent** | Orchestrate, write, test, commit, push, PR |

---

## §1 North star and scope

**Objective:** Ship the leftover features that the specs already promised, and make the README a technical front door that matches what is actually in the tree.

**Deliverables**

- Canary checklist text on JSON and Markdown reports (and scaffold `REPORT.md`)
- Extras-free GitHub Actions CI
- Extensive README (trending technical shape + extensive-readme skill)
- CONTRIBUTING, `examples/README.md`, `.env.example`, `pyproject.toml` metadata
- P2 exit-criteria checkboxes marked; stale “docs-only / P2 is a spec” rows fixed

**Non-goals**

- Live L1 tail / network model client
- L2 `do_policy`
- Hosted collector, HTTP API, Docker, PyPI publish
- MLflow live API
- Auto-apply / in-place `graph.py` rewrite
- Invented `gen_ai.*` keys
- Fake badges, demo GIFs, or engagement bait

---

## §2 Prerequisites and blockers

| Item | Status | Blocks |
|------|--------|--------|
| P0 / P1 / P2 code | done on P2 tip | all |
| User approval to implement without waiting | done | this plan |

---

## §3 Authority and artifact map

| Document | Path | Role |
|----------|------|------|
| P2 spec (canary + CI rows) | `docs/p2-ecosystem.md` | leftover feature truth |
| Methodology | `docs/methodology.md` | canary is confirmatory |
| Refactor | `docs/refactor.md` | no auto-apply |
| Extensive README skill | `.cursor/skills/extensive-readme/` | README shape |
| This file | `IMPLEMENTATION_PLAN.md` | execution contract |
| Progress | `PROGRESS.md` | live status |

---

## §4 Architecture

No new recommender. Canary is a static text list attached to the existing report payload. CI runs the extras-free pytest gate already used locally.

```text
recommend → recommendations_to_dict / _markdown
  + disclaimer
  + canary[]          # leftover: confirmatory checklist, not a deploy button
scaffold REPORT.md renders the same list
```

---

## §5 Workstreams

| ID | Name | Owns paths |
|----|------|------------|
| WS-A | Report canary | `src/superdeterminism/pipeline.py`, `scaffold.py`, tests |
| WS-B | CI | `.github/workflows/ci.yml` |
| WS-C | Front door | `README.md`, CONTRIBUTING, examples, env, pyproject, P2 docs |

N/A — no parallel subagents. Lead owns every file.

---

## §6 Agent orchestration

N/A — single lead, no spawn map.

---

## §7 Phase map

| Phase | Objective | Exit gate |
|-------|-----------|-----------|
| A | Canary checklist on reports | pytest asserts `canary` on JSON/MD/scaffold |
| B | Extras-free CI workflow | workflow file + hygiene grep |
| C | README + leftover docs | extensive-readme checklist; no invented features |
| N | Validate | extras-free pytest green; commit; push; PR |

---

## §8 Todo registry

```yaml
todos:
  - id: canary
    content: "Canary checklist on JSON/MD/scaffold + tests"
    status: pending
  - id: ci
    content: "Extras-free GitHub Actions CI"
    status: pending
  - id: readme
    content: "Extensive technical README"
    status: pending
  - id: docs
    content: "CONTRIBUTING, examples, env, pyproject, P2 checkboxes"
    status: pending
  - id: validate
    content: "pytest, commit, push, PR"
    status: pending
```

---

## §9 Commit matrix

| # | Message | Files |
|---|---------|-------|
| 1 | `docs: plan leftover polish and README rewrite` | IMPLEMENTATION_PLAN, PROGRESS |
| 2 | `feat(report): add canary checklist to JSON/MD reports` | pipeline, scaffold, tests, usage |
| 3 | `ci: extras-free pytest workflow` | `.github/workflows/ci.yml` |
| 4 | `docs: rewrite README as extensive technical front door` | README.md |
| 5 | `docs: refresh contributing, examples, env, and P2 exit` | remaining docs + pyproject |

---

## §10 Test strategy

- Existing CLI tests still see `disclaimer` starting with `simulation`
- New asserts: `canary` is a non-empty list of strings; Markdown has a Canary section
- Scaffold `REPORT.md` includes the checklist
- Extras-free `python -m pytest -q` stays green
- Do not add a live L1 or network test

---

## §11 Research log

- extensive-readme: discover first; numbered `## 1.`…`## N.`; skip HTTP API / deploy
- Trending technical READMEs: 4–7 badges, one-liner, 30-second quickstart, mermaid, comparison table, no fake GIF
- P2 leftover: canary checklist (text) and extras-free CI were deliverables deferred as YAGNI

---

## §12 Risks

| Risk | Mitigation |
|------|------------|
| README invents features | Catalog only CLI flags and adapters that exist |
| Canary looks like a deploy button | Static text; no apply command |
| CI installs extras | `pip install -e ".[dev]"` only |

---

## §13 Documentation sync

README, usage JSON example, P2 exit checkboxes, CONTRIBUTING, LEARNING, PROGRESS, DECISIONS D9.

---

## §14 Validation hardening

`python -m pytest -q`. Import hygiene still forbids LangChain outside the attribute-only LangGraph file.

---

## §15 Cutover

N/A — no production deploy. Done when the PR is up and extras-free tests pass.

---

## §16 Rollback

Revert the branch. Canary is additive; CI is additive.

---

## §17 Open questions

None that block. Live L1 remains reserved (`SUPERDETERMINISM_L1_MODEL`).

---

## §18 Lead agent instructions

Implement this contract without waiting. Ponytail on every code edit. Conventional commits. Push the branch. Open a stacked PR against `cursor/p2-ecosystem-329f` so the diff is only this slice. Do not claim L0/L1 is a production A/B.
