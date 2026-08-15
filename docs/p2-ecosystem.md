# P2 — Lang ecosystem and other agent systems

**Status:** implemented.  
**Depends on:** P0 (done) and P1 (LangGraph adapter + the lazy `--adapter` registry).  
**Normative for:** the implementation PR after P1.  
**Index:** [roadmap.md](roadmap.md). Adjacent: [adapters.md](adapters.md), [ingestion.md](ingestion.md), [0004-agnostic-core.md](decisions/0004-agnostic-core.md).

P2 is when Superdeterminism becomes an open-source repo **other people actually plug into**: the rest of the Lang development system, and separately any other agent stack, through one adapter contract.

## Objective

Same core recommender. Many ingest paths. Optional L1 simulation on high-EV candidates. Still no auto-apply. Still simulation ≠ production.

Someone on LangGraph uses P1. Someone on a house agent uses the custom adapter. Someone on CrewAI or MAF has a path that is not “pretend this is LangGraph.” Agents run the CLI. Humans can too.

## Two tracks (both required for “done”)

Do not ship Track A and call P2 finished. The point of the agnostic core is Track B.

### Track A — Lang development system

Not “more LangGraph.” The rest of how Lang teams already work:

| Sink / surface | P2 job |
|---|---|
| LangSmith | OTLP already; add native export/pull if file dump is not enough. Keep quirk table (retriever→embeddings). |
| Langfuse | OTLP `/api/public/otel`. Coalesce `langfuse.*` vs `gen_ai.*`. |
| MLflow | Trace ingest; do not assume `invoke_workflow` / `plan` / `retrieval` are mapped. |
| LangChain beyond graphs | Chains, LCEL, retrievers that never hit LangGraph. |
| Batch | Directory of trace files → one report (agents: one JSON). |

Live collector / always-on sidecar is **optional** in P2, not required. File/OTLP export remains the default so air-gapped agents still work.

### Track B — Other agent systems (including raw/custom)

A documented **adapter contract**. One extra per framework. Core still has zero framework imports.

| Adapter | Extra | Notes |
|---|---|---|
| CrewAI | `[crewai]` | Role/task loop, not `StateGraph`. Map kickoff → `workflow`. |
| Microsoft Agent Framework | `[maf]` | Native `invoke_agent` / `chat` / `execute_tool`. Dedicated mapper; **do not** treat as LangGraph. |
| Raw / custom | `[custom]` or in-tree example | User implements `load(...)`. We ship a typed protocol + a fixture adapter. |

“Raw” means a team with their own orchestrator who can emit OTLP or the flat advisor JSON. P2’s job is the contract and an example, not a new SDK for every house framework.

## Adapter contract (normative)

Every P2 adapter (and P1, once the second adapter exists) implements the same shape:

```text
Adapter
  name: str                         # "langgraph" | "crewai" | "maf" | "custom"
  load(path_or_bytes) -> list[Trace]
  # optional
  scaffold(report, out_dir) -> None  # write files only; never mutate user source
```

Rules:

- `load` returns P0 `Trace` / `Span` only. No framework types leak out.
- Unknown ops → `NodeKind.UNKNOWN` + ABSTAIN, not a guess that invents `gen_ai.*`.
- `scaffold` is optional. LangGraph has one in P1. Others may ship later.
- Register via `--adapter NAME` or `superdeterminism.adapters:NAME`.
- Core tests run with **no** extras installed.
- Missing extra → stderr + exit `2` (same as P1).
- Refuse-with-reason is allowed (MAF traces passed to `--adapter langgraph` must not silently remap).

This contract is documentation until P2. The `typing.Protocol` class lands when the **second** adapter exists, not before — one implementation does not get an interface.

### Custom-adapter example (ship this)

```text
# examples/custom_adapter.py  — illustrative; user copies
from superdeterminism.models import Trace, Span

NAME = "custom"

def load(path_or_bytes) -> list[Trace]:
    # parse house JSON / OTLP → list[Trace]
    ...
```

A third party must be able to add `--adapter custom` with only this contract + example. That is the P2 “pluggable repo” test.

## Simulation depth (P2)

| Level | P2? |
|---|---|
| L0 tape / historical (P0) | keep as default |
| Batch many traces | yes |
| L1 hybrid fork (replay prefix, live tail) | yes, **opt-in**, high-EV + user flag only |
| L2 live `do_policy` | no, still confirmation / later |
| Planted-truth fixtures in CI | yes |
| Canary checklist in the report | yes (text, not a deploy button) |

L1 may call the user’s model. That is a paid, mutating, opt-in path. Default remains L0.

`--opt-in-l1` must print the simulation ≠ production warning to stderr and refuse unless the flag is present. No implicit L1.

## Package layout (planned)

```text
src/superdeterminism/adapters/
  __init__.py              # Protocol + registry (lands in P2)
  langgraph.py             # from P1
  langfuse.py              # Track A
  mlflow.py                # Track A
  crewai.py                # Track B (or refuse-with-reason stub)
  maf.py                   # Track B (or refuse-with-reason stub)
examples/
  custom_adapter.py
tests/adapters/
  test_langfuse.py
  test_mlflow.py
  test_crewai.py
  test_maf.py
  test_custom_example.py
  test_batch_dir.py
```

Each adapter file is the only place that may import that framework. Core + `models.py` + `pipeline.py` stay extras-free.

## CLI (planned)

```bash
python -m superdeterminism recommend traces.json --adapter crewai --stdout json
python -m superdeterminism recommend --traces-dir DIR --stdout json
python -m superdeterminism recommend traces.json --opt-in-l1   # explicit; warns
```

| Flag | Behaviour |
|---|---|
| `--adapter NAME` | Lazy-load registered adapter; unknown / missing extra → exit `2` |
| `--traces-dir DIR` | Load every `*.json` in DIR; one JSON report |
| `--opt-in-l1` | L1 on high-EV candidates only; stderr warning; default off |

## Implementation phases (when we start P2)

| Phase | Objective | Exit |
|---|---|---|
| 1 | `Protocol` + registry + `examples/custom_adapter.py` | Third-party-shaped test uses only the contract |
| 2 | `--traces-dir` batch | One JSON for a directory of P0 fixtures |
| 3 | Langfuse **or** MLflow ingest | Documented + fixture-tested |
| 4 | CrewAI **or** MAF **or** keep the custom example as the Track B proof | Fixtures; refuse-with-reason if pins are unstable |
| 5 | `--opt-in-l1` behind flag + warning | Default path still L0; no live call without the flag |

Track A and Track B can proceed in parallel after phase 1. Do not skip phase 1 — that is the pluggability gate.

## Tests (acceptance)

- Core extras-free tests still green
- Custom-example adapter produces `list[Trace]` the P0 recommender accepts
- Batch directory → one JSON report
- Langfuse **or** MLflow fixture maps without inventing `gen_ai.*`
- At least one non-Lang adapter (CrewAI or MAF or the custom example) has fixtures
- `--adapter langgraph` on a MAF-shaped fixture refuses with a reason (no silent remap)
- `--opt-in-l1` without the flag never calls a model
- Report still leads with `simulation != production`

## Deliverables

- Adapter contract doc + one worked custom-adapter example
- Langfuse + MLflow ingest paths (OTLP or native export)
- CrewAI extra **or** a refused-with-reason stub if pins are unstable
- MAF extra **or** refuse-with-reason (do not silently remap to LangGraph)
- `recommend --traces-dir DIR` batch
- `--opt-in-l1` behind an explicit flag and a warning
- CI: core tests without extras; adapter tests only when extra installed
- Coverage of planted DET-vs-open-ended fixtures

## Non-goals (P2)

- Auto-apply / auto-PR / rewriting customer graphs
- Becoming a hosted observability product
- Replacing LangSmith, Langfuse, or MLflow
- Wrapping CAR / Tracefork / counterfact as required runtime deps (optional interop later, own ADR)
- Inventing `gen_ai.*` keys
- Claiming L0/L1 is a production A/B test
- Implementing L2 live `do_policy` as default

## Exit criteria

- [ ] A third-party can add `--adapter custom` with only the contract + example
- [ ] At least one non-Lang adapter (CrewAI or MAF or the custom example) has fixtures
- [ ] Langfuse **or** MLflow ingest documented and tested
- [ ] Batch directory → one JSON report
- [ ] Core extras-free tests still green
- [ ] Report still leads with simulation ≠ production

## What “done” looks like for the open-source repo

Someone on LangGraph uses P1. Someone on a house agent uses the custom adapter. Someone on CrewAI or MAF has a path that is not “pretend this is LangGraph.” Agents run the CLI. Humans can too. The architecture advice still comes from the **same** P0 recommender.
