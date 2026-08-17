<p align="center">
  <img src="assets/superdeterminism-logo.svg" width="560" alt="Superdeterminism — Determinism Advisor">
</p>

<p align="center">
  <a href="docs/README.md"><img src="https://img.shields.io/badge/docs-docs%2F-1f6feb" alt="Docs"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-1f6feb" alt="Apache License 2.0"></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/python-3.10%2B-1f6feb" alt="Python 3.10+"></a>
</p>

<p align="center">
  <a href="docs/README.md"><b>Docs</b></a> ·
  <a href="CONTRIBUTING.md"><b>Contributing</b></a> ·
  <a href="LICENSE"><b>License</b></a>
</p>

> Full internals (every package, file map, how the repo runs): [Extensive README](docs/EXTENSIVE.md)

**Determinism Advisor.** A design-time advisor that ingests production agent traces, reconstructs the graph, and estimates which steps should be deterministic tools versus stochastic LLM/subagents — then recommends a refactor with evidence, or abstains.

The GitHub repository is named `superdeterminisiom`. The project name is **Superdeterminism**.

> **Superdeterminism is a design-time advisor you can run today.** It is not a runtime eval platform, a workflow searcher, or a LangChain-only plugin.
> Primary interface: `python -m superdeterminism recommend`. It never auto-applies a refactor.

## See it running

One recorded `classify` span looks perfectly stable (`p_mode` 1.00). With `n=1` the advisor **ABSTAINs**: the Wilson lower bound is 0.21, so a flip is not justified.

```text
$ python -m superdeterminism recommend tests/fixtures/advisor_stable_llm.json --n-min 1 --stdout json
{
  "disclaimer": "simulation != production; canary is confirmatory",
  "estimator": "observational_l0_proxy",
  "recommendations": [
    {
      "node_id": "classify",
      "node_kind": "llm_reasoner",
      "det_class": "llm",
      "action": "ABSTAIN",
      "n": 1,
      "p_mode": 1.0,
      "p_mode_lower": 0.2065,
      "schema_ok": 1.0,
      "failure_rate": 0.0,
      "estimator": "observational_l0_proxy",
      "reasons": [
        "p_mode point 1.00 meets threshold but wilson_lower 0.21 does not"
      ],
      "disclaimer": "simulation != production; canary is confirmatory"
    }
  ]
}
```

<em>Notice the disclaimer and the action. A confident-looking point estimate is not enough; ABSTAIN is a first-class result.</em>

## Why it exists

Teams guess whether a step should be a typed tool or an LLM/subagent. Eval tools score the path you already ran. Architecture-search papers invent new graphs offline. Neither flips **determinism class** on an ingested production graph.

The unclaimed layer is that re-typing — not “nobody does counterfactual agent simulation.” CAR, CausalFlow, Tracefork, AgentReplay, and counterfact already intervene on traces. Superdeterminism asks a different question: *should this node be a function or a model?*

## Core techniques

- **Determinism-class flip.** Re-type a node between deterministic tool and stochastic LLM/subagent (`FlipToDet` / `FlipToNondet`), on the graph reconstructed from traces. This placement policy is local to [`src/superdeterminism/pipeline.py`](src/superdeterminism/pipeline.py). No external write-up yet; the research contract is [docs/methodology.md](docs/methodology.md). Limit: a recommendation is an estimate, not a production canary.
- **L0 observational tape splice.** Default estimator mutates recorded I/O and scores historical variance (`observational_l0_proxy`). It does not re-run the production LLM. Related: [Causal Agent Replay](https://arxiv.org/abs/2606.08275) (`do_policy` on a step — attribution, not class flip). Limit: L0 is invalid once the next call-site misses the cassette.
- **First-class ABSTAIN.** Default `n_min=30` plus a Wilson lower bound on `p_mode`. Weak evidence yields `ABSTAIN`, not a flip. Limit: fixtures that pass `--n-min 1` are for demos and tests, not customer-facing confidence.
- **Agnostic core + adapters.** Core has zero LangChain import. P1 LangGraph lives in [`src/superdeterminism/adapters/langgraph.py`](src/superdeterminism/adapters/langgraph.py). [LangChain `create_agent`](https://docs.langchain.com/oss/python/langchain/agents) is the P1 graph shape. Limit: P2 (CrewAI / MAF / raw custom) is specified, not built.

## The idea

Think of each agent step as having a **type**: function or model. Superdeterminism does not ask “did this run succeed?” It asks “if we changed the type, would the outcome vector get better?” — then either recommends that change or refuses to guess.

Analogy: a compiler does not score yesterday’s binary; it re-types an expression when the evidence says the cheaper form is equivalent. The invariant: **simulation ≠ production**. A canary with the same outcome vector is confirmatory. Temperature 0 is not a seed ([Defeating Nondeterminism in LLM Inference](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/)).

Advisor-owned fields live in `advisor.*` / `det.*`. Never invent `gen_ai.*` keys. OpenTelemetry GenAI conventions are **Development**; we pin a commit in [docs/ingestion.md](docs/ingestion.md).

## How it works

```text
OTLP or flat traces → normalize spans → architecture graph (node_kind, det.class)
  → L0 offline counterfactual → recommend or ABSTAIN → JSON/MD report + optional scaffold
```

`scaffold` writes `REPORT.md`, `WIRING.md`, and illustrative `patches/*.diff`. It does **not** edit `graph.py`. Details: [docs/architecture.md](docs/architecture.md), [docs/usage.md](docs/usage.md).

## Get started

You need **Python 3.10+**. No API key for the advisor itself; it reads traces you already have.

### 1. Install

```bash
pip install -e ".[dev]"
```

### 2. Run

```bash
python -m superdeterminism recommend tests/fixtures/advisor_stable_llm.json --n-min 1 --stdout json
```

LangGraph ingest (optional extra):

```bash
pip install -e ".[dev,langgraph]"
python -m superdeterminism recommend traces.json --adapter langgraph --stdout json
python -m superdeterminism scaffold report.json --out scaffold/RUN
```

Agents: always `--stdout json`. Humans can add `--md report.md`. Full flags: [docs/usage.md](docs/usage.md).

## Go deeper

| Topic | Doc |
|-------|-----|
| Internals, file map | [docs/EXTENSIVE.md](docs/EXTENSIVE.md) |
| Product brief | [docs/overview.md](docs/overview.md) |
| Claim hygiene | [docs/landscape.md](docs/landscape.md) |
| How a flip is estimated | [docs/methodology.md](docs/methodology.md) |
| OTel ingest | [docs/ingestion.md](docs/ingestion.md) |
| Domain graph | [docs/architecture.md](docs/architecture.md) |
| CLI | [docs/usage.md](docs/usage.md) |
| P1 LangGraph | [docs/p1-langgraph.md](docs/p1-langgraph.md) |
| P2 (specified) | [docs/p2-ecosystem.md](docs/p2-ecosystem.md) |
| Agent instructions | [AGENTS.md](AGENTS.md) |

## Repo layout

```text
src/superdeterminism/   Agnostic core + LangGraph adapter
tests/                  Fixtures + pytest
docs/                   Research contract + EXTENSIVE.md
.cursor/                Vendored coding config
```

## Community

Issues and PRs: [CONTRIBUTING.md](CONTRIBUTING.md). Read [AGENTS.md](AGENTS.md) before changing decision rules.

## Acknowledgements

- [OpenTelemetry GenAI semantic conventions](https://github.com/open-telemetry/semantic-conventions-genai) — ingest interchange (Development; pin a commit, not a tag)
- [LangChain / LangGraph](https://docs.langchain.com/oss/python/langchain/agents) — P1 adapter maps `create_agent` and `StateGraph`; core does not import them
- [Causal Agent Replay](https://arxiv.org/abs/2606.08275) — methodology cites `do_policy` / point-of-commitment; we do not claim CAR’s attribution layer
- [Thinking Machines Lab](https://thinkingmachines.ai/blog/defeating-nondeterminism-in-llm-inference/) — residual nondeterminism of hosted greedy decoding

## License

Apache License 2.0. See [LICENSE](LICENSE).
