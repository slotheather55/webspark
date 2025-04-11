from typing import Dict, List, Optional, Any
from datetime import datetime

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """Detailed error information"""
    code: str
    message: str
    details: Optional[str] = None
    suggestions: Optional[List[str]] = None
    request_id: Optional[str] = None
    timestamp: Optional[datetime] = None


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: ErrorDetail

    class Config:
        schema_extra = {
            "example": {
                "error": {
                    "code": "analysis_timeout",
                    "message": "The analysis process timed out after 60 seconds",
                    "details": "The website at example.com took too long to respond",
                    "timestamp": "2023-01-01T12:34:56Z",
                    "request_id": "req-abcd1234",
                    "suggestions": [
                        "Try analyzing a specific page rather than the homepage",
                        "Check if the site is currently experiencing issues",
                        "Consider using the 'basic' analysis depth option"
                    ]
                }
            }
        } 