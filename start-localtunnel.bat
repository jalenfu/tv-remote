@echo off
REM Start FastAPI server in the background
start "FastAPI" cmd /k "cd /d %~dp0 && venv\Scripts\activate && uvicorn main:app --host 0.0.0.0 --port 8000"
REM Wait a few seconds to ensure the server starts
ping 10.0.0.201 -n 5 > nul
REM Start LocalTunnel with a consistent subdomain
lt --port 8000 --subdomain jalenfutvremote
pause 