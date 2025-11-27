@echo off
echo Testing Network Comparison Visualization...

:: Activate the Python environment if it exists
if exist "dlr-env\Scripts\activate.bat" (
    echo Activating Python environment...
    call "dlr-env\Scripts\activate.bat"
) else (
    echo Warning: Python environment not found at dlr-env\Scripts\activate.bat
    echo Continuing with system Python...
)

echo.
echo Checking data availability for network comparison...

:: Run the data availability test script
python test_data_availability.py

echo.
echo Starting network comparison visualization...
echo.
echo Options:
echo 1. Run the full application:   python power_viz_with_database.py
echo 2. Ask AI assistant:           "compare networks for case X, contingency Y"
echo 3. Direct API usage:           python -c "from network_comparison import create_network_comparison; fig = create_network_comparison(5, 2); fig.show()"
echo.
echo Checking for complete cases first will help you select cases with all data available.

:: Prompt for action
set /p action="Select option (1-3) or press Enter to exit: "

if "%action%"=="1" (
    echo Starting power_viz_with_database.py...
    python power_viz_with_database.py
) else if "%action%"=="2" (
    echo Starting power_viz_with_database.py...
    python power_viz_with_database.py
) else if "%action%"=="3" (
    set /p case_id="Enter case ID: "
    set /p cont_id="Enter contingency ID (or leave blank for none): "
    
    if "%cont_id%"=="" (
        echo Running network comparison for case %case_id%...
        python -c "from network_comparison import create_network_comparison; fig = create_network_comparison(%case_id%); fig.show()"
    ) else (
        echo Running network comparison for case %case_id%, contingency %cont_id%...
        python -c "from network_comparison import create_network_comparison; fig = create_network_comparison(%case_id%, %cont_id%); fig.show()"
    )
)

echo.
echo Test complete.
pause