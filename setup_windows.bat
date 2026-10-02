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

echo [1/9] Rebuilding clean Python environment...
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

echo [2/9] Installing backend dependencies...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :fail
python -m pip install -r apps\api\requirements-dev.txt
if errorlevel 1 goto :fail

echo [3/9] Installing pinned MediaPipe runtime...
python -m pip install -r apps\api\requirements-vision.txt
if errorlevel 1 goto :vision_fail

echo [4/9] Installing pretrained-model runtime...
python -m pip install -r apps\api\requirements-bootstrap.txt
if errorlevel 1 goto :bootstrap_fail

echo [5/9] Downloading and verifying 50-word ISL bootstrap model...
python scripts\install_bootstrap.py
if errorlevel 1 goto :bootstrap_fail

python -c "import mediapipe as mp, numpy as np, cv2; from mediapipe.tasks.python import vision as mv; assert mp.__version__=='0.10.21'; assert np.__version__=='1.26.4'; assert cv2.__version__.startswith('4.11.'); assert hasattr(mv,'HolisticLandmarker'); print('Vision runtime: OK')"
if errorlevel 1 goto :vision_fail

python -c "from pathlib import Path; from apps.api.app.services.bootstrap_model import BootstrapKerasModel; m=BootstrapKerasModel(Path('ml/artifacts/bootstrap-50')); assert m.loaded, m.load_error; assert len(m.labels)==50; print('Bootstrap recognizer: OK -',m.version,'-',len(m.labels),'classes')"
if errorlevel 1 goto :bootstrap_fail

echo [6/9] Installing web dependencies...
pushd apps\web
call npm install
if errorlevel 1 (
  popd
  goto :fail
)

echo [7/9] Building production web app...
call npm run build
if errorlevel 1 (
  popd
  goto :fail
)
popd

echo [8/9] Running backend and ML tests...
python -m pytest apps\api\tests -q
if errorlevel 1 goto :fail

echo [9/9] Final runtime verification...
python scripts\check_env.py
if errorlevel 1 goto :fail

echo.
echo ==========================================
echo   SANKET AI SETUP COMPLETE
echo ==========================================
echo Camera tracking + 50-word bootstrap recognition + backend + web build passed.
echo A locally trained SANKET model will automatically override the bootstrap later.
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
echo [ERROR] MediaPipe Holistic Tasks runtime could not be created.
echo Expected: MediaPipe 0.10.21 + NumPy 1.26.4 + OpenCV 4.11.
goto :fail

:bootstrap_fail
echo.
echo [ERROR] The verified 50-word bootstrap recognizer could not be installed or loaded.
echo Check your internet connection and retry START_SANKET.bat.
echo The launcher stopped instead of using unverified/fake weights.
goto :fail

:fail
echo.
echo Setup did not complete. Fix the error shown above and double-click START_SANKET.bat again.
echo.
if "%AUTO_MODE%"=="0" pause
endlocal
exit /b 1
