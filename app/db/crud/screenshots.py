import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.db import models


def create_screenshot(
    db: Session,
    analysis_id: uuid.UUID,
    device_type: str,
    storage_path: str,
    thumbnail_path: Optional[str] = None,
    width: Optional[int] = None,
    height: Optional[int] = None
):
    """Create a new screenshot record"""
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


def get_screenshot(db: Session, screenshot_id: uuid.UUID):
    """Get a screenshot by ID"""
    return db.query(models.Screenshot).filter(models.Screenshot.id == screenshot_id).first()


def get_analysis_screenshots(db: Session, analysis_id: uuid.UUID) -> List[models.Screenshot]:
    """Get all screenshots for an analysis"""
    return db.query(models.Screenshot).filter(
        models.Screenshot.analysis_id == analysis_id
    ).all()


def get_screenshot_by_device(db: Session, analysis_id: uuid.UUID, device_type: str):
    """Get a screenshot for an analysis by device type"""
    return db.query(models.Screenshot).filter(
        models.Screenshot.analysis_id == analysis_id,
        models.Screenshot.device_type == device_type
    ).first()


def update_screenshot(
    db: Session,
    screenshot_id: uuid.UUID,
    storage_path: Optional[str] = None,
    thumbnail_path: Optional[str] = None,
    width: Optional[int] = None,
    height: Optional[int] = None
):
    """Update a screenshot record"""
    db_screenshot = get_screenshot(db, screenshot_id)
    if not db_screenshot:
        return None
    
    if storage_path:
        db_screenshot.storage_path = storage_path
        
    if thumbnail_path:
        db_screenshot.thumbnail_path = thumbnail_path
        
    if width is not None:
        db_screenshot.width = width
        
    if height is not None:
        db_screenshot.height = height
    
    db.commit()
    db.refresh(db_screenshot)
    return db_screenshot


def delete_screenshot(db: Session, screenshot_id: uuid.UUID):
    """Delete a screenshot record"""
    db_screenshot = get_screenshot(db, screenshot_id)
    if not db_screenshot:
        return False
    
    db.delete(db_screenshot)
    db.commit()
    return True 