@echo off
echo Starting Datasette for IEEE 118-Bus Power System Database
echo ========================================================
echo.
echo Database: data.db
echo Configuration: datasette_config.json  
echo Web Interface: http://localhost:8001
echo.
echo Features Available:
echo - Interactive SQL queries
echo - Visual data exploration
echo - Power system analysis views
echo - Export capabilities (JSON/CSV)
echo.

cd /d "%~dp0"
call dlr-env\Scripts\activate
datasette data.db --metadata datasette_config.json --port 8001 --host 0.0.0.0 --open

pause