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
# Agent page removed - no longer using browser automation

# Browser automation has been removed
# The application now focuses on manual analysis only

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
