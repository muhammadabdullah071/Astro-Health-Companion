@echo off
REM Rebuild the database to the known demo state (Windows).
cd /d "%~dp0..\backend"
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
pip install -q -r requirements.txt
python -m app.db.seed
