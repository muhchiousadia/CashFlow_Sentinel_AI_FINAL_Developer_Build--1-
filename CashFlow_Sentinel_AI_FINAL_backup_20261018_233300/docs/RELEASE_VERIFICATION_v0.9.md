# Release Verification — v0.9

## Build checks
- Python compile check: PASS
- Automated tests: 41 passed
- Demo evidence script: PASS
- Synthetic network demo: 3 edges examined, max hop 3
- Demo authorization checks: 5/5 passed
- External actions executed: false

## New coverage
- Transaction upload quality report
- Network upload quality report
- Duplicate-like record warning without automatic deletion
- Self-edge network warning
- Independent Scenario A and Scenario B generation
- Inventory purchase cash impact
- Customer payment delay preserving expected total inflow
- Invalid scenario amount and price reduction rejection

## Required before real-world use
1. Reconcile uploaded transactions to accounting/bank records and confirm opening cash.
2. Add stable transaction IDs and business-approved duplicate resolution.
3. Compare forecasts to independently reconciled actual daily closing cash using `scripts/evaluate_real_data.py`.
4. Perform an independent security review, deploy behind HTTPS, configure backups/retention, MFA/rate limiting and secrets management.
5. Verify all LLM-generated statements against source evidence; do not treat it as regulated financial advice.
6. Confirm competition eligibility and required submission deliverables with the official portal.

This report describes tests run in the build environment only; it is not a certification or proof of production readiness.
