# P2 ecosystem — nawab execution contract

Approved feature-mode plan. Authority for product behaviour is [docs/p2-ecosystem.md](docs/p2-ecosystem.md). Lead follows §18. P1 contract is superseded for execution; keep P0/P1 code as the base.

---

## §0 Plan metadata

| Field | Value |
|-------|-------|
| **Mode** | feature |
| **Stack** | Python 3.10+, P0 core + P1 lazy registry; pytest via `[dev]` |
| **Base branch** | `cursor/p1-langgraph-adapter-329f` until PR #4 merges, then `main` |
| **Feature branch** | `cursor/p2-ecosystem-329f` |
| **Authority docs** | [docs/p2-ecosystem.md](docs/p2-ecosystem.md), [docs/p1-langgraph.md](docs/p1-langgraph.md), [docs/ingestion.md](docs/ingestion.md), [docs/decisions/0004-agnostic-core.md](docs/decisions/0004-agnostic-core.md), this file |
| **Estimated commits** | 12 |
| **Lead agent** | Orchestrate, write, test, commit, push, PR |

---

## §1 North star and scope

**Objective:** The same P0 recommender becomes pluggable. A third party can add `--adapter custom` from the contract + example. Lang teams can batch files and ingest Langfuse (or MLflow). CrewAI/MAF have a path that is not “pretend this is LangGraph.” L1 stays opt-in.

**Deliverables:** Protocol + custom example; `--traces-dir`; Langfuse mapper + MLflow docs; MAF refuse-on-langgraph; CrewAI kickoff→workflow; `--opt-in-l1` gate; planted fixtures; usage docs.

**Non-goals:** second recommender; live collector; L2 default; auto-apply; inventing `gen_ai.*`; full live L1 replay engine; GitHub Actions.

---

## §2 Prerequisites and blockers

| Item | Status | Blocks |
|------|--------|--------|
| P0 core | done (PR #3) | all |
| P1 adapter + registry | done on PR #4 (open) | all |
| P2 spec | done | Phase A |
| This plan approved | done | commit 1 |

---

## §3 Authority and artifact map

- `docs/p2-ecosystem.md` — read-only spec
- `docs/methodology.md` — read-only L0/L1/L2
- this file — writable contract
- `models.py` / `pipeline.py` — read-only unless a one-line hook is unavoidable
- `adapters/__init__.py` + `cli.py` — writable
- `adapters/langgraph.py` — writable only for MAF refuse

---

## §4 Architecture

```text
traces|dir → cli.recommend → resolve(adapter)|load_traces
  → list[Trace] → recommend_traces → opt-in-l1 gate → one JSON
```

Adapters: langgraph, langfuse, crewai, maf, custom (example). One recommender. Attribute-only mappers. `custom` needs no extra. `--opt-in-l1` without flag never calls a model.

---

## §5 Workstreams

WS-A Ecosystem — lead only. Shared CLI + registry; do not parallelize writers.

---

## §6 Spawn map

- S1 Phase A — explore resolve/CLI hooks
- S2 Phase C — Langfuse OTLP attribute names
- S3 Phase N — import-leak + no live call without flag

Parallel limit 2. Lead commits.

---

## §7 Phase map

```text
0 plan → A Protocol → B batch → C Langfuse → D Track B → E L1 → N validate → PR
```

---

## §8 Todos

- phase-0-impl-plan (this commit)
- phase-a-protocol (commits 2–3)
- phase-b-batch (4)
- phase-c-langfuse (5–6)
- phase-d-track-b (7–8)
- phase-e-l1 (9–10)
- phase-n-validate (11–12)

---

## §9 Commit matrix

1. `docs: replace implementation plan with P2 nawab contract`
2. `feat(adapters): add Adapter protocol and extra-optional resolve`
3. `feat(adapters): add custom adapter example`
4. `feat(cli): add --traces-dir batch report`
5. `feat(adapters): map Langfuse OTLP attributes`
6. `docs: document MLflow ingest gaps`
7. `feat(adapters): refuse MAF traces on langgraph`
8. `feat(adapters): map CrewAI kickoff to workflow`
9. `feat(cli): add --opt-in-l1 gate`
10. `test: add planted DET vs open-ended fixtures`
11. `docs: document P2 CLI and adapter contract`
12. `docs: validate P2 and record learnings`

One row per commit.

---

## §10 Test strategy

`python -m pytest -q` extras-free every commit after 2. Extra tests skip. No network. No CI workflow this plan.

---

## §11 Research log

- Pluggability is the P2 bar (custom + Protocol)
- Langfuse is the tested Track A path; MLflow = document omitted ops
- L1 is a gate, not a live runner unless `SUPERDETERMINISM_L1_MODEL` is set
- `resolve()` extra-optional: missing `_EXTRAS` means no extra required

---

## §12 Doc sync

Plan → this file. Phases → PROGRESS + LEARNING. Phase 11 → usage/roadmap. Phase 12 → PR.

---

## §13 Gates

Phase 0: §0–§18 present. A: custom + extras-free pytest. B: batch one JSON. C: Langfuse fixture. D: langgraph-refuses-MAF. E: no model without flag. N: grep + PR.

---

## §14 Hardening

```text
python -m pytest -q
rg -n "import langchain|import langgraph|import crewai|import langfuse" src/superdeterminism --glob '!adapters/*.py'
rg -n "create_react_agent" src
```

---

## §15 Cutover

N/A. Draft PR on this branch. Rollback = revert.

---

## §16 Exit criteria

- [ ] `--adapter custom` from contract + example
- [ ] Non-Lang adapter fixtures
- [ ] Langfuse or MLflow tested
- [ ] `--traces-dir` → one JSON
- [ ] langgraph refuses MAF
- [ ] `--opt-in-l1` omitted never calls a model
- [ ] extras-free pytest green
- [ ] simulation ≠ production
- [ ] Draft P2 PR

---

## §17 Risks

P1 unmerged → branch from P1 tip. Silent MAF-as-LangGraph → commit 7 fixture. Live L1 temptation → annotate-only default.

---

## §18 Execution protocol

```text
1. Approval received. Ponytail on every edit.
2. Branch cursor/p2-ecosystem-329f from P1 tip.
3. Commit 1. Push. Open draft P2 PR.
4. Commits 2–12 per §9. One row per commit.
5. Stop. No L2. No collector.
```

---

## Approval

Mode: feature. Approved. Lead follows §18.
