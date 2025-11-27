@echo off
echo =======================================================================
echo  Power Visualization Integration: data_viz_fall.py + power_viz_with_database.py
echo =======================================================================
echo.

:: Activate the virtual environment
echo Activating virtual environment...
call dlr-env\Scripts\activate.bat

:: Check for command line arguments
if "%1"=="test" goto run_tests
if "%1"=="help" goto show_help

:run_integration
echo.
echo Running power_viz_with_database.py with data_viz_fall.py integration...
echo.
python run_fall_network_integration.py
goto end

:run_tests
echo.
echo Running integration tests...
echo.
python test_fall_network_integration.py
goto end

:show_help
echo.
echo Usage:
echo   run_fall_network_integration.bat       - Run the integration
echo   run_fall_network_integration.bat test  - Run integration tests
echo   run_fall_network_integration.bat help  - Show this help message
echo.
echo Description:
echo   This script integrates data_viz_fall.py's network visualization
echo   into power_viz_with_database.py to ensure proper network diagram
echo   display. Running the integration will launch the application with
echo   the data_viz_fall.py network view enabled.
echo.

:end
pause