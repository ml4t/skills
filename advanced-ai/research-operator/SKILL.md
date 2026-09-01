---
name: ml4t-research-operator
description: "Thin autonomous research operator pattern for ML4T experiments. Use when an agent should inspect artifacts, read skills, run scripts, and produce an auditable recommendation."
when_to_use: "Use when building or supervising an autonomous coding/research loop over case-study files, registries, and ML4T skills"
dependencies: [agent-tool-contracts, agent-state-memory, registry-system]
metadata:
  book_chapters: "24"
  library: ""
paths: ["**/*research_operator*.py", "**/*operator_artifacts*.json", "**/case_studies/**/*.py"]
---
# Research Operator

A research operator is a thin loop around general tools. The methodology should live in skills, the math in libraries, and the case-study logic in project code.

## The Problem

Hard-coding every possible research move into an agent framework creates a brittle demo. Giving the model unrestricted shell and file access creates an unauditable production risk. The useful middle ground is a narrow operator: expose a small set of typed tools, require skill discovery before implementation, sandbox writes, and stop with an evidence-backed recommendation.

## The Pattern

### WRONG
```python
prompt = f"""
You are a quant researcher. Use any files and commands you need.
Try improving the case study and tell me what worked.
Task: {task}
"""
print(llm(prompt))
```

### CORRECT
```python
TOOLS = {
    "list_skills": tool_list_skills,
    "read_skill": tool_read_skill,
    "read_file": sandbox_read_file,
    "query_registry": readonly_sql_query,
    "read_parquet": sandbox_read_parquet,
    "run_bash": sandbox_run_bash,
    "edit_file": sandbox_edit_file,
    "done": finish_with_summary,
}

SYSTEM_PROMPT = """
Before implementation, call list_skills and read the relevant skills.
State the hypothesis, cite the skills used, run the smallest valid experiment,
and finish with an honest recommendation.
"""

state = AgentState(task=task)
while not state.quality_gates.get("done"):
    action = model_choose_action(SYSTEM_PROMPT, state)
    result = TOOLS[action.name](**action.args)
    state.tool_trace.append(log_call(action, result))
    state.checkpoint(run_dir / "state.json")
```

## Operator Contract

- Tool surface stays small: read, query, inspect, execute, edit, skill lookup, done
- Writes go to a sandbox or explicit output directory
- Registry and source repos are read-only unless the task explicitly requires edits
- The agent must read relevant skills before changing code or running experiments
- Final output states hypothesis, method, artifacts, skill usage, metrics, and recommendation

## Guardrails

- **Framework-first design** - if the operator owns methodology, skills become decorative
- **Unbounded shell** - command execution needs cwd, timeout, and write sandbox controls
- **No negative-result path** - a valid run may conclude that the proposed change is worse
- **Missing skill audit** - record which skills were read and whether they were followed

## Checklist

- [ ] Tool schemas and runtime controls are separate from the LLM
- [ ] The loop checkpoints state after every tool call
- [ ] The prompt requires skill discovery before implementation
- [ ] Writes are redirected to a sandbox or declared output directory
- [ ] The final summary includes evidence, artifacts, and an honest recommendation
