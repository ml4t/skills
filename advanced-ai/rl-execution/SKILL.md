---
name: ml4t-rl-execution
description: Reinforcement learning for trade execution and hedging. Use when building adaptive execution strategies that minimize market impact beyond static TWAP/VWAP schedules.
dependencies: [run-backtest, cost-model]
metadata:
  book_chapters: "22"
  library: "ml4t-backtest"
---

# RL for Trade Execution

Fixed execution schedules (TWAP, VWAP) ignore real-time market conditions. An RL agent adapts its execution rate based on order book state, reducing implementation shortfall.

## The Problem

Executing a large order at a fixed rate creates predictable market impact. A 100K-share TWAP sell ignores favorable liquidity bursts and pushes through thin books. The result: 20-50 bps of avoidable shortfall on institutional orders, compounding across thousands of trades per year.

## The Pattern

Model execution as a finite-horizon MDP. State: remaining shares, time left, volume, spread. Action: execution rate. Reward: negative implementation shortfall.

### WRONG

```python
# Static TWAP — ignores market conditions entirely
def twap_execute(total_shares: int, n_slices: int) -> list[int]:
    base = total_shares // n_slices
    remainder = total_shares % n_slices
    return [base + (1 if i < remainder else 0) for i in range(n_slices)]

schedule = twap_execute(100_000, 20)  # Same size every slice, blind to liquidity
```

### CORRECT

```python
import gymnasium as gym
import numpy as np
from gymnasium import spaces

class ExecutionEnv(gym.Env):
    """Agent decides what fraction of remaining shares to execute each step."""
    def __init__(self, total_shares=100_000, n_steps=20):
        super().__init__()
        self.total_shares, self.n_steps = total_shares, n_steps
        self.observation_space = spaces.Box(0, 1, shape=(4,), dtype=np.float32)
        self.action_space = spaces.Box(0, 1, shape=(1,), dtype=np.float32)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.remaining, self.step_idx = self.total_shares, 0
        self.arrival_price = 100.0
        return self._obs(), {}

    def step(self, action):
        shares = int(np.clip(action[0], 0, 1) * self.remaining)
        impact = 0.0001 * (shares / 5000)  # Linear market impact
        exec_price = self.arrival_price * (1 + impact)
        shortfall = (exec_price - self.arrival_price) / self.arrival_price
        reward = -abs(shortfall) * shares / self.total_shares
        self.remaining -= shares
        self.step_idx += 1
        done = self.step_idx >= self.n_steps or self.remaining <= 0
        if done and self.remaining > 0:
            reward -= 0.01  # Non-completion penalty
        return self._obs(), reward, done, False, {}

    def _obs(self):
        return np.array([
            self.remaining / self.total_shares, self.step_idx / self.n_steps,
            np.random.uniform(0.01, 0.05),  # spread
            np.random.uniform(0.3, 1.0),    # volume ratio
        ], dtype=np.float32)
```

## State and Reward Design

**State features** (all normalized to [0, 1]):

| Feature | Purpose |
|---|---|
| Remaining fraction | Urgency — must finish before deadline |
| Time fraction | Deadline proximity |
| Spread | Cost signal — wide spread means wait |
| Volume ratio | Liquidity — high volume means execute more |

**Reward**: `-shortfall - inventory_penalty`. Non-completion penalty is critical; without it, the agent learns to never trade.

## Guardrails

- **Non-completion penalty is mandatory** — without it the agent learns zero-trade is optimal
- **Normalize all state features** — raw share counts and prices break learning
- **Validate against TWAP baseline** — if RL underperforms TWAP, the environment is misconfigured
- **Use square-root impact for large orders** — linear impact underestimates cost at scale
- **Episode = one parent order** — do not mix multiple orders into one episode

## Production Implementation

`ml4t-backtest` provides execution simulation with realistic market impact:

```python
from ml4t.backtest import Engine, BacktestConfig
from ml4t.backtest.models import PerShareCommission, VolumeShareSlippage

config = BacktestConfig(
    slippage=VolumeShareSlippage(impact_factor=0.1),
    commission=PerShareCommission(per_share=0.005),
)
# Use engine's execution model as the RL environment's simulator
```

## Checklist

- [ ] Environment has both time pressure and execution cost in the reward
- [ ] State is normalized (fractions, ratios) not raw values
- [ ] Non-completion is penalized (agent must finish the order)
- [ ] Trained agent beats TWAP baseline on test episodes
- [ ] Action space bounded (cannot execute more than remaining shares)
