@echo off
cd /d "%~dp0\.."
if exist .venv\Scripts\python.exe (
  .venv\Scripts\python.exe -m ml.training.train_template
  .venv\Scripts\python.exe -c "import requests; print('Restart/reload backend model from Diagnostics or POST /api/model/reload')" 2>nul
) else (
  py -3.11 -m ml.training.train_template
)
