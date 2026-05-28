---
name: ml4t-agent-state-memory
description: "Durable agent state, memory, and replay for autonomous research workflows. Use when an agent must resume, audit, or compare multi-step runs."
when_to_use: "Use when designing checkpointable agent state, evidence memory, replay traces, or run comparison artifacts"
dependencies: [agent-tool-contracts]
metadata:
  book_chapters: "24"
  library: ""
paths: ["**/*agent*state*.py", "**/*memory*.py", "**/*trace*.py", "**/*checkpoint*.py"]
---
# Agent State and Memory

Agent memory should be an explicit state object that can be serialized, replayed, and inspected. Chat history is not enough because it loses typed evidence, tool provenance, and quality gate status.

## The Problem

Long-running research agents make dozens of tool calls and intermediate judgments. If the only memory is the prompt transcript, the run cannot be resumed safely, audited by a reviewer, or compared against an ablation. The agent may also reuse stale claims because evidence has no timestamp or source boundary.

## The Pattern

### WRONG
```python
messages = []
messages.append({"role": "user", "content": task})

while True:
    answer = llm(messages)
    messages.append(answer)
    if "done" in answer["content"].lower():
        break
```

### CORRECT
```python
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import json


@dataclass
class AgentState:
    task: str
    evidence: list[dict[str, Any]] = field(default_factory=list)
    tool_trace: list[dict[str, Any]] = field(default_factory=list)
    decisions: list[dict[str, Any]] = field(default_factory=list)
    quality_gates: dict[str, bool] = field(default_factory=dict)

    def checkpoint(self, path: Path) -> None:
        path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> "AgentState":
        return cls(**json.loads(path.read_text(encoding="utf-8")))


state = AgentState(task="Evaluate whether the ensemble improves holdout Sharpe")
state.tool_trace.append(
    {"tool": "query_registry", "status": "ok", "observed_at": current_utc_iso()}
)
state.quality_gates["read_relevant_skills"] = True
state.checkpoint(Path("runs/ensemble_eval/state.json"))
```

## Memory Layers

- **Run state** -- current task, evidence, decisions, open questions, gates
- **Tool trace** -- every external observation with arguments and status
- **Evidence memory** -- source, timestamp, freshness, and extracted claims
- **Long-term memory** -- only stable project facts; never live market facts without dates
- **Replay artifact** -- enough inputs and outputs to re-render the run without live APIs

## Guardrails

- **Transcript-only replay** -- reviewers cannot verify which tools produced which facts
- **Undated evidence** -- market and API observations need explicit timestamps
- **Mutable memory overwrite** -- append decisions; do not silently edit prior reasoning
- **Cross-run contamination** -- reset task state between independent experiments

## Checklist

- [ ] State serializes to a stable JSON artifact
- [ ] Evidence includes source, timestamp, and freshness notes
- [ ] Tool trace can be replayed or inspected without the LLM
- [ ] Quality gates are explicit booleans or statuses
- [ ] Long-term memory excludes ephemeral market observations
