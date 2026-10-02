@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "AUTO_MODE=0"
if /I "%~1"=="--auto" set "AUTO_MODE=1"

echo.
echo ==========================================
echo   SANKET AI - Runtime Repair / Setup
echo ==========================================
echo.

set "PYTHON_CMD="
py -3.11 -c "import sys,platform; assert platform.architecture()[0]=='64bit'" >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py -3.11"

if not defined PYTHON_CMD (
  py -3.12 -c "import sys,platform; assert platform.architecture()[0]=='64bit'" >nul 2>nul
  if not errorlevel 1 set "PYTHON_CMD=py -3.12"
)

if not defined PYTHON_CMD (
  echo [ERROR] 64-bit Python 3.11 or 3.12 was not found.
  echo Install 64-bit Python 3.11 from python.org and enable the Python launcher.
  goto :fail
)

where npm >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Node.js / npm was not found.
  echo Install Node.js 20 or newer, then double-click START_SANKET.bat again.
  goto :fail
)

echo [1/7] Rebuilding the Python environment with compatible vision packages...
if exist ".venv" (
  rmdir /s /q ".venv"
  if exist ".venv" (
    echo [ERROR] Could not remove the old .venv folder.
    echo Close Python terminals/editors using this project and try again.
    goto :fail
  )
)

%PYTHON_CMD% -m venv .venv
if errorlevel 1 goto :fail
call ".venv\Scripts\activate.bat"

echo [2/7] Installing backend dependencies...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :fail
python -m pip install -r apps\api\requirements-dev.txt
if errorlevel 1 goto :fail

echo [3/7] Installing pinned MediaPipe Holistic runtime...
python -m pip install -r apps\api\requirements-vision.txt
if errorlevel 1 goto :vision_fail

python -c "import mediapipe as mp, numpy as np, cv2; from mediapipe.python.solutions import holistic; assert mp.__version__=='0.10.21'; assert np.__version__=='1.26.4'; assert cv2.__version__.startswith('4.11.'); assert hasattr(holistic,'Holistic'); print('Vision stack: OK - MediaPipe',mp.__version__,'NumPy',np.__version__,'OpenCV',cv2.__version__)"
if errorlevel 1 goto :vision_fail

echo [4/7] Installing web dependencies...
pushd apps\web
call npm install
if errorlevel 1 (
  popd
  goto :fail
)

echo [5/7] Building the production web app...
call npm run build
if errorlevel 1 (
  popd
  goto :fail
)
popd

echo [6/7] Running backend and ML tests...
python -m pytest apps\api\tests -q
if errorlevel 1 goto :fail

echo [7/7] Final runtime verification...
python scripts\check_env.py
if errorlevel 1 goto :fail

echo.
echo ==========================================
echo   SANKET AI SETUP COMPLETE
echo ==========================================
echo Vision runtime, backend tests and web build all passed.
echo.

if "%AUTO_MODE%"=="1" (
  endlocal
  exit /b 0
)

echo Starting SANKET AI now...
echo.
python scripts\run_dev.py
set "EXIT_CODE=%errorlevel%"
if not "%EXIT_CODE%"=="0" pause
endlocal
exit /b %EXIT_CODE%

:vision_fail
echo.
echo [ERROR] The compatible MediaPipe Holistic runtime could not be created.
echo Expected: MediaPipe 0.10.21 + NumPy 1.26.4 + OpenCV 4.11.
echo The setup intentionally stopped instead of launching a half-working app.
goto :fail

:fail
echo.
echo Setup did not complete. Fix the error shown above and double-click START_SANKET.bat again.
echo.
if "%AUTO_MODE%"=="0" pause
endlocal
exit /b 1
