# CashFlow Sentinel AI — Expanded Copilot Features

## Included in this build
- **Ask CashFlow Copilot:** evidence-grounded question answering over selected-business transaction and forecast records. If `OPENAI_API_KEY` is configured, an optional OpenAI Responses API call can explain a compact set of transaction/forecast records; otherwise deterministic rules answer supported questions. The answer displays an evidence table and uncertainty note.
- **Explainable Financial Risk Radar:** rule-triggered liquidity, incoming-payment dependency and supplier timing alerts with evidence and recommended actions.
- **Smart Financing & Micro-Loan mock comparison:** invoice factoring, revolving credit line and micro-term working-capital loan compared with illustrative rate, fee, 30-day cost and approval speed. All terms are synthetic assumptions, not live offers.
- **Counterparty vulnerability matrix:** top three recorded counterparties ranked by exposure amount, not probability of default.
- **Financial Time Machine:** baseline versus deterministic what-if forecast for a delayed largest incoming payment, an added inventory outflow, or an assumed cash impact from price reduction.
- **Human review:** uses the existing demo review/audit controls. No external financial action is executed.

## Optional LLM setup
1. Create an API key with your provider account and understand its billing/data terms.
2. Keep the key private. Set `OPENAI_API_KEY` as an environment variable or in Streamlit secrets. Never paste it into chat, source code, screenshots, or a public repository.
3. Restart Streamlit and use **Ask CashFlow Copilot**. Without a key, deterministic evidence-grounded answers still work.
4. The LLM receives a compact set of selected-business transactions and forecast rows. Do not upload confidential or personally identifiable financial data to an external API without authorization and an appropriate data-processing review.

## Limitations
- Bundled data are synthetic; uploaded data quality is the user's responsibility.
- Rule-based risk thresholds and exposure ranking are not calibrated credit-risk models.
- Mock financing rates, fees, costs and approval times are illustrative, not current market offers.
- Price-reduction scenario assumes a cash impact equal to the selected percentage of forecast inflows. It does not model price elasticity, sales volume or margin response.
- The delayed-payment scenario shifts the largest recorded inflow; the entered amount is an illustrative UI parameter and is not used to select a different invoice.
- The optional LLM may make mistakes; validate every answer against the displayed evidence.
- Local password authentication and persistent SQLite audit records are now implemented for controlled demos; they are not production-grade IAM or tamper-proof logs. No bank connection, loan application, payment, or external action is performed.
