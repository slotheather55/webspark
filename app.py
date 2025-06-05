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

# Add browser-use directory to Python path before importing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'browser-use'))

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
from analyzers import browser_automation_agent

# Default URL
DEFAULT_URL = "https://www.penguinrandomhouse.com/books/734292/the-very-hungry-caterpillars-peekaboo-easter-by-eric-carle-illustrated-by-eric-carle/9780593750179/"

def cleanup_old_data():
    """
    Clean up old screenshots and temporary data files before starting new analysis.
    """
    try:
        # Clean up screenshots from browser-use
        screenshot_dir = "browser-use/dom_state_data/"
        if os.path.exists(screenshot_dir):
            screenshot_files = glob.glob(os.path.join(screenshot_dir, "*.png"))
            for file_path in screenshot_files:
                try:
                    os.remove(file_path)
                    logging.info(f"Removed old screenshot: {os.path.basename(file_path)}")
                except Exception as e:
                    logging.warning(f"Could not remove screenshot {file_path}: {e}")
            
            if screenshot_files:
                logging.info(f"Cleaned up {len(screenshot_files)} old screenshot(s)")
        
        # Clean up old log files if they exist
        old_log_paths = [
            "data/browser_automation_logs.txt"
        ]
        
        for log_path in old_log_paths:
            if os.path.exists(log_path):
                try:
                    # Just truncate the file instead of deleting it
                    with open(log_path, 'w', encoding='utf-8') as f:
                        f.write("# Log file cleared for new analysis session\n")
                    logging.info(f"Cleared log file: {log_path}")
                except Exception as e:
                    logging.warning(f"Could not clear log file {log_path}: {e}")
        
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
app.mount("/screenshots", StaticFiles(directory="browser-use/dom_state_data"), name="screenshots")

# Serve specific JSON files directly
@app.get("/ai_discovered_selectors.json")
async def get_ai_discovered_selectors():
    """Serve the AI discovered selectors JSON file."""
    try:
        file_path = Path(__file__).parent / "data" / "ai_discovered_selectors.json"
        if file_path.exists():
            with open(file_path, "r") as f:
                return json.load(f)
        return []  # Return empty array if file doesn't exist
    except Exception as e:
        logging.error(f"Error reading selector file: {e}")
        return []

# Configure templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Renders the main HTML page.
    """
    return templates.TemplateResponse("index.html", {"request": request, "default_url": DEFAULT_URL})

@app.get("/stream")
async def stream(request: Request, url: str = DEFAULT_URL, use_agent_selectors: bool = False):
    """
    Async streaming endpoint for server-sent events.
    """
    url = unquote(url)
    if not re.match(r'^https?://', url):
        print(f"Warning: Stream URL doesn't start with http/https. Prepending https://")
        url = "https://" + url
        
    # Set environment variable for agent selectors if requested
    # This keeps the two flows separate - regular analysis vs agent-enhanced analysis
    if use_agent_selectors:
        print(f"Using agent-discovered selectors for analysis of: {url}")
        os.environ['USE_AGENT_SELECTORS'] = 'true'
    else:
        # Ensure it's unset for regular analysis
        if 'USE_AGENT_SELECTORS' in os.environ:
            del os.environ['USE_AGENT_SELECTORS']

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

@app.get("/stream-agent-analysis")
async def stream_agent_analysis(request: Request, url: str = DEFAULT_URL):
    """
    Async streaming endpoint for AI-enhanced analysis using AI-discovered selectors.
    This endpoint uses tealium_ai_enhanced_analyzer.py instead of the regular tealium_manual_analyzer.py.
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
            print(f"Streaming agent-based analysis for: {url}")
            # Import here to avoid circular imports
            from analyzers import tealium_ai_enhanced_analyzer
            async for update in tealium_ai_enhanced_analyzer.analyze_page_tags_and_events(url):
                yield f"data: {json.dumps(update)}\n\n"
                # Store the results if the update indicates completion
                if update.get("status") == "complete" and "results" in update:
                    final_results = update["results"]

            print(f"Finished agent-based streaming for: {url}")

            # Save the final results to a file if analysis completed successfully
            if final_results and not final_results.get("error"):
                # Create filename without timestamp to overwrite previous analysis
                filename = f"data/tealium_ai_enhanced_analysis.json"
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(final_results, f, indent=2, default=str)
                    print(f"Agent analysis results saved locally to: {filename}")
                except Exception as save_e:
                    print(f"Error saving agent analysis results locally: {save_e}")
            elif final_results and final_results.get("error"):
                 print("Agent analysis completed with error, results not saved locally.")
            else:
                 print("Agent analysis did not yield final results, nothing saved locally.")

        except Exception as e:
            print(f"Error during agent-based streaming analysis for {url}: {e}")
            traceback.print_exc()
            error_payload = {
                "status": "error",
                "message": f"An error occurred on the server during agent analysis: {str(e)}"
            }
            try:
                yield f"data: {json.dumps(error_payload)}\n\n"
            except Exception as yield_e:
                print(f"Error yielding final error message: {yield_e}")

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Agent page endpoints
@app.get("/agent", response_class=HTMLResponse)
async def show_agent_form(request: Request):
    return templates.TemplateResponse("agent.html", {"request": request})

# We'll use the existing agent.html page for agent analysis

# Streaming endpoint for agent logs
@app.get("/stream-agent")
async def stream_agent_logs(request: Request):
    """Stream agent logs in real-time as server-sent events."""
    
    async def agent_log_generator():
        try:
            # Create a log file to monitor
            log_file_path = "data/browser_automation_logs.txt"
            
            # Create an empty log file if it doesn't exist
            if not os.path.exists(log_file_path):
                with open(log_file_path, "w", encoding="utf-8") as f:
                    f.write("INFO: Initializing agent log stream...\n")
            
            # Start monitoring the log file
            last_position = 0
            start_payload = json.dumps({'status': 'starting', 'message': 'Waiting for agent to start...'})
            yield f"data: {start_payload}\n\n"
            
            # Monitor the log file for changes
            timeout_counter = 0
            max_timeout = 300  # 30 seconds max wait time
            
            while timeout_counter < max_timeout:
                try:
                    with open(log_file_path, "r", encoding="utf-8") as f:
                        f.seek(last_position)
                        new_content = f.read()
                        if new_content:
                            timeout_counter = 0  # Reset timeout counter when we get new content
                            last_position = f.tell()
                            # Split by lines and send each as an event
                            for line in new_content.splitlines():
                                if line.strip():
                                    log_payload = json.dumps({'status': 'log', 'message': line})
                                    yield f"data: {log_payload}\n\n"
                        else:
                            timeout_counter += 1
                        
                        # Check if the agent has completed
                        if "Task completed" in new_content or "✅ Task completed" in new_content:
                            complete_payload = json.dumps({'status': 'complete', 'message': 'Agent task completed'})
                            yield f"data: {complete_payload}\n\n"
                            break
                        
                        # Check for errors
                        if "ERROR:" in new_content or "Error:" in new_content:
                            # Don't break, continue streaming to show all logs
                            pass
                            
                    # Small delay to prevent high CPU usage
                    await asyncio.sleep(0.1)
                except Exception as e:
                    error_msg = f"Error reading logs: {str(e)}"
                    print(error_msg)
                    error_payload = json.dumps({'status': 'error', 'message': error_msg})
                    yield f"data: {error_payload}\n\n"
                    # Don't break, try to continue reading after a short delay
                    await asyncio.sleep(1)
            
            # If we reached the timeout, send a message
            if timeout_counter >= max_timeout:
                timeout_payload = json.dumps({'status': 'error', 'message': 'Timeout waiting for agent logs. The agent may still be running.'})
                yield f"data: {timeout_payload}\n\n"
        except Exception as e:
            error_msg = f"Stream error: {str(e)}"
            print(error_msg)
            error_payload = json.dumps({'status': 'error', 'message': error_msg})
            yield f"data: {error_payload}\n\n"
    
    return StreamingResponse(agent_log_generator(), media_type="text/event-stream")

# AJAX endpoint for agent tasks
@app.post("/api/agent")
async def api_run_agent(request: Request):
    """Run the AI test agent and return JSON results."""
    try:
        # Parse the request body
        body = await request.json()
        task = body.get("task")
        
        # Check if the task is a URL and format it properly
        if task and (task.startswith('http://') or task.startswith('https://')):
            if 'click on add to cart' in task.lower() or 'add to cart' in task.lower():
                # This is a URL with an add to cart instruction
                task = f"Navigate to {task} and add the product to cart"
            else:
                # This is just a URL, so add a default instruction
                task = f"Navigate to {task} and analyze the page"
        
        # Clean up old data before starting browser automation
        cleanup_old_data()
        
        # Configure logging to file for streaming
        log_file_path = "data/browser_automation_logs.txt"
        
        # Make sure the log file is created and empty
        with open(log_file_path, 'w', encoding='utf-8') as f:
            f.write("--- Browser Automation Log Start ---\n")
        
        # Configure logging with UTF-8 encoding
        file_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Get the browser-use logger and add our file handler
        browser_use_logger = logging.getLogger("browser_use")
        browser_use_logger.setLevel(logging.INFO)
        browser_use_logger.addHandler(file_handler)
        
        # Configure agent logger
        agent_logger = logging.getLogger("agent")
        agent_logger.setLevel(logging.INFO)
        agent_logger.addHandler(file_handler)
    
        # Run the agent with the configured logging
        result = await browser_automation_agent.main(task)
        
        # Remove the file handler to avoid duplicate logs
        browser_use_logger.removeHandler(file_handler)
        agent_logger.removeHandler(file_handler)
        
        # Check if the agent run was successful
        if result == []:
            # Agent run failed, load the error data from browser_automation_history.json
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write("ERROR: Agent run failed. Check browser_automation_history.json for details\n")
            
            data = json.load(open("data/browser_automation_history.json", "r", encoding="utf-8"))
            return {
                "error": data.get("error", "Unknown error"),
                "history": [], 
                "full_data": data,
                "extracted_selectors": []
            }
        
        # Write completion message to log
        with open(log_file_path, 'a', encoding='utf-8') as f:
            f.write("INFO: ✅ Task completed\n")
        
        # Load the results from browser_automation_history.json
        data = json.load(open("data/browser_automation_history.json", "r", encoding="utf-8"))
        
        # --- Extract and Save Selectors --- #
        successful_selectors = []
        try:
            for entry in data.get("history", []):
                selector_info = entry.get("selector_info")
                if selector_info:
                    action = entry.get("model_output", {}).get("action", [{}])[0]
                    action_type = list(action.keys())[0] if action and isinstance(action, dict) else "unknown"
                    # Check if it's a potentially successful interaction with a valid selector
                    if selector_info.get("selector") and action_type not in ["finish", "fail", "unknown", "go_to_url", "open_tab", "done"]:
                        successful_selectors.append(selector_info)
            
            if successful_selectors:
                print(f"Found {len(successful_selectors)} potential selectors to process.")
                # Pass the extracted list, not the full data dict
                browser_automation_agent.extract_and_save_selectors(successful_selectors)
            else:
                print("No actionable selectors found in agent history to save.")
        except Exception as selector_ex:
             print(f"Error during selector extraction/saving: {selector_ex}")
             # Log this error to the agent log file as well
             with open(log_file_path, 'a', encoding='utf-8') as f:
                 f.write(f"ERROR: Selector extraction/saving failed: {selector_ex}\n{traceback.format_exc()}\n")
             # Decide if this error should make the API call fail or just log it
             # For now, we'll log it and continue returning the main agent data

        # Prepare the final response
        final_response = {
            "history": data.get("history", []), 
            "full_data": data,
            "extracted_selectors": successful_selectors
        }
        
        # Check if there's an error in the data
        if "error" in data:
            final_response["error"] = data.get("error")
        
        return final_response
    except Exception as e:
        # Log the error
        error_msg = f"ERROR: Agent execution failed: {str(e)}\n{traceback.format_exc()}\n"
        print(error_msg)
        
        # Write error to log file for streaming
        with open("data/browser_automation_logs.txt", "a", encoding='utf-8') as f:
            f.write(error_msg)
            
        # Return error response
        return {"error": str(e), "history": [], "full_data": {}, "extracted_selectors": []}

@app.post("/stream-agent-run")
async def stream_agent_run(request: Request):
    data = await request.json()
    task = data.get('task')
    if not task:
        # Return an SSE error message
        async def error_stream():
             yield f"data: {json.dumps({'status': 'error', 'message': 'Task description is required'})}\n\n"
        return StreamingResponse(error_stream(), media_type='text/event-stream', status=400)

    async def generate():
        try:
            # Use 'async for' to iterate through the async generator
            async for message_json in browser_automation_agent.main_generator(task):
                # message_json is already a JSON string from the generator
                yield f"data: {message_json}\n\n" # Format as SSE
                await asyncio.sleep(0.01) # Small sleep to allow event loop switching if needed
        except Exception as e:
            print(f"Error during agent streaming for task '{task}': {e}")
            traceback.print_exc()
            # Yield a final error message in SSE format
            yield f"data: {json.dumps({'status': 'error', 'message': f'Internal server error: {e}'})}\n\n"

    # Return the streaming response
    # Use await generate() if needed, but Response handles async generators directly
    return StreamingResponse(generate(), media_type="text/event-stream")

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
