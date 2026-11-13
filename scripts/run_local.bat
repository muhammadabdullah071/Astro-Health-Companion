@echo off
REM One command start (Windows). Run from the repo root:  scripts\run_local.bat
cd /d "%~dp0..\backend"
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
pip install -q -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 %*
