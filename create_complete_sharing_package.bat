@echo off
echo 📁 Creating complete Power System Analytics sharing package...

:: Set source and destination paths
set SOURCE_DIR=C:\Projects\dlr-database-project
set DEST_DIR=%USERPROFILE%\Desktop\SULI_Fall\Power-System-Analytics-Complete

:: Create destination directory
echo Creating destination folder...
rmdir "%DEST_DIR%" /s /q 2>nul
mkdir "%DEST_DIR%"

echo.
echo 🎯 Copying Core Application files...
copy "%SOURCE_DIR%\power_viz_with_database.py" "%DEST_DIR%\"
copy "%SOURCE_DIR%\data.db" "%DEST_DIR%\"
copy "%SOURCE_DIR%\requirements.txt" "%DEST_DIR%\"

echo.
echo 📊 Copying Visualization Components...
copy "%SOURCE_DIR%\data_viz_fall.py" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\dlr_slr_comparison_figures.py" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\enhanced_network_graphs.py" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\branch_analysis.py" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\bus_analysis.py" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\generator_analysis_functions.py" "%DEST_DIR%\" 2>nul

echo.
echo 🤖 Copying AI & RAG System...
copy "%SOURCE_DIR%\simple_rag.py" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\intelligent_data_completion.py" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\entity_extraction.py" "%DEST_DIR%\" 2>nul

echo.
echo 🔄 Copying Analysis Features...
copy "%SOURCE_DIR%\case_comparison.py" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\network_comparison.py" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\comprehensive_trend_analyzer.py" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\individual_analysis.py" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\data_availability.py" "%DEST_DIR%\" 2>nul

echo.
echo 💾 Copying Database Management...
copy "%SOURCE_DIR%\database_manager.py" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\multi_database_manager.py" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\dynamic_case_management.py" "%DEST_DIR%\" 2>nul

echo.
echo 🔧 Copying Integration Components...
copy "%SOURCE_DIR%\direct_network_integration.py" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\power_viz_integration.py" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\dlr_visualization_bridge.py" "%DEST_DIR%\" 2>nul

echo.
echo 📖 Copying Documentation...
copy "%SOURCE_DIR%\ONEDRIVE_SHARING_GUIDE.md" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\APPLICATION_SETUP_GUIDE.md" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\SHARING_GUIDE.md" "%DEST_DIR%\" 2>nul

echo.
echo ✅ Package creation complete!
echo.
echo 📁 Complete package created at:
echo    %DEST_DIR%
echo.
echo 📊 Package contents:
dir "%DEST_DIR%" /b | find /c /v "" > temp_count.txt
set /p FILE_COUNT=<temp_count.txt
del temp_count.txt
echo    - %FILE_COUNT% files copied
echo    - Ready for OneDrive upload
echo.
echo 🚀 Next steps:
echo    1. Check the folder: %DEST_DIR%
echo    2. Upload the entire folder to OneDrive
echo    3. Share the OneDrive link
echo    4. Recipients get 100%% functionality!
echo.
echo 💡 Opening the destination folder...
explorer "%DEST_DIR%"
echo.
pause