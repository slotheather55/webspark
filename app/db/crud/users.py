import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import get_password_hash, verify_password
from app.db import models


def get_user(db: Session, user_id: uuid.UUID):
    """Get a user by ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    """Get a user by email address"""
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, email: str, password: str):
    """Create a new user"""
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
    """Authenticate a user with email and password"""
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def update_user(db: Session, user_id: uuid.UUID, data: dict):
    """Update user data"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
        
    # Update user fields
    for key, value in data.items():
        # Handle password separately to hash it
        if key == "password" and value is not None:
            value = get_password_hash(value)
            key = "hashed_password"
            
        if hasattr(db_user, key):
            setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user


def deactivate_user(db: Session, user_id: uuid.UUID):
    """Deactivate a user (soft delete)"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
        
    db_user.is_active = False
    db.commit()
    db.refresh(db_user)
    return db_user 