@echo off
echo Freeing up ports and starting all services...

:: Function to kill process on a specific port
setlocal
set "ports=8000 8001 8002 8003"

for %%p in (%ports%) do (
    echo Killing process on port %%p...
    netstat -ano | findstr :%%p >nul
    if %errorlevel%==0 (
        for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%%p') do (
            taskkill /PID %%a /F >nul 2>&1
            echo Process on port %%p killed.
        )
    ) else (
        echo No process found on port %%p.
    )
)

:: Start Services in the Same Terminal
echo Starting services...

:: Start User Service (FastAPI) on port 8000
cd /d "%~dp0\user_services"
start /B uvicorn user_service:app --host 127.0.0.1 --port 8000

:: Start Event Service (Express.js) on port 5000
cd /d "%~dp0\event"
start /B uvicorn event_service:app --host 127.0.0.1 --port 8001

:: Start Booking Service (Express.js) on port 5001
cd /d "%~dp0\booking"
start /B uvicorn booking_service:app --host 127.0.0.1 --port 8002

:: Start Notification Service (Express.js) on port 5002
cd /d "%~dp0\notification"
start /B uvicorn notification_service:app --host 127.0.0.1 --port 8003

:: Wait a few seconds to let services start
timeout /t 5 /nobreak >nul

:: Start frontend server in the same terminal
cd /d "%~dp0\frontend"
start /B python -m http.server 5500

:: Open frontend in Chrome
timeout /t 2 /nobreak >nul
start opera "http://localhost:5500/index.html"

echo All services started successfully!
pause