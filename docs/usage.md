# Usage

Agents and humans use the same CLI. No prompts. No auto-apply. Core has **no** LangChain import.

```bash
pip install -e ".[dev]"
python -m superdeterminism recommend traces.json --stdout json
python -m superdeterminism recommend traces.json --json out.json --md out.md --n-min 30
```

Exit `0` if a report was produced (including all-ABSTAIN). Exit `2` on bad input, unknown adapter, or missing extra.

## P1 — LangGraph adapter

```bash
pip install -e ".[dev,langgraph]"
python -m superdeterminism recommend traces.json --adapter langgraph --stdout json
python -m superdeterminism scaffold report.json --out scaffold/RUN
```

`--adapter langgraph` maps `create_agent` (`model`/`tools`) and custom `StateGraph`, then runs the **same** P0 recommender. Without the extra, that flag exits `2`.

`scaffold` writes `REPORT.md`, `WIRING.md`, and `patches/*.diff` under `--out`. It does **not** edit `graph.py`. All-ABSTAIN reports get reasons only (no patches). Do not apply a patch unless a human asked.

Spec: [p1-langgraph.md](p1-langgraph.md).

## Input

Either OTLP JSON (`resourceSpans`) or:

```json
{
  "traces": [
    {
      "spans": [
        {
          "name": "chat gpt-4",
          "attributes": {
            "gen_ai.operation.name": "chat",
            "langgraph_node": "classify"
          },
          "input": {"text": "status"},
          "output": {"intent": "status"},
          "error": false
        }
      ]
    }
  ]
}
```

`langgraph_node` is a generic attribute in P0. P1 owns checkpoint ns, tools wrappers, and the LangSmith retriever→embeddings quirk.

## Output (JSON)

```json
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
      "p_mode_lower": 0.2,
      "schema_ok": 1.0,
      "failure_rate": 0.0,
      "estimator": "observational_l0_proxy",
      "reasons": ["n=1 < n_min=30"],
      "disclaimer": "simulation != production; canary is confirmatory"
    }
  ]
}
```

Actions: `FlipToDet` | `FlipToNondet` | `STRENGTHEN_SDB` | `ABSTAIN`

Default `--n-min 30`. A single-trace file will **ABSTAIN**. That is correct.

P2 (not built): [p2-ecosystem.md](p2-ecosystem.md).
