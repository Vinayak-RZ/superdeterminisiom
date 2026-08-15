# Determinism Advisor v0 — LangGraph / LangChain refactor assist

This note is the LangGraph-shaped half of Determinism Advisor v0. v0
**recommends** a step flip (LLM/subagent → deterministic typed tool, or the
reverse) and may later emit a **report + optional scaffold**. It does not
rewrite the user's graph, open a PR, or apply a patch.

Sources: [docs.langchain.com Graph API](https://docs.langchain.com/oss/python/langgraph/use-graph-api),
[graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api),
[workflows vs agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents),
[subgraphs](https://docs.langchain.com/oss/python/langgraph/use-subgraphs),
[interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts),
[checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers),
[LangGraph v1 migration](https://docs.langchain.com/oss/python/migrate/langgraph-v1),
[LangChain v1 migration](https://docs.langchain.com/oss/python/migrate/langchain-v1),
[create_agent](https://docs.langchain.com/oss/python/langchain/agents),
[subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents).
Adapter hook points live in [`docs/adapters.md`](adapters.md).

---

## 1. LangGraph node types (what a scaffold can name)

A production graph is a `StateGraph` whose nodes are just callables. The
interesting types for a flip are not subclasses — they are **how the callable
is wired**.

| Kind | What it is | Import / hook | Flip relevance |
|---|---|---|---|
| **Function node** | `(state) -> dict` (or `Command`) | `StateGraph.add_node(name, fn)` | Default scaffold target. Deterministic tools land here. |
| **Tool** | `@tool` / `BaseTool`; model emits `tool_calls` | `langchain.tools.tool`; executed by `ToolNode` or `create_agent`'s tools node | Typed I/O contract for LLM → tool. |
| **ToolNode** | Prebuilt executor for a tool list | `langgraph.prebuilt.ToolNode` | Stays when the *model* still chooses tools; disappears when a step is lifted out of the ReAct loop. |
| **Subgraph** | Compiled graph used as a node | `add_node("x", compiled)` or `compiled.invoke(...)` inside a wrapper | LLM/subagent side of a tool → LLM flip. |
| **Send** | Dynamic map-reduce fan-out | `from langgraph.types import Send` | Out of v0 scope. CAR already refuses it. |
| **Command** | State update + hop in one return | `from langgraph.types import Command` | Tools may `return Command(update=...)`. CAR v1 refuses Command-returning tools. |
| **interrupt** | Dynamic pause; resume via `Command(resume=...)` | `from langgraph.types import interrupt` | Requires a checkpointer + `thread_id`. Node restarts from the top on resume. |
| **Checkpointer** | Super-step snapshots | `graph.compile(checkpointer=...)` | Persistence / HITL / time-travel. Not a node; a compile-time arg. |

### Function nodes

First argument is always state. Return a **partial update**, do not mutate.

```python
from typing_extensions import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.messages import AnyMessage, AIMessage

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    intent: str

def classify_intent(state: State) -> dict:
    # deterministic: no model
    text = state["messages"][-1].content.lower()
    intent = "refund" if "refund" in text else "other"
    return {"intent": intent}
```

`add_node` accepts either `add_node(fn)` (name = `fn.__name__`) or
`add_node("classify_intent", classify_intent)`.

### Tools

```python
from langchain.tools import tool
from pydantic import BaseModel, Field

class LookupArgs(BaseModel):
    order_id: str = Field(description="Order id, e.g. ORD-1234")

@tool(args_schema=LookupArgs)
def lookup_order(order_id: str) -> str:
    """Fetch a single order by id. Deterministic given the store."""
    return store.get(order_id)
```

A tool is **not** a graph node by itself. It becomes one when:

- a custom graph does `add_node("tools", ToolNode([lookup_order]))`, or
- `create_agent(..., tools=[lookup_order])` builds the internal tools node.

Tools can read graph state via injected `ToolRuntime` (Python) and can return
`Command(update={...})` to write channels. If they return `Command`, use
`ToolNode` (it propagates `Command`); a hand-rolled tool loop must do that
itself. See [Use the graph API → Command inside tools](https://docs.langchain.com/oss/python/langgraph/use-graph-api#use-inside-tools).

### Subgraphs

Two official patterns ([use-subgraphs](https://docs.langchain.com/oss/python/langgraph/use-subgraphs)):

```python
# Shared keys: compiled subgraph *is* the node.
parent.add_node("researcher", researcher_graph.compile())

# Different schemas: wrapper maps parent ↔ child.
def call_researcher(state: ParentState) -> dict:
    out = researcher_graph.invoke({"query": state["question"]})
    return {"notes": out["answer"]}
parent.add_node("researcher", call_researcher)
```

LangGraph can only **statically discover** subgraphs that are added as nodes or
called directly from a node. A subgraph hidden inside a `@tool` is invisible to
`get_state(subgraphs=True)` and to interrupt inspection. That is why the
[subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents)
docs warn: if you need nested state / HITL, invoke the child from a **node**,
not from a tool.

### Send API

`Send(node_name, state_dict)` fans out N copies of a node, each with its own
input. Reducers (`Annotated[list[T], operator.add]`) merge results.

```python
from langgraph.types import Send

def continue_to_jokes(state: OverallState):
    return [Send("generate_joke", {"subject": s}) for s in state["subjects"]]

builder.add_conditional_edges("generate_topics", continue_to_jokes, ["generate_joke"])
```

v0 must **name** a Send hop in the report ("this step is a map-reduce fan-out;
scaffold not generated") and stop. Do not rewrite it into a sequential node.

### Command

```python
from typing import Literal
from langgraph.types import Command

def route(state: State) -> Command[Literal["refund_tool", "talk"]]:
    if state["intent"] == "refund":
        return Command(update={"routed": True}, goto="refund_tool")
    return Command(update={"routed": True}, goto="talk")
```

`Command[Literal[...]]` is required for graph rendering. `graph=Command.PARENT`
hops out of a subgraph; shared keys then **must** have a reducer on the parent.

`Command(resume=...)` is the **only** `Command` meant as *input* to
`invoke` / `stream` / `stream_events`. `update` / `goto` / `graph` are return
values from nodes.

### interrupt

```python
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver

def approval_node(state: State) -> dict:
    approved = interrupt({"action": "issue_refund", "amount": state["amount"]})
    return {"approved": approved}

graph = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "case-42"}}
# pause
graph.invoke({"amount": 80}, config)
# resume — value becomes the return of interrupt()
graph.invoke(Command(resume=True), config)
```

On resume the **whole node restarts**. Side effects before `interrupt()` run
again. Functional-API `task` / `interrupt` order is load-bearing for
determinism ([graph-api compiling notes](https://docs.langchain.com/oss/python/langgraph/graph-api)).

### Checkpointer

Compile-time, not a node:

```python
from langgraph.checkpoint.memory import InMemorySaver
# production: PostgresSaver / sqlite / custom BaseCheckpointSaver

graph = builder.compile(checkpointer=InMemorySaver())
```

Checkpoints are written at **super-step** boundaries (and per-task writes
inside a super-step for pending-write recovery). `thread_id` is the primary
key. Namespace `""` is the root graph; subgraphs use `"node:uuid"` joined by
`|`. Tracefork's tape-backed saver implements the same
`BaseCheckpointSaver` surface (`get_tuple` / `put` / `put_writes` / `list`) —
see [`docs/adapters.md`](adapters.md).

Durable production savers live in separate packages
(`langgraph-checkpoint-postgres`, etc.). v0 never swaps a checkpointer.

---

## 2. What a typical production LangGraph looks like

Two blessed shapes in 2026:

### A. Custom `StateGraph` (workflow you own)

File-path convention in user repos (what the scaffold should grep):

```
src/<app>/graph.py          # StateGraph, add_node / add_edge / compile
src/<app>/state.py          # TypedDict / MessagesState
src/<app>/nodes/*.py        # one callable per node
src/<app>/tools/*.py        # @tool functions
src/<app>/routers.py        # should_continue / path_map
```

Canonical ReAct-shaped custom graph
([workflows-agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents)):

```python
from typing import Literal
from langchain.messages import SystemMessage, ToolMessage
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode

def llm_call(state: MessagesState) -> dict:
    return {"messages": [llm_with_tools.invoke(
        [SystemMessage("You are a support agent.")] + state["messages"]
    )]}

def should_continue(state: MessagesState) -> Literal["tools", "__end__"]:
    last = state["messages"][-1]
    return "tools" if getattr(last, "tool_calls", None) else END

builder = StateGraph(MessagesState)
builder.add_node("llm_call", llm_call)
builder.add_node("tools", ToolNode([lookup_order, issue_refund]))
builder.add_edge(START, "llm_call")
builder.add_conditional_edges("llm_call", should_continue, ["tools", END])
builder.add_edge("tools", "llm_call")
agent = builder.compile(checkpointer=checkpointer)
```

`ToolNode` handles parallel tool execution, error wrapping, `ToolRuntime`
injection, and `Command` propagation. Prefer it over a hand-rolled
`for tool_call in ...` loop unless the scaffold is *replacing* that loop
with a single deterministic node.

### B. `create_agent` (LangChain 1.x harness on LangGraph)

```python
from langchain.agents import create_agent

agent = create_agent(
    model,
    tools=[lookup_order, issue_refund],
    system_prompt="You are a support agent.",
    middleware=[...],          # CAR hooks here
    checkpointer=checkpointer, # same compile-time object
)
# invoke is still a graph:
await agent.ainvoke({"messages": [{"role": "user", "content": "..."}]})
```

Internally this is still `model → tools → model → …`. The streaming node
formerly named `"agent"` is now **`"model"`**
([LangChain v1 migration](https://docs.langchain.com/oss/python/migrate/langchain-v1#streaming-node-name-rename)).
v0 reports and scaffolds must use `"model"`, not `"agent"`.

A production tree often *composes* both: a parent `StateGraph` with
deterministic routers / extractors, and one `create_agent` (or compiled
subgraph) for the hops that still need a model.

---

## 3. Diff: replace an LLM node with a typed tool

Advisor trigger: a step's I/O is regular (enum, id lookup, schema fill,
policy table) and residual nondeterminism is not buying quality.

### 3a. Custom graph — lift the hop out of the ReAct loop

**Before** (`src/app/nodes/classify.py`): the model both classifies and
chats.

```python
def classify(state: State) -> dict:
    ai = llm.invoke([
        SystemMessage("Classify intent as refund|other. Reply with one word."),
        *state["messages"],
    ])
    return {"intent": ai.content.strip().lower(), "messages": [ai]}
```

**After** — two files the scaffold may emit:

`scaffold/generated/tools/classify_intent.py`

```python
from typing import Literal
from pydantic import BaseModel, Field

class ClassifyIn(BaseModel):
    text: str = Field(min_length=1)

class ClassifyOut(BaseModel):
    intent: Literal["refund", "other"]

def classify_intent(text: str) -> ClassifyOut:
    """Deterministic stand-in. Replace the body; keep the types."""
    lowered = text.lower()
    if "refund" in lowered or "money back" in lowered:
        return ClassifyOut(intent="refund")
    return ClassifyOut(intent="other")
```

`scaffold/generated/nodes/classify.py`

```python
from langchain.messages import HumanMessage
from app.tools.classify_intent import classify_intent

def classify(state: State) -> dict:
    text = next(
        m.content for m in reversed(state["messages"])
        if isinstance(m, HumanMessage) or getattr(m, "type", None) == "human"
    )
    return {"intent": classify_intent(text).intent}
```

Wiring note (do **not** auto-edit `graph.py`; print this in the report):

```diff
# src/app/graph.py
- builder.add_node("classify", llm_classify)
+ builder.add_node("classify", classify)   # generated/nodes/classify.py
  builder.add_edge(START, "classify")
  builder.add_conditional_edges("classify", route_on_intent, ["refund_flow", "talk"])
```

The node **name stays `classify`**. Downstream edges, checkpointer channel
layout, and counterfact recipe keys keep working. Only the callable
changes.

### 3b. Still inside `create_agent` — add a typed tool, shrink the prompt

When the hop must remain model-chosen (the model decides *whether* to
look up):

```diff
# src/app/agent.py
  from langchain.agents import create_agent
+ from app.tools.lookup_order import lookup_order

  agent = create_agent(
      model,
-     tools=[],
+     tools=[lookup_order],
-     system_prompt="Look up the order in your head and guess the status.",
+     system_prompt="Call lookup_order before answering status questions.",
  )
```

This is a **weaker** flip: the model still exists. The advisor should say
so. The strong flip is 3a (parent node, no model on that step).

### 3c. Messages-contract variant (keep `ToolNode`)

If other nodes consume `ToolMessage`s, the scaffold should emit an
AIMessage+ToolMessage pair rather than a bare channel write:

```python
from langchain.messages import AIMessage, ToolMessage

def classify(state: State) -> dict:
    out = classify_intent(state["messages"][-1].content)
    call_id = "call_classify_deterministic"
    return {
        "intent": out.intent,
        "messages": [
            AIMessage(content="", tool_calls=[{
                "id": call_id, "name": "classify_intent",
                "args": {"text": state["messages"][-1].content},
            }]),
            ToolMessage(content=out.model_dump_json(), tool_call_id=call_id),
        ],
    }
```

Only emit this shape when a recorded trajectory / CAR reconstruction
depends on `tool_call_id` pairing. Otherwise prefer the plain channel
update in 3a.

### Tests the scaffold may add

`scaffold/generated/tests/test_classify_intent_determinism.py`

```python
import pytest
from app.tools.classify_intent import classify_intent

@pytest.mark.parametrize("text,intent", [
    ("I want a refund for ORD-1", "refund"),
    ("Where is my package?", "other"),
])
def test_classify_is_stable(text, intent):
    assert classify_intent(text).intent == intent
    assert classify_intent(text) == classify_intent(text)  # bit-stable
```

---

## 4. Diff: replace a rigid tool with an LLM / subagent

Advisor trigger: the typed tool's failure mode is "schema too tight"
(unparseable input, novel phrasings, multi-hop research) and attribution
blames *that tool step*, not the model that called it.

### 4a. Custom graph — swap the node callable for a compiled agent

**Before** (`src/app/tools/extract_fields.py`): regex / JSON-only.

```python
@tool
def extract_fields(blob: str) -> str:
    """Parse order_id and amount with a regex. Fails on prose."""
    ...
```

**After** — new subgraph, same parent node name:

`scaffold/generated/subagents/extract_fields.py`

```python
from typing import Literal
from pydantic import BaseModel, Field
from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy  # 1.x; prompted output is gone

class Fields(BaseModel):
    order_id: str | None = None
    amount: float | None = None
    confidence: Literal["high", "low"] = "low"

def build_extractor(model):
    return create_agent(
        model,
        tools=[],
        system_prompt=(
            "Extract order_id and amount from messy user text. "
            "If either is missing, set it null and confidence=low."
        ),
        response_format=ToolStrategy(Fields),  # not a prompt-only schema
    )
```

`scaffold/generated/nodes/extract_fields.py`

```python
def extract_fields(state: State) -> dict:
    result = extractor.invoke({"messages": state["messages"]})
    # ToolStrategy lands a structured payload; adapt to your state keys.
    parsed = Fields.model_validate(result["structured_response"])
    return {"order_id": parsed.order_id, "amount": parsed.amount}
```

Wiring:

```diff
- builder.add_node("extract_fields", ToolNode([extract_fields_regex]))
+ builder.add_node("extract_fields", extract_fields)  # LLM subgraph wrapper
```

Or, if parent and child share `messages`, pass the compiled agent
directly: `builder.add_node("extract_fields", build_extractor(model))`.

### 4b. Subagent-as-tool (supervisor still chooses)

[Subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents)
are tools that invoke a child `create_agent`. The parent stays a
`create_agent`; the rigid tool is replaced by a child loop.

```python
from langchain.tools import tool

extractor = build_extractor(model)

@tool
def extract_fields(text: str) -> str:
    """LLM subagent: extract order_id and amount from messy text."""
    result = extractor.invoke({
        "messages": [{"role": "user", "content": text}]
    })
    return result["messages"][-1].content
```

```diff
  agent = create_agent(
      supervisor_model,
-     tools=[extract_fields_regex],
+     tools=[extract_fields],  # subagent tool
  )
```

Honest limitation (copy into the report): LangGraph **cannot** statically
discover a subgraph invoked from a tool. Nested `interrupt` / `get_state`
will not see the child. If the recommendation includes HITL inside the
new subagent, emit 4a (node-level subgraph), not 4b.

### 4c. Soften a tool in place (same node, smarter body)

Sometimes the graph topology should not change — only the tool body:

```diff
  @tool
  def extract_fields(blob: str) -> str:
-     return regex_or_raise(blob)
+     try:
+         return regex_or_raise(blob)
+     except ParseError:
+         return llm_structured.invoke(blob)  # fallback; mark as nondeterministic
```

v0 may propose this as a **hybrid** with an explicit
`source="llm_fallback"` note for CAR / Tracefork. It is not a topology
edit.

---

## 5. LangChain 1.x / LangGraph 2026 API surface

Pinned ranges used by CAR's extra (mid-2026, verify at install):
`langchain>=1.3,<2`, `langgraph>=1.2,<2`, `langchain-core>=1.4,<2`.
Python **3.10+** (3.9 dropped).

### Blessed vs deprecated

| Symbol | Status (2026) | Use instead |
|---|---|---|
| `langchain.agents.create_agent` | **Current** standard harness | — |
| `langgraph.prebuilt.create_react_agent` | **Deprecated**; removal slated for **LangGraph 2.0** | `create_agent` |
| `langgraph.prebuilt.ToolNode` | Current, custom graphs | still correct |
| `langgraph.prebuilt.ValidationNode` | Deprecated | `create_agent` validates tool args |
| `langgraph.prebuilt.AgentState` (+ Pydantic variants) | Deprecated | `langchain.agents.AgentState` (TypedDict only) |
| `MessageGraph` | Deprecated | `StateGraph` with a `messages` key |
| HITL types (`HumanInterrupt`, …) | Deprecated | `langchain.agents.middleware.human_in_the_loop.*` |
| `config_schema=` on the old prebuilt | Deprecated since ~0.6; gone in 2.0 | `context_schema` / `context=` |

Migration is mechanical for the factory, not for hooks:

```python
# v0 / old
from langgraph.prebuilt import create_react_agent
agent = create_react_agent(model, tools, prompt="...")

# v1 / current
from langchain.agents import create_agent
agent = create_agent(model, tools, system_prompt="...")
```

What actually moved (scaffold authors must not emit the old knobs):

- `prompt=` → `system_prompt=`; dynamic prompts are **middleware**, not a callable prompt.
- `pre_model_hook` / `post_model_hook` → `AgentMiddleware.before_model` / `after_model`.
- Tool error handling → `wrap_tool_call`.
- Structured output: prompted mode **removed**; use `ToolStrategy` / `ProviderStrategy`.
- Runtime injection: `context` argument, not `config["configurable"]`.
- Streaming node name: `"agent"` → `"model"`.
- Pre-bound models are not supported on `create_agent`; bind tools inside the harness.

`create_react_agent` still **runs** on LangGraph 1.x. Do not treat a
deprecation warning as a rewrite mandate. A known footgun: some IDEs
point `create_react_agent` at the **classic** `langchain.agents` ReAct
helper, which does **not** speak `stream_mode="messages"`
([langchain#34613](https://github.com/langchain-ai/langchain/issues/34613)).
The replacement is `langchain.agents.create_agent`, not
`langchain.agents.create_react_agent`.

### `create_agent` as a graph

`create_agent(...)` returns a compiled LangGraph. You can still
`compile`-style things via its kwargs (`checkpointer`, `middleware`,
`state_schema` through middleware). You cannot `add_node` onto it
without wrapping it as a subgraph in a parent `StateGraph`. That is the
v0 rule:

- Flip **inside** the harness → change `tools=` / `middleware=` / `system_prompt=`.
- Flip **out of** the harness → parent `StateGraph` + `add_node`.

---

## 6. What v0 should emit vs refuse

### Do not (v0 hard no)

- Open or apply a PR. No `git commit` of the user's app, no
  `apply_recommendation` against a live `counterfact.StateGraph`.
- Rewrite `graph.py` / `agent.py` in place. The user's checkpointer
  schema, `thread_id` layout, and adapter wraps are load-bearing.
- Invent `Send` / `Command(goto=...)` / `interrupt` rewrites. Report
  "control-flow primitive; human owns this" and stop.
- Hide a new subgraph inside a `@tool` when the recommendation mentions
  HITL, `get_state(subgraphs=True)`, or CAR reconstruction.
- Emit `create_react_agent`, `MessageGraph`, `prompt=`, Pydantic
  `AgentState`, or `"agent"` as the model node name.
- Touch checkpointer choice, reducer annotations, or message-id
  assignment (Tracefork uuid patch / CAR `tool_call_id` pairing).
- Claim bit-exact replay after a flip. A topology change **invalidates**
  old tapes / trajectories; say so.
- Auto-run CrewAI or Microsoft Agent Framework adapters (later; see
  [`docs/adapters.md`](adapters.md)).

### Do (report + optional scaffold)

A v0 run writes a directory the human copies from. Suggested layout:

```
scaffold/<run_id>/
  REPORT.md                         # locus, evidence, flip direction, confidence
  WIRING.md                         # exact add_node / tools= lines to change
  generated/
    tools/<step>.py                 # Pydantic in/out + stub body
    nodes/<step>.py                 # StateGraph callable
    subagents/<step>.py             # only for tool → LLM
    tests/test_<step>_determinism.py
  patches/<step>.diff               # unified diff, never applied
  ADAPTERS.md                       # which wraps to re-bind (see adapters.md)
```

`REPORT.md` must include:

1. **Step identity** — graph node name *and* adapter step id (CAR
   `Step.index`, Tracefork `Step.step_id`, counterfact node key). These
   are not the same string.
2. **Direction** — `llm_to_tool` or `tool_to_llm`.
3. **Evidence** — flip-rate / causal locus / ablation delta, with CIs
   if the upstream engine provided them.
4. **Shape** — `create_agent` harness vs custom `StateGraph` vs subgraph
   vs Send/Command (refused).
5. **Contract** — proposed `ClassifyIn` / `ClassifyOut` (or equivalent)
   inferred from recorded tool args / structured outputs. Mark fields
   the recorder never saw as `TODO`.
6. **Invalidation** — "re-record after applying; old tape/trajectory is
   not comparable."
7. **Adapter follow-up** — one line each for CAR / Tracefork /
   counterfact (re-wrap middleware, re-`bind` the model, keep
   `add_node` name so the recipe still clones).

`patches/*.diff` is illustrative. A later v1 may offer an `--apply`
flag behind an explicit human confirmation; v0 stops at the file.

### How a later generator would work (not v0)

1. Parse the user's graph the same way counterfact already does: record
   `add_node` / `add_edge` / `add_conditional_edges` into a recipe
   (`counterfact/graph.py` `_BuildRecipe`). Do not import
   `counterfact.StateGraph` unless the user already did.
2. Classify each node: `llm` (calls a chat model), `tool` (`ToolNode` or
   `@tool` body), `subgraph` (compiled graph), `control` (Command / Send
   / interrupt).
3. Join advisor output `{node, direction, schema}` to that recipe.
4. Emit the files above. For `create_agent`-only apps, skip the recipe
   and emit `tools=` / parent-wrapper snippets only.
5. Still do not apply.

---

## File-path cheat sheet (LangGraph / LangChain)

| Concern | Upstream path |
|---|---|
| `StateGraph.add_node` / `compile` | `langgraph/graph/state.py` (`libs/langgraph/langgraph/graph/state.py`) |
| `Send`, `Command`, `interrupt` | `langgraph.types` |
| `ToolNode` | `langgraph.prebuilt.tool_node.ToolNode` |
| `create_agent` | `langchain.agents.create_agent` (`langchain/agents/factory`) |
| `AgentMiddleware` (`wrap_model_call`, `wrap_tool_call`) | `langchain.agents.middleware` |
| `create_react_agent` (legacy) | `langgraph.prebuilt` → `langchain-classic` |
| Checkpointer interface | `langgraph.checkpoint.base.BaseCheckpointSaver` |
| In-memory saver | `langgraph.checkpoint.memory.InMemorySaver` |
| Docs (graph) | `https://docs.langchain.com/oss/python/langgraph/use-graph-api` |
| Docs (agents) | `https://docs.langchain.com/oss/python/langchain/agents` |
| Docs (migrate) | `https://docs.langchain.com/oss/python/migrate/langgraph-v1` |
