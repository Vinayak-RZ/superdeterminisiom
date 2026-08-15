# P1 — LangGraph / LangChain adapter

**Status:** implemented.  
**Depends on:** P0 core (`src/superdeterminism/`).  
**Normative for:** the next implementation PR. Do not start P1 code until this spec is the source of truth.  
**Index:** [roadmap.md](roadmap.md). Adjacent: [adapters.md](adapters.md), [refactor.md](refactor.md), [0003-no-auto-apply.md](decisions/0003-no-auto-apply.md), [0004-agnostic-core.md](decisions/0004-agnostic-core.md).

P1 is the easy drop-in for teams already on LangGraph / LangChain 1.x. Agents and humans run the same CLI. P1 only teaches the core how to read Lang traces and how to emit a **scaffold**. It never auto-applies a patch.

The core still has **zero** LangChain / LangGraph imports. Those imports live only in `superdeterminism.adapters.langgraph`.

## Objective

Take a LangGraph or LangChain 1.x production graph’s traces, map them onto P0 `Trace` / `node_kind` / `det.class`, run the **existing** L0 recommender, and optionally emit a report + scaffold the human (or a coding agent) copies.

P1 does **not** invent a second recommender.

## What P0 already does (do not reimplement)

| Already in P0 | P1 must not redo |
|---|---|
| OTLP JSON + `{traces:[{spans:[...]}]}` ingest | Keep; adapter may *pre-map* then call `recommend_traces` |
| `gen_ai.operation.name` → `node_kind` | Keep as fallback when Lang attrs are missing |
| Reads `langgraph_node` as a **generic** attribute | P1 *owns* the quirks (checkpoint ns, triggers, retriever→embeddings) |
| L0 recommend + Wilson + hard override | Call it; do not fork decision rules |
| `--stdout json` / `--md` / exit 0 on ABSTAIN / exit 2 on bad input | Same contract |
| Stdlib-only default install | Extra is optional |

## Deliverables

| Artifact | What |
|---|---|
| Extra | `pip install superdeterminism[langgraph]` — optional. Core install stays stdlib-only. |
| Mapper | `src/superdeterminism/adapters/langgraph.py` — spans + `langgraph_node` / checkpoint ns → core `Trace` |
| CLI flag | `superdeterminism recommend traces.json --adapter langgraph` |
| Scaffold command | `superdeterminism scaffold report.json --out scaffold/RUN` |
| Quirks | LangSmith OTLP retriever→embeddings; `create_agent` nodes `"model"` + `"tools"` |
| Scaffold tree | `scaffold/<run_id>/{REPORT.md,WIRING.md,patches/*.diff}` — illustrative. Keep **node name**, change callable. |
| Docs | Agent-oriented: one command, JSON schema, “do not apply the patch yourself unless the human asked” |
| Tests | Fixtures for `create_agent` and custom `StateGraph`; no network |

## Pins

```text
langchain>=1.3,<2
langgraph>=1.2,<2
langchain-core>=1.4,<2
```

Use `langchain.agents.create_agent`. **Do not emit `create_react_agent`** (deprecated; removal slated for LangGraph 2.0). Also do not emit `MessageGraph`, `ValidationNode`, Pydantic `AgentState` as the graph state, `prompt=`, `pre_model_hook`. Dynamic prompts and tool errors are middleware.

Two production shapes P1 **must** map:

1. Custom `StateGraph` (`llm_call` ↔ `ToolNode` + `should_continue`)
2. `create_agent(...)` internal nodes `"model"` + `"tools"` (the old `"agent"` name is gone)

Classify with **`langgraph_node` + child ops**, not the word “agent.”

## Package layout (planned)

```text
src/superdeterminism/
  __init__.py              # unchanged — no adapter imports
  models.py                # unchanged — no LangChain types
  pipeline.py              # unchanged recommender; may accept pre-mapped traces
  cli.py                   # add --adapter and scaffold subcommand
  adapters/
    __init__.py            # registry: name → load callable; lazy import
    langgraph.py           # ONLY file that may import langchain / langgraph
tests/adapters/
  test_langgraph.py        # skipped or xfail if extra not installed
  fixtures/
    create_agent_otlp.json
    stategraph_otlp.json
    langsmith_retriever_quirk.json
```

`adapters/__init__.py` must not import `langgraph.py` at module load. Resolve `--adapter langgraph` lazily so `pip install -e ".[dev]"` still runs core tests without the extra.

## CLI (planned)

```bash
pip install -e ".[dev,langgraph]"
python -m superdeterminism recommend traces.json --adapter langgraph --stdout json
python -m superdeterminism scaffold report.json --out scaffold/RUN
```

| Flag / command | Behaviour |
|---|---|
| `--adapter langgraph` | Use the LangGraph mapper, then the P0 recommender |
| `--adapter` omitted | P0 generic ingest (today’s behaviour) |
| `--adapter` unknown | stderr + exit `2` |
| `--adapter langgraph` without extra | stderr: install `[langgraph]` + exit `2` |
| `scaffold` | Writes files under `--out`. Does **not** edit the user’s `graph.py` or open a PR |
| `scaffold` on an all-ABSTAIN report | Writes REPORT.md with reasons only; **no** `patches/*.diff` |

Exit codes stay P0: `0` if a report was produced (including all-ABSTAIN); `2` on bad input / missing extra / unknown adapter.

No prompts. Agents always `--stdout json`.

## Mapping rules (P1-only)

| Incoming | Core |
|---|---|
| `langgraph_node` | `node_id` (overrides span name) |
| `langgraph_checkpoint_ns` nonempty | nested `subagent` / `workflow` boundary |
| `langgraph_triggers` | infer router edges when no span exists |
| LangSmith `span.kind=retriever` | `retriever` even if op was `embeddings` |
| `create_agent` node `tools` wrapping ToolNode | drop scaffolding; keep child `execute_tool` |
| `__start__` / `__end__` | drop |
| Azure / Foundry every-node-`invoke_agent` | remap with `langgraph_node` + child ops |

P0 already *reads* `langgraph_node` if present as a generic attribute. P1 owns the quirks and the scaffold. Do not move LangChain types into `superdeterminism.models`.

Unknown ops → `NodeKind.UNKNOWN` + ABSTAIN. Never invent `gen_ai.*` keys.

## Scaffold rules

From [refactor.md](refactor.md) and [0003-no-auto-apply.md](decisions/0003-no-auto-apply.md):

- Keep `add_node("classify", ...)` name
- FlipToDet → typed function / `@tool` lifted out of the ReAct loop
- FlipToNondet → `create_agent` subgraph wrapped in proposer/verifier/commit/reject
- STRENGTHEN_SDB → keep proposer, emit a gate stub
- ABSTAIN → no patch, reasons only
- Refuse: Send, Command-returning tools, interrupt rewrites, checkpointer swaps
- Do not emit deprecated APIs (`create_react_agent`, `MessageGraph`, …)

`scaffold` writes files. It does **not** edit the user’s `graph.py` or open a PR.

## Implementation phases (when we start P1)

| Phase | Objective | Exit |
|---|---|---|
| 1 | Extra + lazy registry + `--adapter langgraph` wiring | Core tests still pass without extra; missing extra → exit 2 |
| 2 | Mapper for both graph shapes + LangSmith retriever quirk | Fixture tests, no network |
| 3 | `scaffold` command + REPORT / WIRING / illustrative diffs | Never touches user source; ABSTAIN has no patch |
| 4 | Agent docs in [usage.md](usage.md) | One command, JSON schema, no prompts |

One recommender. No decision-rule fork.

## Tests (acceptance)

- Core suite (`python -m pytest -q`) green with **only** `[dev]` installed
- With `[langgraph]`: both graph-shape fixtures map to expected `node_id` / `node_kind`
- LangSmith retriever-as-embeddings fixture maps to `retriever`
- `--adapter langgraph` without extra → exit 2
- `scaffold` writes under `--out` only; a tmp user `graph.py` is bitwise unchanged
- No `import langchain` / `import langgraph` under `src/superdeterminism/` except `adapters/langgraph.py` (grep gate)

## Non-goals (P1)

- Live LLM / L1 / L2 replay
- LangSmith / Langfuse / MLflow **APIs** (file/OTLP export only; live sinks are P2)
- CrewAI, MAF, raw custom adapters (P2)
- Auto-apply, auto-PR
- Wrapping CAR / Tracefork / counterfact as hard dependencies
- Importing LangChain from `superdeterminism.pipeline` or `models.py`
- A `Protocol` class (lands when the **second** adapter exists — P2)

## Exit criteria

- [ ] `pip install -e ".[dev,langgraph]"` ; core tests still pass without the extra
- [ ] `--adapter langgraph` maps both graph shapes on fixtures
- [ ] `scaffold` writes REPORT + illustrative diff; never touches user source
- [ ] Agent docs: one command, JSON schema, no interactive prompts
- [ ] No `import langchain` / `import langgraph` under `src/superdeterminism/` except `adapters/langgraph.py`

## After P1

P2. See [p2-ecosystem.md](p2-ecosystem.md).
