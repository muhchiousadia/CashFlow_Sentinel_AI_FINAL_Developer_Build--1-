# 5-minute demo script — CashFlow Sentinel AI

**Before recording:** use only bundled synthetic data; close unrelated windows; ensure the app is running; keep screenshots/logs of the actual test run. Do not present illustrative assumptions as predictions.

## 0:00–0:30 — Problem
“SMEs can have a liquidity problem even when sales look healthy: customer receipts may be late while supplier obligations remain due. Our prototype helps the owner inspect the forecast, stress-test a payment delay, and compare evidence-labelled options before acting.”

## 0:30–1:20 — Baseline forecast
Show business selector, forecast start date, horizon, opening cash, ending cash, minimum cash, shortfall days, and daily chart. Explain that output is conditional on entered transactions and opening cash.

## 1:20–2:20 — Payment-delay shock
Select an incoming payer-to-receiver edge. Set a delay (for example 10 days) and run the deterministic simulation. Compare baseline and scenario values. If the selected sample does not create a shortfall, state that honestly: the purpose is to quantify the change, not guarantee a negative balance. Use a separately documented synthetic stress case if you need to demonstrate shortfall detection.

## 2:20–3:10 — Action comparison
Show the editable estimated relief/cost assumptions. Explain that early payment requests and supplier negotiations require counterparties’ agreement; delaying inventory can create stockout risk; borrowing is disabled. The system ranks options based on user-entered assumptions, not learned predictions.

## 3:10–4:10 — Agent brief
Show recommendations with evidence, uncertainty, and approval notes. Explain that this version is a transparent rule-based agent; do not call it an LLM or trained AI model.

## 4:10–4:45 — Security workflow
Sign in with a local owner account, show that the role is attached to the account, submit a review decision, restart the app, and confirm the persistent SQLite audit record remains. Explain that this is local prototype authentication, not production IAM.

## 4:45–5:00 — Close
“Our remaining validation priorities are independent real-data evaluation, production IAM hardening, and tamper-resistant audit infrastructure. No real-world action is executed.”
