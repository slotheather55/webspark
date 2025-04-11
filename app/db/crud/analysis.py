from datetime import datetime
import uuid
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session

from app.db import models
from app.schemas import analysis as analysis_schema


def create_analysis(db: Session, analysis: analysis_schema.AnalysisCreate, user_id: Optional[uuid.UUID] = None):
    """Create a new analysis record"""
    db_analysis = models.Analysis(
        url=str(analysis.url),
        options=analysis.options.dict(),
        user_id=user_id
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    return db_analysis


def get_analysis(db: Session, analysis_id: uuid.UUID):
    """Get analysis by ID"""
    return db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()


def get_user_analyses(db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100):
    """Get all analyses for a user"""
    return db.query(models.Analysis).filter(
        models.Analysis.user_id == user_id
    ).order_by(models.Analysis.created_at.desc()).offset(skip).limit(limit).all()


def get_public_analyses(db: Session, skip: int = 0, limit: int = 100):
    """Get all public (non-user) analyses"""
    return db.query(models.Analysis).filter(
        models.Analysis.user_id == None
    ).order_by(models.Analysis.created_at.desc()).offset(skip).limit(limit).all()


# Alias functions to match the names used in the endpoints
def get_multi_by_user(db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100):
    """Alias for get_user_analyses"""
    return get_user_analyses(db, user_id, skip, limit)


def count_by_user(db: Session, user_id: uuid.UUID):
    """Count analyses for a user"""
    return db.query(models.Analysis).filter(models.Analysis.user_id == user_id).count()


def get_multi_public(db: Session, skip: int = 0, limit: int = 100):
    """Alias for get_public_analyses"""
    return get_public_analyses(db, skip, limit)


def count_public(db: Session):
    """Count public analyses"""
    return db.query(models.Analysis).filter(models.Analysis.user_id == None).count()


def update_analysis_status(
    db: Session, 
    analysis_id: uuid.UUID, 
    status: str,
    error: Optional[str] = None
):
    """Update the status of an analysis"""
    db_analysis = get_analysis(db, analysis_id)
    if not db_analysis:
        return None
        
    db_analysis.status = status
    
    if status == "completed":
        db_analysis.completed_at = datetime.utcnow()
        if db_analysis.created_at:
            db_analysis.duration = (db_analysis.completed_at - db_analysis.created_at).total_seconds()
    
    if error:
        db_analysis.error = error
        
    db.commit()
    db.refresh(db_analysis)
    return db_analysis


def update_analysis_results(
    db: Session,
    analysis_id: uuid.UUID,
    summary: Optional[Dict] = None,
    content_analysis: Optional[Dict] = None,
    tealium_analysis: Optional[Dict] = None
):
    """Update analysis results"""
    db_analysis = get_analysis(db, analysis_id)
    if not db_analysis:
        return None
        
    if summary:
        db_analysis.summary = summary
        
    if content_analysis:
        db_analysis.content_analysis = content_analysis
        
    if tealium_analysis:
        db_analysis.tealium_analysis = tealium_analysis
        
    db.commit()
    db.refresh(db_analysis)
    return db_analysis


def update_analysis(
    db: Session,
    analysis_id: uuid.UUID,
    data: Dict[str, Any]
):
    """Update any analysis fields"""
    db_analysis = get_analysis(db, analysis_id)
    if not db_analysis:
        return None
    
    # Update fields
    for key, value in data.items():
        if hasattr(db_analysis, key):
            setattr(db_analysis, key, value)
    
    db.commit()
    db.refresh(db_analysis)
    return db_analysis


def delete_analysis(db: Session, analysis_id: uuid.UUID):
    """Delete an analysis record"""
    db_analysis = get_analysis(db, analysis_id)
    if not db_analysis:
        return False
    
    db.delete(db_analysis)
    db.commit()
    return True 