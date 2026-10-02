@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3.11 scripts\check_env.py
  py -3.11 scripts\run_dev.py
) else (
  python scripts\check_env.py
  python scripts\run_dev.py
)
endlocal
