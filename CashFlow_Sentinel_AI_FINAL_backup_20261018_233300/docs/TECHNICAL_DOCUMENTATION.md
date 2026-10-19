# CashFlow Sentinel AI — Technical Documentation

**Competition track:** 2026 Shenzhen International FinTech Competition, Topic E — SME Finance Copilot  
**Version:** 0.3 prototype  
**Status:** Demonstration prototype; not a production financial system.

## 1. Executive summary
CashFlow Sentinel AI is an explainable SME liquidity decision-support prototype. It transforms dated inflow/outflow records into a daily cash forecast, allows a user to stress-test a selected incoming payment delay, compares user-supplied action assumptions, and generates a rule-based decision brief. It preserves human decision ownership and does not perform payments, lending decisions, or external communications.

## 2. Problem and target user
Small businesses may face short-term liquidity pressure when customer receipts arrive late while supplier bills and operating expenses remain due. A forecast alone does not explain what to check next. The prototype combines a date-based forecast with a deterministic shock scenario and evidence-labelled action options.

## 3. Proposed value and differentiation hypothesis
The differentiating hypothesis is a compact workflow that connects (a) a dated cash forecast, (b) an explicit payment-delay stress test, (c) evidence and uncertainty for each recommendation, and (d) a human review record. This is a hypothesis to validate, not a claim of global novelty. Competitor products already provide cash forecasting and scenario planning; the project must be evaluated on traceability, usability, safe action gating, and scenario evidence.

## 4. Architecture
1. `src/data_loader.py` validates required columns, dates, numeric values, directions, and basic blank fields.
2. `src/cashflow_engine.py` aggregates dated inflows/outflows and calculates closing cash over a chosen horizon.
3. `src/scenario_engine.py` shifts a matching receiver-side inflow date to simulate a deterministic payment delay.
4. `src/action_optimizer.py` ranks action options using manually supplied relief/cost assumptions, feasibility, and net estimated benefit.
5. `src/network_risk.py` performs a deterministic, bounded, multi-hop propagation stress test with explicit assumed liquidity buffers.
6. `src/security.py` centralizes demo permission checks and validates/sanitizes owner-review audit records.
7. `src/agent.py` produces an explainable rule-based brief grounded in forecast/transaction evidence.
8. `app.py` provides the Streamlit UI, scenario charts, network trace, permission-gated review workflow, and evidence exports.

## 5. Core calculation
For each day *t*:

`closing_cash[t] = closing_cash[t-1] + inflows[t] - outflows[t]`

The initial closing balance is the user-entered opening cash plus that day's net flow. A shortfall day is a day where closing cash is below zero. The current stress test moves a selected incoming transaction date forward by a chosen number of days and recomputes the receiver's forecast. The new network stress test traverses connected payer-to-receiver edges up to a bounded hop count. If the incoming shock exceeds the receiver buffer assumption, downstream obligations due on/after the shock date are conservatively marked as delayed. The buffer assumptions are not calibrated cash positions, and this is not a probability forecast or proof of real-world contagion.

## 6. Agent behaviour
The agent is a transparent, deterministic rules engine, not an LLM or trained ML model. It can flag forecast shortfalls, point to the next listed incoming/outgoing record, and attach evidence, uncertainty, and human-review notes. It does not autonomously execute recommendations.

## 7. Data contract
### Transactions CSV
Required fields: `business_id,business_name,date,direction,category,amount,counterparty_id,description`.
- `direction`: `inflow` or `outflow`
- `amount`: non-negative numeric value
- `date`: parseable date
- Use one consistent currency and clearly document its unit.

### Network CSV
Required fields: `from_business_id,to_business_id,amount,expected_date,delay_days,relationship_type`.
- Directed edge means payer/source → receiver/destination for the modeled receipt.
- Amount and delay are non-negative; dates must parse.

## 8. Security and compliance controls
Implemented in this demo: input schema/value validation; synthetic-data warning; no external execution integration; centralized `require_permission` checks for simulation, export, and review-record operations; viewer cannot run simulations or record reviews; analyst can simulate/export but cannot record owner decisions; owner tier can record a validated review decision; notes are normalized and capped; persistent local SQLite audit records explicitly set `external_action_executed=False`; unit tests verify allowed and denied paths.

Important limitation: local username/password authentication and account-backed roles are implemented for a controlled demo, but this is not production IAM. SQLite logs persist locally but are not tamper-resistant. No independent security audit has been completed. Do not expose the app publicly or upload highly sensitive data. Production use would require a reviewed identity provider, MFA, TLS, rate limiting, session expiry, secure secrets, backup/retention, tenant isolation, threat modelling, and independent review.

## 9. Evaluation plan
Evaluate with deterministic hand-calculated test cases and clearly labelled synthetic scenarios:
- Calculation correctness: daily closing balances match hand calculations.
- Delay response: shifting an inflow changes dates and the forecast as expected.
- Shortfall detection: negative balances and shortfall days are counted correctly.
- Recommendation traceability: every agent recommendation includes evidence and uncertainty.
- Security workflow: viewer cannot run simulations or record a review; analyst cannot record an owner review; owner review records are sanitized and explicitly state that no external action ran. Multi-hop synthetic chain test reaches two downstream hops; high buffers stop propagation.
- Robustness: malformed dates, missing columns, negative amounts, invalid direction, unknown network edges, and horizon boundaries.

Report measured results from actual runs only. Do not invent prediction accuracy, customer impact, or financial savings.

## 10. Known limitations / risk register
- Bundled data are synthetic and not ground truth.
- Opening cash is user-entered and not bank-reconciled.
- Inflows may be late or unpaid; no calibrated probability model exists.
- Network propagation is deterministic and conservative; per-node buffers are user assumptions, edge traversal is bounded, and the model is not calibrated against historical payment data.
- Action relief/cost/feasibility are user assumptions.
- Rule-based agent is not generative AI or trained ML.
- Local password authentication is implemented for demo use; SQLite logs persist locally but are not tamper-resistant.
- Output is decision support, not financial advice or a lending decision.

## 11. Reproducibility
Use Python 3.10+ (Python 3.11 recommended), install `requirements.txt`, run `python -m pytest -q`, then `python scripts/run_demo_evidence.py`, then `python -m streamlit run app.py`. The evidence script creates reproducible CSV/JSON outputs from bundled synthetic data. Preserve the exact terminal output and your own screenshots/video as execution evidence; the generated evidence is not real-world validation. This documentation must be updated if code changes.
