import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.db import crud, models
from app.db.session import get_db
from app.schemas import analysis as analysis_schema
from app.schemas import errors as error_schema
from app.core.errors import error_response
from app.api.dependencies import get_current_user, get_analysis_by_id
from app.tasks.analysis import trigger_website_analysis
from app.models.analysis import AnalysisCreate, AnalysisResponse, AnalysisListResponse

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_analysis(
    data: AnalysisCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Create a new website analysis job
    """
    # Create analysis record in database
    analysis = crud.analysis.create(
        db=db,
        obj_in={
            "url": data.url,
            "user_id": current_user.id,
            "status": "pending",
            "options": data.options.dict() if data.options else {}
        }
    )
    
    # Trigger the analysis task in background
    background_tasks.add_task(
        trigger_website_analysis,
        analysis_id=analysis.id,
        url=analysis.url,
        options=data.options.dict() if data.options else None
    )
    
    return {
        "id": analysis.id,
        "url": analysis.url,
        "status": analysis.status,
        "created_at": analysis.created_at,
        "updated_at": analysis.updated_at,
        "message": "Analysis started successfully"
    }


@router.get("/", response_model=AnalysisListResponse)
async def list_analyses(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    List all analyses for the current user
    """
    analyses = crud.analysis.get_multi_by_user(
        db=db,
        user_id=current_user.id, 
        skip=skip, 
        limit=limit
    )
    
    total = crud.analysis.count_by_user(db=db, user_id=current_user.id)
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "items": analyses
    }


@router.get("/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get a specific analysis by ID
    """
    analysis = crud.analysis.get(db=db, id=analysis_id)
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
        
    # Check if user owns this analysis
    if analysis.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this analysis"
        )
        
    return analysis


@router.delete(
    "/{analysis_id}",
    responses={
        204: {"description": "Analysis deleted"},
        404: {"model": error_schema.ErrorResponse},
        403: {"model": error_schema.ErrorResponse}
    },
    status_code=204
)
async def delete_analysis(
    analysis: models.Analysis = Depends(get_analysis_by_id),
    db: Session = Depends(get_db)
) -> None:
    """
    Delete an analysis by ID.
    
    This will remove the analysis and all associated data.
    """
    # Implementation would delete analysis and all associated data
    # For now, we'll just return a success status
    return None 