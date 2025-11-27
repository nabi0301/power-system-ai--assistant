@echo off
echo ===============================================================
echo Power System Visualization Tool with AI Assistant
echo ===============================================================

REM Define database path
set DB_PATH=C:/Projects/dlr-database-project/data.db

REM Check if the user has provided an API key
set API_KEY=%1
set MOCK_MODE=0

REM Check if API key provided as argument
if "%API_KEY%"=="" goto check_env_var
echo Using provided API key
set OPENAI_API_KEY=%API_KEY%
goto start_app

:check_env_var
REM Check if OPENAI_API_KEY is already set in environment
if not "%OPENAI_API_KEY%"=="" goto api_key_exists
echo No OpenAI API key provided or found in environment.
echo Running in enhanced rule-based mode (mock LLM)...
set MOCK_MODE=1
goto start_app

:api_key_exists
echo Using API key from environment variable OPENAI_API_KEY

:start_app
REM Start the app with the appropriate settings
if %MOCK_MODE%==1 goto start_mock
REM Start with real LLM if API key is available
python start_llm_app.py --db-path "%DB_PATH%"
goto check_error

:start_mock
REM Start with mock LLM mode (enhanced rules without API)
python start_llm_app.py --db-path "%DB_PATH%" --mock-llm

:check_error
REM If the script fails, pause to see the error
if %ERRORLEVEL% NEQ 0 echo Error starting the application.
if %ERRORLEVEL% NEQ 0 echo You can try running the app directly with: python data_viz_fall.py
if %ERRORLEVEL% NEQ 0 pause