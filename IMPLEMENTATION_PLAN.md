# Superdeterminism research contract (nawab v2)

Approved execution contract for the **docs-only** research phase (complete). Product tiers after that:

| Tier | Status | Spec |
|------|--------|------|
| P0 agnostic core | implemented | `src/superdeterminism/` |
| P1 LangGraph adapter | specified, not built | [docs/p1-langgraph.md](docs/p1-langgraph.md) |
| P2 ecosystem + other stacks | specified, not built | [docs/p2-ecosystem.md](docs/p2-ecosystem.md) |

Index: [docs/roadmap.md](docs/roadmap.md). The sections below are the historical nawab v2 research plan; do not treat them as the P1 implementation contract.

---

Historical nawab 18-section plan (docs-only research; complete). Skills: [nawab-plans](.cursor/skills/nawab-plans/SKILL.md), [planning.mdc](.cursor/rules/planning.mdc), [documentation.mdc](.cursor/rules/documentation.mdc), [extensive-readme](.cursor/skills/extensive-readme/SKILL.md), [learn-while-building](.cursor/skills/learn-while-building/SKILL.md), [agentic-system-design](.cursor/skills/agentic-system-design/SKILL.md).

---

## §0 Plan metadata

| Field | Value |
|-------|-------|
| **Mode** | feature |
| **Stack** | Markdown / git only. No application package. |
| **Base branch** | `main` |
| **Feature branch** | `cursor/determinism-advisor-docs-329f` |
| **Authority** | this file |
| **Estimated commits** | 8 (medium docs feature) |
| **Lead agent** | orchestrate, write, commit, push, update PR #1 |

Already on the branch: `0898037` README/LICENSE; `4d41000` vendored cursor-config-coding@437a548; `0619eff` nawab v1; `bb0ac00` Phase R commit 1 (front door).

---

## §1 North star and scope

**Objective:** A research contract any later agent can execute without inventing whitespace, ingest mappings, or flip methodology — and a repo front door that does not lie about missing files.

**Deliverables:** revised front door; `PROJECT_OVERVIEW.md`, `DECISIONS.md`, `LEARNING.md`; research docs; ADRs; vendor guides under `docs/cursor-config/`; this plan; `PROGRESS.md`.

**Non-goals:** simulator/CLI/package; auto-refactor; repo rename; re-vendor unless pin breaks; Cloud environment build; product project-mode plan (P1).

| P0 | P1 |
|----|----|
| Front door + required nawab files + research set + ADRs | Product v0 plan; Spec Kit `.specify/`; CI; environment snapshot |

---

## §2 Prerequisites

| Item | Status | Blocks | Resolution |
|------|--------|--------|------------|
| cursor-config-coding vendored | done | agent skills | keep; guides moved to `docs/cursor-config/` |
| User approval of this plan | **done** | — | implement requested |
| Phase R commit 1 | **done** | — | `bb0ac00` |
| Agent Patterns MCP | unavailable here | pattern ids | do not invent ids |
| OTel GenAI | Development | ingest pin | pin a commit in `docs/ingestion.md` |

---

## §3 Authority map

| Doc | Path | Role |
|-----|------|------|
| This plan | `IMPLEMENTATION_PLAN.md` | writable contract |
| Overview | `PROJECT_OVERVIEW.md` | purpose / constraints |
| Decisions | `DECISIONS.md` + `docs/decisions/` | ADRs |
| Progress / learning | `PROGRESS.md`, `LEARNING.md` | live status |
| Agent rules | `AGENTS.md` | claim hygiene |
| Vendor pin | `.cursor/VENDOR.md` | read-only |

Subagents are read-only. Lead writes all files.

---

## §4 Architecture (documented, not built)

```mermaid
flowchart LR
  traces[OTLP_traces] --> ingest[Normalize]
  ingest --> graph[node_kind_and_det_class]
  graph --> sim[L0_offline_counterfactual]
  sim --> recs[Recommend_or_ABSTAIN]
  recs --> report[Report_optional_scaffold]
```

Differentiation: counterfactual **re-typing** of nodes on ingested production graphs — not score-the-path, not search-a-new-workflow.

Trust: no secrets; never invent `gen_ai.*`; Advisor fields `advisor.*` / `det.*`; simulation ≠ production.

---

## §5 Workstreams

| ID | Name | Owns | Depends | Agent |
|----|------|------|---------|-------|
| WS-R | Revise done work | front door, root nawab files, vendor doc move | approval | lead |
| WS-A | Research docs | `docs/overview.md` … ADRs | WS-R | lead |
| WS-B | Product v0 | future `src/` | later plan | — |

---

## §6 Spawn map

**Parallel limit:** 2. Lead commits.

### S1 — citation recheck

- **Type:** explore, readonly
- **Trigger:** start of Phase A
- **Read:** citation list in §11
- **Write:** none
- **Return:** URL → status / title drift
- **Do NOT:** edit files
- **Sync:** before landscape + ingestion commits

### S2 — claim hygiene

- **Type:** generalPurpose, readonly
- **Trigger:** after research docs exist
- **Read:** `docs/**/*.md`, README, AGENTS
- **Return:** forbidden-phrase hits; broken relative links
- **Do NOT:** edit files
- **Sync:** Phase N commit

---

## §7 Phase map

| Phase | Objective | WS | Exit gate |
|-------|-----------|-----|-----------|
| R | Fix completed artifacts | WS-R | no dangling research links; required root files; vendor guides moved |
| A | Write research contract | WS-A | all research paths exist; each ≤ ~400 lines |
| N | Validate | both | S2 clean; forbidden-claim grep; LEARNING.md notes |
| Cutover | N/A — docs feature | — | — |

---

## §8 Todos

- `approve-plan` — done
- `phase-r-front-door` — done (`bb0ac00`)
- `phase-r-replace-impl-plan` — this commit
- `phase-a-overview-landscape` — pending
- `phase-a-ingest-arch` — pending
- `phase-a-methodology` — pending
- `phase-a-adapters-refactor` — pending
- `phase-a-roadmap-adrs` — pending
- `phase-n-validate` — pending
- `product-v0-plan` — deferred

---

## §9 Commit matrix (8 rows)

| # | WS | Commit | Status |
|---|-----|--------|--------|
| 1 | R | `docs: revise front door and add nawab required files` | done `bb0ac00` |
| 2 | R | `docs: replace implementation plan with nawab v2` | this commit |
| 3 | A | `docs: add overview and landscape` | pending |
| 4 | A | `docs: add ingest and architecture` | pending |
| 5 | A | `docs: add determinism-flip methodology` | pending |
| 6 | A | `docs: add adapters, refactor, roadmap, references, ADRs` | pending |
| 7 | A | `docs: point front door at finished research set` | pending |
| 8 | N | `docs: validate research contract` | pending |

Gates: see original nawab v2 plan. Do not pad. Do not start product commits.

---

## §10 Test and CI

- Fast: `test -f` for promised paths; `rg` for forbidden whitespace claims
- Medium: every link in README / docs/README / AGENTS resolves
- Slow / CI: N/A until a product plan

---

## §11 Research log

| Topic | Choice | Source |
|-------|--------|--------|
| Whitespace | Tight claim only (determinism-class flip on ingested graphs) | CAR 2606.08275, CausalFlow 2605.25338, Tracefork, counterfact, MaAS, DeepEval, Galileo |
| Ingest | OTLP + `advisor.*` / `det.*` | OTel semantic-conventions-genai (Development; core v1.42 moved GenAI) |
| Sim | v0 offline L0; no production LLM re-run | CAR `do_policy`; Tracefork/AgentReplay tapes; WHEN2TOOL 2605.09252 |
| Refactor | Report + scaffold; keep node name | LangGraph `create_agent` |
| README | Honest now; extensive-readme pass in commit 7 | extensive-readme skill |
| Required root docs | PROJECT_OVERVIEW + DECISIONS | documentation.mdc |
| Vendor docs | `docs/cursor-config/` | avoid colliding with research |
| MCP | Skip live query this session | server not connected |

---

## §12 Doc sync

| Event | Update |
|-------|--------|
| Approved | this file |
| Phase R/A/N done | PROGRESS.md + LEARNING.md |
| Arch choice | DECISIONS.md + docs/decisions |

---

## §13 Gates

- Human: this plan approved (done)
- Human: separate approval before simulator code
- Phase R: no dangling research links (commit 1)
- Phase A: all research files exist, ≤ ~400 lines
- Phase N: S2 + grep

---

## §14 Hardening

Walk README, AGENTS, docs/README, all research files. Forbidden-claim grep. No `gen_ai.*` inventions. ponytail-review N/A (prose). speckit-converge N/A (no `.specify/`).

---

## §15 Cutover

N/A — documentation feature.

---

## §16 Exit criteria (P0)

- [x] This plan approved before remaining writes
- [x] PROJECT_OVERVIEW.md, DECISIONS.md, LEARNING.md exist
- [x] Vendor guides live under docs/cursor-config/
- [x] All Phase A research paths exist
- [x] Front door links only to files that exist
- [x] Landscape safe vs unsafe claims
- [x] Methodology names L0/L1/L2 and ABSTAIN
- [x] ADRs 0001–0003 exist
- [x] LEARNING.md has Phase R and Phase A notes
- [x] PR #1 updated

P1: product project-mode plan; CI; environment build.

---

## §17 Risks

| Risk | Mitigation |
|------|------------|
| Adjacent tool ships a determinism advisor | Date landscape; S1 recheck |
| OTel names move | Pin commit |
| L0 overconfidence | Limitations first; ABSTAIN |
| extensive-readme invents a product | Discover-only; skip empty API/test sections |
| Vendor move breaks AGENTS links | Fixed in `bb0ac00` |

---

## §18 Execution protocol

```text
1. Approval received
2. Phase R commits 1–2
3. Spawn S1; Phase A commits 3–7
4. Spawn S2; Phase N commit 8
5. Update PR #1
6. Stop. No product code.
```

## Open questions

- After Phase N, draft the product project-mode plan next, or stop at the research contract?

## Approval

Mode: feature. Approved. Lead follows §18.
