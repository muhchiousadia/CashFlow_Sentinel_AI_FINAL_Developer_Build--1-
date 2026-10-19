# Competition submission checklist — Topic E

## Required package
- [x] Source code and README
- [x] Technical documentation (architecture, calculation, data contract, limitations)
- [x] Security self-assessment and known-risk list
- [x] Automated tests
- [x] Demo script
- [x] Presentation deck (separate file in package)
- [ ] Actual run screenshots and raw test output collected from the submitting team's machine
- [ ] Final team/member and institution details checked against official eligibility rules
- [ ] Final upload completed in official portal before deadline
- [ ] Confirm latest rules, deadline/time zone, accepted file formats, and any required declarations from the official portal

## Evidence to collect (do not fabricate)
1. Terminal output from `python -m pytest -q`.
2. Screenshot of baseline forecast.
3. Screenshot of payment-delay scenario before/after values.
4. Screenshot of agent evidence and uncertainty.
5. Screenshot of security review decision and exported audit CSV.
6. README and dependency list matching the exact submitted code.

## Claims policy
- Describe the agent as rule-based unless a real LLM/ML component is implemented and tested.
- Describe the network scenario as deterministic single-edge stress testing; do not claim multi-hop contagion modelling yet.
- Do not claim global first, production-grade security, real-world savings, or prediction accuracy without evidence.
- All bundled data and action values are synthetic/illustrative.

## Final submission safety
The app is a prototype, not financial advice. It must not be connected to real payment, lending, email, or bank systems without additional security and compliance work. Submission is not complete until the team verifies official portal fields and uploads the package.


## Version 0.4 verification additions
- [ ] Run `python -m pytest -q` and preserve exact terminal output.
- [ ] Run `python scripts/run_demo_evidence.py`; inspect `evidence/demo_evidence_summary.json`.
- [ ] In the UI, run the multi-hop network shock and download `network_propagation_evidence.csv`.
- [ ] Demonstrate Tier 0 denied simulation/review and Tier 1 denied owner-review recording.
- [ ] Demonstrate Tier 2 review record with `external_action_executed=False`.
- [ ] Capture your own screenshots/video from the running application.
- [ ] Do not describe synthetic evidence as real customer/financial validation.
