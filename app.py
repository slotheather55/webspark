import sys
import asyncio

# Set the Proactor event loop on Windows for subprocess support.
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import json
import re
import traceback
from urllib.parse import unquote

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
        try:
            print(f"Streaming analysis for: {url}")
            async for update in gemini_analyzer.analyze_page_tags_and_events(url):
                yield f"data: {json.dumps(update)}\n\n"
            print(f"Finished streaming for: {url}")
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
