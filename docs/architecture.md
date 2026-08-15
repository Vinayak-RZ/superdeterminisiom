# Architecture

Domain model for Superdeterminism. OTel is the interchange ([ingestion.md](ingestion.md)); this file is the contract we persist. Role flips: [type-lattice.md](type-lattice.md). Hub: [orchestrator.md](orchestrator.md).

## Graph

Reconstruct \(G = (V, E)\) from traces. Nodes are *architecture steps*, not raw spans. Drop scaffolding (`__start__`, `__end__`, ToolNode wrappers that only fan out).

Each node has:

| Field | Meaning |
|---|---|
| `node_kind` | See enum below |
| `det.class` | Advisor-owned determinism class |
| `schema` | Input/output contract if known |
| `side_effects` | Whether the node mutates the world |
| `langgraph_node` | Framework name, when present |

`node_kind` is a **versioned internal enum**. Never persist raw `gen_ai.operation.name` as the graph contract.

```text
node_kind ∈ {
  deterministic_tool,
  llm_reasoner,
  subagent,
  router,
  retriever,
  workflow
}
```

## Mapping: span → node_kind

| Incoming signal | → `node_kind` |
|---|---|
| `invoke_workflow` | `workflow` |
| `invoke_agent` / `create_agent` | `subagent` if nested under another agent/workflow; else envelope + inner `chat` = `llm_reasoner` |
| `chat` / `generate_content` / `text_completion` / `plan` | `llm_reasoner` |
| `execute_tool` + type `function`/`extension` + no LLM/`invoke_agent` children + name not `transfer_to_*` / `handoff` | `deterministic_tool` |
| `execute_tool` + child `invoke_agent` or `transfer_to_*` | `router` + target `subagent` |
| `retrieval` / `search_memory` / `gen_ai.tool.type=datastore` / OpenInference `RETRIEVER` / LangSmith `retriever` | `retriever` |
| `embeddings` | supporting; attach to following retriever or drop |
| Memory writes | `deterministic_tool` unless the store calls an LLM |
| MCP `tools/call` | same as `execute_tool` (dedup if both present) |
| OpenInference `CHAIN` / LangSmith `chain` | `router` if only fan-in/out; `workflow` if it wraps a subgraph; else drop |
| Conditional / `goto` / `Command` | `router` |

## det.class (Advisor-owned)

| `node_kind` | default `det.class` |
|---|---|
| `deterministic_tool` | `deterministic` (unless allowlist says `external` / `timeful`) |
| `retriever` | `stochastic_index` |
| `llm_reasoner` | `llm` (promote to `llm_seeded` only if seed **and** temperature=0 — still not a seed; see methodology) |
| `subagent` | `composite` (inherit worst child) |
| `router` | `deterministic` if code-edge; `llm` if the model chose the next node |
| `workflow` | `composite` |

A **role flip** changes `node_kind` and usually `det.class` at a *decision* node, not at the side-effecting descendant. A **determinism flip** is the subset that only changes `det.class` (tool ↔ LLM). CAR’s point-of-commitment rule: flip the latest step whose interval still excludes zero, not the tool that executed the harm.

The **orchestrator** is not a seventh `node_kind`. It is a graph-level envelope identified from root `invoke_workflow` / parent `invoke_agent` / kickoff. Advisor labels: `advisor.orchestrator.id`, `advisor.orchestrator.kind`. Never invent `gen_ai.orchestrator.*`.

## Example — LangGraph ReAct + subgraph

Support agent, three tools (`lookup_order`, `issue_refund`, `search_kb`), subgraph `policy_check` (rules + one LLM). After mapping:

```text
workflow:support_triage
  ├─ llm_reasoner:agent#1
  ├─ deterministic_tool:lookup_order
  ├─ llm_reasoner:agent#2
  ├─ retriever:search_kb
  ├─ deterministic_tool:issue_refund
  ├─ subagent:policy_check          # inferred boundary
  │    ├─ deterministic_tool:rules
  │    └─ llm_reasoner:justify
  └─ llm_reasoner:agent#3
```

Missing on the wire and inferred: `det.class`, handoff, conditional edges, “chosen together” for parallel tools (shared parent + overlapping time).

## What we will not model in v0

- Send / map-reduce fan-out
- Command-returning tools as first-class control
- Microsoft Agent Framework traces as LangGraph (dedicated `--adapter maf` or refuse)
- Invented `gen_ai.agent.handoff.*` or `gen_ai.orchestrator.*`
