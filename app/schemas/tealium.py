from typing import Dict, List, Optional, Any
import uuid

from pydantic import BaseModel


class DataLayerVariable(BaseModel):
    """Data layer variable information"""
    name: str
    value: Any
    type: str


class DataLayerIssue(BaseModel):
    """Issue with data layer implementation"""
    type: str
    description: str
    details: Optional[str] = None
    examples: Optional[List[str]] = None
    recommendation: Optional[str] = None


class DataLayerAnalysis(BaseModel):
    """Data layer analysis"""
    variables: Dict[str, Any]
    issues: List[DataLayerIssue] = []


class TagInfo(BaseModel):
    """Tag information"""
    id: str
    name: str
    vendor: Optional[str] = None
    category: Optional[str] = None
    status: str  # active, inactive
    load_time: Optional[int] = None  # ms
    requests: Optional[int] = None


class TagIssue(BaseModel):
    """Issue with tag implementation"""
    tag_id: Optional[str] = None
    tag_name: Optional[str] = None
    type: str
    description: str
    details: Optional[str] = None
    recommendation: Optional[str] = None


class TagAnalysis(BaseModel):
    """Tag implementation analysis"""
    total: int
    active: int
    inactive: int
    vendor_distribution: Dict[str, int]
    details: List[TagInfo]
    issues: List[TagIssue] = []


class PerformanceRecommendation(BaseModel):
    """Performance optimization recommendation"""
    description: str
    impact: str  # high, medium, low
    implementation: Optional[str] = None


class PerformanceAnalysis(BaseModel):
    """Tag performance analysis"""
    total_size: Optional[float] = None  # KB
    load_time: Optional[float] = None  # seconds
    request_count: Optional[int] = None
    page_load_impact: Optional[str] = None
    recommendations: List[PerformanceRecommendation] = []


class TealiumAnalysis(BaseModel):
    """Complete Tealium implementation analysis"""
    detected: bool
    version: Optional[str] = None
    profile: Optional[str] = None
    data_layer: DataLayerAnalysis
    tags: TagAnalysis
    performance: PerformanceAnalysis


class ValidationIssue(BaseModel):
    """Validation issue for Tealium implementation"""
    path: str
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    message: str
    severity: str  # error, warning, info


class ValidationRequest(BaseModel):
    """Request to validate Tealium implementation"""
    data_layer: Dict[str, Any]
    expected_schema: Dict[str, Any]


class ValidationResponse(BaseModel):
    """Response for Tealium validation"""
    valid: bool
    issues: List[ValidationIssue] = [] 