@echo off
echo =======================================
echo    Launching TasteBuddy (Backend + Frontend)
echo =======================================

REM ----- START BACKEND -----

echo Starting backend...
start cmd /k "cd backend && venv\Scripts\activate && uvicorn main:app --reload --host 127.0.0.1 --port 8000"

REM ----- WAIT FOR BACKEND TO FULLY BOOT -----
timeout /t 2 >nul

REM ----- START FRONTEND -----

echo Starting frontend on http://localhost:5500 ...
start cmd /k "cd frontend && python -m http.server 5500"

REM ----- OPEN BROWSER -----
timeout /t 1 >nul
start "" http://localhost:5500

echo All systems running. TasteBuddy is live!
exit
