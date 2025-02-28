from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import crud, models
from app.db.session import get_db
from app.schemas import tealium as tealium_schema
from app.schemas import errors as error_schema
from app.api.dependencies import get_analysis_by_id
from app.services.tealium.validators import validate_data_layer

router = APIRouter()


@router.get(
    "/analysis/{analysis_id}",
    responses={
        200: {"description": "Tealium analysis data"},
        404: {"model": error_schema.ErrorResponse},
        403: {"model": error_schema.ErrorResponse}
    }
)
async def get_tealium_analysis(
    analysis: models.Analysis = Depends(get_analysis_by_id)
) -> Any:
    """
    Get Tealium implementation analysis for a specific analysis.
    """
    if not analysis.tealium_analysis:
        raise HTTPException(
            status_code=404,
            detail="No Tealium analysis available for this analysis"
        )
    
    return analysis.tealium_analysis


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