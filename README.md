# WebSpark: Web Analytics Tool

WebSpark is a web analytics platform focused on comprehensive Tealium tracking analysis. It provides detailed analytics monitoring and tracking vendor detection.

## 🚀 Features

### **Analytics Features**  
- **Tealium Event Capture**: Deep analysis of tag manager implementations
- **Vendor Detection**: Identify analytics providers and tracking scripts
- **Data Layer Analysis**: Inspect utag_data variables and configurations
- **Interaction Monitoring**: Track events triggered by user interactions
- **Multi-Provider Support**: OpenAI, Azure OpenAI, Anthropic, Google

## 🛠 Technology Stack

- **Backend**: Python 3.11+, FastAPI, uvicorn
- **Browser Automation**: Playwright for webpage analysis  
- **AI/LLM**: OpenAI GPT-4, Azure OpenAI, langchain
- **Frontend**: HTML5, CSS3, JavaScript ES6+
- **Real-time**: Server-Sent Events (SSE)
- **Dependencies**: 198+ Python packages for comprehensive functionality

## ⚡ Quick Start

### Prerequisites
- **Python 3.11+** (required for modern syntax support)
- **Git** for repository cloning
- **4GB+ RAM** for browser automation
- **API Keys**: OpenAI or Azure OpenAI account

### 1-Minute Setup
```bash
# Clone and setup
git clone <your-repo-url> webspark
cd webspark

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Configure environment
echo "OPENAI_API_KEY=your_key_here" > .env
echo "MODEL_PROVIDER=openai" >> .env

# Launch
python app.py
```

**🌐 Access the application:**
- Main analyzer: `http://localhost:5000`

## 📋 Complete Installation Guide

For production deployment, see our comprehensive guide:
**[📖 INSTALLATION.md](docs/INSTALLATION.md)**

Includes:
- ✅ Production-ready setup steps
- ✅ Troubleshooting common issues  
- ✅ Azure OpenAI configuration
- ✅ Docker deployment options
- ✅ Comprehensive test suite

## 🎯 How It Works

### **Analytics Analysis**  
1. **Input**: Target URL + discovered selectors
2. **Processing**: Monitor interactions, capture Tealium events, analyze vendors
3. **Output**: Comprehensive analytics report with event data

## 📁 Project Structure
```
webspark/
├── 📁 analyzers/              # Core analysis engines
│   ├── tealium_manual_analyzer.py     # Regular flow analyzer
│   └── tealium_ai_enhanced_analyzer.py # Enhanced analyzer
├── 📁 data/                   # Generated data & results
├── 📁 static/                 # Frontend assets
├── 📁 templates/              # HTML interfaces  
├── 📁 docs/                   # Documentation
├── app.py                     # FastAPI main application
├── requirements.txt           # Python dependencies
└── .env                       # Environment configuration
```

## 🔧 Configuration

### **OpenAI Setup** (Default)
```env
MODEL_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key
```

### **Azure OpenAI Setup**
```env
MODEL_PROVIDER=azure
AZURE_TENANT_ID=your_tenant_id
AZURE_CLIENT_ID=your_client_id  
AZURE_CLIENT_SECRET=your_client_secret
AZURE_DEPLOYMENT_MODEL=your_model_deployment
AZURE_API_BASE=https://your-resource.openai.azure.com/
```

## 📊 Usage Examples

### **Analytics Analysis**  
```
URL: https://ecommerce-site.com
Result: Tealium events, vendor analysis, data layer inspection
```

## 🌟 Key Benefits

1. **Comprehensive Coverage**: Captures analytics events and tracking  
2. **Real-time Monitoring**: Live progress tracking and logging
3. **Multi-Provider Support**: Works with various analytics providers
4. **Production Ready**: Robust error handling and recovery

## 📞 Support & Documentation

- **Installation Issues**: See [INSTALLATION.md](docs/INSTALLATION.md)
- **Project Context**: See [CLAUDE.md](docs/CLAUDE.md)  
- **Architecture**: See [PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)

## 🏷 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- **Playwright**: Browser automation infrastructure
- **OpenAI**: GPT-4 model for visual AI
- **FastAPI**: Modern Python web framework