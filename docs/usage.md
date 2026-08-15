# Usage (P0 core)

Agents and humans use the same CLI. No prompts. No auto-apply. Core has **no** LangChain import.

```bash
pip install -e ".[dev]"
python -m superdeterminism recommend traces.json --stdout json
python -m superdeterminism recommend traces.json --json out.json --md out.md --n-min 30
```

Exit `0` if a report was produced (including all-ABSTAIN). Exit `2` on bad input.

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

`langgraph_node` is read as a generic attribute in P0. P1 adds a real LangGraph adapter (`--adapter langgraph` + `scaffold`). Spec: [p1-langgraph.md](p1-langgraph.md).

## Output actions

`FlipToDet` | `FlipToNondet` | `STRENGTHEN_SDB` | `ABSTAIN`

Default `--n-min 30`. A single-trace file will **ABSTAIN** (Wilson lower bound will not clear 0.70). That is correct.

Every report includes `simulation != production; canary is confirmatory`.

P1 (not built): [p1-langgraph.md](p1-langgraph.md) — `--adapter langgraph` + scaffold.  
P2 (not built): [p2-ecosystem.md](p2-ecosystem.md) — Lang sinks + CrewAI/MAF/custom.
