@echo off
cd /d "%~dp0"

echo ========================================
echo   🚀 Starting Sentica Analytics
echo ========================================
echo.

REM Kill old processes (Python + Node)
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im node.exe >nul 2>&1

REM Start Backend (Flask)
echo 🔧 Starting Backend...
start "Sentica Backend" cmd /k "cd /d %~dp0 && python app.py"
timeout /t 6 >nul

REM Start Frontend (React + Vite)
echo 🎨 Starting Frontend...
start "Sentica Frontend" cmd /k "cd /d D:\Sentica\frontend && npm run dev"
timeout /t 10 >nul

REM Open Browser
echo 🌐 Opening browser at http://localhost:5173
start http://localhost:5173

echo.
echo ✅ Sentica is now running!
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:5173
echo.
pause
