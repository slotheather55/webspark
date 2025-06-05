@echo off
REM WebSpark Production Installation Script for Windows
REM This script installs WebSpark in a production environment

echo 🚀 WebSpark Production Installation
echo ====================================

set ENV_NAME=webspark

echo 1. Starting installation...

echo 2. Creating fresh virtual environment...
if exist %ENV_NAME% rmdir /s /q %ENV_NAME%
python -m venv %ENV_NAME% --clear
call %ENV_NAME%\Scripts\activate.bat

echo 3. Verifying clean environment...
python --version
pip --version

echo 4. Upgrading pip...
python -m pip install --upgrade pip

echo 5. Installing browser-use framework...
cd browser-use
pip install -e .
if errorlevel 1 (
    echo ❌ Failed to install browser-use
    exit /b 1
)
cd ..

echo 6. Installing requirements...
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install requirements
    exit /b 1
)

echo 7. Installing browsers (this may take a few minutes - downloading ~233MB)...
playwright install --with-deps chromium
if errorlevel 1 (
    echo ❌ Failed to install browsers
    exit /b 1
)

echo 8. Testing installation...
python -c "from browser_use import Agent; import playwright, fastapi; from langchain_openai import ChatOpenAI; from app import app; print('✅ All components imported successfully')"
if errorlevel 1 (
    echo ❌ Installation test failed
    exit /b 1
)

echo.
echo 🎉 WebSpark installation completed successfully!
echo.
echo Next steps:
echo 1. Set environment variables ^(MODEL_PROVIDER, OPENAI_API_KEY, etc.^)
echo.
echo 2. Activate environment and run:
echo    %ENV_NAME%\Scripts\activate.bat
echo    python app.py
echo.
echo 3. Access WebSpark at:
echo    http://localhost:5000

pause