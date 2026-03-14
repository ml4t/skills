---
name: ml4t-production-readiness
description: Checklist for deploying strategies to production
category: workflows
type: workflow
dependencies: [model-validation, drift-detection, kill-switch, exposure-analysis]
book_chapters: [26, 27]
---

# Production Readiness

Final checklist before deploying a strategy to production.

## Stage Overview

```
1. Model → 2. Data → 3. Execution → 4. Monitoring → 5. Governance
```

## Stage 1: Model Artifacts

```python
ARTIFACTS_CHECKLIST = {
    'model_file': 'models/strategy_v1.pkl',
    'feature_config': 'config/features.yaml',
    'cost_model': 'config/costs.yaml',
    'risk_limits': 'config/limits.yaml',
    'version': 'v1.0.0'
}

# Version control
assert all_artifacts_in_git(ARTIFACTS_CHECKLIST)
assert model_hash_matches_training_log()
```

## Stage 2: Data Pipeline

```python
DATA_CHECKLIST = {
    'sources_documented': True,
    'refresh_schedule': 'daily 6:00 AM ET',
    'fallback_configured': True,
    'validation_enabled': True,
    'pit_correctness_verified': True
}

def verify_data_pipeline():
    """Pre-deployment data checks."""
    # Test data freshness
    latest = get_latest_data_timestamp()
    assert latest >= yesterday(), "Stale data"

    # Test fallback
    with mock_source_failure():
        data = load_data()
        assert data is not None, "Fallback failed"
```

## Stage 3: Execution System

```python
EXECUTION_CHECKLIST = {
    'broker_connectivity': test_broker_connection(),
    'order_validation': test_order_limits(),
    'position_reconciliation': True,
    'cost_tracking': True,
    'audit_logging': True
}

def test_order_flow():
    """Paper trade before live."""
    order = create_test_order(size=100, symbol='SPY')
    result = paper_trade(order)
    assert result.status == 'FILLED'
    assert result.slippage < 0.001
```

## Stage 4: Monitoring

```python
MONITORING_CONFIG = {
    'metrics': ['sharpe_rolling', 'drawdown', 'exposure', 'psi'],
    'alert_thresholds': {
        'drawdown': -0.15,
        'psi': 0.25,
        'sharpe_rolling': 0.5
    },
    'check_interval': 60,  # seconds
    'alert_channels': ['slack', 'email', 'pagerduty']
}

from ml4t.monitoring import start_monitoring

monitor = start_monitoring(
    portfolio=live_portfolio,
    config=MONITORING_CONFIG,
    kill_switch=kill_switch
)
```

## Stage 5: Governance

```python
GOVERNANCE_CHECKLIST = {
    'strategy_owner': 'team@example.com',
    'risk_approval': 'risk_committee_2024_01_15',
    'compliance_review': 'legal_2024_01_10',
    'documentation': 'docs/strategy_v1/',
    'incident_playbook': 'runbooks/strategy_v1.md',
    'review_schedule': 'quarterly'
}

def generate_deployment_report():
    """Generate deployment sign-off document."""
    return {
        'strategy': ARTIFACTS_CHECKLIST['version'],
        'deployment_date': datetime.now().isoformat(),
        'approvers': ['risk_officer', 'tech_lead', 'portfolio_manager'],
        'validation_results': validation_results,
        'monitoring_config': MONITORING_CONFIG
    }
```

## Final Checklist

```
MODEL
- [ ] Model artifacts versioned and reproducible
- [ ] Training code matches deployed model
- [ ] Feature pipeline identical to training

DATA
- [ ] Data sources documented
- [ ] Refresh schedule configured
- [ ] Fallback sources tested
- [ ] Point-in-time correctness verified

EXECUTION
- [ ] Broker connectivity tested
- [ ] Paper trading completed
- [ ] Order limits configured
- [ ] Position reconciliation automated

MONITORING
- [ ] Kill switch configured
- [ ] Alert thresholds set
- [ ] Drift detection enabled
- [ ] Dashboard operational

GOVERNANCE
- [ ] Risk approval obtained
- [ ] Compliance review complete
- [ ] Documentation current
- [ ] Incident playbook written
```
