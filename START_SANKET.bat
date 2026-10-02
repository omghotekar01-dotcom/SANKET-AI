@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title SANKET AI
set "PYTHONPATH=%CD%"

echo.
echo ==========================================
echo   SANKET AI
echo   One-click launcher
echo ==========================================
echo.

set "NEED_SETUP=0"

if not exist ".venv\Scripts\python.exe" set "NEED_SETUP=1"
if not exist "apps\web\node_modules" set "NEED_SETUP=1"

if "%NEED_SETUP%"=="0" (
  ".venv\Scripts\python.exe" scripts\check_env.py > "%TEMP%\sanket_runtime_check.log" 2>&1
  if errorlevel 1 set "NEED_SETUP=1"
)

if "%NEED_SETUP%"=="1" (
  echo [SANKET AI] Runtime is missing, outdated, or incompatible.
  echo [SANKET AI] Repairing it automatically. This is normally only needed once.
  echo.
  call setup_windows.bat --auto
  if errorlevel 1 goto :fail
)

echo.
echo [SANKET AI] Runtime ready.
echo [SANKET AI] Starting backend + web interface...
echo.
".venv\Scripts\python.exe" scripts\run_dev.py
set "EXIT_CODE=%errorlevel%"

if not "%EXIT_CODE%"=="0" (
  echo.
  echo [SANKET AI] The app stopped with error code %EXIT_CODE%.
  echo If this window shows an error, send that error to the team.
  pause
)

endlocal
exit /b %EXIT_CODE%

:fail
echo.
echo ==========================================
echo   SANKET AI COULD NOT START
echo ==========================================
echo Review the error above. Nothing was hidden.
echo.
pause
endlocal
exit /b 1
