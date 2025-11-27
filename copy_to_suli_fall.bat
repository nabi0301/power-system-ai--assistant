@echo off
echo 📁 Copying Power System Analytics App to SULI_Fall folder...

:: Set source and destination paths
set SOURCE_DIR=C:\Projects\dlr-database-project
set DEST_DIR=%USERPROFILE%\Desktop\SULI_Fall\Power-System-Analytics

:: Create destination directory
echo Creating destination folder...
mkdir "%DEST_DIR%" 2>nul

:: Copy essential application files
echo Copying core application files...
copy "%SOURCE_DIR%\power_viz_with_database.py" "%DEST_DIR%\"
copy "%SOURCE_DIR%\data.db" "%DEST_DIR%\"
copy "%SOURCE_DIR%\requirements.txt" "%DEST_DIR%\"

:: Copy visualization components
echo Copying visualization components...
copy "%SOURCE_DIR%\data_viz_fall.py" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\dlr_slr_comparison_figures.py" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\enhanced_network_graphs.py" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\branch_analysis.py" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\bus_analysis.py" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\generator_analysis_functions.py" "%DEST_DIR%\" 2>nul

:: Copy AI and analysis features
echo Copying AI and analysis features...
copy "%SOURCE_DIR%\simple_rag.py" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\intelligent_data_completion.py" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\case_comparison.py" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\network_comparison.py" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\comprehensive_trend_analyzer.py" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\individual_analysis.py" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\dynamic_case_management.py" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\data_availability.py" "%DEST_DIR%\" 2>nul

:: Copy database management
echo Copying database management...
copy "%SOURCE_DIR%\database_manager.py" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\multi_database_manager.py" "%DEST_DIR%\" 2>nul

:: Copy documentation and guides
echo Copying documentation...
copy "%SOURCE_DIR%\ONEDRIVE_SHARING_GUIDE.md" "%DEST_DIR%\"
copy "%SOURCE_DIR%\APPLICATION_SETUP_GUIDE.md" "%DEST_DIR%\" 2>nul
copy "%SOURCE_DIR%\SHARING_GUIDE.md" "%DEST_DIR%\" 2>nul

echo ✅ Copy complete!
echo 📁 Files copied to: %DEST_DIR%
echo 📋 Next steps:
echo    1. Check the copied files in SULI_Fall folder
echo    2. Upload SULI_Fall folder to OneDrive
echo    3. Share the OneDrive link
echo.
pause