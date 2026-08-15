# Roadmap — P0 / P1 / P2

This repo is an open-source advisor that **agents** (and humans) run against existing agent traces to decide where determinism belongs, then improve the architecture. It is not a LangChain plugin that only works inside one framework.

```text
P2  Lang ecosystem + other stacks     →  src/superdeterminism/adapters/  (implemented)
P1  LangGraph / LangChain adapter     →  src/superdeterminism/adapters/langgraph.py  (implemented)
P0  Agnostic core                     →  src/superdeterminism/  (implemented)
```

The **core never imports LangChain**. Adapters only translate traces (and later scaffolds) into the core model.

## P0 — Agnostic core (implemented)

Package any agent or human can run on exported traces.

- Ingest OTLP JSON **or** a flat advisor trace list
- Map spans → `node_kind` + `det.class`
- L0 recommend: Wilson intervals, FlipToDet / FlipToNondet / STRENGTHEN_SDB / ABSTAIN
- Hard override for commit / spend / PII / auth names
- CLI JSON (agents) + Markdown (humans)
- Stdlib only. No live LLM. No auto-apply

```bash
python -m superdeterminism recommend traces.json --stdout json
```

Usage: [usage.md](usage.md).

## P1 — LangGraph / LangChain adapter (implemented)

Easy drop-in for LangGraph / LangChain 1.x.

```bash
pip install -e ".[langgraph]"
python -m superdeterminism recommend traces.json --adapter langgraph --stdout json
python -m superdeterminism scaffold report.json --out scaffold/RUN
```

Full spec: **[p1-langgraph.md](p1-langgraph.md)**. Usage: [usage.md](usage.md).

- Optional extra `[langgraph]`
- `--adapter langgraph` maps `create_agent` and custom `StateGraph`
- Scaffold (keep node name). Never auto-apply
- No LangChain types in `superdeterminism.models`

## P2 — Lang ecosystem + other agent systems (implemented)

Pluggable adapters. Same P0 recommender.

```bash
python -m superdeterminism recommend traces.json --adapter custom --stdout json
python -m superdeterminism recommend --traces-dir DIR --stdout json
python -m superdeterminism recommend traces.json --opt-in-l1 --stdout json
```

Full spec: **[p2-ecosystem.md](p2-ecosystem.md)**. Usage: [usage.md](usage.md).

- Track A: Langfuse coalesce (tested); MLflow omitted ops stay UNKNOWN
- Track B: custom example, CrewAI kickoff→workflow, MAF dedicated mapper
- `--adapter langgraph` refuses MAF-shaped traces
- Opt-in L1 is a gate, not a live runner; L0 remains default

## Shared rules (all tiers)

- Simulation ≠ production
- Never invent `gen_ai.*` keys
- No auto-apply / no in-place `graph.py` rewrite
- ABSTAIN is first-class
- Agents drive the CLI (JSON in/out, no prompts); humans can too
- One recommender. Many adapters.
