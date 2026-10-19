@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3 -m venv .venv
    ) else (
        where python >nul 2>nul
        if errorlevel 1 (
            echo Python 3.11 or newer was not found. Install Python and enable the Python launcher or add python.exe to PATH.
            goto :failed
        )
        python -m venv .venv
    )
    if errorlevel 1 (
        echo Could not create the project virtual environment.
        goto :failed
    )
)

".venv\Scripts\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
if errorlevel 1 (
    echo Python 3.11 or newer is required. Recreate .venv with a Python 3.11+ interpreter.
    goto :failed
)

".venv\Scripts\python.exe" -c "import pandas, plotly, streamlit" >nul 2>nul
if errorlevel 1 (
    echo Installing project dependencies...
    ".venv\Scripts\python.exe" -m pip --version >nul 2>nul
    if errorlevel 1 (
        ".venv\Scripts\python.exe" -m ensurepip --upgrade
        if errorlevel 1 (
            echo Could not initialize pip in the virtual environment.
            goto :failed
        )
    )
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Dependency installation failed. Check your internet connection and requirements.txt.
        goto :failed
    )
)

".venv\Scripts\python.exe" -m streamlit run app.py
if errorlevel 1 (
    echo Streamlit exited with an error. Review the output above.
    goto :failed
)
exit /b 0

:failed
pause
exit /b 1
