# Webspark - Macro Recorder & Tealium Analysis Tool

Webspark is a powerful web automation tool that records user interactions on websites and analyzes Tealium tag implementations. It features a modern, intuitive interface for recording macros and performing comprehensive tag analysis.

## 🚀 Features

- 🎯 **Macro Recording**: Record user interactions on any website
- 📊 **Tealium Analysis**: Analyze tag implementations and track events  
- 🎨 **Modern UI**: Clean, responsive interface with dark theme
- 🔄 **Real-time Streaming**: Live analysis with progress tracking
- 💾 **Data Export**: Export analysis results and macro data
- 🚀 **Fast Performance**: Built with FastAPI and modern web technologies

## 🛠 Technology Stack

- **Backend**: Python 3.8+, FastAPI, uvicorn
- **Browser Automation**: Playwright for webpage analysis  
- **Frontend**: HTML5, CSS3, JavaScript ES6+
- **Real-time**: Server-Sent Events (SSE)
- **UI Framework**: Custom CSS with Font Awesome icons

## ⚡ Environment Setup

### Prerequisites
- **Python 3.8+** (required)
- **Git** for repository cloning
- **4GB+ RAM** for browser automation
- **Modern web browser** (Chrome/Chromium recommended)

### 1. Create Virtual Environment

**Important**: Use the `webspark` environment name for consistency:

```bash
# Create virtual environment (DO NOT use conda)
python -m venv webspark

# Activate environment
# Windows:
webspark\Scripts\activate

# macOS/Linux:
source webspark/bin/activate
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
python -m playwright install chromium

# Verify installation
python -c "from playwright.sync_api import sync_playwright; print('✅ Playwright ready')"
```

### 3. Launch Application

```bash
# Start the server
python app.py
```

**🌐 Access the application:**
- Homepage: `http://localhost:5000`
- Macro Recorder: `http://localhost:5000/record`

## 📁 Project Structure

```
webspark/
├── app.py                     # Main FastAPI application
├── analyzers/                 # Analysis modules
│   ├── tealium_manual_analyzer.py
│   └── macro_tealium_analyzer.py
├── core/                      # Core functionality
│   └── macro_recorder.py
├── static/                    # Frontend assets
│   ├── *.css                 # Stylesheets
│   ├── recorder.js           # Main JavaScript
│   ├── macros.css           # Macro cards styling
│   └── images/              # Static images
├── templates/                 # HTML templates
│   ├── index.html           # Homepage
│   └── record.html          # Recording page
├── data/                     # Generated data (gitignored)
│   ├── macros/              # Saved macro files
│   └── *_analysis.json      # Analysis results
├── requirements.txt          # Python dependencies
├── selectors_config.py      # Element selector configuration
└── .gitignore              # Git ignore rules
```

## 🎯 How to Use

### Recording Macros

1. **Navigate to recorder**: `http://localhost:5000/record`
2. **Enter target URL**: Input the website you want to record
3. **Start recording**: Click "Start Recording" button
4. **Interact with website**: Click links, buttons, forms, etc.
5. **Stop recording**: Click "Stop Recording" to save the macro

### Analyzing Macros

1. **Find saved macro**: Check the "Saved Macros" section
2. **Click analyze**: Press the green "Analyze" button
3. **Watch progress**: Real-time analysis with progress tracking
4. **Review results**: Detailed Tealium event analysis and vendor detection

### Data Export

- Analysis results are automatically saved to `data/` directory
- Download buttons available in the UI for specific reports
- Macro data stored as JSON files in `data/macros/`

## 🔧 Configuration

### Environment Variables (Optional)

Create a `.env` file for custom settings:

```env
# Application settings
DEBUG=False
HOST=0.0.0.0
PORT=5000

# Browser settings
BROWSER_HEADLESS=True
ANALYSIS_TIMEOUT=300

# Logging
LOG_LEVEL=INFO
```

### Selector Configuration

Modify `selectors_config.py` to customize analysis targets:

```python
SELECTORS_CONFIG = {
    "affiliate_links": ".affiliate-buttons a",
    "add_to_cart": "[data-testid='add-to-cart'], .add-to-cart",
    "checkout": ".checkout-button, [href*='checkout']"
}
```

## 🐛 Troubleshooting

### Common Issues

**🔧 Browser not found:**
```bash
python -m playwright install chromium
```

**🔧 Port already in use:**
The app automatically tries ports 5000, 5001, 5002.

**🔧 Permission errors (Windows):**
Run command prompt as Administrator for Playwright installation.

**🔧 Virtual environment issues:**
```bash
# Deactivate and recreate
deactivate
rmdir /s webspark  # Windows
# rm -rf webspark    # macOS/Linux
python -m venv webspark
webspark\Scripts\activate
pip install -r requirements.txt
```

### Debug Mode

Enable detailed logging:
```bash
# Windows
set LOG_LEVEL=DEBUG
python app.py

# macOS/Linux  
LOG_LEVEL=DEBUG python app.py
```

## 🚀 Production Deployment

### Using Uvicorn

```bash
# Install production server
pip install uvicorn[standard]

# Run production server
uvicorn app:app --host 0.0.0.0 --port 5000 --workers 4
```

### Using Gunicorn (Linux/macOS)

```bash
pip install gunicorn
gunicorn app:app --bind 0.0.0.0:5000 --workers 4
```

## 💡 Development

### Code Style
- **Python**: Follow PEP 8 guidelines
- **JavaScript**: ES6+ features, async/await preferred  
- **CSS**: CSS custom properties for theming

### Adding Features
1. Backend changes: Modify `app.py` and `analyzers/`
2. Frontend changes: Update `static/` and `templates/`
3. Test thoroughly with different websites
4. Update documentation

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make changes and test
4. Commit: `git commit -m 'Add feature'`
5. Push: `git push origin feature-name`
6. Submit pull request

---

**⚠️ Important Notes:**
- Use `webspark` virtual environment name for consistency
- DO NOT use conda - use standard Python venv
- Respect website terms of service when recording macros
- Screenshots and macro data are excluded from git commits