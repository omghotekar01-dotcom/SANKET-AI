@echo off
setlocal
cd /d "%~dp0"
echo [1/4] Creating Python 3.11 virtual environment...
py -3.11 -m venv .venv
call .venv\Scripts\activate.bat
echo [2/4] Installing backend...
python -m pip install --upgrade pip
pip install -r apps\api\requirements-dev.txt
pip install -r apps\api\requirements-vision.txt
echo [3/4] Installing frontend...
cd apps\web
call npm install
cd ..\..
echo [4/4] Running backend tests...
python -m pytest apps\api\tests -q
echo Setup complete. Run run_dev.bat
endlocal
