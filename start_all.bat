@echo off
echo ╔══════════════════════════════════════════╗
echo ║   TN Events Backend - Starting All       ║
echo ║   User :3000 / Vendor :3001 / Admin:3002 ║
echo ╚══════════════════════════════════════════╝
echo.

cd /d "%~dp0"

:: Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo [WARN] No venv found. Using system Python.
)

echo [1/3] Starting User Server on http://localhost:3000
start "TN Events - User (3000)" cmd /k "cd /d "%~dp0server_user" && python app.py"

timeout /t 2 /nobreak > NUL

echo [2/3] Starting Vendor Server on http://localhost:3001
start "TN Events - Vendor (3001)" cmd /k "cd /d "%~dp0server_vendor" && python app.py"

timeout /t 2 /nobreak > NUL

echo [3/3] Starting Admin Server on http://localhost:3002
start "TN Events - Admin (3002)" cmd /k "cd /d "%~dp0server_admin" && python app.py"

echo.
echo ✅ All 3 servers started!
echo.
echo   User    → http://localhost:3000
echo   Vendor  → http://localhost:3001
echo   Admin   → http://localhost:3002
echo.
echo   Admin login: admin@tnevents.com / Admin@TN2024!
echo.
pause
