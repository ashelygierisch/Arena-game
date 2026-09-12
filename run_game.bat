@echo off
setlocal
cd /d "%~dp0"
title NEON DOMINATION: AI Arena

set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo Creating .venv...
  py -3 -m venv .venv
  if errorlevel 1 (
    echo Python was not found. Install Python 3 and try again.
    pause
    exit /b 1
  )
)

"%PY%" -c "import streamlit" >nul 2>&1
if errorlevel 1 (
  echo Installing Streamlit into .venv...
  "%PY%" -m pip install "streamlit>=1.32.0" "streamlit-option-menu>=0.3.13"
  if errorlevel 1 (
    echo Install failed.
    pause
    exit /b 1
  )
)

echo.
echo Starting NEON DOMINATION: AI Arena
echo Open this URL if the browser does not appear:
echo   http://localhost:8501
echo Close this window to stop the game.
echo.

start "" "http://localhost:8501"
"%PY%" -m streamlit run app.py --server.headless true --server.port 8501 --browser.gatherUsageStats false
if errorlevel 1 (
  echo Streamlit failed to start.
  pause
  exit /b 1
)
pause
