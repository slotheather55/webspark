import sys
import asyncio

# Set the Proactor event loop on Windows for subprocess support.
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import json
import re
import traceback
from urllib.parse import unquote
from datetime import datetime # Added for timestamping filename

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import gemini_analyzer

# Default URL
DEFAULT_URL = "https://www.penguinrandomhouse.com/books/734292/the-very-hungry-caterpillars-peekaboo-easter-by-eric-carle-illustrated-by-eric-carle/9780593750179/"

# Create FastAPI instance
app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

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
            print(f"Streaming analysis for: {url}")
            async for update in gemini_analyzer.analyze_page_tags_and_events(url):
                yield f"data: {json.dumps(update)}\n\n"
                # Store the results if the update indicates completion
                if update.get("status") == "complete" and "results" in update:
                    final_results = update["results"]

            print(f"Finished streaming for: {url}")

            # Save the final results to a file if analysis completed successfully
            if final_results and not final_results.get("error"):
                # Create filename (similar to terminal version)
                sanitized_url_part = re.sub(r'^https?://', '', final_results.get('url','unknown_url'))
                sanitized_url_part = re.sub(r'[/:*?"<>|\\\\.]', '_', sanitized_url_part)[:50]
                filename = f"tealium_analysis_{sanitized_url_part}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=False)
