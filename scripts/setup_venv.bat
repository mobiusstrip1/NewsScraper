@echo off
setlocal

cd /d "%~dp0.."

python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt

if not exist .env (
  copy .env.example .env
  echo Created .env from .env.example
)

echo Done. Activate with: .venv\Scripts\activate.bat
