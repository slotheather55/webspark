from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import crud, models
from app.db.session import get_db
from app.schemas import analysis as analysis_schema
from app.schemas import errors as error_schema
from app.api.dependencies import get_current_active_user, get_analysis_by_id
from app.services.storage.cloud import get_screenshot_url

router = APIRouter()


@router.get(
    "/{analysis_id}",
    response_model=analysis_schema.ScreenshotResponse,
    responses={
        404: {"model": error_schema.ErrorResponse},
        403: {"model": error_schema.ErrorResponse}
    }
)
async def get_screenshots(
    analysis_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_active_user)
) -> Any:
    """
    Get screenshots for a specific analysis by ID.
    
    Returns URLs to the screenshots for each device type.
    """
    # Get analysis from database
    analysis = crud.analysis.get_analysis(db, analysis_id)
    
    if not analysis:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found"
        )
    
    # Check if user owns this analysis (only if both user and analysis.user_id exist)
    if current_user and analysis.user_id and analysis.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this analysis"
        )
    
    # Get screenshots from database
    screenshots = crud.get_analysis_screenshots(db, analysis.id)
    
    if not screenshots:
        return {"screenshots": {}}
    
    # Generate URLs for screenshots
    screenshot_urls = {}
    for screenshot in screenshots:
        # Generate signed URL for the screenshot
        url = get_screenshot_url(screenshot.storage_path)
        screenshot_urls[screenshot.device_type] = url
    
    return {"screenshots": screenshot_urls}


@router.get(
    "/{analysis_id}/{device_type}",
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "Screenshot image"
        },
        404: {"model": error_schema.ErrorResponse},
        403: {"model": error_schema.ErrorResponse}
    }
)
async def get_screenshot_image(
    device_type: str,
    analysis: models.Analysis = Depends(get_analysis_by_id),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get a specific screenshot image by analysis ID and device type.
    
    Returns the image file directly.
    """
    # Check device type
    if device_type not in ["desktop", "tablet", "mobile"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid device type: {device_type}. Valid types are: desktop, tablet, mobile"
        )
    
    # Get screenshots from database
    screenshots = crud.get_analysis_screenshots(db, analysis.id)
    
    # Find the screenshot for the requested device type
    screenshot = next((s for s in screenshots if s.device_type == device_type), None)
    
    if not screenshot:
        raise HTTPException(
            status_code=404, 
            detail=f"No screenshot found for device type: {device_type}"
        )
    
    # Implementation would redirect to or serve the actual image
    # For now, we'll just return a placeholder response
    return {"url": get_screenshot_url(screenshot.storage_path)} 