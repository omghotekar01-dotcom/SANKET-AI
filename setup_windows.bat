@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "AUTO_MODE=0"
if /I "%~1"=="--auto" set "AUTO_MODE=1"

echo.
echo ==========================================
echo   SANKET AI - Full Runtime Setup
echo ==========================================
echo.

set "PYTHON_CMD="
py -3.11 -c "import platform; assert platform.architecture()[0]=='64bit'" >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=py -3.11"

if not defined PYTHON_CMD (
  py -3.12 -c "import platform; assert platform.architecture()[0]=='64bit'" >nul 2>nul
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

echo [1/10] Rebuilding clean Python environment...
if exist ".venv" (
  rmdir /s /q ".venv"
  if exist ".venv" (
    echo [ERROR] Could not remove the old .venv folder.
    echo Close terminals/editors using this project and try again.
    goto :fail
  )
)

%PYTHON_CMD% -m venv .venv
if errorlevel 1 goto :fail
call ".venv\Scripts\activate.bat"

echo [2/10] Installing backend dependencies...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :fail
python -m pip install -r apps\api\requirements-dev.txt
if errorlevel 1 goto :fail

echo [3/10] Installing pinned MediaPipe runtime...
python -m pip install -r apps\api\requirements-vision.txt
if errorlevel 1 goto :vision_fail

echo [4/10] Installing 50-word recognizer runtime...
python -m pip install -r apps\api\requirements-bootstrap.txt
if errorlevel 1 goto :model_fail

echo [5/10] Downloading and verifying 50-word model assets...
python scripts\install_bootstrap.py
if errorlevel 1 goto :model_fail

echo [6/10] Verifying camera + recognition models...
python -c "import numpy as np, cv2; from apps.api.app.services.landmark_service import mp,mv; assert mp is not None and mp.__version__=='0.10.21'; assert np.__version__=='1.26.4'; assert cv2.__version__.startswith('4.11.'); assert mv is not None and hasattr(mv,'HolisticLandmarker'); print('Vision runtime: OK')"
if errorlevel 1 goto :vision_fail

python -c "from pathlib import Path; from mediapipe.tasks.python import vision as mv; from apps.api.app.services.bootstrap_model import BootstrapKerasModel; assert hasattr(mv,'HolisticLandmarker'); m=BootstrapKerasModel(Path('ml/artifacts/bootstrap-50')); assert m.loaded, m.load_error; assert len(m.labels)==50; print('Combined vision + 50-word BiLSTM runtime: OK -',m.version)"
if errorlevel 1 goto :model_fail

echo [7/10] Installing web dependencies...
pushd apps\web
call npm install
if errorlevel 1 (
  popd
  goto :fail
)

echo [8/10] Building production web app...
call npm run build
if errorlevel 1 (
  popd
  goto :fail
)
popd

echo [9/10] Running backend and ML tests...
python -m pytest apps\api\tests -q
if errorlevel 1 goto :fail

echo [10/10] Final full-runtime verification...
set "PYTHONPATH=%CD%"
python scripts\check_env.py
if errorlevel 1 goto :fail
python -c "from apps.api.app.runtime import model, perception; assert perception.available, perception.reason; assert model.loaded, model.load_error; assert len(model.labels)==50; print('Integrated SANKET runtime: OK -',model.backend,model.version)"
if errorlevel 1 goto :fail

echo.
echo ==========================================
echo   SANKET AI FULL SETUP COMPLETE
echo ==========================================
echo Camera tracking + 50-word interpretation + backend + web passed.
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
echo [ERROR] MediaPipe Holistic runtime could not be created.
echo Expected: MediaPipe 0.10.21 + NumPy 1.26.4 + OpenCV 4.11.
goto :fail

:model_fail
echo.
echo [ERROR] The 50-word interpretation model could not be installed or loaded.
echo Check your internet connection, then double-click START_SANKET.bat again.
goto :fail

:fail
echo.
echo Setup did not complete. Fix the error shown above and double-click START_SANKET.bat again.
echo.
if "%AUTO_MODE%"=="0" pause
endlocal
exit /b 1
