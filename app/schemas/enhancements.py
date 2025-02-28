from datetime import datetime
from typing import Dict, List, Optional, Any
import uuid

from pydantic import BaseModel, AnyUrl, Field, validator


class EnhancementCreate(BaseModel):
    """Create enhancement request"""
    categories: List[str] = ["value_proposition", "content_strategy", "feature_development", "conversion_optimization", "technical_implementation"]
    
    @validator("categories")
    def validate_categories(cls, v):
        """Validate enhancement categories"""
        valid_categories = [
            "value_proposition", 
            "content_strategy", 
            "feature_development",
            "conversion_optimization", 
            "technical_implementation"
        ]
        for category in v:
            if category not in valid_categories:
                raise ValueError(f"Invalid category: {category}. Valid categories are: {valid_categories}")
        return v

    class Config:
        schema_extra = {
            "example": {
                "categories": [
                    "value_proposition", 
                    "content_strategy", 
                    "conversion_optimization"
                ]
            }
        }


class EnhancementResponse(BaseModel):
    """Response after creating enhancement request"""
    enhancement_id: uuid.UUID
    status: str = "pending"

    class Config:
        schema_extra = {
            "example": {
                "enhancement_id": "e1f2g3h4-i5j6-7890-klmn-opqrst123456",
                "status": "pending"
            }
        }


class ImplementationStep(BaseModel):
    """Implementation step for a recommendation"""
    description: str
    order: int


class Recommendation(BaseModel):
    """Enhancement recommendation"""
    id: str
    category: str
    title: str
    description: str
    details: Optional[str] = None
    impact: str  # high, medium, low
    effort: str  # high, medium, low
    implementation: str
    implementation_steps: Optional[List[ImplementationStep]] = None
    examples: Optional[List[str]] = None


class CategoryRecommendations(BaseModel):
    """Recommendations for a specific category"""
    title: str
    count: int
    recommendations: List[Recommendation]


class EnhancementDetail(BaseModel):
    """Detailed enhancement results"""
    enhancement_id: uuid.UUID
    analysis_id: uuid.UUID
    url: AnyUrl
    timestamp: datetime
    status: str
    categories: Dict[str, CategoryRecommendations]
    error: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "enhancement_id": "e1f2g3h4-i5j6-7890-klmn-opqrst123456",
                "analysis_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "url": "https://example.com",
                "timestamp": "2023-01-01T12:34:56Z",
                "status": "completed",
                "categories": {
                    "value_proposition": {
                        "title": "Value Proposition Enhancements",
                        "count": 2,
                        "recommendations": [
                            {
                                "id": "vp-1",
                                "category": "value_proposition",
                                "title": "Clarify primary value proposition on homepage",
                                "description": "Current headline is vague.",
                                "details": "The current homepage headline doesn't communicate a specific value proposition...",
                                "impact": "high",
                                "effort": "low",
                                "implementation": "Update the H1 headline on the homepage",
                                "implementation_steps": [
                                    {"description": "Identify target audience pain points", "order": 1},
                                    {"description": "Draft new headline options", "order": 2}
                                ],
                                "examples": ["Save 5 hours per week", "Increase conversion rates by 15%"]
                            }
                        ]
                    }
                }
            }
        }


class ExportRequest(BaseModel):
    """Request to export enhancement recommendations"""
    enhancement_id: uuid.UUID
    format: str = "pdf"  # pdf, docx, html
    
    @validator("format")
    def validate_format(cls, v):
        """Validate export format"""
        valid_formats = ["pdf", "docx", "html"]
        if v not in valid_formats:
            raise ValueError(f"Invalid format: {v}. Valid formats are: {valid_formats}")
        return v


class ExportResponse(BaseModel):
    """Response after requesting export"""
    download_url: str

    class Config:
        schema_extra = {
            "example": {
                "download_url": "https://example.com/downloads/enhancement-123.pdf"
            }
        } 