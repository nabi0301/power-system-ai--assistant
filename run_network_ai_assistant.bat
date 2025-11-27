@echo off
echo Starting Power Visualization with Network Graph AI Assistant...

:: Activate the Python environment if it exists
if exist "dlr-env\Scripts\activate.bat" (
    echo Activating Python environment...
    call dlr-env\Scripts\activate.bat
) else (
    echo Warning: Python environment not found at dlr-env\Scripts\activate.bat
)

:: Run the power visualization with network graph AI assistant
python power_viz_with_database.py

:: Pause to show any errors before closing
pause