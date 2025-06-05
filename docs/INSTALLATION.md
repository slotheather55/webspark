# WebSpark Production Installation Guide

## Prerequisites

- **Python 3.11 or higher** (Required for browser-use compatibility)
- **Git** (for cloning repository)
- **Anaconda/Miniconda** (recommended for environment management)
- **Windows/Linux/macOS** (tested on all platforms)
- **4GB+ RAM** recommended for browser automation
- **2GB+ disk space** for dependencies and browsers

## 🚀 Production-Ready Installation

### Step 1: System Preparation

```bash
# Ensure Python 3.11+ is available
python --version  # Should show 3.11.x or higher

# Update package managers (Linux/macOS)
sudo apt update && sudo apt upgrade -y  # Ubuntu/Debian
# OR
brew update && brew upgrade            # macOS
```

### Step 2: Create Isolated Environment

```bash
# Remove any existing webspark environment
conda env remove -n webspark-prod

# Create fresh production environment with Python 3.11
conda create -n webspark-prod python=3.11 -y

# Activate the environment
conda activate webspark-prod

# Verify Python version
python --version  # Must show Python 3.11.x
```

### Step 3: Clone and Setup Repository

```bash
# Clone the repository
git clone <your-repo-url> webspark-prod
cd webspark-prod

# Verify project structure
ls -la  # Should show app.py, requirements.txt, browser-use/, etc.
```

### Step 4: Install Dependencies (Critical Order)

**⚠️ IMPORTANT: Install in this exact order to avoid conflicts**

```bash
# 4.1: Install browser-use framework first (includes langchain dependencies)
cd browser-use
pip install -e .
cd ..

# 4.2: Install all other requirements
pip install -r requirements.txt

# 4.3: Install Playwright browsers (downloads ~300MB)
playwright install chromium
# Optional: Install all browsers
# playwright install
```

### Step 5: Environment Configuration

```bash
# Copy example environment file
cp .env.example .env  # If exists, or create new

# Edit environment variables
nano .env  # or vim .env or code .env
```

**Required `.env` configuration:**
```env
# Model Configuration (set to 'openai' or 'azure')
MODEL_PROVIDER=openai

# OpenAI Configuration (if using OpenAI)
OPENAI_API_KEY=your_openai_api_key_here

# Azure OpenAI Configuration (if using Azure)
AZURE_TENANT_ID=your_azure_tenant_id
AZURE_CLIENT_ID=your_azure_client_id  
AZURE_CLIENT_SECRET=your_azure_client_secret
AZURE_DEPLOYMENT_MODEL=your_deployment_name
AZURE_API_BASE=https://your-resource.openai.azure.com/

# Optional: Additional providers
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key
```

### Step 6: Verify Installation

```bash
# Test critical imports
python -c "from browser_use import Agent; print('✅ browser-use OK')"
python -c "import playwright; print('✅ playwright OK')"
python -c "import fastapi; print('✅ fastapi OK')"
python -c "from langchain_openai import ChatOpenAI; print('✅ langchain OK')"

# Test environment variables
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✅ .env loaded')"
```

### Step 7: Launch Application

```bash
# Development mode (recommended for first test)
python app.py

# Production mode with auto-restart
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5000 --timeout 120
```

**✅ Success Indicators:**
- Server starts without errors
- Logs show "Using OpenAI with model: gpt-4o" or "Using Azure OpenAI..."
- Web interface accessible at `http://localhost:5000`
- Agent page loads at `http://localhost:5000/agent`

## 🔧 Troubleshooting & Common Issues

### Critical Dependencies Explained

**Why install browser-use first?**
- Contains `langchain-core==0.3.49` (pinned version required)
- Includes `patchright` (Playwright fork optimized for AI automation)
- Prevents version conflicts with other langchain packages

**Key Package Versions:**
- `Python 3.11+` - Required for modern type syntax (`X | Y` unions)
- `langchain-core==0.3.49` - Exact version needed by browser-use
- `patchright>=1.51.0` - Playwright fork with AI enhancements
- `fastapi>=0.115.12` - Async web framework with streaming support

### Installation Verification Commands

```bash
# Full system check
python -c "
import sys
print(f'✅ Python {sys.version}')
import browser_use
print(f'✅ browser-use {browser_use.__version__}')
import playwright
print('✅ playwright OK')
from langchain_openai import ChatOpenAI, AzureChatOpenAI
print('✅ langchain providers OK')
import fastapi
print(f'✅ fastapi {fastapi.__version__}')
from dotenv import load_dotenv
import os
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY', 'Not set')
print(f'✅ Environment: {\"OPENAI_API_KEY\" if api_key != \"Not set\" else \"No API keys\"} configured')
"
```

### Server Health Check

```bash
# Test server startup (should exit gracefully after verification)
timeout 10 python app.py 2>&1 | grep -E "(Starting|Using|Uvicorn running)" || echo "⚠️ Server startup issues"

# Test specific endpoints
curl -f http://localhost:5000/ >/dev/null 2>&1 && echo "✅ Main page OK" || echo "⚠️ Main page failed"
curl -f http://localhost:5000/agent >/dev/null 2>&1 && echo "✅ Agent page OK" || echo "⚠️ Agent page failed"
```

## 🌐 Production Deployment

### Option 1: Development Mode
```bash
# Single process, auto-reload on file changes
python app.py
```

### Option 2: Production Mode (Recommended)
```bash
# Multi-worker, production-optimized
pip install gunicorn  # If not in requirements.txt

gunicorn app:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:5000 \
  --timeout 120 \
  --keepalive 2 \
  --max-requests 1000 \
  --max-requests-jitter 50
```

### Option 3: Docker Deployment
```dockerfile
# Create Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt browser-use/ ./
RUN cd browser-use && pip install -e .
COPY . .
RUN pip install -r requirements.txt && \
    playwright install chromium

EXPOSE 5000
CMD ["gunicorn", "app:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:5000"]
```

## ❌ Common Issues & Solutions

### 1. **ModuleNotFoundError: No module named 'browser_use'**
```bash
# Solution: Verify browser-use installation
cd browser-use && pip install -e . && cd ..
python -c "import browser_use; print('✅ Fixed')"
```

### 2. **TypeError: unsupported operand type(s) for |**
```bash
# Solution: Upgrade Python version
python --version  # Must be 3.11+
conda install python=3.11  # Upgrade if needed
```

### 3. **langchain version conflicts**
```bash
# Solution: Reinstall in correct order
pip uninstall langchain langchain-core langchain-openai -y
cd browser-use && pip install -e . && cd ..
pip install -r requirements.txt
```

### 4. **Playwright browsers not found**
```bash
# Solution: Install browsers after playwright package
pip install playwright
playwright install chromium  # Minimum required
# OR install all browsers: playwright install
```

### 5. **API Key errors**
```bash
# Solution: Check environment variables
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('OPENAI_API_KEY:', 'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET')"
```

### 6. **Port already in use**
```bash
# Solution: Kill process using port 5000
lsof -ti:5000 | xargs kill -9  # macOS/Linux
# Windows: netstat -ano | findstr :5000
```

### 7. **Azure OpenAI configuration**
```bash
# Solution: Set MODEL_PROVIDER correctly
echo "MODEL_PROVIDER=azure" >> .env
# Verify all Azure variables are set
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
azure_vars = ['AZURE_TENANT_ID', 'AZURE_CLIENT_ID', 'AZURE_CLIENT_SECRET', 'AZURE_DEPLOYMENT_MODEL', 'AZURE_API_BASE']
missing = [var for var in azure_vars if not os.getenv(var)]
print('✅ Azure config complete' if not missing else f'❌ Missing: {missing}')
"
```

## 📋 Complete Test Suite

Run this comprehensive test before deployment:

```bash
#!/bin/bash
# WebSpark Installation Test Suite

echo "🧪 WebSpark Installation Test Suite"
echo "=================================="

# Test 1: Python version
echo "1. Testing Python version..."
python -c "import sys; assert sys.version_info >= (3, 11), f'Python 3.11+ required, got {sys.version}'; print('✅ Python version OK')"

# Test 2: Core dependencies
echo "2. Testing core dependencies..."
python -c "
try:
    import browser_use, playwright, fastapi, uvicorn
    from langchain_openai import ChatOpenAI, AzureChatOpenAI
    print('✅ Core dependencies OK')
except ImportError as e:
    print(f'❌ Missing dependency: {e}')
    exit(1)
"

# Test 3: Environment variables
echo "3. Testing environment configuration..."
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
openai_key = os.getenv('OPENAI_API_KEY')
model_provider = os.getenv('MODEL_PROVIDER', 'openai')
if model_provider == 'openai' and not openai_key:
    print('⚠️ OPENAI_API_KEY not set but MODEL_PROVIDER=openai')
elif model_provider == 'azure':
    azure_vars = ['AZURE_TENANT_ID', 'AZURE_CLIENT_ID', 'AZURE_CLIENT_SECRET', 'AZURE_DEPLOYMENT_MODEL', 'AZURE_API_BASE']
    missing = [var for var in azure_vars if not os.getenv(var)]
    if missing:
        print(f'❌ Azure config incomplete: {missing}')
        exit(1)
print('✅ Environment configuration OK')
"

# Test 4: File structure
echo "4. Testing project structure..."
python -c "
import os
required_files = ['app.py', 'requirements.txt', 'browser-use/', 'analyzers/', 'templates/', 'static/']
missing = [f for f in required_files if not os.path.exists(f)]
if missing:
    print(f'❌ Missing files: {missing}')
    exit(1)
print('✅ Project structure OK')
"

# Test 5: Server startup (quick test)
echo "5. Testing server startup..."
timeout 5 python -c "
import asyncio
from app import app
print('✅ App imports successfully')
" 2>/dev/null || echo "⚠️ App import issues (check logs)"

echo "=================================="
echo "🎉 Installation test complete!"
echo "   Ready to run: python app.py"
```

## 🚀 Quick Start Commands

Copy and run these commands for immediate deployment:

```bash
# One-liner installation script
conda env remove -n webspark-prod -y 2>/dev/null; \
conda create -n webspark-prod python=3.11 -y && \
conda activate webspark-prod && \
cd browser-use && pip install -e . && cd .. && \
pip install -r requirements.txt && \
playwright install chromium && \
echo "✅ Installation complete! Run: python app.py"

# Quick verification
python -c "from browser_use import Agent; import fastapi; print('✅ Ready to launch')"

# Launch server
python app.py
```

## 📞 Support & Troubleshooting

If issues persist:
1. **Check logs**: Look for detailed error messages in terminal
2. **Verify versions**: Ensure Python 3.11+ and all dependencies match requirements
3. **Clean install**: Remove environment and reinstall from scratch
4. **Check permissions**: Ensure write access to data/ directory
5. **Review .env**: Verify all API keys and configuration are correct

**Common Success Patterns:**
- Clean environment + exact installation order = success
- Browser-use first → requirements.txt → playwright install
- Python 3.11+ → proper API keys → server starts cleanly