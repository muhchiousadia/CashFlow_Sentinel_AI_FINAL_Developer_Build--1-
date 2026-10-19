# Architecture — CashFlow Sentinel AI MVP 0.3

1. `data_loader.py` validates CSV schema, dates, directions, and amounts.
2. `cashflow_engine.py` calculates daily closing cash from dated inflows/outflows.
3. `scenario_engine.py` moves a selected incoming payment date to model deterministic delay.
4. `action_optimizer.py` ranks illustrative user-entered action assumptions.
5. `agent.py` generates an explainable rule-based brief from forecast and transaction evidence.
6. Streamlit displays forecasts, recommendations, simulated permission tiers, and persistent local SQLite audit logs.

## Agent status
The current agent is a transparent rule-based decision-support agent. It is not a generative LLM or trained ML model and does not predict payment-delay probabilities. Its purpose is traceable recommendations and safe workflow demonstration.

## Security status
Implemented demo controls: CSV validation, synthetic-data warning, local password authentication, database-backed roles, owner-review form, persistent SQLite audit records and CSV export, no external action execution. Not production security: no MFA, account lockout, TLS configuration, tamper-resistant remote logging, backup/retention policy, or independent security review.

## Limitations
Network-wide contagion is not yet modelled. Add a well-defined graph model and validate it against documented scenarios before claiming network-wide risk detection.
