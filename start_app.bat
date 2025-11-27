@echo off
echo ========================================
echo   Power System Visualization App
echo ========================================
echo.

echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo Python found! Starting application...
echo.
echo The application will open at: http://127.0.0.1:8054
echo.
echo Press Ctrl+C to stop the application
echo ========================================
echo.

python power_viz_with_database.py

echo.
echo Application stopped.
pause