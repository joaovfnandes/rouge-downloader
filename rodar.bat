@echo off
chcp 65001 >nul
setlocal
title Rouge Downloader
cd /d "%~dp0"

set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" (
    where py >nul 2>nul
    if not errorlevel 1 (
        py -3.12 -m venv ".venv"
    ) else (
        python -m venv ".venv"
    )
)
if not exist "%PY%" (
    echo ERRO: instale o Python 3.12 ou use a versão portátil da página Releases.
    pause
    exit /b 1
)

"%PY%" -m pip install -r requirements.txt
if errorlevel 1 (
    pause
    exit /b 1
)

start "" http://127.0.0.1:5000
"%PY%" app.py
pause
