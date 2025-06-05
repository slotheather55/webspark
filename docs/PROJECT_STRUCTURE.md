# WebSpark Project Structure Analysis

## Core Application Files

### **Main Application**
- **`app.py`** (434 lines) - FastAPI server with all endpoints
  - 8 endpoints total
  - Real-time streaming with Server-Sent Events
  - Static file serving and JSON data endpoints

### **Analysis Engines**
- **`gemini_analyzer.py`** (948 lines) - Core Tealium analysis engine
  - Playwright browser automation
  - Vendor tag detection (Google Analytics, GTM, Tealium, etc.)
  - Event capture and analysis
  - Uses selectors from `selectors_config.py`

- **`agent_gemini_analyzer.py`** (532 lines) - Enhanced analyzer
  - Same functionality as `gemini_analyzer.py`
  - Uses agent-discovered selectors from `agent_discovered_selectors.json`
  - Better coverage for dynamic pages

### **AI Agent System**
- **`test_agent.py`** (496 lines) - AI browser automation
  - GPT-4 powered navigation
  - Automatic GDPR banner dismissal
  - 1920x1080 viewport configuration
  - Selector discovery and saving
  - Enhanced page element extraction

### **Configuration**
- **`selectors_config.py`** - Manual selector definitions
  - Page type mappings
  - Element selector configurations
  - Domain-specific rules

## Web Interface

### **Templates**
- **`templates/index.html`** - Main analyzer homepage
- **`templates/agent.html`** - Agent workflow interface

### **Static Assets**
- **`static/base.css`** - Core styling
- **`static/header.css`** - Header components
- **`static/footer.css`** - Footer components
- **`static/analyzer-form.css`** - Form styling
- **`static/results.css`** - Results display
- **`static/stream.css`** - Real-time streaming interface
- **`static/scripts.js`** - Frontend JavaScript
- **`static/images/`** - Visual assets

## Data Files

### **Generated Data**
- **`agent_discovered_selectors.json`** - AI-discovered selectors
- **`out.json`** - Agent execution history
- **`agent_logs.txt`** - Real-time agent logs
- **`tealium_analysis_*.json`** - Regular analysis results
- **`agent_tealium_analysis_*.json`** - Enhanced analysis results

### **Screenshots**
- **`browser-use/dom_state_data/*.png`** - Browser state captures

## API Endpoints

### **Pages**
- `GET /` - Main analyzer page
- `GET /agent` - Agent workflow page

### **Data Endpoints**
- `GET /agent_discovered_selectors.json` - Serve discovered selectors
- `GET /static/*` - Static file serving
- `GET /screenshots/*` - Screenshot serving

### **Analysis Streaming**
- `GET /stream` - Regular analysis (Server-Sent Events)
- `GET /stream-agent-analysis` - Agent-enhanced analysis (SSE)

### **Agent Execution**
- `GET /stream-agent` - Agent log monitoring (SSE)
- `POST /api/agent` - Run agent task (JSON response)
- `POST /stream-agent-run` - Run agent with streaming (SSE)

## Legacy/Unused Files

### **Alternative Implementations**
- **`main.py`** - Different FastAPI setup (unused)
- **`run_agent.py`** - CSV-based selector automation (legacy)
- **`init_db.py`** - Database initialization (unused)

### **Test Files**
- **`tests/`** directory - Various test scripts
- **`links_product_page.csv`** - CSV selector data (legacy)

### **Documentation**
- **`integration-plan.md`** - Planning document
- **`project-schema.md`** - Schema documentation
- **`project-specs.md`** - Specifications

## Dependencies

### **Python (requirements.txt)**
- FastAPI + Uvicorn (web server)
- Playwright (browser automation)
- OpenAI/Anthropic APIs (LLM integration)
- Browser-use framework (AI agent system)
- 198 total dependencies

### **Node.js (package.json)**
- Frontend tooling dependencies
- CSS/JS build tools

## Browser-Use Framework
- **`browser-use/`** directory - Complete AI browser automation framework
- Local copy with WebSpark-specific modifications
- Playwright-based with AI visual analysis
- GPT-4 integration for element recognition

## Architecture Flow

1. **User Interface** → `templates/agent.html` or `templates/index.html`
2. **Agent Discovery** → `test_agent.py` → `agent_discovered_selectors.json`
3. **Enhanced Analysis** → `agent_gemini_analyzer.py` → `agent_tealium_analysis_*.json`
4. **Regular Analysis** → `gemini_analyzer.py` → `tealium_analysis_*.json`
5. **Real-time Updates** → Server-Sent Events → Frontend display

## Key Integrations

- **OpenAI GPT-4** - Agent decision making and visual analysis
- **Playwright** - Browser automation and page interaction
- **Tealium** - Tag management and analytics event capture
- **FastAPI** - Async web framework with streaming support
- **Browser-use** - AI-powered browser automation framework