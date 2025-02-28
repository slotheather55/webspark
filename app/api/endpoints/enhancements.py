import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.db import crud, models
from app.db.session import get_db
from app.schemas import enhancements as enhancement_schema
from app.schemas import errors as error_schema
from app.api.dependencies import get_analysis_by_id, get_enhancement_by_id, get_current_active_user
from app.tasks.enhancements import trigger_enhancement_generation, generate_enhancement_suggestions

router = APIRouter()


@router.post(
    "/generate",
    response_model=enhancement_schema.EnhancementResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        404: {"model": error_schema.ErrorResponse},
        403: {"model": error_schema.ErrorResponse}
    }
)
async def create_enhancement(
    data: enhancement_schema.EnhancementCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_active_user)
) -> Any:
    """
    Generate enhancement suggestions for a specific analysis.
    
    This will trigger an AI-powered analysis to generate product enhancement suggestions
    based on the analysis results.
    """
    # Get analysis from database
    analysis = crud.analysis.get_analysis(db, data.analysis_id)
    
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
    
    # Create enhancement record
    enhancement = crud.enhancements.create_enhancement(
        db=db,
        enhancement=data, 
        analysis_id=analysis.id
    )
    
    # Trigger enhancement generation in background
    background_tasks.add_task(
        generate_enhancement_suggestions,
        enhancement_id=enhancement.id
    )
    
    return {
        "enhancement_id": enhancement.id,
        "status": enhancement.status
    }


@router.get(
    "/{enhancement_id}",
    responses={
        404: {"model": error_schema.ErrorResponse},
        403: {"model": error_schema.ErrorResponse}
    }
)
async def get_enhancement(
    enhancement_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_active_user)
) -> Any:
    """
    Get enhancement suggestions by ID.
    
    Returns the enhancement suggestions for a specific enhancement ID.
    """
    # Convert string to UUID
    try:
        enhancement_uuid = uuid.UUID(enhancement_id)
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail="Invalid enhancement ID format"
        )
    
    # Get enhancement from database
    enhancement = crud.enhancements.get_enhancement(db, enhancement_uuid)
    
    # Rest of the function remains the same...    
    if not enhancement:
        raise HTTPException(
            status_code=404,
            detail="Enhancement not found"
        )
    
    # Get the associated analysis to check permissions
    analysis = crud.analysis.get_analysis(db, enhancement.analysis_id)
    
    # Check if user owns this analysis (only if both user and analysis.user_id exist)
    if current_user and analysis and analysis.user_id and analysis.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this enhancement"
        )
    
    return {
        "id": enhancement.id,
        "analysis_id": enhancement.analysis_id,
        "status": enhancement.status,
        "categories": enhancement.categories,
        "created_at": enhancement.created_at,
        "updated_at": enhancement.updated_at,
        "completed_at": enhancement.completed_at,
        "recommendations": enhancement.recommendations or {},
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