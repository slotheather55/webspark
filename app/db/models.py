import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, 
    Integer, String, Text, JSON, Float
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    analyses = relationship("Analysis", back_populates="user")


class Analysis(Base):
    """Website analysis model"""
    __tablename__ = "analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, in_progress, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)  # in seconds
    error = Column(Text, nullable=True)
    
    # Analysis options
    options = Column(JSON, nullable=False, default={})
    
    # Analysis results
    summary = Column(JSON, nullable=True)
    content_analysis = Column(JSON, nullable=True)
    tealium_analysis = Column(JSON, nullable=True)
    
    # Relationships
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    user = relationship("User", back_populates="analyses")
    screenshots = relationship("Screenshot", back_populates="analysis")
    enhancements = relationship("Enhancement", back_populates="analysis")


class Screenshot(Base):
    """Screenshots captured during analysis"""
    __tablename__ = "screenshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_type = Column(String, nullable=False)  # desktop, tablet, mobile
    storage_path = Column(String, nullable=False)
    thumbnail_path = Column(String, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id"), nullable=False)
    analysis = relationship("Analysis", back_populates="screenshots")


class Enhancement(Base):
    """Enhancement recommendations"""
    __tablename__ = "enhancements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String, nullable=False, default="pending")  # pending, in_progress, completed, failed
    categories = Column(JSON, nullable=False, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    
    # Results
    recommendations = Column(JSON, nullable=True)
    
    # Relationships
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id"), nullable=False)
    analysis = relationship("Analysis", back_populates="enhancements") 