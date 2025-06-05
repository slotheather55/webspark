# WebSpark Project Context

## Overview
WebSpark is a web analytics tool that captures and analyzes Tealium tracking events on e-commerce websites. It features AI-powered element discovery and comprehensive event tracking across two complementary workflows.

## Two Main Flows

### 1. Agent Flow (AI-Powered Discovery)
- **What it does**: Uses AI to automatically navigate websites, discover interactive elements, and capture selectors
- **How it works**: 
  - AI agent (GPT-4) controls browser using browser-use library with 1920x1080 viewport
  - **Automatically dismisses GDPR/cookie banners first** (mandatory step)
  - Navigates with natural language instructions (e.g., "navigate to URL and add product to cart")
  - **Captures ALL interactions**: clicked elements, page elements, navigation actions
  - Saves comprehensive selector list to `agent_discovered_selectors.json`
  - Generates screenshots and detailed history in `out.json`
- **Capabilities**:
  - Complex multi-step workflows (navigate → dismiss banner → add to cart)
  - Adaptive element discovery without predefined selectors
  - Visual page analysis with element highlighting
  - Automatic retry and error handling
- **Access**: `/agent` endpoint
- **Key files**: `test_agent.py`, `agent_gemini_analyzer.py`

### 2. Regular Flow (CSS Selector-Based Analysis)
- **What it does**: Monitors predefined page elements for Tealium events using discovered or manual selectors
- **How it works**:
  - Uses selectors from `selectors_config.py` OR `agent_discovered_selectors.json`
  - Monitors specific elements for interaction events
  - Captures Tealium/analytics data when events fire
  - Faster execution, ideal for repeated analysis
- **Data Sources**:
  - Manual selectors in `selectors_config.py`
  - **Agent-discovered selectors** from previous AI runs
- **Access**: `/` endpoint (main page)
- **Key files**: `gemini_analyzer.py`, `selectors_config.py`

## Integrated Workflow
- **Step 1**: Run Agent Flow to discover elements and interactions
- **Step 2**: Use discovered selectors for comprehensive Tealium analysis
- **Step 3**: Regular Flow can reuse selectors for ongoing monitoring

## File Structure
```
webspark/
├── app.py                    # FastAPI main application
├── test_agent.py            # AI agent browser automation
├── gemini_analyzer.py       # Regular flow analyzer
├── agent_gemini_analyzer.py # Agent-enhanced analyzer
├── selectors_config.py      # Manual CSS selector definitions
├── agent_discovered_selectors.json # AI-discovered selectors
├── out.json                 # Agent execution history
├── requirements.txt         # All dependencies (Python 3.11+)
├── browser-use/             # Browser automation library
└── templates/               # Web interface templates
```

## Quick Start

### Agent Flow (Recommended First Step)
1. Start server: `python app.py`
2. Go to `http://localhost:5000/agent`
3. Enter task: `"Navigate to [URL] and [action]"` 
   - Example: `"https://example.com and click add to cart"`
4. Watch AI navigate, dismiss banners, and perform actions
5. **Result**: Saves discovered selectors for use in Regular Flow

### Regular Flow (Analysis & Monitoring)
1. Go to `http://localhost:5000`
2. Enter URL to analyze
3. **Uses agent-discovered selectors automatically**
4. View captured Tealium events and analytics data

## Current Implementation Status

### ✅ Working Features
- **AI Agent Navigation**: Full browser control with GPT-4
- **GDPR Banner Auto-Dismissal**: Mandatory first step
- **Selector Discovery**: Captures clicked and page elements
- **Large Viewport**: 1920x1080 for better element visibility
- **Comprehensive Logging**: Detailed execution history
- **Web Interface**: Real-time streaming logs
- **Tealium Analysis**: Event capture and monitoring
- **JSON Export**: Structured data output

### 🔧 Technical Details
- **Python**: 3.11+ required (uses modern type syntax)
- **Browser**: Headless Chrome via browser-use/Playwright
- **LLM**: GPT-4 for visual analysis and decision making
- **Viewport**: 1920x1080 (configurable)
- **Max Steps**: 50 actions per task
- **Memory**: Optional memory features available

## GDPR/Cookie Banner Handling
The Agent Flow automatically handles cookie consent:
- **Mandatory first action**: Dismiss any consent banners before main task
- **Detection**: Looks for Accept, Agree, Submit, OK buttons
- **Smart identification**: Recognizes GDPR notices, privacy popups
- **Built-in behavior**: No configuration needed
- **Logging**: Documents banner dismissal in execution history

## Integration Benefits
1. **Discovery**: Agent finds elements you might miss manually
2. **Automation**: No need to inspect page source for selectors
3. **Reusability**: Discovered selectors work for ongoing monitoring
4. **Accuracy**: AI adapts to page changes and dynamic content
5. **Comprehensive**: Captures both direct interactions and page context