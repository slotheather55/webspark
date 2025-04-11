from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status


class DetailedHTTPException(HTTPException):
    """HTTP exception with detailed error information"""
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str = None,
        details: Optional[str] = None,
        suggestions: Optional[List[str]] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.error_code = error_code
        self.details = details
        self.suggestions = suggestions or []
        super().__init__(status_code=status_code, detail=detail, headers=headers)


# Custom exceptions
class URLAccessError(DetailedHTTPException):
    """Exception raised when a URL cannot be accessed"""
    def __init__(
        self, 
        detail: str = "Unable to access the provided URL",
        error_code: str = "url_access_error",
        details: Optional[str] = None, 
        suggestions: Optional[List[str]] = None
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code,
            details=details,
            suggestions=suggestions,
        )


class AnalysisProcessError(DetailedHTTPException):
    """Exception raised during the analysis process"""
    def __init__(
        self, 
        detail: str = "Error during website analysis",
        error_code: str = "analysis_process_error",
        details: Optional[str] = None, 
        suggestions: Optional[List[str]] = None
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code=error_code,
            details=details,
            suggestions=suggestions,
        )


class OpenAIError(DetailedHTTPException):
    """Exception raised when interacting with OpenAI API"""
    def __init__(
        self, 
        detail: str = "Error with OpenAI API",
        error_code: str = "openai_error",
        details: Optional[str] = None, 
        suggestions: Optional[List[str]] = None
    ):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            error_code=error_code,
            details=details,
            suggestions=suggestions,
        )


class ResultProcessingError(DetailedHTTPException):
    """Exception raised when processing analysis results"""
    def __init__(
        self, 
        detail: str = "Error processing analysis results",
        error_code: str = "result_processing_error",
        details: Optional[str] = None, 
        suggestions: Optional[List[str]] = None
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code=error_code,
            details=details,
            suggestions=suggestions,
        )


# API error responses
def error_response(
    error_code: str, 
    message: str, 
    details: Optional[str] = None,
    suggestions: Optional[List[str]] = None,
    request_id: Optional[str] = None,
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """Generate a standardized error response"""
    response = {
        "error": {
            "code": error_code,
            "message": message,
        }
    }
    
    if details:
        response["error"]["details"] = details
    
    if suggestions:
        response["error"]["suggestions"] = suggestions
        
    if request_id:
        response["error"]["requestId"] = request_id
        
    if timestamp:
        response["error"]["timestamp"] = timestamp
        
    return response 


class BaseAppError(HTTPException):
    """Base application error class"""
    def __init__(
        self,
        detail: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: Optional[str] = None,
        details: Optional[Any] = None
    ):
        self.error_code = error_code
        self.details = details
        super().__init__(status_code=status_code, detail=detail)


class AuthError(BaseAppError):
    """Authentication and authorization errors"""
    def __init__(
        self,
        detail: str,
        error_code: Optional[str] = None,
        details: Optional[Any] = None
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=error_code or "auth_error",
            details=details
        )


class PermissionError(BaseAppError):
    """Permission errors"""
    def __init__(
        self,
        detail: str,
        error_code: Optional[str] = None,
        details: Optional[Any] = None
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=error_code or "permission_error",
            details=details
        )


class NotFoundError(BaseAppError):
    """Resource not found errors"""
    def __init__(
        self,
        detail: str,
        error_code: Optional[str] = None,
        details: Optional[Any] = None
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=error_code or "not_found",
            details=details
        )


class ValidationError(BaseAppError):
    """Data validation errors"""
    def __init__(
        self,
        detail: str,
        error_code: Optional[str] = None,
        details: Optional[Any] = None
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code=error_code or "validation_error",
            details=details
        )


class DatabaseError(BaseAppError):
    """Database errors"""
    def __init__(
        self,
        detail: str,
        error_code: Optional[str] = None,
        details: Optional[Any] = None
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code or "database_error",
            details=details
        )


class BrowserError(BaseAppError):
    """Browser automation errors"""
    def __init__(
        self,
        detail: str,
        error_code: Optional[str] = None,
        details: Optional[Any] = None
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code or "browser_error",
            details=details
        )


class OpenAIError(BaseAppError):
    """OpenAI API errors"""
    def __init__(
        self,
        detail: str,
        error_code: Optional[str] = None,
        details: Optional[Any] = None
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code or "openai_error",
            details=details
        )


class StorageError(BaseAppError):
    """Cloud storage errors"""
    def __init__(
        self,
        detail: str,
        error_code: Optional[str] = None,
        details: Optional[Any] = None
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code or "storage_error",
            details=details
        )


class RateLimitError(BaseAppError):
    """Rate limiting errors"""
    def __init__(
        self,
        detail: str,
        error_code: Optional[str] = None,
        details: Optional[Any] = None
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code=error_code or "rate_limit_error",
            details=details
        )


class ConfigError(BaseAppError):
    """Configuration errors"""
    def __init__(
        self,
        detail: str,
        error_code: Optional[str] = None,
        details: Optional[Any] = None
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code or "config_error",
            details=details
        ) 