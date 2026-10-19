# CashFlow Sentinel AI v0.9 Final — Local AI and Rule-Based Chat Setup

## What is included
- Python Rule-Based Chat works offline without an API key and provides deterministic answers for supported topics.
- Ollama Local AI is an optional local language model for natural-language explanations.
- Financial calculations, forecasts, and stress tests remain in Python. The language model cannot execute payments or loans.
- Chat responses include an evidence table and an uncertainty note.

## 1. Install Ollama (optional)
1. Download the Windows installer from [ollama.com/download](https://ollama.com/download).
2. Open a new PowerShell or VS Code terminal and run `ollama run qwen2.5:3b`.
3. Wait for the model to download, then try a prompt. Type `/bye` to exit.
4. Check installed models with `ollama list`.
5. Keep Ollama running while using Local AI mode. The default URL is `http://localhost:11434`.

For a computer with 8 GB of RAM, start with `qwen2.5:3b`. If it is too slow, try `ollama run qwen2.5:1.5b`, then enter `qwen2.5:1.5b` in the dashboard's model field.

## 2. Install project dependencies
Open the project root in VS Code or PowerShell. This is the folder containing `app.py` and `requirements.txt`.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If Python 3.11 is not installed, use an installed supported version shown by `py -0p` in place of `-3.11`.

## 3. Run the app

```powershell
.\run_app.bat
```

Create the local owner account on first run, using a unique password of at least 12 characters. This local authentication is for prototype/demo use only.

## 4. Use chat
Open `8. Finance Chat — Python Rules + Free Local AI` and choose one of these modes:
- `Python Rule-Based (offline)`: works without Ollama or internet and supports a limited set of finance questions.
- `Ollama Local AI (free)`: requires Ollama to be running and the selected model to be downloaded.

Try: `Why is my cash decreasing?`, `Is there a cash shortage risk?`, `Which customer payments matter most?`, or `help`.

## Troubleshooting
- **`ollama` is not recognized:** Restart the terminal after installing Ollama, or check that Ollama is installed.
- **Connection refused:** Open the Ollama desktop app, or run `ollama serve` in a separate terminal if needed.
- **Model not found:** Run `ollama pull qwen2.5:3b`, then check with `ollama list`. If you use a different installed model, enter its exact name in the dashboard's model field.
- **Slow response:** Close other applications or try `qwen2.5:1.5b`.
- **Local model unavailable:** Switch to Python Rule-Based mode.

## Data privacy and limitations
Ollama requests are sent to the local service at the configured URL. The app sends the selected business's compact transaction and forecast context (up to 30 rows of each) to that model. Keep the URL local unless you deliberately configure a trusted server. Model output may be inaccurate; verify amounts against the evidence table. No real bank, loan, payment, email, or external action is connected. Bundled data are synthetic. This is a prototype, not production financial software.
