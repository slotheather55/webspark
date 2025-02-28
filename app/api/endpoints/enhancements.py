import uuid
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.db import crud, models
from app.db.session import get_db
from app.schemas import enhancements as enhancement_schema
from app.schemas import errors as error_schema
from app.api.dependencies import get_analysis_by_id, get_enhancement_by_id
from app.tasks.enhancements import trigger_enhancement_generation

router = APIRouter()


@router.post(
    "/generate",
    response_model=enhancement_schema.EnhancementResponse,
    status_code=202,
    responses={
        400: {"model": error_schema.ErrorResponse},
        404: {"model": error_schema.ErrorResponse},
        403: {"model": error_schema.ErrorResponse},
        500: {"model": error_schema.ErrorResponse}
    }
)
async def generate_enhancements(
    enhancement: enhancement_schema.EnhancementCreate,
    analysis_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    analysis: models.Analysis = Depends(get_analysis_by_id),
    db: Session = Depends(get_db)
) -> Any:
    """
    Generate enhancement recommendations for an analysis.
    
    This will immediately return with an enhancement ID and begin processing in the background.
    """
    # Check if analysis is completed
    if analysis.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Cannot generate enhancements for an incomplete analysis"
        )
    
    # Create enhancement record
    db_enhancement = crud.create_enhancement(db, enhancement, analysis.id)
    
    # Trigger enhancement generation in background
    background_tasks.add_task(
        trigger_enhancement_generation,
        str(db_enhancement.id),
        str(analysis.id),
        enhancement.categories
    )
    
    return {
        "enhancement_id": db_enhancement.id,
        "status": db_enhancement.status
    }


@router.get(
    "/{enhancement_id}",
    response_model=enhancement_schema.EnhancementDetail,
    responses={
        404: {"model": error_schema.ErrorResponse},
        403: {"model": error_schema.ErrorResponse}
    }
)
async def get_enhancement(
    enhancement: models.Enhancement = Depends(get_enhancement_by_id),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get details of a specific enhancement by ID.
    """
    # Get the associated analysis
    analysis = crud.get_analysis(db, enhancement.analysis_id)
    
    return {
        "enhancement_id": enhancement.id,
        "analysis_id": enhancement.analysis_id,
        "url": analysis.url,
        "timestamp": enhancement.created_at,
        "status": enhancement.status,
        "categories": enhancement.recommendations or {},
        "error": enhancement.error
    }


@router.get(
    "/analysis/{analysis_id}",
    response_model=List[enhancement_schema.EnhancementDetail],
    responses={
        404: {"model": error_schema.ErrorResponse},
        403: {"model": error_schema.ErrorResponse}
    }
)
async def get_analysis_enhancements(
    analysis: models.Analysis = Depends(get_analysis_by_id),
    db: Session = Depends(get_db)
) -> Any:
    """
    Get all enhancements for a specific analysis.
    """
    enhancements = crud.get_analysis_enhancements(db, analysis.id)
    
    # Convert to response model format
    enhancement_list = []
    for enhancement in enhancements:
        enhancement_list.append({
            "enhancement_id": enhancement.id,
            "analysis_id": enhancement.analysis_id,
            "url": analysis.url,
            "timestamp": enhancement.created_at,
            "status": enhancement.status,
            "categories": enhancement.recommendations or {},
            "error": enhancement.error
        })
    
    return enhancement_list


@router.post(
    "/export",
    response_model=enhancement_schema.ExportResponse,
    responses={
        400: {"model": error_schema.ErrorResponse},
        404: {"model": error_schema.ErrorResponse},
        403: {"model": error_schema.ErrorResponse},
        500: {"model": error_schema.ErrorResponse}
    }
)
async def export_enhancement(
    export_request: enhancement_schema.ExportRequest,
    background_tasks: BackgroundTasks,
    enhancement: models.Enhancement = Depends(get_enhancement_by_id)
) -> Any:
    """
    Export enhancement recommendations to a file (PDF, DOCX, or HTML).
    
    This will generate the export file in the background and return a download URL.
    """
    # Check if enhancement is completed
    if enhancement.status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Cannot export incomplete enhancement recommendations"
        )
    
    # Implementation would create an export in the requested format
    # For now, we'll just return a placeholder response
    return {
        "download_url": f"https://example.com/downloads/enhancement-{enhancement.id}.{export_request.format}"
    } 