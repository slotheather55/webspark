from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import uuid

from pydantic import BaseModel, Field, HttpUrl, validator

# Status enum for analysis
class AnalysisStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# Input models
class AnalysisOptions(BaseModel):
    """Options for website analysis"""
    device_types: List[str] = Field(["desktop", "mobile"], description="Device types to analyze")
    modules: List[str] = Field(["screenshots", "content", "tealium"], description="Analysis modules to run")
    include_ai_analysis: bool = Field(True, description="Whether to run AI analysis")
    
    @validator("device_types")
    def validate_device_types(cls, v):
        valid_device_types = ["desktop", "mobile"]
        for device_type in v:
            if device_type not in valid_device_types:
                raise ValueError(f"Invalid device type: {device_type}. Valid options are {valid_device_types}")
        return v


class AnalysisCreate(BaseModel):
    """Model for creating a new analysis"""
    url: HttpUrl = Field(..., description="URL to analyze")
    options: Optional[AnalysisOptions] = Field(None, description="Analysis options")


class AnalysisBase(BaseModel):
    """Base model for analysis responses"""
    analysis_id: uuid.UUID
    url: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class AnalysisResponse(AnalysisBase):
    """Model for analysis response"""
    message: Optional[str] = None
    error: Optional[str] = None


class AnalysisListResponse(BaseModel):
    """Model for list of analyses response"""
    total: int
    skip: int
    limit: int
    items: List[AnalysisBase]


class Analysis(AnalysisBase):
    """Complete analysis model with results"""
    options: Dict[str, Any] = {}
    user_id: uuid.UUID
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    class Config:
        orm_mode = True


# Output models
class ScreenshotInfo(BaseModel):
    """Information about a screenshot"""
    path: str
    thumbnail_path: str
    width: int
    height: int
    url: Optional[str] = None
    thumbnail_url: Optional[str] = None


class ContentAnalysisResult(BaseModel):
    """Result of content analysis"""
    summary: str
    analysis: Dict[str, Any]
    critical_issues: List[Dict[str, Any]]
    overall_score: int


class TealiumAnalysisResult(BaseModel):
    """Result of Tealium analysis"""
    summary: str
    analysis: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    overall_score: int


class AnalysisResult(BaseModel):
    """Full analysis result"""
    url: HttpUrl
    analysis_id: uuid.UUID
    screenshots: Dict[str, ScreenshotInfo]
    content_analysis: Dict[str, Any]
    tealium_analysis: Optional[Dict[str, Any]] = None
    ai_analysis: Optional[Dict[str, Any]] = None
    completed_at: Optional[datetime] = None


class AnalysisDB(BaseModel):
    """Analysis model as stored in the database"""
    id: uuid.UUID
    url: str
    name: Optional[str] = None
    status: AnalysisStatus
    options: Dict[str, Any]
    results: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True 