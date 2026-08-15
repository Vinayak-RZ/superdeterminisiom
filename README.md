# Superdeterminism

**Determinism Advisor** — an open-source design-time advisor for agentic architectures.

It takes an existing agent graph (via production traces), runs **counterfactual re-typing** of nodes between deterministic tools and stochastic LLM/subagents, and tells developers which steps should be hard-coded versus delegated to a model — with evidence, not gut feel.

> Not “score the path you already ran.” Not “search a new workflow from scratch.”
> Counterfactual *re-typing* of nodes on ingested production graphs.

The GitHub repository is still named `superdeterminisiom`. The project name is **Superdeterminism**.

## The problem

Every team on LangChain, LangGraph, CrewAI, or a custom stack eventually asks: *should this step be a typed tool call, or should I hand it to the model?*

Today that decision is intuition, then (maybe) validated after the fact by eval platforms. Those tools score what a trace **did**. They do not simulate what it **would do** under a different determinism split, and they do not recommend a structural change.

The failure modes are symmetric:

- Over-delegate to LLMs where a function would be cheaper, faster, and auditable.
- Over-constrain with rigid tools where the task needs judgment, and the agent breaks on the first uncoded edge case.

## What it does

1. **Ingest** — read existing execution traces over OTLP / GenAI semantic conventions. No new instrumentation required if you already emit LangSmith, Langfuse, MLflow, or raw OTel.
2. **Map** — reconstruct the architecture as a graph. Tag each step as currently deterministic or non-deterministic from observed behavior.
3. **Simulate** — for ambiguous or high-variance steps, estimate the counterfactual: *what if this node were the other type?* v0 does this offline (historical variance + tape splice). It does not re-run your production LLM by default.
4. **Recommend** — a ranked list of flips with estimated deltas (cost, latency, failure, variance, auditability, compliance) and confidence intervals. Abstain when the evidence is weak.
5. **Assist the refactor** — for LangGraph/LangChain, emit a report and an optional scaffold. v0 does **not** rewrite your graph or open a PR.

## Who it is for

Developers past the prototype stage who need evidence for where determinism belongs — especially in regulated or cost-sensitive systems, where non-determinism has to be justified or minimized.

## What already exists (and what does not)

Eval and observability platforms (LangSmith, MLflow, DeepEval, Galileo, Langfuse) **observe and score** runs. Counterfactual replay tools (CAR, CausalFlow, Tracefork, AgentReplay, counterfact) **intervene on actions or agents**. Architecture-search papers (MaAS, AFlow) **invent new workflows offline**.

None of them flip *determinism class* on an ingested production graph and recommend a refactor. That is the layer this project claims. See [docs/landscape.md](docs/landscape.md) for the closeness matrix and the claims we will **not** make.

## Status

**Documentation and research only.** There is no simulator, CLI, or adapter code in this repository yet.

v0 (when implemented) is LangGraph/LangChain only, read-only OTLP ingest, recommendation as a report. See [docs/roadmap.md](docs/roadmap.md).

## Documentation

| Doc | What it covers |
|---|---|
| [docs/README.md](docs/README.md) | Doc map |
| [docs/overview.md](docs/overview.md) | Problem, loop, audience, why now |
| [docs/landscape.md](docs/landscape.md) | Adjacent tools; safe vs unsafe claims |
| [docs/ingestion.md](docs/ingestion.md) | OTel GenAI substrate and vendor quirks |
| [docs/architecture.md](docs/architecture.md) | Domain model: `node_kind`, `det.class` |
| [docs/methodology.md](docs/methodology.md) | How a determinism flip is estimated |
| [docs/adapters.md](docs/adapters.md) | LangGraph v0; later CrewAI / MAF |
| [docs/refactor.md](docs/refactor.md) | Report + scaffold; no auto-apply |
| [docs/roadmap.md](docs/roadmap.md) | v0 scope, non-goals, risks |
| [docs/references.md](docs/references.md) | Bibliography (dated 2026-08-15) |
| [docs/decisions/](docs/decisions/) | ADRs |

## License

Apache License 2.0. See [LICENSE](LICENSE).
