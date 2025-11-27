@echo off
echo ========================================
echo   GitLab Repository Setup Script
echo ========================================
echo.

REM Check if git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not installed or not in PATH
    echo Please install Git and try again
    echo Download from: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo Git found! Setting up GitLab repository...
echo.

REM Get user input
set /p USERNAME="Enter your GitLab username: "
set /p PROJECT_NAME="Enter project name (default: power-system-visualization): "
if "%PROJECT_NAME%"=="" set PROJECT_NAME=power-system-visualization

echo.
echo Setting up repository: %PROJECT_NAME%
echo GitLab URL will be: https://gitlab.com/%USERNAME%/%PROJECT_NAME%
echo.

REM Initialize git repository
echo Step 1: Initializing git repository...
git init
if errorlevel 1 (
    echo ERROR: Failed to initialize git repository
    pause
    exit /b 1
)

REM Create .gitignore
echo Step 2: Creating .gitignore file...
(
echo # Python
echo __pycache__/
echo *.pyc
echo *.pyo
echo *.pyd
echo .Python
echo build/
echo develop-eggs/
echo dist/
echo downloads/
echo eggs/
echo .eggs/
echo lib/
echo lib64/
echo parts/
echo sdist/
echo var/
echo wheels/
echo *.egg-info/
echo .installed.cfg
echo *.egg
echo.
echo # Environment
echo .env
echo .venv/
echo venv/
echo ENV/
echo env/
echo.
echo # IDE
echo .vscode/
echo .idea/
echo *.swp
echo *.swo
echo.
echo # Project specific
echo *.log
echo temp/
echo test_output/
echo *.backup
) > .gitignore

REM Create README.md
echo Step 3: Creating README.md...
(
echo # 🔌 Power System Visualization Application
echo.
echo An interactive web application for power system analysis with AI assistant capabilities.
echo.
echo ## ✨ Features
echo.
echo - 🌐 **Interactive Network Visualization**: IEEE 118-bus power system topology
echo - 📊 **SLR vs DLR Comparison**: Static vs Dynamic Line Rating analysis for 5 scenarios  
echo - 🤖 **AI Assistant**: Chat interface with power system knowledge and data completion
echo - 📈 **Multi-Case Analysis**: Base case 42 with contingencies 56, 90, 123, 124, 158
echo - 🔍 **Intelligent Data Completion**: AI fills missing data using physics-based algorithms
echo.
echo ## 🚀 Quick Start
echo.
echo 1. **Clone the repository:**
echo    ```bash
echo    git clone https://gitlab.com/%USERNAME%/%PROJECT_NAME%.git
echo    cd %PROJECT_NAME%
echo    ```
echo.
echo 2. **Install dependencies:**
echo    ```bash
echo    pip install -r requirements.txt
echo    ```
echo.
echo 3. **Run the application:**
echo    ```bash
echo    python power_viz_with_database.py
echo    ```
echo.
echo 4. **Open in browser:**
echo    [http://127.0.0.1:8054](http://127.0.0.1:8054^)
echo.
echo ## 📋 System Requirements
echo.
echo - Python 3.8+
echo - 4GB RAM (8GB recommended^)
echo - Modern web browser
echo.
echo ## 📖 Documentation
echo.
echo - [Complete Setup Guide](APPLICATION_SETUP_GUIDE.md^)
echo - [Sharing Instructions](SHARING_GUIDE.md^)
echo - [GitLab Guide](GITLAB_SHARING_GUIDE.md^)
echo - [File Verification](verify_setup.py^)
echo.
echo ## 🎯 Key Features to Try
echo.
echo 1. **SLR vs DLR Analysis**: Select Base Case 42 → "🔄 SLR vs DLR (5 Scenarios^)"
echo 2. **AI Chat**: Click 🤖 icon → Ask "Check data quality" or "Explain SLR vs DLR"
echo 3. **Network Graphs**: Explore "🌐 Network Graph" with different contingencies
echo 4. **Data Completion**: Click "🔍 Analyze Data Quality" for intelligent gap filling
echo.
echo ## 🤝 Contributing
echo.
echo Contributions are welcome! Please read the setup guide and test your changes locally.
echo.
echo ## 📄 License
echo.
echo This project is for educational and research purposes.
) > README.md

REM Add files to git
echo Step 4: Adding files to git...
git add .
if errorlevel 1 (
    echo ERROR: Failed to add files to git
    pause
    exit /b 1
)

REM Create initial commit
echo Step 5: Creating initial commit...
git commit -m "Initial commit: Power System Visualization Application

- Interactive IEEE 118-bus power system visualization
- SLR vs DLR comparison analysis (5 scenarios)
- AI assistant with data completion capabilities  
- Network graph visualization with violation detection
- Multi-case contingency analysis
- Comprehensive setup and sharing documentation"

if errorlevel 1 (
    echo ERROR: Failed to create initial commit
    pause
    exit /b 1
)

REM Add GitLab remote
echo Step 6: Adding GitLab remote...
git remote add origin https://gitlab.com/%USERNAME%/%PROJECT_NAME%.git
if errorlevel 1 (
    echo ERROR: Failed to add GitLab remote
    pause
    exit /b 1
)

REM Set main branch and prepare for push
git branch -M main

echo.
echo ========================================
echo   Repository Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Create repository on GitLab:
echo    - Go to https://gitlab.com
echo    - Click "+" → "New project/repository"  
echo    - Use project name: %PROJECT_NAME%
echo    - Set visibility as desired
echo    - DO NOT initialize with README
echo.
echo 2. Push your code:
echo    git push -u origin main
echo.
echo 3. Your repository will be at:
echo    https://gitlab.com/%USERNAME%/%PROJECT_NAME%
echo.
echo 4. Share with others:
echo    git clone https://gitlab.com/%USERNAME%/%PROJECT_NAME%.git
echo.
echo Press any key to open GitLab in your browser...
pause >nul

REM Open GitLab in default browser
start https://gitlab.com

echo.
echo When ready to push, run:
echo git push -u origin main
echo.
pause