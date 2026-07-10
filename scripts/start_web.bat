@echo off
setlocal

cd /d "%~dp0.."

if exist ".venv\Scripts\activate.bat" (
  call ".venv\Scripts\activate.bat"
)

python -m streamlit run web/app.py --server.headless true --server.port 8502
