# Roadmap — P0 / P1 / P2

This repo is an open-source advisor that **agents** (and humans) run against existing agent traces to decide where determinism belongs, then improve the architecture. It is not a LangChain plugin that only works inside one framework.

Layering:

```text
P2  Lang ecosystem sinks + other frameworks (CrewAI, MAF, raw/custom)
P1  LangGraph / LangChain adapter (easy drop-in)
P0  Agnostic core  ← no framework dependency
```

The **core never imports LangChain**. Adapters only translate traces and (later) scaffolds into the core model.

## P0 — Agnostic core (this implementation)

A Python package any agent or human can run on exported traces.

- Ingest OTLP JSON **or** a flat advisor trace list (no live collector)
- Map spans → `node_kind` + `det.class` from GenAI ops (and dual keys)
- L0 recommend: historical variance, Wilson intervals, FlipToDet / FlipToNondet / STRENGTHEN_SDB / ABSTAIN
- Hard override for commit / spend / PII / auth node names
- CLI + JSON report (stable for agents) and Markdown (for humans)
- Stdlib only. No LangChain, no live LLM, no auto-apply
- Tests on fixtures

**Who runs it:** `python -m superdeterminism recommend traces.json --json`

**Non-goals for P0:** LangGraph remapping, scaffolds, LangSmith/Langfuse APIs, L1/L2 replay, other frameworks.

## P1 — LangGraph / LangChain adapter

Thin layer **on top of** P0. Core stays framework-free.

- Map `langgraph_node`, `create_agent` (`model` / `tools`), LangSmith OTLP quirks
- Optional scaffold (keep node name, change callable). Never auto-apply
- Agent-oriented docs: “here is the one command and the JSON schema”
- Extra: `superdeterminism[langgraph]` optional extra only

Does **not** put LangChain types in the core graph.

## P2 — Lang ecosystem + other agent systems

By P2 the same core should plug into:

| Track | What |
|---|---|
| Lang development system | LangSmith / Langfuse / MLflow OTLP sinks, more of LangChain than LangGraph |
| Other stacks | CrewAI, Microsoft Agent Framework, raw/custom agents via a documented adapter contract |
| Simulation depth | L1 hybrid fork for high-EV candidates; batch many traces |
| Robustness | planted-truth fixtures in CI, coverage reports, canary checklist |

Adapter contract (P2, not implemented in P0): ingest bytes/spans → core `Trace` list. One extra per framework. Core still has zero framework imports.

## Shared rules (all tiers)

- Simulation ≠ production
- Never invent `gen_ai.*` keys
- No auto-apply / no in-place `graph.py` rewrite
- ABSTAIN is first-class
- Designed so **agents** can drive the CLI (JSON in/out, no prompts); humans can too
