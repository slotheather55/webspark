import uuid
from typing import Generator
import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.db import crud, models


def get_current_active_user(
    current_user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> models.User:
    """Get current active user (optional)"""
    if not current_user_id:
        return None  # Anonymous user

    user = crud.get_user(db, uuid.UUID(current_user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


def get_analysis_by_id(
    analysis_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
) -> models.Analysis:
    """Get analysis by ID, checking user permission"""
    analysis = crud.get_analysis(db, analysis_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
        
    # If the analysis belongs to a user, check that it's the current user
    if analysis.user_id and current_user and analysis.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this analysis"
        )
        
    return analysis


def get_enhancement_by_id(
    enhancement_id: uuid.UUID, 
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
) -> models.Enhancement:
    """Get enhancement by ID, checking user permission"""
    enhancement = crud.get_enhancement(db, enhancement_id)
    if not enhancement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enhancement not found"
        )
        
    # Get the associated analysis to check permissions
    analysis = crud.get_analysis(db, enhancement.analysis_id)
    
    # If the analysis belongs to a user, check that it's the current user
    if analysis and analysis.user_id and current_user and analysis.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this enhancement"
        )
        
    return enhancement 