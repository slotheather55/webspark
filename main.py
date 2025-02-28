import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.api.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Product Manager Enhancer API",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files from React build
app.mount("/static", StaticFiles(directory="build/static"), name="static")

# Root route to serve React app
@app.get("/")
async def root():
    return FileResponse("build/index.html")

# Catch all routes for React Router
@app.get("/{full_path:path}")
async def catch_all(full_path: str):
    # If path starts with api, let it pass through to the API router
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API route not found")
    
    # For all other paths, serve the React app
    if os.path.exists(f"build/{full_path}"):
        return FileResponse(f"build/{full_path}")
    return FileResponse("build/index.html")

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 