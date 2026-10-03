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

echo [1/13] Rebuilding clean Python environment...
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

echo [2/13] Installing backend dependencies...
python -m pip install --upgrade pip setuptools wheel
if errorlevel 1 goto :fail
python -m pip install -r apps\api\requirements-dev.txt
if errorlevel 1 goto :fail

echo [3/13] Installing pinned MediaPipe runtime...
python -m pip install -r apps\api\requirements-vision.txt
if errorlevel 1 goto :vision_fail

echo [4/13] Installing OpenVINO fallback recognizer...
python -m pip install -r apps\api\requirements-bootstrap.txt
if errorlevel 1 goto :model_fail

echo [5/13] Installing CPU PyTorch for official OpenHands INCLUDE...
python -m pip install --index-url https://download.pytorch.org/whl/cpu "torch>=2.5,<3"
if errorlevel 1 goto :openhands_fail
python -m pip install -r apps\api\requirements-openhands.txt
if errorlevel 1 goto :openhands_fail

echo [6/13] Downloading fallback 50-word model...
python scripts\install_bootstrap.py
if errorlevel 1 goto :model_fail

echo [7/13] Downloading and converting official AI4Bharat OpenHands model...
python scripts\install_openhands.py
if errorlevel 1 goto :openhands_fail

echo [8/13] Verifying MediaPipe + both recognizers...
python scripts\smoke_live_runtime.py
if errorlevel 1 goto :model_fail
python scripts\smoke_openhands_runtime.py
if errorlevel 1 goto :openhands_fail

echo [9/13] Installing web dependencies...
pushd apps\web
call npm install
if errorlevel 1 (
  popd
  goto :fail
)

echo [10/13] Building production web app...
call npm run build
if errorlevel 1 (
  popd
  goto :fail
)
popd

echo [11/13] Running backend and ML tests...
python -m pytest apps\api\tests -q
if errorlevel 1 goto :fail

echo [12/13] Checking full environment...
set "PYTHONPATH=%CD%"
python scripts\check_env.py
if errorlevel 1 goto :fail

echo [13/13] Verifying integrated model selection...
python -c "from apps.api.app.runtime import model, perception; assert perception.available, perception.reason; assert model.loaded, model.load_error; assert model.backend=='ai4bharat_include_slgcn_pytorch', (model.backend,model.selection_reason); assert len(model.labels)==263; print('Integrated SANKET runtime: OK -',model.backend,model.version)"
if errorlevel 1 goto :openhands_fail

echo.
echo ==========================================
echo   SANKET AI FULL SETUP COMPLETE
echo ==========================================
echo MediaPipe + official OpenHands INCLUDE SL-GCN + safe fallback + web passed.
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
echo [ERROR] MediaPipe Solutions Holistic runtime could not be created.
echo Expected: MediaPipe 0.10.21 + NumPy 1.26.4 + OpenCV 4.11.
goto :fail

:openhands_fail
echo.
echo [ERROR] The official AI4Bharat OpenHands INCLUDE recognizer could not be installed or loaded.
echo Check your internet connection. SANKET has not replaced the existing fallback model.
goto :fail

:model_fail
echo.
echo [ERROR] The fallback interpretation model could not be installed or loaded.
echo Check your internet connection, then double-click START_SANKET.bat again.
goto :fail

:fail
echo.
echo Setup did not complete. Fix the error shown above and double-click START_SANKET.bat again.
echo.
if "%AUTO_MODE%"=="0" pause
endlocal
exit /b 1
