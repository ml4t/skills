---
name: ml4t-agent-orchestration
description: "Multi-agent architecture for trading workflows with specialized agents and audit trails. Use when coordinating research, execution, and risk agents."
when_to_use: "Use when building autonomous or semi-autonomous trading systems with separation of concerns"
dependencies: [strategy-workflow, kill-switch]
metadata:
  book_chapters: "24"
  library: ""
paths: ["**/*agent*.py", "**/*rl*.py", "**/*rag*.py", "**/*graph*.py", "**/*knowledge*.py", "**/*orchestrat*.py"]
---
# Agent Orchestration for Trading

A monolithic trading bot couples signal generation, risk checking, and execution into one opaque process. When it fails, you cannot tell which stage went wrong. Multi-agent design makes each decision visible and auditable.

## The Problem

A single script that generates signals, sizes positions, and executes trades is a single point of failure with no audit trail. When it takes a $500K position in a low-liquidity name, was it the signal, a risk bypass, or an execution bug? Without separation, post-mortem is guesswork.

## The Pattern

Decompose into specialized agents with typed interfaces. Each agent has one responsibility, logs every decision, and the orchestrator enforces sequencing and approval gates.

### WRONG

```python
def run_trading_bot(universe):
    data = download_data(universe)
    signals = generate_signals(data)
    for symbol, signal in signals.items():
        size = signal * portfolio_value * 0.1  # No risk check
        execute_trade(symbol, size)             # No approval gate
        # Crashes halfway → some trades executed, some not
```

### CORRECT

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol
import logging

@dataclass(frozen=True)
class Signal:
    symbol: str
    direction: float   # [-1, 1]
    confidence: float  # [0, 1]
    source: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

class Agent(Protocol):
    def run(self, context: dict) -> dict: ...

class SignalAgent:
    """Generates signals. No execution authority."""
    def run(self, context: dict) -> dict:
        signals = self._generate(context["data"])
        logging.info(f"SignalAgent: {len(signals)} signals")
        return {"signals": signals}
    def _generate(self, data) -> list[Signal]: return []

class RiskAgent:
    """Filters signals. Can only reject, never create."""
    def __init__(self, max_pos_pct=0.05):
        self.max_pos_pct = max_pos_pct
    def run(self, context: dict) -> dict:
        approved = [s for s in context["signals"]
                    if self._check(s, context["portfolio"])]
        logging.info(f"RiskAgent: {len(approved)}/{len(context['signals'])} approved")
        return {"approved_signals": approved}
    def _check(self, signal, portfolio) -> bool: return True

class ExecutionAgent:
    """Converts approved signals to orders."""
    def run(self, context: dict) -> dict:
        orders = [{"symbol": s.symbol, "side": "buy" if s.direction > 0 else "sell",
                    "shares": 100, "signal_source": s.source}
                  for s in context["approved_signals"]]
        return {"orders": orders}

class Orchestrator:
    def __init__(self, agents: list):
        self.agents = agents
        self.audit_log: list[dict] = []
    def run(self, context: dict) -> dict:
        for agent in self.agents:
            result = agent.run(context)
            self.audit_log.append({"agent": agent.__class__.__name__,
                                   "timestamp": datetime.utcnow().isoformat()})
            context.update(result)
        return context

pipeline = Orchestrator([SignalAgent(), RiskAgent(), ExecutionAgent()])
```

## Guardrails

- **Risk agent can only reject, never create signals** — separation of offense and defense is fundamental
- **Every decision logged with provenance** — which signal, which model, which risk check, when
- **Human gate for high-stakes actions** — novel positions or large sizes require human approval
- **Orchestrator halts on any exception** — one agent crashing must not leave partial executions
- **Fail-safe default is no action** — any unhandled error stops the pipeline without executing

## Production Implementation

No ml4t library for orchestration. Use Python `Protocol` for typed agent contracts, structured logging to JSON/SQLite for audit trails, and a dashboard (Streamlit or internal) for human-in-the-loop approval.

## Checklist

- [ ] Each agent has exactly one responsibility (signal, risk, execution)
- [ ] Risk agent cannot create positions, only filter/reject
- [ ] Every decision logged with timestamp and provenance
- [ ] Human approval gate exists for orders above threshold
- [ ] Pipeline halts safely on any agent exception (no partial execution)
- [ ] Audit log is queryable (structured format, not free text)
