@echo off
echo 🚀 Starting Power System Visualization App (Fast Mode)
echo ⚡ Skipping AI chat for ultra-fast startup...
echo.

set DLR_FAST_MODE=1
set PYTHONPATH=%cd%

echo Starting app with Python...
"%cd%\dlr-env\Scripts\python.exe" data_viz_fall.py

pause