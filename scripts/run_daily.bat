@echo off
setlocal

cd /d "%~dp0.."

if exist ".venv\Scripts\activate.bat" (
  call ".venv\Scripts\activate.bat"
)

if not exist logs mkdir logs
if not exist digest mkdir digest
if not exist data mkdir data

python src\main.py >> logs\run.log 2>&1
