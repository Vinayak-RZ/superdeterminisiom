# Ingestion

How traces enter Superdeterminism. The interchange is **OTLP**. The domain model is not OTel — see [architecture.md](architecture.md).

**Convention pin (Development, no tags):** [open-telemetry/semantic-conventions-genai](https://github.com/open-telemetry/semantic-conventions-genai) commit `c739977ae690961f36e435504e5c1febaef1f7f3` (2026-07-30), as verified by [Konishi 2026-08-02](https://hidekazu-konishi.com/entry/opentelemetry_genai_semantic_conventions_guide.html). Core repo [v1.42.0](https://github.com/open-telemetry/semantic-conventions/releases/tag/v1.42.0) (2026-06-12) deprecated and moved all `gen_ai.*` material. Do not cite a GenAI semconv version after that; cite a **commit**.

Every GenAI document is **Status: Development**. Names may change. Pin instrumentation versions. Record `advisor.schema_version` on every imported trace.

## What we consume

Prefer `gen_ai.operation.name` when present. Well-known values (all Development):

| Value | Meaning |
|---|---|
| `chat` / `generate_content` / `text_completion` | Model inference |
| `execute_tool` | Tool execution (`execute_tool {gen_ai.tool.name}`) |
| `invoke_agent` | Agent invocation (CLIENT remote / INTERNAL in-process) |
| `invoke_workflow` | Graph / crew / runner entry |
| `plan` | Explicit planning (only if instrumentation can tell it from generic reasoning) |
| `retrieval` | Vector / search retrieve |
| `embeddings` | Embeddings (usually supporting, not a graph step) |
| `create_agent` | Hosted agent creation |
| memory ops | `search_memory`, `create_memory`, `update_memory`, `upsert_memory`, `delete_memory`, store lifecycle |
| MCP | Not an operation name. `tools/call` sets `gen_ai.operation.name = execute_tool` |

Do **not** invent `gen_ai.*` keys. Advisor fields live in `advisor.*` / `det.*`.

## Dual-key coalescing

Producers still emit mixed generations. Coalesce; never sum token pairs (duplicates are the same count):

- `COALESCE(gen_ai.provider.name, gen_ai.system)`
- `COALESCE(gen_ai.usage.input_tokens, gen_ai.usage.prompt_tokens)`
- `COALESCE(gen_ai.input.messages, gen_ai.prompt.*)`

## Vendor quirks (v0 must handle)

| Producer | Quirk |
|---|---|
| LangSmith OTLP | Maps `retriever` → `embeddings`. Prefer `langsmith.span.kind=retriever`. Run type `chain` is not `invoke_workflow`. |
| Official SIG LangChain instrumentor | `opentelemetry-instrumentation-genai-langchain` — closest to spec. Not the Traceloop wheel `opentelemetry-instrumentation-langchain`. |
| OpenInference | Parallel vocabulary (`openinference.span.kind`). LangGraph node named `researcher` is often `CHAIN`, not `AGENT`. |
| OpenLLMetry | Extra `traceloop.span.kind`; often legacy token keys. |
| MLflow ingest | Table omits `invoke_workflow`, `plan`, `retrieval`, memory. |
| Azure / Foundry tracer | Every LangGraph node → `invoke_agent`; retrievers sometimes → `execute_tool`. Remap with `langgraph_node`. |

## v0 ingest paths (LangGraph / LangChain only)

**Path A — LangSmith OTLP** if they already use LangSmith: `LANGSMITH_OTEL_ENABLED=true`, fan-out via collector. Docs: [Trace with OpenTelemetry](https://docs.langchain.com/langsmith/trace-with-opentelemetry).

**Path B — SIG instrumentor** (preferred if starting fresh):

```text
pip install opentelemetry-instrumentation-genai-langchain
OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental
```

**Path C — Azure tracer** only if they already sink to App Insights. Inflated `subagent` count; remap.

LangGraph injects `langgraph_node`, `langgraph_step`, `langgraph_triggers`, `langgraph_path`, `langgraph_checkpoint_ns`. v0 classifies with **`langgraph_node` + child ops**, not the word “agent.” SIG comment: LangGraph nodes are Python functions; there is no `invoke_agent` unless metadata asks for it.

## Gaps OTel does not cover

| Advisor concept | In spec? | Closest signal |
|---|---|---|
| Subagent handoff | No (PR #98 unreleased; out of scope for LangGraph) | Nested `invoke_agent` / `invoke_workflow` + `langgraph_checkpoint_ns` |
| Determinism class | No | Heuristic from op + children + temperature/seed |
| Delegation boundary | No | Parent/child + checkpoint namespace |
| Conditional edge | Often no span | Infer from `langgraph_triggers` and sibling order |

## Privacy

Message bodies, tool args/results, and retrieval docs are **Opt-In**. Do not require content capture for v0 mapping. Content helps L0 splice; if absent, abstain on that step.

ADR: [0001-otel-ingest.md](decisions/0001-otel-ingest.md).
