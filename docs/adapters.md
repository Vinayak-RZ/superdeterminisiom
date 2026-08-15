# Determinism Advisor v0 — framework adapters

How existing record / replay / attribution tools hook into LangGraph today,
and what that means for a later refactor scaffold. Pair with
[`docs/refactor.md`](refactor.md) (node types, flip diffs, v0 non-goals).

v0 reads adapter **outputs** (a trajectory, a tape, a diagnostic report). It
does not install adapters, wrap graphs, or re-bind transports.

---

## Hook comparison (LangGraph)

| | **CAR** (`causal-agent-replay`) | **Tracefork** | **counterfact** |
|---|---|---|---|
| Repo | [jaineet17/causal-agent-replay](https://github.com/jaineet17/causal-agent-replay) | [pratik916/tracefork](https://github.com/pratik916/tracefork) | [counterfact-labs/counterfact](https://github.com/counterfact-labs/counterfact) |
| LangGraph module | `src/car/adapters/langgraph.py` | `src/tracefork/adapters/langchain.py` | `counterfact/graph.py` (+ `tracing.py`) |
| Extra | `causal-agent-replay[langgraph]` | `tracefork[frameworks]` | core dep on `langgraph` (drop-in import) |
| Capture seam | `AgentMiddleware` on `create_agent` | httpx transport on the chat model + optional callbacks | wrap every `add_node` callable |
| Step structure | CAR `Trajectory` / `Step` | `StepDAG` from `BaseCallbackHandler` | `TracingContext` per node |
| Replay | `LangChainPolicy` + `LangChainToolEnvironment` (live model/tools) | tape bytes + `make_tape_backed_checkpointer` | `clone_with_ablation` / `diagnose` re-runs the graph |
| Supported shape | `create_agent` / `create_react_agent` **linear** tool loop | any graph whose model talks OpenAI/Anthropic httpx | any `StateGraph` built through `counterfact.StateGraph` |
| Honest refusals | parallel tool calls, `Command` tools, Send, subgraphs, truncated runs | unrecorded HTTP (hard error on replay) | no recipe → no `diagnose` (raw LangGraph) |

A flip **invalidates** CAR trajectories and Tracefork tapes for the changed
step (I/O contract moved). counterfact's recipe still clones if the **node
name** is unchanged — which is why scaffolds keep `add_node("classify", ...)`.

---

## CAR — `create_agent` middleware

### Files

```
src/car/adapters/__init__.py          # package docstring; lists extras
src/car/adapters/langgraph.py         # LangGraphRecorder, LangChainPolicy,
                                      # LangChainToolEnvironment,
                                      # disable_parallel_tool_calls()
src/car/adapters/crewai.py            # later; see below
src/car/adapters/openai_agents.py
RESEARCH/phase_5_adapters.md          # faithfulness analysis (2026-06-11)
RESEARCH/phase_7_crewai.md
```

Pins (from `RESEARCH/phase_5_adapters.md`): `langchain>=1.3,<2`,
`langgraph>=1.2,<2`, `langchain-core>=1.4,<2`.

### How it hooks

CAR does **not** wrap `StateGraph`. It wraps LangChain 1.x
`create_agent` via `AgentMiddleware`:

```python
from langchain.agents import create_agent
from car.adapters.langgraph import (
    LangGraphRecorder,
    LangChainPolicy,
    LangChainToolEnvironment,
    disable_parallel_tool_calls,
)
from car.record.recorder import codec_for

recorder = LangGraphRecorder()
agent = create_agent(
    model,
    tools,
    system_prompt="...",
    middleware=[
        disable_parallel_tool_calls(),  # BEFORE the recorder
        recorder,
    ],
)
await agent.ainvoke({"messages": [HumanMessage("...")]})
trajectory = recorder.trajectory("my-run")
```

Why middleware, not callbacks or the checkpointer
(`RESEARCH/phase_5_adapters.md`):

- `wrap_model_call(request, handler)` sees the full **logical** request:
  `messages`, the per-request `system_message` (this **never** enters graph
  state — `create_agent` injects it at call time), `tools`, the `model`
  object, `model_settings`.
- `wrap_tool_call` sees `{name, args, id}` and the resulting `ToolMessage`.
- Callbacks (`on_chat_model_start`) lose clean tool schemas in 1.x.
- Checkpointer mining has no system prompt, no schemas, no sampling.

Messages are stored in the **OpenAI-projected** wire format via public
`convert_to_openai_messages` / `convert_to_openai_tool`, so
`DeterministicReplay.verify_reconstruction` is the same invariant as the
native recorder. Provider is `"langchain"`.

### Replay / attribution

```python
result = await contrastive_attribution(
    trajectory,
    policy=LangChainPolicy(model),               # resample YOUR model
    environment=LangChainToolEnvironment(tools), # rerun YOUR tools
    codec=codec_for("langchain"),
    outcome_fn=...,
    bad_label=...,
)
print(result.causal_locus)
```

`LangChainPolicy.sample` rebuilds
`[SystemMessage(state.system_prompt)] + convert_to_messages(state.messages)`
and `bind_tools(state.tool_schemas)`. Construction-time model settings are
**not** re-applied in v1.

`LangChainToolEnvironment.observe` invokes the real tool with a full
ToolCall dict (`name` / `args` / `id` / `type`) so `InjectedToolCallId`
works. Tools that need `ToolRuntime` / `InjectedState` raise rather than
being silently stubbed.

### What CAR will refuse after a flip

`LangGraphRecorder.trajectory()` raises `ReplayError` (never guesses) when:

- nothing was recorded (middleware not installed);
- more than one `tool_call` in a turn — ship `disable_parallel_tool_calls()`;
- a tool returns anything other than `ToolMessage` (**`Command` tools**);
- a final answer appears mid-loop, or the run never finals (interrupt /
  truncated);
- unmatched `tool_call_id`s (parallel execution or a non-linear graph);
- Send-API fan-out, supervisor/swarm, subgraphs, `jump_to` short-circuits.

**Scaffold implication:** an `llm_to_tool` flip that lifts a hop *out* of
`create_agent` into a parent `StateGraph` node is **outside CAR v1's
certified shape**. The report must say: "re-record the remaining
`create_agent` loop; the new parent node is invisible to
`LangGraphRecorder`." A `tool_to_llm` flip that stays inside
`create_agent` (new child called as a tool) is recordable only if the
child is a string-returning `@tool` and still one call per turn — the
child's inner model calls are **not** CAR steps.

Do not point the user at `create_react_agent` "for CAR compatibility."
CAR accepts that shape as legacy; the blessed wrap is `create_agent`.

---

## Tracefork — transport bind + optional checkpointer

### Files

```
src/tracefork/adapters/__init__.py     # re-exports; import-guarded
src/tracefork/adapters/base.py         # FrameworkAdapter, Step, StepDAG
src/tracefork/adapters/langchain.py    # LangChainAdapter, TraceforkCallbackCore,
                                       # TapeBackedCheckpointStore,
                                       # make_callback_handler,
                                       # make_tape_backed_checkpointer
src/tracefork/adapters/crewai.py       # later
src/tracefork/transport.py             # the actual byte seam
src/tracefork/tape.py
```

`langchain-*` / `langgraph` are optional. `import tracefork` and the
offline suite run with none of them installed. Real imports happen only
inside `require_langchain` / `require_langgraph` and the two factories.

### How it hooks

Two seams, **one** byte capture (httpx). Callbacks never capture bytes.

```python
from tracefork import (
    LangChainAdapter,
    make_callback_handler,
    make_tape_backed_checkpointer,
)

adapter = LangChainAdapter()
# Replay: ChatOpenAI via root_client.copy(http_client=...);
# ChatAnthropic has no http_client — bind seeds _client / _async_client
# with object.__setattr__ before first cached_property access.
result = adapter.bind(chat_model, tape, mode="replay")

handler = make_callback_handler()          # BaseCallbackHandler → StepDAG
checkpointer = make_tape_backed_checkpointer(tape)

graph = builder.compile(checkpointer=checkpointer)
graph.invoke(inputs, config={"configurable": {"thread_id": "t1"}},
             # plus the handler on the model / graph callbacks
)
```

`LangChainAdapter.bind`:

| Family | Detection | Injection |
|---|---|---|
| OpenAI | `"openai"` in module, or `root_client` | `root_client.copy(http_client=...)`; re-point `client` / `async_client` at `.chat.completions` |
| Anthropic | `"anthropic"` in module/class | replay: fresh `Anthropic(http_client=...)`; record: copy existing client and swap transport |
| unknown | — | `injected_fields=()` + a notes string; nothing silent |

On replay, `patch_uuid=True` installs a `ReplayNondet`-backed uuid patch
so framework-generated ids match the tape.

`make_tape_backed_checkpointer(tape)` returns a `BaseCheckpointSaver`
(`TapeBackedCheckpointer`) that implements `get_tuple` / `put` /
`put_writes` / `list`. `put_writes` is a no-op: the tape, not pending
writes, is the source of LLM I/O truth. `put` stores
`(checkpoint, metadata)` keyed by `configurable.thread_id` /
`checkpoint["id"]` and records `tape_index=len(tape.exchanges)`.

Together: LangGraph time-travel restores **graph** state from the
checkpointer; the bound model replays **bytes** from the tape. That is
the "bit-exact and $0" story in the module docstring.

`TraceforkCallbackCore` mirrors `BaseCallbackHandler` method names
(`on_chain_*`, `on_llm_*`, `on_chat_model_*`, `on_tool_*`) but does not
import LangChain. `make_callback_handler` is the thin subclass.

### Scaffold implication

- An `llm_to_tool` flip that **removes** a model call also removes a
  tape exchange. Replay of the *old* tape against the *new* graph will
  sha256-fail (request body no longer matches) or error on an
  unrecorded request. Report: "re-record; do not `tracefork verify`
  across the flip."
- Keep using `adapter.bind(model, tape)` on whatever chat model
  **remains**. The new deterministic node does not need a transport.
- If the user compiles with `make_tape_backed_checkpointer`, do not
  swap it. Node-name-stable flips still checkpoint; the tape just has
  fewer LLM exchanges.
- Do not emit a second capture path (custom callback that logs
  payloads). That would violate Tracefork's "callbacks are
  observer-only" invariant.

---

## counterfact — drop-in `StateGraph`

### Files

```
counterfact/__init__.py          # re-exports StateGraph, END, START
counterfact/graph.py             # StateGraph, CounterfactualGraph, _BuildRecipe
counterfact/tracing.py           # wrap_node, TracingContext
counterfact/diagnostics.py       # diagnose orchestrator
counterfact/recommendations.py   # text recs; apply_recommendation is conservative
counterfact/spec.py              # build_graph_from_spec IR
counterfact/integrations/        # OpenAI Agents, Braintrust — not LangGraph
```

### How it hooks

Replace the import. No middleware, no transport.

```python
# from langgraph.graph import StateGraph, END
from counterfact import StateGraph, END

graph = StateGraph(MyState)
graph.add_node("retriever", retriever_fn)
graph.add_node("synthesizer", synthesizer_fn)
graph.add_edge("retriever", "synthesizer")
graph.add_edge("synthesizer", END)
graph.set_entry_point("retriever")
pipeline = graph.compile()          # → CounterfactualGraph

result = pipeline.invoke({"query": "..."})
trace = pipeline.get_trace()
report = pipeline.diagnose(input_state={"query": "..."}, domain="rag")
```

`counterfact.graph.StateGraph` subclasses
`langgraph.graph.StateGraph` and:

1. Records a `_BuildRecipe` (`nodes`, `node_kwargs`, `edges`,
   `conditional_edges`, `entry_point`, `finish_point`, `compile_kwargs`,
   optional `node_io`).
2. Wraps each callable with `wrap_node(name, fn)` so invoke/stream
   fill a `TracingContext`.
3. `compile(...)` returns `CounterfactualGraph`, which forwards
   `invoke` / `ainvoke` / `stream` / `astream` / `get_graph` / unknown
   attrs to the real compiled graph, then adds `get_trace`, `eval`,
   `diagnose`, `clone_with_replacement`, `apply_recommendation`.

`add_node` only recipes the common shapes
`add_node(name, fn)` and `add_node(name, action=fn)`. Compiled
subgraphs, `ToolNode` instances, and `add_node(fn)` (name-from-`__name__`)
are best-effort. A scaffold that emits `add_node(classify)` without a
string name may drop out of the recipe — always emit
`add_node("classify", classify)`.

`diagnose` **requires** the recipe. A raw
`from langgraph.graph import StateGraph` pipeline cannot be attributed.
The report should say so rather than asking the user to "just import
counterfact" after the fact (recipe is empty for an already-compiled
graph).

### `apply_recommendation` — why v0 must not call it

`CounterfactualGraph.apply_recommendation` rebuilds from a mutated
recipe and supports only:

| `intervention_type` | Behavior |
|---|---|
| `add_agent` | Insert a node; **passthrough stub** (`state -> state`) unless `rec._impl_fn` is set |
| `modify_agent` | `clone_with_replacement`; stub is `lambda state: state` |
| `remove_loop` | Drop conditional/back edges into `target_agent`; dangling nodes get `→ END` |
| `restructure` | `NotImplementedError` — "too open-ended to apply automatically" |

That last line is the v0 policy in their own words. Even the supported
types insert **no-op stubs**, not a typed tool or a `create_agent`
subgraph. Advisor output is a **human-readable recommendation** plus
our scaffold files, not `pipeline.apply_recommendation(rec)`.

### Scaffold implication

- Keep node names stable so `diagnose` / Shapley keys still match
  pre-flip reports (with a caveat: the callable changed, so
  attribution is a new experiment).
- If the user is not already on `counterfact.StateGraph`, do not add
  that import as part of an LLM↔tool flip. It is a different product
  decision.
- `to_spec()` / `build_graph_from_spec` is a possible later IR for
  the generator in [`docs/refactor.md`](refactor.md) §6. v0 does not
  emit a spec.

---

## What the scaffold's `ADAPTERS.md` should say

Copy-paste block the generator fills in:

```markdown
## After you apply this flip by hand

- **CAR:** If the flipped step left `create_agent`, re-run with the
  same `LangGraphRecorder` middleware. If you lifted it into a parent
  node, CAR will not see it — that is expected. Do not wrap the new
  `@tool` in a second recorder.
- **Tracefork:** `adapter.bind(model, new_tape, mode="record")` and
  compile with the same `make_tape_backed_checkpointer` only if you
  still need time-travel. Old tapes will not verify.
- **counterfact:** Keep `add_node("<same-name>", new_fn)`. Re-run
  `diagnose` as a new experiment. Do not call `apply_recommendation`.
```

---

## Later adapters (not v0)

One paragraph each. v0 does not generate CrewAI or Microsoft Agent
Framework scaffolds; it may *mention* them when a recorded run
obviously came from those extras.

### CrewAI

CrewAI is a role/task/crew loop, not a `StateGraph`. CAR's adapter
(`src/car/adapters/crewai.py`, extra `causal-agent-replay[crewai]`)
wraps the agent's `llm=` with `CrewAIRecorder(BaseLLM)`: the 1.15
native-tool `AgentExecutor` calls `llm.call(messages, tools=...)` once
per iteration and executes tools itself, so the wrapper sees one action
per model call. Harvest tool results from later `role:"tool"` messages
by `tool_call_id`. Replay is `CrewAIPolicy` + `CrewAIToolEnvironment`
(CrewAI's own `convert_tools_to_openai_schema` /
`format_native_tool_output_for_agent`). v1 refuses ReAct-text mode
(detected via the post-tool-reasoning nudge), streaming LLMs (dropped
ids), parallel calls, planning mode, context-window summarization, and
`result_as_answer` short-circuits. Tracefork's adapter
(`src/tracefork/adapters/crewai.py`) does **not** wrap `BaseLLM`: it
binds LiteLLM's module-level `client_session` / `aclient_session` to
the existing `TraceforkTransport`, and optionally attaches a
`BaseEventListener` (`make_event_listener`) for crew/agent/task/tool/LLM
boundaries — parent/child ids are best-effort (`id()` of task/agent
objects). A later advisor scaffold would emit a typed CrewAI `BaseTool`
(or a new `Task`) plus "set `Agent(llm=CrewAIRecorder(llm))` again",
not a LangGraph `add_node` diff.

### Microsoft Agent Framework

MAF (AutoGen + Semantic Kernel successor; Python package
`agent-framework`) uses `WorkflowBuilder` + `Executor` + edges, not
`StateGraph`. Checkpointing is a `CheckpointStorage` passed at build
(`InMemoryCheckpointStorage`, `FileCheckpointStorage`,
`CosmosCheckpointStorage`) or overridden on `workflow.run(...)`;
snapshots land at **super-step** boundaries under a BSP model the docs
call out as the determinism/fault-tolerance guarantee
([checkpoints](https://learn.microsoft.com/en-us/agent-framework/workflows/checkpoints),
[workflows](https://learn.microsoft.com/en-us/agent-framework/workflows/workflows)).
HITL is `ctx.request_info()` + `@response_handler` on the executor
(the old `RequestInfoExecutor` node is gone). Nested graphs are
`WorkflowExecutor`. Resume is `workflow.run(checkpoint_id=...)`, not
`Command(resume=...)`. None of CAR / Tracefork / counterfact ship an
MAF adapter today. A later adapter would likely wrap the chat-client
transport (Tracefork-style) or the executor `handler` (counterfact-style
`wrap_node`), and a later scaffold would emit a typed `Executor` class
plus `builder.add_edge(...)` notes — vocabulary is `executor` / `edge`
/ `superstep`, not `node` / `ToolNode` / `interrupt`. Until that
exists, Determinism Advisor v0 should refuse MAF traces with a pointer
here rather than pretending they are LangGraph.

---

## File-path cheat sheet (adapters)

| Concern | Path |
|---|---|
| CAR LangGraph recorder | `src/car/adapters/langgraph.py` |
| CAR CrewAI recorder | `src/car/adapters/crewai.py` |
| CAR adapter research | `RESEARCH/phase_5_adapters.md`, `RESEARCH/phase_7_crewai.md` |
| Tracefork LangChain/LangGraph | `src/tracefork/adapters/langchain.py` |
| Tracefork CrewAI | `src/tracefork/adapters/crewai.py` |
| Tracefork adapter registry | `src/tracefork/adapters/__init__.py` |
| Tracefork byte seam | `src/tracefork/transport.py` |
| counterfact drop-in graph | `counterfact/graph.py` |
| counterfact node wrap | `counterfact/tracing.py` (`wrap_node`) |
| counterfact recs (do not auto-apply) | `counterfact/graph.py` `apply_recommendation` |
| LangChain middleware types | `langchain.agents.middleware` (`AgentMiddleware`, `ModelRequest`, `ToolCallRequest`) |
| LangGraph checkpointer ABC | `langgraph.checkpoint.base.BaseCheckpointSaver` |
