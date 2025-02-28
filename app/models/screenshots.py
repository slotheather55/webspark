from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import uuid

from pydantic import BaseModel, Field, HttpUrl


class DeviceType(str, Enum):
    DESKTOP = "desktop"
    MOBILE = "mobile"
    TABLET = "tablet"


class ScreenshotDimensions(BaseModel):
    """Dimensions of a screenshot"""
    width: int
    height: int


class ScreenshotCreate(BaseModel):
    """Create a new screenshot record"""
    analysis_id: uuid.UUID
    device_type: DeviceType
    url: HttpUrl
    original_path: str
    thumbnail_path: str
    dimensions: ScreenshotDimensions
    original_url: Optional[str] = None
    thumbnail_url: Optional[str] = None


class ScreenshotDB(BaseModel):
    """Screenshot model as stored in the database"""
    id: uuid.UUID
    analysis_id: uuid.UUID
    device_type: str
    url: str
    original_path: str
    thumbnail_path: str
    width: int
    height: int
    original_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class ScreenshotResponse(BaseModel):
    """Screenshot response for API"""
    id: uuid.UUID
    analysis_id: uuid.UUID
    device_type: str
    url: str
    original_url: str
    thumbnail_url: str
    width: int
    height: int
    created_at: datetime
    
    class Config:
        orm_mode = True


class ScreenshotListResponse(BaseModel):
    """List of screenshots for API"""
    items: List[ScreenshotResponse]
    total: int
    page: int
    page_size: int 