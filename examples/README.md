# Custom adapter example

Copy [`custom_adapter.py`](custom_adapter.py) when your traces are not LangGraph, Langfuse, MAF, or CrewAI.

The contract is one function:

```python
def load(path_or_bytes: Path | str | bytes) -> list[Trace]:
    ...
```

`--adapter custom` loads this file (`examples.custom_adapter`). No extra is required.

```bash
python -m superdeterminism recommend traces.json --adapter custom --stdout json
```

Rules:

- Return P0 `list[Trace]` only. Do not recommend inside the adapter.
- Do not invent `gen_ai.*` keys. Coalesce vendor fields onto existing `gen_ai.operation.name` values, or leave the span `UNKNOWN` and let the core **ABSTAIN**.
- Keep `NAME = "custom"` or register a new name in `src/superdeterminism/adapters/__init__.py` `_MODULES`.
- If the adapter needs a framework package, add it as an extra and a `_EXTRAS` entry. Missing from `_EXTRAS` means no extra required.

See [docs/p2-ecosystem.md](../docs/p2-ecosystem.md) and [docs/adapters.md](../docs/adapters.md).
