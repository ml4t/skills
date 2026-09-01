---
name: ml4t-agent-tool-contracts
description: "Typed tool contracts for autonomous research agents. Use when exposing files, search, databases, or execution tools to an LLM agent."
when_to_use: "Use when building agent tool schemas, validating tool inputs, attaching provenance, or restricting tool execution"
dependencies: []
metadata:
  book_chapters: "24"
  library: ""
paths: ["**/*agent*tool*.py", "**/*tool_contract*.py", "**/*research_operator*.py"]
---
# Agent Tool Contracts

An agent tool is an API boundary, not a prompt convenience. Every tool needs a typed input schema, a narrow execution policy, and a result object that records provenance.

## The Problem

LLM agents fail badly when tools accept vague strings and return unstructured text. The model cannot distinguish stale search results from fresh ones, allowed paths from forbidden paths, or recoverable tool errors from final evidence. Worse, a prompt-injected page can ask the agent to call another tool unless the execution layer enforces policy outside the model.

## The Pattern

### WRONG
```python
def run_tool(name: str, args: str) -> str:
    if name == "read_file":
        return open(args).read()
    if name == "search":
        return web_search(args)
    raise ValueError(name)
```

### CORRECT
```python
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ToolResult:
    ok: bool
    value: Any
    source: str
    observed_at: str
    policy: str


def read_file(path: str, root: Path) -> ToolResult:
    requested = Path(path).expanduser().resolve()
    allowed = root.resolve()
    if allowed not in requested.parents and requested != allowed:
        return ToolResult(False, "path outside sandbox", path, "", "deny")

    return ToolResult(
        ok=True,
        value=requested.read_text(encoding="utf-8"),
        source=str(requested),
        observed_at=current_utc_iso(),
        policy="sandbox-read",
    )


READ_FILE_SCHEMA = {
    "name": "read_file",
    "description": "Read a UTF-8 text file inside the sandbox.",
    "input_schema": {
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
        "additionalProperties": False,
    },
}
```

## Contract Rules

- Make schemas strict: `required` fields and `additionalProperties: false`
- Validate paths, domains, SQL mode, and write targets in code, not in the prompt
- Return structured `ok/error/source/observed_at` fields for every tool
- Keep tool names verb-first and task-specific: `query_registry`, not `database`
- Log every call with arguments, status, duration, and result size

## Guardrails

- **Unbounded filesystem access** - reject absolute paths unless explicitly allowlisted
- **Prompt-mediated policy** - never ask the model whether a tool call is safe
- **String-only results** - downstream stages need provenance fields, not formatted tables
- **Hidden writes** - file, shell, and network tools need separate read/write permissions

## Checklist

- [ ] Every tool has a strict schema with no extra properties
- [ ] Runtime policy checks are outside the model prompt
- [ ] Results include provenance and freshness metadata
- [ ] Tool calls are recorded in an audit log
- [ ] Search, shell, database, and filesystem tools have separate permissions
