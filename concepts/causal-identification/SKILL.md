---
name: ml4t-causal-identification
description: "Validate causal claims using DAG adjustment sets, bad-control detection, and refutation tests. Use when distinguishing genuine factor effects from confounded associations."
when_to_use: "Use when a predictive signal looks promising and you need to assess whether it reflects a causal mechanism or spurious correlation"
dependencies: [lookahead-bias, point-in-time]
metadata:
  book_chapters: "7, 15"
  library: ""
paths: ["**/*causal*.py", "**/*dag*.py", "**/*dowhy*.py", "**/*econml*.py", "**/*dml*.py", "**/*refut*.py"]
---
# Causal Identification

A factor with IC 0.04 could be a real effect or a confounded association. Without a DAG and refutation tests, you cannot tell which. Conditioning on the wrong variables - mediators, colliders, post-treatment - can create or destroy apparent signal.

## The Problem

"Kitchen sink regression" - conditioning on every available variable - is the default in ML pipelines. But including a collider (e.g., fund flows driven by both momentum and returns) induces spurious correlation (~-0.25 between independent variables). Including a mediator (the channel through which the treatment operates) attenuates the true effect. Including a post-treatment variable introduces bias of unknown sign. The DAG determines which variables are admissible controls.

## The Pattern

### WRONG
```python
import numpy as np
from sklearn.linear_model import Ridge

# Kitchen-sink: include everything as controls
# fund_flow is a COLLIDER (driven by both momentum and returns) - induces bias
X = np.column_stack([momentum, volatility, fund_flow, sector_return])
model = Ridge().fit(X, forward_returns)
print(f"Momentum coeff: {model.coef_[0]:.4f}")  # Biased by collider conditioning
```

### CORRECT
```python
from dowhy import CausalModel

# Step 1: Specify DAG - encode your mechanism assumptions
graph = """
digraph {
    volatility -> momentum;
    volatility -> forward_returns;
    momentum -> forward_returns;
    momentum -> fund_flow;
    forward_returns -> fund_flow;
}"""
# fund_flow is a collider (momentum -> fund_flow <- forward_returns)
# It must NOT be in the adjustment set

# Step 2: Identify estimand from the DAG
model = CausalModel(data=df, treatment="momentum",
                     outcome="forward_returns", graph=graph)
estimand = model.identify_effect()
# DoWhy computes the backdoor adjustment set: {volatility}

# Step 3: Estimate with valid controls only
estimate = model.estimate_effect(estimand, method_name="backdoor.linear_regression")
print(f"Causal effect: {estimate.value:.4f}")
```

## Adjustment Set Rules

| Variable Role | Include as Control? | Why |
|--------------|--------------------|----|
| Confounder (common cause of T and Y) | **Yes** | Blocks backdoor paths |
| Pre-treatment predictor of Y | **Yes** | Improves precision |
| Mediator (on causal path T→M→Y) | **No** | Changes estimand |
| Collider (common effect of T and Y) | **No** | Induces spurious correlation |
| Post-treatment variable | **No** | Bias of unknown sign |

**Pre-treatment timing discipline**: only condition on variables determined strictly before treatment time. Do not condition on portfolio outcomes, realized performance, or contemporaneous market variables.

## Refutation Tests

Every causal claim must survive refutation before informing trading decisions:

```python
# Placebo treatment: replace momentum with random noise - effect should vanish
placebo = model.refute_estimate(estimand, estimate, method_name="placebo_treatment_refuter")
print(f"Placebo effect: {placebo.new_effect:.4f}")  # Should be ~0

# Sensitivity: how strong must an omitted confounder be to flip the sign?
sensitivity = model.refute_estimate(estimand, estimate,
    method_name="add_unobserved_common_cause",
    confounders_effect_on_treatment="linear", confounders_effect_on_outcome="linear",
    effect_strength_on_treatment=0.5, effect_strength_on_outcome=0.5)
```

If a confounder at 10-20% effect strength flips the sign, the result is fragile.

## Guardrails

- **Specify the DAG before fitting** - post-hoc DAGs rationalize results instead of testing assumptions
- **Never condition on colliders** - the fund-flow collider trap creates ~-0.25 spurious correlation between independent variables
- **Enforce pre-treatment timing** - all controls must be determined strictly before treatment time
- **Placebo tests are mandatory** - a pipeline that finds effects with random treatment is broken
- **Sensitivity analysis calibrates confidence** - report the confounder strength at which the effect flips sign
- **Causal discovery (PCMCI, NOTEARS) generates hypotheses, not conclusions** - validate discovered structure with independent data

## Production Implementation

No `ml4t-*` library covers causal estimation. Use DoWhy for identification and refutation, EconML for Double Machine Learning on continuous treatments, and tfp-causalimpact for discrete event studies:

```python
from econml.dml import LinearDML
from sklearn.ensemble import GradientBoostingRegressor

dml = LinearDML(model_y=GradientBoostingRegressor(), model_t=GradientBoostingRegressor())
dml.fit(Y=returns, T=momentum, W=confounders)  # W = valid adjustment set from DAG
print(f"ATE: {dml.ate():.4f}, 95% CI: {dml.ate_interval()}")
```

## Checklist

- [ ] DAG specified and committed before any estimation
- [ ] Adjustment set derived from backdoor criterion - no colliders, mediators, or post-treatment variables
- [ ] Estimand declared (ATE, ATT, or CATE) before fitting
- [ ] Placebo treatment test returns near-zero effect
- [ ] Sensitivity analysis reports the confounder strength that flips the sign
- [ ] Results stable across subperiods and alternative nuisance model specifications
