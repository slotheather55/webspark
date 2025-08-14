#!/bin/bash

# WebSpark Production Installation Script
# This script installs WebSpark in a production environment

set -e  # Exit on any error

echo "🚀 WebSpark Production Installation"
echo "===================================="

# Variables
ENV_NAME="webspark"

echo "1. Creating virtual environment..."
rm -rf $ENV_NAME 2>/dev/null || true
python3 -m venv $ENV_NAME
source $ENV_NAME/bin/activate

echo "2. Checking Python version in environment..."
python --version
if ! python -c "import sys; assert sys.version_info >= (3, 11)" 2>/dev/null; then
    echo "❌ Python 3.11+ required in virtual environment. Please install Python 3.11+ on your system."
    exit 1
fi

echo "3. Upgrading pip..."
python -m pip install --upgrade pip

echo "4. Installing requirements..."
pip install -r requirements.txt

echo "5. Installing browsers (this may take a few minutes - downloading ~233MB)..."
playwright install --with-deps chromium

echo "6. Testing installation..."
python -c "import playwright, fastapi; from app import app; print('✅ All components imported successfully')"

echo ""
echo "🎉 WebSpark installation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Configure any needed environment variables"
echo ""
echo "2. Activate environment and run:"
echo "   source $ENV_NAME/bin/activate"
echo "   python app.py"
echo ""
echo "3. Access WebSpark at:"
echo "   http://localhost:5000"