@echo off
echo Starting Datasette for Power System Database (Simple Version)
echo ============================================================
echo.
echo Database: data.db
echo Web Interface: http://localhost:8001
echo.

cd /d "%~dp0"
call dlr-env\Scripts\activate
echo Starting Datasette server...
datasette data.db --port 8001 --host 0.0.0.0 --open

pause