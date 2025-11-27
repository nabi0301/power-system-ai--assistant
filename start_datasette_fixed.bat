@echo off
echo =====================================
echo  Starting Datasette for Power System
echo =====================================
echo.
echo Database: data.db
echo URL: http://127.0.0.1:8001
echo.
echo After starting, you should see:
echo 1. Datasette homepage
echo 2. Link to "data" database
echo 3. List of tables when you click on "data"
echo.
echo Press Ctrl+C to stop the server
echo.

cd /d "%~dp0"
call dlr-env\Scripts\activate
echo Starting server...
datasette data.db --port 8001 --host 127.0.0.1