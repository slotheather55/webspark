# WebSpark Production Installation

## 🚀 Quick Install

### Linux/macOS:
```bash
chmod +x install.sh
./install.sh
```

### Windows:
```cmd
install.bat
```

## 📋 What it does:
1. ✅ Checks Python 3.11+ 
2. ✅ Creates `webspark` virtual environment
3. ✅ Installs browser-use + langchain
4. ✅ Installs clean requirements (13 packages)
5. ✅ Downloads Chromium browser (~233MB)
6. ✅ Tests all imports

## ⚙️ Configuration

**Environment Variables (set separately in production):**

**Required for OpenAI:**
- `MODEL_PROVIDER=openai`
- `OPENAI_API_KEY=<your_key>`

**Required for Azure OpenAI:**
- `MODEL_PROVIDER=azure`
- `AZURE_TENANT_ID=<tenant_id>`
- `AZURE_CLIENT_ID=<client_id>`
- `AZURE_CLIENT_SECRET=<client_secret>`
- `AZURE_DEPLOYMENT_MODEL=<model_name>`
- `AZURE_API_BASE=<azure_endpoint>`

## 🎯 Launch WebSpark

### Linux/macOS:
```bash
source webspark/bin/activate
python app.py
```

### Windows:
```cmd
webspark\Scripts\activate.bat
python app.py
```

**Access:** `http://localhost:5000`

## 🧪 Test Installation

Use test scripts to verify before production:

```bash
./install_test.sh     # Linux/macOS
install_test.bat      # Windows
```

## 📁 Clean Requirements

New `requirements.txt` contains only essential packages:
- FastAPI + uvicorn (web server)
- Playwright (browser automation) 
- Core utilities (dotenv, requests, etc.)
- Total: 13 packages vs 198 original

**Dependencies handled separately:**
- browser-use (includes langchain + AI providers)
- Browsers (downloaded by playwright)

## 🎉 Success!

After successful installation:
- ✅ WebSpark server at `http://localhost:5000`
- ✅ Agent workflow at `http://localhost:5000/agent`
- ✅ All features working (AI automation + analytics)