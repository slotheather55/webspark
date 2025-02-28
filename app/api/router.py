from fastapi import APIRouter

from app.api.endpoints import analysis, enhancements, screenshots, tealium

api_router = APIRouter()

api_router.include_router(
    analysis.router, 
    prefix="/analysis", 
    tags=["analysis"]
)

api_router.include_router(
    enhancements.router, 
    prefix="/enhancements", 
    tags=["enhancements"]
)

api_router.include_router(
    screenshots.router, 
    prefix="/screenshots", 
    tags=["screenshots"]
)

api_router.include_router(
    tealium.router, 
    prefix="/tealium", 
    tags=["tealium"]
) 