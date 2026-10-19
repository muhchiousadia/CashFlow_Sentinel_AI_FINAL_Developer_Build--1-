# CashFlow Sentinel AI

An explainable Streamlit cash-flow decision-support prototype. Bundled transaction and network datasets are synthetic.

## Run on Windows

1. Install Python 3.11 or newer and ensure the Python launcher (`py`) or `python.exe` is available.
2. Open this project folder in VS Code.
3. Double-click `run_app.bat`, or run it from PowerShell:

   ```powershell
   .\run_app.bat
   ```

The launcher creates `.venv` when needed, installs the requirements if application dependencies are missing, and starts Streamlit. Open the URL printed in the terminal (normally http://localhost:8501). Stop the server with Ctrl+C.

For manual setup, run these commands from this folder:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
.\.venv\Scripts\python.exe -m streamlit run .\app.py
```

The first visit prompts you to create an owner account. Later, sign in or use **Create account** to register a viewer. Passwords must contain at least 12 characters. Owner accounts can manage roles from the app. Existing account and audit data are stored locally in `data\cfs_security.sqlite3`; keep this database private and backed up.

## Features

- Cash-flow forecasts, input-quality reporting, and payment-delay scenarios
- Scenario comparison, action ranking, and supply-chain payment shock analysis
- Financial risk radar, counterparty analysis, and financing comparisons
- Evidence-based Python chat and optional Ollama local-model chat
- Login, registration, role-based authorization, human review, and SQLite audit logging

Use the Light/Dark selector and sidebar navigation to access the dashboard sections. Sign out from the sidebar to end the current session.

## Optional local AI

Rule-Based chat works offline and requires no model or API key. For Ollama, install Ollama and run a model such as:

```powershell
ollama run qwen2.5:3b
```

See [the local AI setup guide](./docs/guides/LOCAL_AI_SETUP_EN.md) and [architecture documentation](./docs/ARCHITECTURE.md).

## Tests

Run from the project folder:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Project layout

- `app.py`: Streamlit entry point
- `src\`: forecasting, scenarios, data validation, AI, authentication, and authorization
- `data\`: synthetic sample CSVs and the local private SQLite database
- `tests\`: unit and UI regression tests
- `docs\`, `evidence\`, `deliverables\`: project documentation and review/presentation materials

## Safety and limitations

Forecasts and network shock propagation are deterministic scenarios, not calibrated probability forecasts. Financing options are illustrative. No real payments, lending decisions, bank integrations, or external messages are executed. Authentication and audit logging are for a local prototype, not production use; the app has no production identity provider, MFA, rate limiting, password recovery, secure shared hosting, or tenant isolation. Do not expose it to the public internet or upload highly sensitive production data.

The source ZIP intentionally excludes the local SQLite database, virtual environments, caches, and secrets. A fresh install creates a new database on first run; retain the existing database separately if you need its accounts and audit history.
