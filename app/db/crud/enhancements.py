from datetime import datetime
import uuid
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session

from app.db import models
from app.schemas import enhancements as enhancement_schema


def create_enhancement(
    db: Session, 
    enhancement: enhancement_schema.EnhancementCreate, 
    analysis_id: uuid.UUID
):
    """Create a new enhancement record"""
    db_enhancement = models.Enhancement(
        analysis_id=analysis_id,
        categories=enhancement.categories
    )
    
    # Add name if provided
    if enhancement.name:
        db_enhancement.name = enhancement.name
        
    db.add(db_enhancement)
    db.commit()
    db.refresh(db_enhancement)
    return db_enhancement


def get_enhancement(db: Session, enhancement_id: uuid.UUID):
    """Get enhancement by ID"""
    return db.query(models.Enhancement).filter(
        models.Enhancement.id == enhancement_id
    ).first()


def get_analysis_enhancements(db: Session, analysis_id: uuid.UUID):
    """Get all enhancements for an analysis"""
    return db.query(models.Enhancement).filter(
        models.Enhancement.analysis_id == analysis_id
    ).all()


def update_enhancement_status(
    db: Session,
    enhancement_id: uuid.UUID,
    status: str,
    error: Optional[str] = None
):
    """Update enhancement status"""
    db_enhancement = get_enhancement(db, enhancement_id)
    if not db_enhancement:
        return None
        
    db_enhancement.status = status
    
    if status == "completed":
        db_enhancement.completed_at = datetime.utcnow()
    
    if error:
        db_enhancement.error = error
        
    db.commit()
    db.refresh(db_enhancement)
    return db_enhancement


def update_enhancement_recommendations(
    db: Session,
    enhancement_id: uuid.UUID,
    recommendations: Dict[str, Any]
):
    """Update enhancement recommendations"""
    db_enhancement = get_enhancement(db, enhancement_id)
    if not db_enhancement:
        return None
        
    db_enhancement.recommendations = recommendations
    db_enhancement.status = "completed"
    db_enhancement.completed_at = datetime.utcnow()
        
    db.commit()
    db.refresh(db_enhancement)
    return db_enhancement


def update_enhancement(
    db: Session,
    enhancement_id: uuid.UUID,
    data: Dict[str, Any]
):
    """Update any enhancement fields"""
    db_enhancement = get_enhancement(db, enhancement_id)
    if not db_enhancement:
        return None
    
    # Update fields
    for key, value in data.items():
        if hasattr(db_enhancement, key):
            setattr(db_enhancement, key, value)
    
    db.commit()
    db.refresh(db_enhancement)
    return db_enhancement


def delete_enhancement(db: Session, enhancement_id: uuid.UUID):
    """Delete an enhancement record"""
    db_enhancement = get_enhancement(db, enhancement_id)
    if not db_enhancement:
        return False
    
    db.delete(db_enhancement)
    db.commit()
    return True 