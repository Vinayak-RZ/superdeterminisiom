# P1 LangGraph adapter — nawab execution contract

Approved feature-mode plan. Authority for product behaviour is [docs/p1-langgraph.md](docs/p1-langgraph.md). Lead follows §18. Historical research plan (nawab v2 docs-only) is superseded for execution; keep research docs as read-only authority.

---

## §0 Plan metadata

| Field | Value |
|-------|-------|
| **Mode** | feature |
| **Stack** | Python 3.10+, stdlib P0 core; optional `langchain>=1.3,<2`, `langgraph>=1.2,<2`, `langchain-core>=1.4,<2`; pytest via `[dev]` |
| **Base branch** | `main` (PR #3 merged) |
| **Feature branch** | `cursor/p1-langgraph-adapter-329f` |
| **Authority docs** | [docs/p1-langgraph.md](docs/p1-langgraph.md), [docs/refactor.md](docs/refactor.md), [docs/decisions/0003-no-auto-apply.md](docs/decisions/0003-no-auto-apply.md), [docs/decisions/0004-agnostic-core.md](docs/decisions/0004-agnostic-core.md), this file |
| **Estimated commits** | 8 |
| **Lead agent** | Orchestrate, write, test, commit, push, PR |

---

## §1 North star and scope

**Objective:** Agents and humans can run `--adapter langgraph` on exported LangGraph / LangChain 1.x traces, get the **same** P0 L0 recommendations, and optionally write an illustrative scaffold — never an auto-applied patch.

**Deliverables:**

- Optional extra `[langgraph]` in `pyproject.toml`
- Lazy registry in `src/superdeterminism/adapters/` (no import of `langgraph.py` at package load)
- Mapper `adapters/langgraph.py` — attribute-only; may import LangChain only here
- CLI: `recommend --adapter langgraph` and `scaffold report.json --out DIR`
- Fixtures + tests under `tests/adapters/`
- Agent docs in `docs/usage.md`

**Non-goals:**

- Second recommender or decision-rule fork in `pipeline.py`
- LangChain types in `models.py`
- `typing.Protocol` (P2)
- Live LLM / L1 / L2, LangSmith/Langfuse/MLflow APIs, CrewAI/MAF/custom
- Auto-apply, auto-PR, in-place `graph.py` rewrite
- `create_react_agent`, `MessageGraph`, `ValidationNode`, `prompt=`, `pre_model_hook`
- Wrapping CAR / Tracefork / counterfact as deps
- GitHub Actions CI

**Priority:**

| Priority | Items |
|----------|-------|
| **Must ship** | extra + lazy `--adapter` + both graph-shape mappings + LangSmith retriever quirk + write-only `scaffold` + extras-free core tests |
| **Defer** | Protocol, `--traces-dir`, L1, other stacks |

---

## §2 Prerequisites and blockers

| Item | Status | Blocks | Resolution |
|------|--------|--------|------------|
| P0 package + CLI + tests | done (PR #3) | all | call `recommend_traces`; do not rewrite |
| P1 spec | done | Phase A | [docs/p1-langgraph.md](docs/p1-langgraph.md) |
| This plan approved | done | commit 1 | user approved |
| Agent Patterns MCP | unavailable | — | do not invent catalog IDs |
| LangGraph 1.x pins | specified | extras-on tests | install only on extras-on path |

---

## §3 Authority and artifact map

| Document | Path | Role |
|----------|------|------|
| P1 spec | `docs/p1-langgraph.md` | read-only product spec |
| Methodology | `docs/methodology.md` | read-only decision rules |
| This plan | `IMPLEMENTATION_PLAN.md` | writable execution contract |
| Progress / learning | `PROGRESS.md`, `LEARNING.md` | writable per phase |
| Decisions | `DECISIONS.md` + ADRs | writable only if a new choice appears |
| Core models / pipeline | `src/superdeterminism/models.py`, `pipeline.py` | read-only unless a one-line hook is unavoidable |
| Spec Kit | `.specify/` | N/A |

Subagents: authority docs read-only. Lead writes plan, progress, and code.

---

## §4 Architecture and system map

```text
traces.json → cli.recommend
  ├─ adapter omitted → pipeline.load_traces
  └─ --adapter langgraph → adapters.lazy_load → adapters.langgraph.load
        → list[Trace] → pipeline.recommend_traces → JSON/MD
report.json → cli.scaffold → --out REPORT.md + WIRING.md + patches/*.diff
```

**Target layout (new paths):**

```text
src/superdeterminism/adapters/__init__.py
src/superdeterminism/adapters/langgraph.py
src/superdeterminism/scaffold.py
tests/adapters/test_langgraph.py
tests/adapters/test_scaffold.py
tests/adapters/test_adapter_cli.py
tests/adapters/fixtures/create_agent_otlp.json
tests/adapters/fixtures/stategraph_otlp.json
tests/adapters/fixtures/langsmith_retriever_quirk.json
```

**Design rules:**

- Mapper is attribute-only. Do not instantiate `StateGraph` or call a model.
- Extra is pin documentation + lazy presence check. Missing extra → stderr + exit 2.
- One recommender. Adapter returns `list[Trace]`.
- Scaffold writes under `--out` only. A tmp user `graph.py` must be bitwise unchanged.
- Trust: no network, no secrets, no prompts, never invent `gen_ai.*`.

---

## §5 Workstreams

| ID | Name | Owns | Depends | Agent |
|----|------|------|---------|-------|
| WS-A | Adapter | `adapters/`, CLI flags, scaffold, adapter tests, usage | P0 + this plan | lead |

---

## §6 Agent orchestration and spawn map

| ID | Trigger | Type | readonly | Task | Sync |
|----|---------|------|----------|------|------|
| S1 | Phase A start | explore | true | P0 hooks; models/pipeline need no Lang types | before commit 2 |
| S2 | Phase B start | explore / docs | true | `create_agent` nodes still `model`+`tools`; `create_react_agent` deprecated | before commit 4 |
| S3 | Phase N | lead | true | import leak + `create_react_agent` grep | before PR update |

**Parallel limit:** 2. Lead commits everything. Subagents do not edit.

---

## §7 Phase map and dependencies

```text
Phase 0 (plan) → A (registry) → B (mapper) → C (scaffold) → D (docs) → N (validate) → P1 PR
```

| Phase | Objective | Commits | Exit gate |
|-------|-----------|---------|-----------|
| 0 | This contract in-repo | 1 | §0–§18 present |
| A | Extra + lazy `--adapter` | 2–3 | extras-free pytest; unknown/missing adapter exit 2 |
| B | Mapper + three fixtures | 4 | both graph shapes + retriever quirk |
| C | `scaffold` | 5 | `--out` only; ABSTAIN has no patches; graph.py unchanged |
| D | Docs | 6 | usage one JSON command |
| N | Hardening | 7–8 | extras-free + extras-on + import grep |
| Cutover | N/A | — | library CLI |

---

## §8 Todo registry

```yaml
todos:
  - id: approve-plan
    status: done
  - id: phase-0-impl-plan
    content: "Commit 1: IMPLEMENTATION_PLAN.md + PROGRESS"
    status: in_progress
  - id: phase-a-registry
    content: "Commits 2-3: extra, lazy registry, --adapter CLI"
    status: pending
  - id: phase-b-mapper
    content: "Commit 4: mapper + fixtures"
    status: pending
  - id: phase-c-scaffold
    content: "Commit 5: scaffold command"
    status: pending
  - id: phase-d-docs
    content: "Commit 6: usage / AGENTS / roadmap"
    status: pending
  - id: phase-n-validate
    content: "Commits 7-8: gates, LEARNING, PR"
    status: pending
```

---

## §9 Commit matrix

Work class: medium feature → **8 commits**. One row = one commit.

| # | Commit | Contents | Gate |
|---|--------|----------|------|
| 1 | `docs: replace implementation plan with P1 nawab contract` | this file, PROGRESS | §0–§18 present |
| 2 | `chore(adapters): add lazy registry and langgraph extra` | pyproject extras, `adapters/` stub | extras-free `pytest -q` |
| 3 | `feat(cli): add --adapter with missing-extra exit 2` | cli `--adapter`, adapter CLI tests | `pytest -q` |
| 4 | `feat(adapters): map create_agent and StateGraph traces` | mapper + three fixtures | extras-free green; extras-on or skip |
| 5 | `feat(cli): add scaffold command` | scaffold writer + tests | `pytest -q`; graph.py unchanged |
| 6 | `docs: document P1 CLI and scaffold` | usage, AGENTS, roadmap | links resolve |
| 7 | `test: extras-free import grep and adapter acceptance` | grep tests | `pytest -q` |
| 8 | `docs: validate P1 and record learnings` | LEARNING, PROGRESS, PR | §16 checklist |

---

## §10 Test and CI strategy

| Tier | Purpose | Command |
|------|---------|---------|
| Fast | extras-free unit | `python -m pytest -q` with only `[dev]` |
| Medium | extras-on mapper | `pip install -e ".[dev,langgraph]"` then pytest; no network |
| Slow | N/A | no live graph / LLM |
| CI | N/A this plan | commands above are the gates |

Adapter tests that need the extra use `pytest.importorskip` / skip. Core tests stay in `tests/test_*.py`. Adapter tests live under `tests/adapters/`.

---

## §11 Research log and decisions

| Topic | Choice | Source |
|-------|--------|--------|
| Claim hygiene | re-typing on ingested graphs only | `docs/landscape.md` |
| Pins | langchain>=1.3,<2; langgraph>=1.2,<2; langchain-core>=1.4,<2 | `docs/adapters.md` / CAR |
| create_agent nodes | `model` + `tools`; never emit `create_react_agent` | LangChain agents docs + S2 |
| Mapper vs runtime | attribute-only; extra is presence + pins | ponytail + ADR 0004 |
| No Protocol | one implementation does not get an interface | `docs/p2-ecosystem.md` |
| Scaffold | keep node name; never auto-apply | ADR 0003 |
| MCP | skip; do not invent pattern IDs | server unavailable |

---

## §12 Documentation and artifact sync

| Event | Update |
|-------|--------|
| Plan approved | this file (commit 1) |
| Phase complete | PROGRESS.md, LEARNING.md |
| Arch choice | DECISIONS.md + ADR (none expected) |
| Phase D | docs/usage.md, docs/roadmap.md |
| Phase N | P1 PR body |

---

## §13 Quality gates and checkpoints

| Gate | When | Blocks |
|------|------|--------|
| §0–§18 in this file | end Phase 0 | Phase A |
| extras-free pytest; missing/unknown adapter → 2 | end A | Phase B |
| three fixture mappings | end B | Phase C |
| scaffold isolation; ABSTAIN no patches | end C | Phase D |
| usage one-command JSON | end D | Phase N |
| extras-free + extras-on + import grep | end N | PR ready |

Human: this plan approved (done).

---

## §14 Validation and hardening

```text
python -m pytest -q
rg -n "import langchain|import langgraph" src/superdeterminism --glob '!adapters/langgraph.py'
rg -n "create_react_agent" src
```

Also: claim-hygiene grep on new docs; ponytail-review on the P1 diff; run the two usage commands on fixtures.

---

## §15 Rollout and cutover

N/A — no production consumer switch. Ship is a draft PR on `cursor/p1-langgraph-adapter-329f`. Rollback = revert the PR.

---

## §16 Exit criteria

**Must pass:**

- [x] `pip install -e ".[dev]"` ; `python -m pytest -q` green (no langgraph extra)
- [x] `--adapter langgraph` without extra → exit 2
- [x] `--adapter langgraph` maps `create_agent` and custom `StateGraph` fixtures
- [x] LangSmith retriever quirk → `retriever`
- [x] `scaffold` writes REPORT + illustrative diff; never touches user source; ABSTAIN has no patch
- [x] Agent docs: one command, JSON, no prompts
- [x] No LangChain import outside `adapters/langgraph.py`
- [x] P0 decision rules unchanged
- [x] Draft P1 PR with gate evidence

**Defer:** Protocol, `--traces-dir`, `--opt-in-l1`, CrewAI/MAF, GitHub Actions.

---

## §17 Risks and contingencies

| Risk | Mitigation | Contingency |
|------|------------|-------------|
| Lang extra install fails | mapper tests skip; missing-extra CLI still tested | ship extras-free gates |
| `create_agent` node names drift | S2 recheck | map `model`/`tools`; refuse `agent` envelope |
| Fork `recommend_traces` | pipeline read-only | revert decision-rule edits |
| Scaffold looks like auto-apply | graph.py unchanged test | docs say copy-only |
| Import leak | commit 2 + commit 7 grep | fix before PR |
| P2 scope creep | §1 non-goals | descope |

---

## §18 Execution protocol

```text
1. Approval received. Load this plan + ponytail on every code edit.
2. Branch cursor/p1-langgraph-adapter-329f from main.
3. Commit 1: write IMPLEMENTATION_PLAN.md. Push. Open draft P1 PR.
4. Spawn S1. Commits 2–3 (Phase A). Gate. PROGRESS + LEARNING.
5. Spawn S2. Commit 4 (Phase B). Gate.
6. Commit 5 (Phase C). Gate.
7. Commit 6 (Phase D). Gate.
8. Commits 7–8 (Phase N): grep, both pytest modes, LEARNING, update PR.
9. Stop. Do not start P2.
```

One §9 row per commit. Never batch rows.

---

## Approval

Mode: feature. Approved. Lead follows §18. No adapter code before commit 1.
