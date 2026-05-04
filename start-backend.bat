@echo off
cd /d "%~dp0backend"
call venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8001 --reload --timeout-keep-alive 1800 --timeout-graceful-shutdown 1800
