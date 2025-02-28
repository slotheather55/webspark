from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union

from pydantic import BaseModel, EmailStr, Field, validator


class UserRole(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    USER = "user"


class UserBase(BaseModel):
    """Base model for user data"""
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    is_active: bool = True


class UserCreate(UserBase):
    """Model for creating a new user"""
    password: str
    
    @validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserUpdate(BaseModel):
    """Model for updating an existing user"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    
    @validator("password")
    def validate_password(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserLogin(BaseModel):
    """Model for user login"""
    email: EmailStr
    password: str


class UserDB(UserBase):
    """Model as stored in the database"""
    id: int
    hashed_password: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class UserResponse(UserBase):
    """User model for API responses"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class UserListResponse(BaseModel):
    """List of users for API"""
    items: List[UserResponse]
    total: int
    page: int
    page_size: int


class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int
    role: UserRole


class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: str
    exp: int
    role: UserRole 