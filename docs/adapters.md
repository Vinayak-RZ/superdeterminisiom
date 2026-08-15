# Adapters

v0 reads traces and (later) adapter **outputs**. It does not install adapters, wrap graphs, or re-bind transports.

## v0: LangGraph / LangChain 1.x only

Use `langchain.agents.create_agent`. Pins used by CAR’s LangGraph adapter: `langchain>=1.3,<2`, `langgraph>=1.2,<2`, `langchain-core>=1.4,<2`.

**`create_react_agent` is deprecated;** removal is slated for LangGraph 2.0. Do not emit it. Do not follow IDE hints to classic `langchain.agents.create_react_agent`.

Also deprecated: `MessageGraph`, `ValidationNode`, Pydantic `AgentState` as the graph state, `prompt=`, `pre_model_hook`. Dynamic prompts and tool errors are middleware.

Two production shapes:

1. Custom `StateGraph` (`llm_call` ↔ `ToolNode` + `should_continue`)
2. `create_agent(...)` with internal nodes `"model"` + `"tools"` (the old `"agent"` name is gone)

v0 must understand both. Classify with `langgraph_node` + child ops ([architecture.md](architecture.md)).

## How neighbors hook in (we do not reimplement them)

| | CAR | Tracefork | counterfact |
|---|---|---|---|
| Repo | [jaineet17/causal-agent-replay](https://github.com/jaineet17/causal-agent-replay) | [pratik916/tracefork](https://github.com/pratik916/tracefork) | [counterfact-labs/counterfact](https://github.com/counterfact-labs/counterfact) |
| Seam | `AgentMiddleware` on `create_agent` | httpx transport + optional callbacks | wrap every `add_node` callable |
| Replay | live model + tools | tape bytes + tape-backed checkpointer | `clone_with_ablation` / `diagnose` |
| Refuses | parallel tools, `Command` tools, Send, subgraphs, truncated runs | unrecorded HTTP | no recipe → no `diagnose` |

A flip **invalidates** CAR trajectories and Tracefork tapes for the changed step. Scaffolds keep the **node name** so a counterfact recipe still clones.

Wrapping these as dependencies is **not** a v0 decision. That needs a later ADR.

## Later adapters

**CrewAI.** Role/task loop, not `StateGraph`. CAR wraps `Agent(llm=...)`; Tracefork binds LiteLLM. Real eval depth comes from DeepEval / Langfuse / MLflow. Not v0.

**Microsoft Agent Framework (MAF).** Autogen + Semantic Kernel unified; 1.0 GA April 2026. Native OTel (`invoke_agent`, `chat`, `execute_tool`). No CAR/Tracefork/counterfact adapter today. **v0 refuses MAF traces** rather than treat them as LangGraph.

## What v0 will not ingest

- Send / map-reduce as a first-class graph
- Command-returning tools as control-flow
- Truncated or unverified tapes
- Traces that cannot be mapped to `langgraph_node` without guessing
