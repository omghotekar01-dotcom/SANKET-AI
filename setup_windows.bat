@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo.
echo ==========================================
echo   SANKET AI - Windows Setup
echo ==========================================
echo.

set "PYTHON_CMD="
py -3.11 -c "import sys" >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py -3.11"

if not defined PYTHON_CMD (
  py -3.12 -c "import sys" >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=py -3.12"
)

if not defined PYTHON_CMD (
  echo [ERROR] Python 3.11 or 3.12 was not found.
  echo Install Python 3.11 from python.org, enable the Python launcher, then run this file again.
  goto :fail
)

where npm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js / npm was not found.
  echo Install Node.js 20 or newer, then run this file again.
  goto :fail
)

echo [1/6] Creating the Python virtual environment...
%PYTHON_CMD% -m venv .venv
if errorlevel 1 goto :fail

call .venv\Scripts\activate.bat

echo [2/6] Installing backend and test dependencies...
python -m pip install --upgrade pip
if errorlevel 1 goto :fail
python -m pip install -r apps\api\requirements-dev.txt
if errorlevel 1 goto :fail

echo [3/6] Installing MediaPipe vision runtime...
python -m pip install -r apps\api\requirements-vision.txt
if errorlevel 1 goto :vision_fail
python -c "import mediapipe as mp; assert hasattr(mp, 'solutions') and hasattr(mp.solutions, 'holistic'); print('MediaPipe Holistic: OK')"
if errorlevel 1 goto :vision_fail

echo [4/6] Installing frontend dependencies...
pushd apps\web
call npm install
if errorlevel 1 (
  popd
  goto :fail
)

echo [5/6] Verifying the production web build...
call npm run build
if errorlevel 1 (
  popd
  goto :fail
)
popd

echo [6/6] Running backend tests...
python -m pytest apps\api\tests -q
if errorlevel 1 goto :fail

echo.
echo ==========================================
echo   SETUP COMPLETE
echo ==========================================
echo MediaPipe, backend tests and the web production build all passed.
echo Run: run_dev.bat
echo.
pause
exit /b 0

:vision_fail
echo.
echo [ERROR] MediaPipe Holistic did not install correctly.
echo Make sure this virtual environment was created with Python 3.11 or 3.12.
echo Delete the .venv folder and run setup_windows.bat again after fixing Python.
goto :fail

:fail
echo.
echo Setup did not complete. Fix the error shown above and run setup_windows.bat again.
echo.
pause
exit /b 1
