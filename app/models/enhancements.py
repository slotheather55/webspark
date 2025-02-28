from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union

from pydantic import BaseModel, Field, validator


# Status enum for enhancements
class EnhancementStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class EnhancementCreate(BaseModel):
    """Create a new enhancement request"""
    analysis_id: int
    name: Optional[str] = None
    categories: List[str] = ["value_proposition", "content_strategy", "conversion_optimization"]
    
    @validator("categories")
    def validate_categories(cls, v):
        valid_categories = [
            "value_proposition", 
            "content_strategy", 
            "feature_development", 
            "conversion_optimization", 
            "technical_implementation"
        ]
        
        for category in v:
            if category not in valid_categories:
                raise ValueError(f"Invalid category: {category}. Valid options are {valid_categories}")
        return v


class RecommendationBase(BaseModel):
    """Base model for a recommendation"""
    id: str
    title: str
    category: str
    description: str
    rationale: str
    implementation: List[str]
    impact: str
    effort: str


class ImplementationPlan(BaseModel):
    """Detailed implementation plan for a recommendation"""
    enhancement_id: str
    title: str
    background: str
    implementation_plan: Dict[str, Any]
    success_metrics: List[Dict[str, Any]]
    risks: List[Dict[str, Any]]


class EnhancementResult(BaseModel):
    """Enhancement result model"""
    enhancement_id: int
    analysis_id: int
    categories: List[str]
    recommendations: Dict[str, Dict[str, Any]]
    completed_at: Optional[datetime] = None


class EnhancementDB(BaseModel):
    """Enhancement model as stored in the database"""
    id: int
    analysis_id: int
    name: Optional[str] = None
    status: EnhancementStatus
    categories: List[str]
    results: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


# API response models
class EnhancementResponse(BaseModel):
    """Enhancement response for API"""
    id: int
    analysis_id: int
    name: Optional[str] = None
    status: EnhancementStatus
    categories: List[str]
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class EnhancementListResponse(BaseModel):
    """List of enhancements for API"""
    items: List[EnhancementResponse]
    total: int
    page: int
    page_size: int


class ImplementationPlanRequest(BaseModel):
    """Request for an implementation plan"""
    recommendation_id: str 