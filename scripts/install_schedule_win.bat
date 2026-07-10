@echo off
setlocal

set "ROOT=%~dp0.."
set "ROOT=%ROOT:~0,-1%"
set "TASK=AINewsDigest"
set "RUNNER=%ROOT%\scripts\run_daily.bat"

schtasks /Create /SC DAILY /TN "%TASK%" /TR "\"%RUNNER%\"" /ST 08:00 /F

echo Installed Windows scheduled task: %TASK%
echo Runs daily at 08:00
echo Runner: %RUNNER%
