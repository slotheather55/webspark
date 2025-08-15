# Webspark Macro Recording & Analysis Guide

## Overview

Webspark is a macro recording and analysis system designed to capture user interactions on websites and analyze their Tealium event tracking performance. This system allows you to record user journeys, test selectors across page changes, and analyze marketing tag performance.

## Core Components

### 1. Macro Recorder (`/record`)
- **Purpose**: Capture user interactions on live websites through an interactive viewport
- **Technology**: Playwright browser automation with screenshot-based interaction
- **Output**: Structured macro files with selectors, timestamps, and interaction data

### 2. Analysis Engine (`/analyze`)  
- **Purpose**: Test recorded macro selectors against websites to verify Tealium tracking
- **Technology**: Headless browser automation with event monitoring
- **Output**: Detailed reports on selector success rates and event capture

### 3. Interactive Viewport
- **Purpose**: Real-time browser interaction through screenshot overlay
- **Technology**: Server-sent events (SSE) for live updates
- **Features**: Click coordinate translation, scroll simulation, cookie dismissal

## Recording Process

### Step 1: Start Recording Session
1. Navigate to `/record` page
2. Enter target URL in the input field
3. Click "Start Recording" button
4. Browser session launches in headless mode
5. Live screenshot appears in viewport container

### Step 2: Interact with Webpage
1. **Click Elements**: Click anywhere on the screenshot
   - Coordinates are automatically scaled to browser viewport
   - Actions are recorded with CSS selectors, XPath, and ARIA attributes
   - Visual feedback shows click registration

2. **Scroll Page**: Use viewport scroll functionality
   - Scroll events are amplified for better desktop-like experience
   - Page position is tracked and maintained

3. **Monitor Events**: Real-time Tealium event capture
   - Events appear in the right panel during recording
   - Network beacons show tracking requests
   - JavaScript events are monitored and displayed

### Step 3: Stop Recording
1. Click "Stop Recording" button
2. Session terminates and browser closes
3. Macro is automatically saved with timestamp
4. Actions list shows complete interaction sequence

## Saved Macro Structure

Each recorded macro contains:

```json
{
  "id": "unique_session_id",
  "name": "Macro Name",
  "url": "https://target-website.com",
  "timestamp": "2025-01-15T10:30:00Z",
  "actions": [
    {
      "type": "click",
      "selector": "#product-button",
      "locator_bundle": {
        "css_selector": "#product-button",
        "xpath": "//button[@id='product-button']",
        "text": "Add to Cart",
        "role": "button",
        "aria_label": "Add product to cart"
      },
      "coordinates": {"x": 450, "y": 200},
      "timestamp": 1642248600000
    }
  ]
}
```

## Analysis Process

### Step 1: Select Macro for Analysis
1. Navigate to `/record` or `/analyze` page
2. Select saved macro from the list
3. Click "Analyze" button on macro card
4. Analysis engine initializes

### Step 2: Analysis Execution
The analysis engine performs these steps:

1. **Initialization**
   - Launches headless browser with Tealium monitoring
   - Injects event capture scripts
   - Sets up network request monitoring

2. **Page Load**
   - Navigates to original macro URL
   - Waits for DOM content to load
   - Automatically dismisses cookie banners/overlays

3. **Selector Testing**
   - Tests each recorded action's selectors
   - Uses multiple fallback strategies:
     - Direct CSS selector (most reliable)
     - Scoped CSS within expanded panels
     - Text-based element matching
     - ARIA role + name attributes
     - XPath expressions
     - Href pattern matching

4. **Event Monitoring**
   - Captures Tealium events triggered by each interaction
   - Records network requests to tracking endpoints
   - Monitors JavaScript console for tracking-related logs
   - Analyzes i.gif payload responses

### Step 3: Results Interpretation

#### Success Metrics
- **Element Found**: Selector successfully located element
- **Element Visible**: Element was visible and clickable
- **Click Successful**: Interaction completed without errors
- **Events Triggered**: Tealium events fired after interaction

#### Selector Strategies
- **recorded_selector**: Original CSS selector from recording
- **scoped_css**: Selector scoped to expanded content areas
- **text_based**: Element found by visible text content
- **role_name**: ARIA role and accessible name attributes
- **href_heuristic**: Link matching by URL patterns
- **xpath**: XPath expression fallback

#### Event Analysis
- **Tealium Events**: Specific tracking events captured
- **Network Beacons**: HTTP requests to tracking services
- **Console Logs**: JavaScript tracking-related messages
- **i.gif Payloads**: Tealium data collection responses

## Technical Architecture

### Browser Automation
- **Playwright**: Chromium browser automation
- **Headless Mode**: Background browser execution
- **Screenshot API**: Live viewport image capture
- **Coordinate Scaling**: Display-to-browser coordinate translation

### Event Monitoring
- **Init Scripts**: JavaScript injection for event capture
- **Network Interception**: Request/response monitoring
- **Console Capture**: JavaScript error and log tracking
- **Response Analysis**: Tealium payload parsing

### Data Storage
- **Session Management**: In-memory session tracking
- **File Storage**: JSON-based macro persistence
- **Results Caching**: Analysis result storage

## Common Issues & Solutions

### 1. Viewport Click Accuracy
**Problem**: Clicks register on wrong elements
**Solution**: Coordinate scaling system translates display coordinates to browser viewport

### 2. Cookie Overlay Blocking
**Problem**: Cookie banners prevent interaction
**Solution**: Automatic dismissal system with common selector patterns

### 3. Selector Reliability
**Problem**: CSS selectors fail across page changes
**Solution**: Multiple fallback strategies with robust element finding

### 4. Event Capture Timing
**Problem**: Events fire after analysis completes
**Solution**: Smart polling system waits for events before proceeding

### 5. UI State Management
**Problem**: Interface becomes unresponsive after recording
**Solution**: Proper state reset and cleanup procedures

## Best Practices

### Recording
1. **Wait for Page Load**: Ensure page fully loads before interacting
2. **Clear Interactions**: Click precisely on target elements
3. **Meaningful Names**: Use descriptive macro names
4. **Test Immediately**: Run analysis soon after recording

### Analysis
1. **Stable Environment**: Use consistent network conditions
2. **Current Content**: Analyze on live, current website versions
3. **Multiple Runs**: Execute analysis multiple times for reliability
4. **Review Logs**: Check live log panel for detailed execution info

### Troubleshooting
1. **Browser DevTools**: Use browser developer tools for selector validation
2. **Network Panel**: Monitor actual tracking requests
3. **Console Logs**: Check for JavaScript errors or tracking issues
4. **Element Inspector**: Verify element visibility and attributes

## API Endpoints

### Recording
- `POST /api/browser/start`: Start recording session
- `GET /api/browser/{session_id}/screenshot`: Get live screenshot
- `POST /api/browser/{session_id}/click`: Send click interaction
- `POST /api/browser/{session_id}/scroll`: Send scroll interaction
- `POST /api/browser/{session_id}/stop`: Stop recording session

### Analysis
- `POST /api/analyze/macro`: Start macro analysis
- `GET /api/analyze/macro/{session_id}/stream`: Get analysis progress stream
- `GET /api/macros`: List saved macros
- `GET /api/macros/{macro_id}`: Get specific macro data

## File Structure

```
webspark/
├── app.py                          # FastAPI main application
├── core/
│   ├── macro_recorder.py           # Browser automation & recording
│   └── session_manager.py          # Session lifecycle management
├── analyzers/
│   ├── tealium_manual_analyzer.py  # Manual analysis engine
│   └── macro_tealium_analyzer.py   # Macro analysis engine
├── static/
│   ├── recorder.js                 # Frontend recording logic
│   ├── viewport.css                # Viewport styling
│   ├── stream.css                  # Analysis interface styling
│   └── results.css                 # Results display styling
├── templates/
│   ├── index.html                  # Analysis page
│   └── record.html                 # Recording page
└── data/
    ├── macros/                     # Saved macro files
    └── analysis_results/           # Analysis output files
```

## Expected Behavior

### Normal Recording Flow
1. User clicks "Start Recording" → Browser launches → Screenshot appears
2. User clicks on screenshot → Action recorded → Visual feedback shown
3. User clicks "Stop Recording" → Session ends → Macro saved
4. Macro appears in saved macros list → Ready for analysis

### Normal Analysis Flow
1. User clicks "Analyze" on macro → Analysis engine starts → Live log appears
2. Engine tests each selector → Progress shown in stages → Results populate
3. Analysis completes → Results displayed in tabs → Summary available
4. User can view detailed breakdown → Download results → Copy data

### Error Scenarios
- **Recording fails to start**: Browser launch timeout or port conflicts
- **Screenshots not loading**: Network issues or browser crashes
- **Clicks not registering**: Coordinate scaling or overlay issues
- **Analysis errors**: Selector failures or network timeouts
- **UI becoming unresponsive**: State management or cleanup issues

## Performance Considerations

### Recording Performance
- Screenshot polling rate: 2-3 FPS for responsive feel
- Action debouncing: Prevent duplicate interactions
- Memory management: Proper session cleanup

### Analysis Performance
- Parallel selector testing: Multiple strategies simultaneously
- Smart timeouts: Adaptive waiting for slow-loading content
- Result streaming: Live progress updates via SSE

### Browser Resource Management
- Session isolation: Independent browser contexts
- Memory cleanup: Proper page and context disposal
- Port management: Dynamic port allocation for sessions

This system provides a comprehensive solution for recording user interactions and analyzing their tracking performance, with robust error handling and multiple fallback strategies to ensure reliable results across different website configurations.