from datetime import datetime
import uuid
from typing import Dict, List, Optional, Union, Any

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.db import models
from app.schemas import analysis as analysis_schema
from app.schemas import enhancements as enhancement_schema


# User CRUD operations
def get_user(db: Session, user_id: uuid.UUID):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, email: str, password: str):
    hashed_password = get_password_hash(password)
    db_user = models.User(
        email=email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# Analysis CRUD operations
def create_analysis(db: Session, analysis: analysis_schema.AnalysisCreate, user_id: Optional[uuid.UUID] = None):
    db_analysis = models.Analysis(
        url=analysis.url,
        options=analysis.options.dict(),
        user_id=user_id
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    return db_analysis


def get_analysis(db: Session, analysis_id: uuid.UUID):
    return db.query(models.Analysis).filter(models.Analysis.id == analysis_id).first()


def get_user_analyses(db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100):
    return db.query(models.Analysis).filter(
        models.Analysis.user_id == user_id
    ).order_by(models.Analysis.created_at.desc()).offset(skip).limit(limit).all()


def update_analysis_status(
    db: Session, 
    analysis_id: uuid.UUID, 
    status: str,
    error: Optional[str] = None
):
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


# Screenshot CRUD operations
def create_screenshot(
    db: Session,
    analysis_id: uuid.UUID,
    device_type: str,
    storage_path: str,
    thumbnail_path: Optional[str] = None,
    width: Optional[int] = None,
    height: Optional[int] = None
):
    db_screenshot = models.Screenshot(
        analysis_id=analysis_id,
        device_type=device_type,
        storage_path=storage_path,
        thumbnail_path=thumbnail_path,
        width=width,
        height=height
    )
    db.add(db_screenshot)
    db.commit()
    db.refresh(db_screenshot)
    return db_screenshot


def get_analysis_screenshots(db: Session, analysis_id: uuid.UUID):
    return db.query(models.Screenshot).filter(
        models.Screenshot.analysis_id == analysis_id
    ).all()


# Enhancement CRUD operations
def create_enhancement(
    db: Session, 
    enhancement: enhancement_schema.EnhancementCreate, 
    analysis_id: uuid.UUID
):
    db_enhancement = models.Enhancement(
        analysis_id=analysis_id,
        categories=enhancement.categories
    )
    db.add(db_enhancement)
    db.commit()
    db.refresh(db_enhancement)
    return db_enhancement


def get_enhancement(db: Session, enhancement_id: uuid.UUID):
    return db.query(models.Enhancement).filter(
        models.Enhancement.id == enhancement_id
    ).first()


def get_analysis_enhancements(db: Session, analysis_id: uuid.UUID):
    return db.query(models.Enhancement).filter(
        models.Enhancement.analysis_id == analysis_id
    ).all()


def update_enhancement_status(
    db: Session,
    enhancement_id: uuid.UUID,
    status: str,
    error: Optional[str] = None
):
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
    db_enhancement = get_enhancement(db, enhancement_id)
    if not db_enhancement:
        return None
        
    db_enhancement.recommendations = recommendations
    db_enhancement.status = "completed"
    db_enhancement.completed_at = datetime.utcnow()
        
    db.commit()
    db.refresh(db_enhancement)
    return db_enhancement 