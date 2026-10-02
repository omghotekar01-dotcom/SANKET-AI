@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo.
  echo [SANKET AI] Virtual environment not found.
  echo Run setup_windows.bat first.
  echo.
  pause
  exit /b 1
)

echo [SANKET AI] Checking the installed runtime...
".venv\Scripts\python.exe" scripts\check_env.py
if errorlevel 1 (
  echo.
  echo [SANKET AI] Required runtime packages are missing.
  echo Run setup_windows.bat again.
  echo.
  pause
  exit /b 1
)

echo [SANKET AI] Starting backend and web app from the project virtual environment...
".venv\Scripts\python.exe" scripts\run_dev.py
set EXIT_CODE=%errorlevel%

if not "%EXIT_CODE%"=="0" (
  echo.
  echo [SANKET AI] Development server stopped with error code %EXIT_CODE%.
  pause
)

endlocal
exit /b %EXIT_CODE%
