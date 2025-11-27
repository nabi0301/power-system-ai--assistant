@echo off
echo Starting Fall 2025 Power System Visualization...
echo =============================================
echo.

REM Kill any existing Python processes that might be using the ports
taskkill /F /IM python.exe /FI "WINDOWTITLE eq data_viz*" >nul 2>&1
taskkill /F /IM python.exe /FI "WINDOWTITLE eq simple_fall_viz*" >nul 2>&1

REM Activate virtual environment if it exists
if exist "dlr-env\Scripts\activate.bat" (
    echo Activating virtual environment...
    call dlr-env\Scripts\activate.bat
)

REM Run the simplified visualization script
echo Starting simplified visualization server...
start "simple_fall_viz" python simple_fall_viz.py

REM Wait a moment for the server to start
timeout /t 3 /nobreak > nul

REM Open the browser
echo Opening web browser...
start http://127.0.0.1:8056

echo.
echo If the browser does not open automatically, try these URLs:
echo http://127.0.0.1:8056
echo http://127.0.0.1:8057
echo http://127.0.0.1:8058
echo.
echo Close this window to stop the server when done.