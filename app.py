import sys
import asyncio
import json
import logging
import os
import re
import time
import traceback
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote
import uvicorn
import glob
import shutil


# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s',
    encoding='utf-8'  # Add UTF-8 encoding to handle emoji characters
)

# Set the Proactor event loop on Windows for subprocess support.
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from analyzers import tealium_manual_analyzer

# Default URL
DEFAULT_URL = "https://www.penguinrandomhouse.com/books/734292/the-very-hungry-caterpillars-peekaboo-easter-by-eric-carle-illustrated-by-eric-carle/9780593750179/"

def cleanup_old_data():
    """
    Clean up old screenshots and temporary data files before starting new analysis.
    """
    try:
        # Clean up old log files if they exist
        # This section has been cleaned up after removing browser-use
        
        # Clean up old timestamped analysis files
        try:
            data_dir = "data/"
            if os.path.exists(data_dir):
                # Remove old timestamped files
                old_pattern_files = glob.glob(os.path.join(data_dir, "*_analysis_*_202*.json"))
                for file_path in old_pattern_files:
                    try:
                        os.remove(file_path)
                        logging.info(f"Removed old analysis file: {os.path.basename(file_path)}")
                    except Exception as e:
                        logging.warning(f"Could not remove old analysis file {file_path}: {e}")
                
                if old_pattern_files:
                    logging.info(f"Cleaned up {len(old_pattern_files)} old analysis file(s)")
        except Exception as e:
            logging.warning(f"Error cleaning up old analysis files: {e}")
                    
    except Exception as e:
        logging.error(f"Error during cleanup: {e}")
        # Don't fail the analysis if cleanup fails

# Create FastAPI instance
app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
# Screenshot mounting removed - no longer using browser-use


# Configure templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Renders the main HTML page.
    """
    return templates.TemplateResponse("index.html", {"request": request, "default_url": DEFAULT_URL})

@app.get("/stream")
async def stream(request: Request, url: str = DEFAULT_URL):
    """
    Async streaming endpoint for server-sent events.
    """
    url = unquote(url)
    if not re.match(r'^https?://', url):
        print(f"Warning: Stream URL doesn't start with http/https. Prepending https://")
        url = "https://" + url

    async def event_generator():
        final_results = None # Variable to store the final results
        try:
            # Clean up old data before starting new analysis
            cleanup_old_data()
            print(f"Streaming analysis for: {url}")
            async for update in tealium_manual_analyzer.analyze_page_tags_and_events(url):
                yield f"data: {json.dumps(update)}\n\n"
                # Store the results if the update indicates completion
                if update.get("status") == "complete" and "results" in update:
                    final_results = update["results"]

            print(f"Finished streaming for: {url}")

            # Save the final results to a file if analysis completed successfully
            if final_results and not final_results.get("error"):
                # Create filename without timestamp to overwrite previous analysis
                filename = f"data/tealium_manual_analysis.json"
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(final_results, f, indent=2, default=str)
                    print(f"Analysis results saved locally to: {filename}")
                except Exception as save_e:
                    print(f"Error saving analysis results locally: {save_e}")
            elif final_results and final_results.get("error"):
                 print("Analysis completed with error, results not saved locally.")
            else:
                 print("Analysis did not yield final results, nothing saved locally.")

        except Exception as e:
            print(f"Error during streaming analysis for {url}: {e}")
            traceback.print_exc()
            error_payload = {
                "status": "error",
                "message": f"An error occurred on the server during analysis: {str(e)}"
            }
            try:
                yield f"data: {json.dumps(error_payload)}\n\n"
            except Exception as yield_e:
                print(f"Error yielding final error message: {yield_e}")

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# Record page route  
@app.get("/record", response_class=HTMLResponse)
async def show_record_page(request: Request):
    return templates.TemplateResponse("record.html", {"request": request, "default_url": DEFAULT_URL})



# Import macro recording functionality
from core.macro_recorder import recorder_manager

# API endpoints for macro recording
@app.get("/api/record/check-browser")
async def check_browser_availability():
    """Check if Playwright browser is available"""
    try:
        from playwright.async_api import async_playwright
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        await browser.close()
        
        return {
            "success": True,
            "message": "Browser is available and working"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Browser check failed: {str(e)}",
            "suggestion": "You may need to install Playwright browsers. Run: python -m playwright install chromium"
        }

@app.post("/api/record/start")
async def start_recording_session(request: Request):
    """Start a new macro recording session"""
    try:
        body = await request.json()
        url = body.get("url")
        macro_name = body.get("macro_name", "")
        
        if not url:
            return {"success": False, "error": "URL is required"}
        
        # Check browser availability first
        browser_check = await check_browser_availability()
        if not browser_check["success"]:
            return {
                "success": False, 
                "error": f"Browser not available: {browser_check['error']}",
                "suggestion": browser_check.get("suggestion", "")
            }
        
        success, session_id, message = await recorder_manager.start_recording_session(url, macro_name)
        
        if success:
            return {
                "success": True,
                "session_id": session_id,
                "message": message
            }
        else:
            return {
                "success": False,
                "error": message
            }
            
    except Exception as e:
        import traceback
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}

@app.get("/api/record/stream/{session_id}")
async def stream_recorded_actions(session_id: str):
    """Stream recorded actions via Server-Sent Events"""
    async def event_generator():
        session = recorder_manager.get_session(session_id)
        if not session:
            yield f"data: {json.dumps({'error': 'Session not found'})}\n\n"
            return
        
        # Create a queue to collect actions
        action_queue = asyncio.Queue()
        
        async def action_listener(action):
            await action_queue.put(action)
        
        # Add listener to session
        session.add_action_listener(action_listener)
        
        try:
            # Keep connection alive and stream actions
            while session.is_active:
                try:
                    # Wait for an action with timeout
                    action = await asyncio.wait_for(action_queue.get(), timeout=1.0)
                    action_data = {
                        "type": action.action_type,
                        "selector": action.selector,
                        "text": action.text,
                        "coordinates": action.coordinates,
                        "timestamp": action.timestamp,
                        "description": action.description
                    }
                    yield f"data: {json.dumps(action_data)}\n\n"
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    
        finally:
            # Remove listener when connection closes
            session.remove_action_listener(action_listener)
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/record/save")
async def save_recorded_macro(request: Request):
    """Save a completed recording session as a macro"""
    try:
        body = await request.json()
        session_id = body.get("session_id")
        macro_data = body.get("macro_data", {})
        
        if not session_id:
            return {"success": False, "error": "Session ID is required"}
        
        success, macro_id, message = await recorder_manager.stop_recording_session(
            session_id, save_macro=True
        )
        
        if success:
            return {
                "success": True,
                "macro_id": macro_id,
                "message": message
            }
        else:
            return {
                "success": False,
                "error": message
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/record/stop/{session_id}")
async def force_stop_recording(session_id: str):
    """Force stop a recording session"""
    try:
        success, macro_id, message = await recorder_manager.stop_recording_session(
            session_id, save_macro=False
        )
        
        return {
            "success": success,
            "message": message
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/macros/list")
async def list_saved_macros():
    """Get a list of all saved macros"""
    try:
        macros = recorder_manager.storage.list_macros()
        return {
            "success": True,
            "macros": [macro.to_dict() for macro in macros]
        }
    except Exception as e:
        return {"success": False, "error": str(e), "macros": []}

@app.delete("/api/macros/{macro_id}")
async def delete_macro(macro_id: str):
    """Delete a saved macro"""
    try:
        success = recorder_manager.storage.delete_macro(macro_id)
        if success:
            return {"success": True, "message": "Macro deleted successfully"}
        else:
            return {"success": False, "error": "Failed to delete macro"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/macros/{macro_id}")
async def get_macro(macro_id: str):
    """Get a specific macro by ID"""
    try:
        macro = recorder_manager.storage.load_macro(macro_id)
        if macro:
            return {"success": True, "macro": macro.to_dict()}
        else:
            return {"success": False, "error": "Macro not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/macros/{macro_id}")
async def update_macro(macro_id: str, request: Request):
    """Update macro metadata"""
    try:
        body = await request.json()
        macro = recorder_manager.storage.load_macro(macro_id)
        
        if not macro:
            return {"success": False, "error": "Macro not found"}
        
        # Update the fields
        if "name" in body:
            macro.name = body["name"]
        if "description" in body:
            macro.description = body["description"]
        
        # Save the updated macro
        success = recorder_manager.storage.save_macro(macro)
        
        if success:
            return {"success": True, "message": "Macro updated successfully"}
        else:
            return {"success": False, "error": "Failed to update macro"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/macros/import")
async def import_macro(request: Request):
    """Import a macro from JSON data"""
    try:
        body = await request.json()
        macro_data = body.get("macro_data")
        
        if not macro_data:
            return {"success": False, "error": "No macro data provided"}
        
        # Import the macro
        from core.macro_recorder import Macro
        import uuid
        
        # Generate new ID for imported macro
        macro_data["id"] = str(uuid.uuid4())
        macro_data["created_at"] = datetime.now().isoformat()
        
        # Add imported suffix to name to avoid conflicts
        if not macro_data.get("name", "").endswith("(imported)"):
            macro_data["name"] = macro_data.get("name", "Imported Macro") + " (imported)"
        
        macro = Macro.from_dict(macro_data)
        success = recorder_manager.storage.save_macro(macro)
        
        if success:
            return {"success": True, "macro_id": macro.id, "message": "Macro imported successfully"}
        else:
            return {"success": False, "error": "Failed to save imported macro"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/macros/play/{macro_id}")
async def play_macro(macro_id: str):
    """Start playback of a saved macro"""
    try:
        success, playback_id, message = await recorder_manager.start_playback_session(macro_id)
        
        if success:
            return {
                "success": True,
                "playback_id": playback_id,
                "message": message
            }
        else:
            return {
                "success": False,
                "error": message
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/macros/playback/stream/{playback_id}")
async def stream_macro_playback(playback_id: str):
    """Stream macro playback progress via Server-Sent Events"""
    async def event_generator():
        playback = recorder_manager.get_playback(playback_id)
        if not playback:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Playback session not found'})}\n\n"
            return
        
        # Create a queue to collect playback events
        event_queue = asyncio.Queue()
        
        async def playback_listener(data):
            await event_queue.put(data)
        
        # Add listener to playback session
        playback.add_playback_listener(playback_listener)
        
        try:
            # Keep connection alive and stream playback events
            while playback.is_active:
                try:
                    # Wait for an event with timeout
                    event = await asyncio.wait_for(event_queue.get(), timeout=1.0)
                    yield f"data: {json.dumps(event)}\n\n"
                    
                    # Check if playback completed
                    if event.get('type') in ['complete', 'error']:
                        break
                        
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    
        finally:
            # Remove listener when connection closes
            playback.remove_playback_listener(playback_listener)
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/api/macros/playback/{playback_id}/stop")
async def stop_macro_playback(playback_id: str):
    """Stop an active macro playback"""
    try:
        playback = recorder_manager.get_playback(playback_id)
        if not playback:
            return {"success": False, "error": "Playback session not found"}
        
        playback.stop_playback()
        return {"success": True, "message": "Playback stopped"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/macros/play-with-analysis/{macro_id}")
async def play_macro_with_analysis(macro_id: str):
    """Start macro playback with integrated tag analysis"""
    try:
        # Start the playback session
        success, playback_id, message = await recorder_manager.start_playback_session(macro_id)
        
        if not success:
            return {"success": False, "error": message}
        
        # Get the playback session and macro details
        playback = recorder_manager.get_playback(playback_id)
        if not playback:
            return {"success": False, "error": "Failed to get playback session"}
        
        # Set up analysis integration
        # This will monitor the playback page for tag events during macro execution
        await setup_playback_analysis_integration(playback)
        
        return {
            "success": True,
            "playback_id": playback_id,
            "macro_name": playback.macro.name,
            "message": "Macro playback with analysis started successfully"
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

async def setup_playback_analysis_integration(playback_session):
    """Set up analysis integration for macro playback"""
    try:
        if not playback_session.page:
            return
        
        # Inject the same analysis scripts used by the regular analyzer
        await playback_session.page.evaluate("""
            // Enhanced analysis integration for macro playback
            window.macroAnalysis = {
                events: [],
                tags: {},
                
                // Capture tealium events during playback
                captureEvents: function() {
                    // Monitor utag events
                    if (window.utag && window.utag.track) {
                        const originalTrack = window.utag.track;
                        window.utag.track = function(event_type, data) {
                            console.log('MACRO_ANALYSIS_EVENT:' + JSON.stringify({
                                type: 'utag_track',
                                event_type: event_type,
                                data: data,
                                timestamp: Date.now(),
                                url: window.location.href
                            }));
                            
                            return originalTrack.apply(this, arguments);
                        };
                    }
                    
                    // Monitor gtag events
                    if (window.gtag) {
                        const originalGtag = window.gtag;
                        window.gtag = function(command, target_id, parameters) {
                            console.log('MACRO_ANALYSIS_EVENT:' + JSON.stringify({
                                type: 'gtag',
                                command: command,
                                target_id: target_id,
                                parameters: parameters,
                                timestamp: Date.now(),
                                url: window.location.href
                            }));
                            
                            return originalGtag.apply(this, arguments);
                        };
                    }
                    
                    // Monitor Facebook Pixel events
                    if (window.fbq) {
                        const originalFbq = window.fbq;
                        window.fbq = function(event_type, event_name, parameters) {
                            console.log('MACRO_ANALYSIS_EVENT:' + JSON.stringify({
                                type: 'facebook_pixel',
                                event_type: event_type,
                                event_name: event_name,
                                parameters: parameters,
                                timestamp: Date.now(),
                                url: window.location.href
                            }));
                            
                            return originalFbq.apply(this, arguments);
                        };
                    }
                    
                    // Monitor network requests for tracking calls
                    const originalFetch = window.fetch;
                    window.fetch = function(url, options) {
                        if (typeof url === 'string' && 
                            (url.includes('google-analytics') || 
                             url.includes('facebook.com') || 
                             url.includes('tealium') ||
                             url.includes('collect'))) {
                            
                            console.log('MACRO_ANALYSIS_EVENT:' + JSON.stringify({
                                type: 'network_request',
                                url: url,
                                method: options?.method || 'GET',
                                timestamp: Date.now(),
                                source_url: window.location.href
                            }));
                        }
                        
                        return originalFetch.apply(this, arguments);
                    };
                    
                    console.log('✅ Macro analysis integration initialized');
                }
            };
            
            // Start capturing immediately
            window.macroAnalysis.captureEvents();
        """)
        
        # Add console listener to capture analysis events
        analysis_events = []
        
        def handle_analysis_console(msg):
            if "MACRO_ANALYSIS_EVENT:" in msg.text:
                try:
                    event_data = json.loads(msg.text.replace("MACRO_ANALYSIS_EVENT:", ""))
                    analysis_events.append(event_data)
                    logging.info(f"Captured analysis event during macro playback: {event_data['type']}")
                except Exception as e:
                    logging.error(f"Error parsing analysis event: {e}")
        
        playback_session.page.on("console", handle_analysis_console)
        
        # Store analysis events in the playback session for later retrieval
        playback_session.analysis_events = analysis_events
        
        logging.info("Analysis integration set up for macro playback")
        
    except Exception as e:
        logging.error(f"Failed to set up playback analysis integration: {e}")

@app.get("/api/macros/playback/{playback_id}/analysis")
async def get_playback_analysis_results(playback_id: str):
    """Get analysis results from macro playback"""
    try:
        playback = recorder_manager.get_playback(playback_id)
        if not playback:
            return {"success": False, "error": "Playback session not found"}
        
        # Get collected analysis events
        analysis_events = getattr(playback, 'analysis_events', [])
        
        # Process and categorize the events
        results = {
            "macro_name": playback.macro.name,
            "macro_url": playback.macro.url,
            "total_events": len(analysis_events),
            "events_by_type": {},
            "timeline": [],
            "summary": {
                "tracking_calls": 0,
                "user_interactions": len(playback.macro.actions),
                "network_requests": 0
            }
        }
        
        # Categorize events
        for event in analysis_events:
            event_type = event.get('type', 'unknown')
            if event_type not in results["events_by_type"]:
                results["events_by_type"][event_type] = []
            results["events_by_type"][event_type].append(event)
            
            # Add to timeline
            results["timeline"].append({
                "timestamp": event.get('timestamp', 0),
                "type": event_type,
                "description": f"{event_type} event",
                "details": event
            })
            
            # Update summary
            if event_type in ['utag_track', 'gtag', 'facebook_pixel']:
                results["summary"]["tracking_calls"] += 1
            elif event_type == 'network_request':
                results["summary"]["network_requests"] += 1
        
        # Sort timeline by timestamp
        results["timeline"].sort(key=lambda x: x.get('timestamp', 0))
        
        return {
            "success": True,
            "analysis_results": results
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/macros/{macro_id}/analyze-tealium-events")
async def analyze_macro_tealium_events(macro_id: str):
    """Analyze actual Tealium events triggered by macro click selectors"""
    try:
        macro = recorder_manager.storage.load_macro(macro_id)
        if not macro:
            return {"success": False, "error": "Macro not found"}
        
        # Extract click selectors from macro actions
        macro_selectors = []
        for action in macro.actions:
            if action.action_type == 'click' and action.selector:
                macro_selectors.append({
                    'selector': action.selector,
                    'description': action.description or f"Click: {action.selector}",
                    'action_type': action.action_type
                })
        
        if not macro_selectors:
            return {"success": False, "error": "No click actions found in macro"}
        
        # Start the analysis using streaming
        return {
            "success": True,
            "message": f"Starting Tealium analysis for {len(macro_selectors)} click actions",
            "macro_name": macro.name,
            "macro_url": macro.url,
            "click_actions": len(macro_selectors)
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/macros/{macro_id}/analyze-tealium-events/stream")
async def stream_macro_tealium_analysis(macro_id: str):
    """Stream Tealium analysis results for macro click selectors"""
    async def event_generator():
        final_results = None
        try:
            macro = recorder_manager.storage.load_macro(macro_id)
            if not macro:
                yield f"data: {json.dumps({'error': 'Macro not found'})}\n\n"
                return
            
            # Extract click selectors from macro actions  
            macro_selectors = []
            for action in macro.actions:
                if action.action_type == 'click' and action.selector:
                    macro_selectors.append({
                        'selector': action.selector,
                        'description': action.description or f"Click: {action.selector}",
                        'action_type': action.action_type,
                        'locator_bundle': getattr(action, 'locator_bundle', None)
                    })
            
            if not macro_selectors:
                yield f"data: {json.dumps({'error': 'No click actions found in macro'})}\n\n"
                return

            # Server-side debug logging so progress is visible in terminal
            logging.info(f"[MacroAnalysis] Starting stream for macro '{macro.name}' ({macro.id}) on URL: {macro.url}")
            logging.info(f"[MacroAnalysis] Click actions to test: {len(macro_selectors)}")
            
            # Import the macro analyzer
            from analyzers.macro_tealium_analyzer import analyze_macro_tealium_events
            
            # Stream the analysis
            async for update in analyze_macro_tealium_events(macro.url, macro_selectors, macro.name):
                try:
                    status = update.get('status')
                    message = update.get('message') or ''
                    if status == 'complete' and 'results' in update:
                        final_results = update['results']
                    if status == 'selector_completed':
                        result = (update.get('result') or {})
                        sel_desc = result.get('description') or (update.get('selector_description') or '')
                        strategy = result.get('strategy_used') or 'unknown'
                        clicked_el = result.get('clicked_element') or {}
                        href = clicked_el.get('href')
                        text = (clicked_el.get('text') or '').strip() if isinstance(clicked_el.get('text'), str) else ''
                        logging.info(
                            f"[MacroAnalysis] Selector completed: {sel_desc} | strategy={strategy}"
                            + (f" | href={href}" if href else "")
                            + (f" | text='{text[:120]}'" if text else "")
                        )
                    elif status == 'testing_selector':
                        sel_desc = update.get('selector_description') or ''
                        logging.info(f"[MacroAnalysis] Testing selector: {sel_desc}")
                    elif status == 'error':
                        logging.error(f"[MacroAnalysis] Error: {message}")
                    elif status == 'complete':
                        logging.info("[MacroAnalysis] Analysis complete")
                    elif status:
                        logging.info(f"[MacroAnalysis] {status}: {message}")
                except Exception:
                    # Never break streaming on logging failure
                    pass
                yield f"data: {json.dumps(update)}\n\n"
                
        except Exception as e:
            error_payload = {
                "status": "error",
                "message": f"Analysis failed: {str(e)}",
                "error": str(e)
            }
            yield f"data: {json.dumps(error_payload)}\n\n"
        finally:
            try:
                if final_results and not final_results.get('error'):
                    out_path = Path('data') / 'macro_tealium_analysis.json'
                    with open(out_path, 'w', encoding='utf-8') as f:
                        json.dump(final_results, f, indent=2, default=str)
                    logging.info(f"Saved macro analysis results to {out_path}")
            except Exception as save_e:
                logging.warning(f"Failed to save macro analysis results: {save_e}")
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


# Browser automation has been removed
# The application now focuses on manual analysis and macro recording

if __name__ == "__main__":
    # Try different ports if the default one is in use
    port = 5000
    for attempt in range(3):
        try:
            print(f"Attempting to start server on port {port}...")
            uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
            break
        except OSError as e:
            if "address already in use" in str(e).lower() or "only one usage of each socket address" in str(e).lower():
                print(f"Port {port} is already in use, trying port {port+1}")
                port += 1
                if attempt == 2:  # Last attempt
                    print(f"All ports tried are in use. Please manually specify an available port.")
                    sys.exit(1)
            else:
                raise

