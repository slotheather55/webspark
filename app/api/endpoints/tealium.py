import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import crud, models
from app.db.session import get_db
from app.schemas import tealium as tealium_schema
from app.schemas import errors as error_schema
from app.api.dependencies import get_current_active_user
from app.services.tealium.validators import validate_data_layer

router = APIRouter()


@router.get(
    "/analysis/{analysis_id}",
    responses={
        404: {"model": error_schema.ErrorResponse},
        403: {"model": error_schema.ErrorResponse}
    }
)
async def get_tealium_analysis(
    analysis_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_active_user)
) -> Any:
    """
    Get Tealium analysis data for a specific analysis by ID.
    
    Returns the Tealium analysis data including data layer, events, and tags.
    """
    # Convert string ID to UUID object
    try:
        analysis_uuid = uuid.UUID(analysis_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid analysis ID format"
        )
    
    # Get analysis from database
    analysis = crud.analysis.get_analysis(db, analysis_uuid)
    
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
    
    # Get Tealium analysis data
    tealium_data = analysis.tealium_analysis
    
    if not tealium_data:
        return {
            "message": "No Tealium analysis data available for this analysis",
            "data_layer": {},
            "events": [],
            "tags": [],
            "issues": [],
            "recommendations": [],
            "performance": {}
        }
    
    return tealium_data


@router.post(
    "/validate",
    response_model=tealium_schema.ValidationResponse,
    responses={
        400: {"model": error_schema.ErrorResponse},
        500: {"model": error_schema.ErrorResponse}
    }
)
async def validate_tealium(
    validation_request: tealium_schema.ValidationRequest
) -> Any:
    """
    Validate a Tealium data layer against an expected schema.
    """
    validation_result = validate_data_layer(
        validation_request.data_layer,
        validation_request.expected_schema
    )
    
    return validation_result