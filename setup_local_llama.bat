@echo off
echo 🦙 Setting up Local LLaMA with Ollama for RAG System
echo ================================================
echo.

echo 📋 Checking if Ollama is installed...
where ollama >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Ollama is installed!
) else (
    echo ❌ Ollama not found. Please install from: https://ollama.ai/
    echo.
    echo 📥 Installation steps:
    echo    1. Download and install Ollama from https://ollama.ai/
    echo    2. Restart this script
    pause
    exit /b 1
)

echo.
echo 🔍 Checking available models...
ollama list

echo.
echo 📥 Recommended models for power system analysis:
echo    • llama3:8b    - Latest, good balance of speed/quality
echo    • llama2:7b    - Stable, well-tested
echo    • codellama    - Good for technical analysis
echo.

choice /C 123S /M "Select: [1] llama3:8b [2] llama2:7b [3] codellama [S] Skip download"

if errorlevel 4 goto skip_download
if errorlevel 3 set MODEL=codellama
if errorlevel 2 set MODEL=llama2:7b
if errorlevel 1 set MODEL=llama3:8b

echo.
echo 🔄 Pulling model: %MODEL%
echo This may take 5-15 minutes depending on your internet speed...
ollama pull %MODEL%

if %errorlevel% equ 0 (
    echo ✅ Model %MODEL% downloaded successfully!
) else (
    echo ❌ Failed to download model. Check your internet connection.
    pause
    exit /b 1
)

:skip_download
echo.
echo 🚀 Starting Ollama server...
echo Press Ctrl+C to stop the server when done.
echo.
echo 📝 Your RAG system will automatically detect and use the local model.
echo 🌐 Server will be available at: http://localhost:11434
echo.

ollama serve