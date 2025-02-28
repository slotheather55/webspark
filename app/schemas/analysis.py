from datetime import datetime
from typing import Dict, List, Optional, Any, Union
import uuid

from pydantic import BaseModel, AnyUrl, Field, validator


class AnalysisOptions(BaseModel):
    """Options for website analysis"""
    devices: List[str] = ["desktop", "tablet", "mobile"]
    depth: str = "full"  # "basic", "full", "comprehensive"
    check_tealium: bool = True
    screenshot_viewports: bool = True
    include_subpages: bool = False
    max_subpages: int = 0
    custom_scripts: List[str] = []

    @validator("devices")
    def validate_devices(cls, v):
        """Validate device types"""
        valid_devices = ["desktop", "tablet", "mobile"]
        for device in v:
            if device not in valid_devices:
                raise ValueError(f"Invalid device type: {device}. Valid types are: {valid_devices}")
        return v

    @validator("depth")
    def validate_depth(cls, v):
        """Validate analysis depth"""
        valid_depths = ["basic", "full", "comprehensive"]
        if v not in valid_depths:
            raise ValueError(f"Invalid analysis depth: {v}. Valid depths are: {valid_depths}")
        return v

    class Config:
        schema_extra = {
            "example": {
                "devices": ["desktop", "tablet", "mobile"],
                "depth": "full",
                "check_tealium": True,
                "screenshot_viewports": True,
                "include_subpages": False,
                "max_subpages": 0,
                "custom_scripts": []
            }
        }


class AnalysisCreate(BaseModel):
    """Create analysis request"""
    url: AnyUrl
    options: AnalysisOptions = Field(default_factory=AnalysisOptions)

    class Config:
        schema_extra = {
            "example": {
                "url": "https://example.com",
                "options": {
                    "devices": ["desktop", "tablet", "mobile"],
                    "depth": "full",
                    "check_tealium": True,
                    "screenshot_viewports": True
                }
            }
        }


class AnalysisResponse(BaseModel):
    """Response after creating analysis"""
    analysis_id: uuid.UUID
    status: str = "pending"

    class Config:
        schema_extra = {
            "example": {
                "analysis_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "status": "pending"
            }
        }


class ScreenshotInfo(BaseModel):
    """Screenshot information"""
    screenshot: str
    status: str
    width: Optional[int] = None
    height: Optional[int] = None


class DeviceResults(BaseModel):
    """Results for each device type"""
    desktop: Optional[ScreenshotInfo] = None
    tablet: Optional[ScreenshotInfo] = None
    mobile: Optional[ScreenshotInfo] = None


class PageMetadata(BaseModel):
    """Metadata about the analyzed page"""
    title: Optional[str] = None
    description: Optional[str] = None


class AnalysisSummary(BaseModel):
    """Summary of the analysis"""
    title: str
    page_metadata: Optional[PageMetadata] = None
    device_results: Optional[DeviceResults] = None


class AnalysisDetail(BaseModel):
    """Detailed analysis results"""
    analysis_id: uuid.UUID
    url: AnyUrl
    status: str
    timestamp: datetime
    duration: Optional[float] = None
    summary: Optional[AnalysisSummary] = None
    content_analysis: Optional[Dict[str, Any]] = None
    tealium_analysis: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "analysis_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "url": "https://example.com",
                "status": "completed",
                "timestamp": "2023-01-01T12:34:56Z",
                "duration": 42.5,
                "summary": {
                    "title": "Example Website Analysis",
                    "page_metadata": {
                        "title": "Example Site",
                        "description": "This is an example website"
                    },
                    "device_results": {
                        "desktop": {"screenshot": "url-to-image", "status": "completed"},
                        "tablet": {"screenshot": "url-to-image", "status": "completed"},
                        "mobile": {"screenshot": "url-to-image", "status": "completed"}
                    }
                }
            }
        }


class AnalysisList(BaseModel):
    """List of analyses"""
    analyses: List[AnalysisDetail]
    total: int
    page: int
    limit: int


class ScreenshotResponse(BaseModel):
    """Response containing screenshot URLs"""
    screenshots: Dict[str, str]

    class Config:
        schema_extra = {
            "example": {
                "screenshots": {
                    "desktop": "url-to-desktop-image",
                    "tablet": "url-to-tablet-image",
                    "mobile": "url-to-mobile-image"
                }
            }
        }


class AnalysisStatus(BaseModel):
    """Status update for analysis"""
    status: str
    message: Optional[str] = None
    progress: Optional[float] = None  # 0.0 to 1.0
    eta: Optional[int] = None  # estimated seconds remaining 