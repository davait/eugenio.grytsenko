"""
Pydantic schemas for request and response validation.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    """Base schema for user data."""
    email: EmailStr
    username: str = Field(..., min_length=6, max_length=20, pattern=r'^[a-zA-Z0-9]+$')
    full_name: Optional[str] = None
    department: str = Field(..., pattern=r'^(Tech|RRHH|Sales)$')

class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    """Schema for updating an existing user."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=6, max_length=20, pattern=r'^[a-zA-Z0-9]+$')
    full_name: Optional[str] = None
    department: Optional[str] = Field(None, pattern=r'^(Tech|RRHH|Sales)$')

class UserInDB(UserBase):
    """Schema representing user data as stored in the database."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserResponse(UserInDB):
    """Schema for the response format when returning user data."""
    pass 