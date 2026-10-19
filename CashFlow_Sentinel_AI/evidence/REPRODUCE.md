# Reproducing the evidence

From the project root, activate the project's virtual environment and run:

```powershell
python -m pytest -q
python scripts/run_demo_evidence.py
python -m streamlit run app.py
```

The committed evidence CSV/JSON files are generated from bundled synthetic sample data. Re-running the script regenerates the baseline forecast, network propagation trace, check summary, and checks CSV. Capture a fresh screenshot or screen recording from your own running application for visual evidence; no screenshot is represented here as a real user/customer outcome.
