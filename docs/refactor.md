# Refactor assist

v0 **recommends** a flip and may emit a **report + optional scaffold**. It does not rewrite the user’s graph, open a PR, or apply a patch.

ADR: [0003-no-auto-apply.md](decisions/0003-no-auto-apply.md).

## Rule

Keep the **node name**. Change the callable. Tell the human which `add_node` / `tools=` line to edit. Re-record after apply — old CAR trajectories and Tracefork tapes are not comparable.

## Node kinds a scaffold can name

| Kind | Hook | Flip note |
|---|---|---|
| Function node | `StateGraph.add_node(name, fn)` | Default scaffold target |
| Tool | `langchain.tools.tool` | Typed I/O; not a node until `ToolNode` / `create_agent` |
| ToolNode | `langgraph.prebuilt.ToolNode` | Stays when the model still chooses tools |
| Subgraph | `add_node("x", compiled)` | LLM/subagent side of a tool → LLM flip |
| Send | `langgraph.types.Send` | **v0 refuses** |
| Command | `Command(update=, goto=)` | CAR v1 refuses Command-returning tools |
| interrupt | `interrupt(payload)` | Node restarts from the top on resume |
| Checkpointer | `compile(checkpointer=...)` | Not a node |

## LLM → typed tool

Strong flip: lift the hop **out** of the ReAct loop.

```diff
- builder.add_node("classify", llm_classify)
+ builder.add_node("classify", classify)  # generated/nodes/classify.py
```

Scaffold emits typed in/out, a pure function, a node wrapper, and a stability test. Weaker flip: add `@tool` to `create_agent(..., tools=)` and leave the model in charge.

## Rigid tool → LLM / subagent

```diff
- builder.add_node("extract_fields", ToolNode([extract_fields_regex]))
+ builder.add_node("extract_fields", extract_fields)  # create_agent subgraph
```

Use structured-output strategies current to LangChain 1.x (`ToolStrategy` / `ProviderStrategy`). Subagent-as-tool is OK only if HITL / nested state is not required. Wrap any new LLM in the four-part gate from [methodology.md](methodology.md). Bare FlipToNondet of a commit path is forbidden.

## What v0 may emit

```text
scaffold/<run_id>/
  REPORT.md
  WIRING.md
  ADAPTERS.md
  generated/{tools,nodes,subagents,tests}/
  patches/*.diff          # illustrative; human copies
```

## What v0 must not do

- Auto-apply PRs or rewrite `graph.py` in place
- Invent Send / Command / interrupt edits
- Hide HITL subgraphs inside tools
- Emit deprecated APIs (`create_react_agent`, `MessageGraph`, …)
- Swap checkpointers
- Claim bit-exact replay across a flip
