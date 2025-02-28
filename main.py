import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import os
import logging

from app.api.router import api_router
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Product Manager Enhancer API",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Add middleware to log all requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url.path}")
    logger.debug(f"Headers: {request.headers}")
    try:
        response = await call_next(request)
        logger.info(f"Response: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise

# Custom exception handler for 405 Method Not Allowed
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 405:
        logger.error(f"Method Not Allowed: {request.method} {request.url.path}")
        logger.error(f"Available routes: {[route for route in app.routes]}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": f"Method {request.method} not allowed for {request.url.path}. Available methods: {exc.headers.get('allow', 'None')}"}
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

# Set up CORS with more appropriate settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, limit this to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files from React build
app.mount("/static", StaticFiles(directory="build/static"), name="static")

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

# Debug endpoint to list all routes
@app.get("/debug/routes")
async def debug_routes():
    routes = []
    for route in app.routes:
        routes.append({
            "path": route.path,
            "name": route.name,
            "methods": route.methods if hasattr(route, "methods") else None,
        })
    return {"routes": routes}

# Root route to serve React app
@app.get("/")
async def root():
    return FileResponse("build/index.html")

# Catch all routes for React Router
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    # For all paths except API routes, serve the React app
    if os.path.exists(f"build/{full_path}"):
        return FileResponse(f"build/{full_path}")
    return FileResponse("build/index.html")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 