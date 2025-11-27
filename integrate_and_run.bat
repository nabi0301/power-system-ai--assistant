@echo off
echo Running the integration script for Power Visualization...
python integrate_power_viz.py
if %errorlevel% neq 0 (
    echo Integration failed. See above for details.
    pause
    exit /b %errorlevel%
)

echo.
echo Integration completed. Starting the application...
python run_integrated_app.py
pause