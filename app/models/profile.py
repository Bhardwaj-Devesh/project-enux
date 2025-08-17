from pydantic import BaseModel, validator, HttpUrl
from typing import List, Optional
from datetime import datetime


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    website: Optional[HttpUrl] = None
    interests: Optional[List[str]] = []
    stage: Optional[str] = None
    avatar_url: Optional[str] = None

    @validator('full_name')
    def validate_full_name(cls, v):
        if v and len(v) > 100:
            raise ValueError('Full name must be less than 100 characters')
        return v

    @validator('bio')
    def validate_bio(cls, v):
        if v and len(v) > 500:
            raise ValueError('Bio must be less than 500 characters')
        return v

    @validator('company')
    def validate_company(cls, v):
        if v and len(v) > 100:
            raise ValueError('Company must be less than 100 characters')
        return v

    @validator('location')
    def validate_location(cls, v):
        if v and len(v) > 100:
            raise ValueError('Location must be less than 100 characters')
        return v

    @validator('interests')
    def validate_interests(cls, v):
        if v and len(v) > 10:
            raise ValueError('Maximum 10 interests allowed')
        if v:
            for interest in v:
                if len(interest) > 50:
                    raise ValueError('Each interest must be less than 50 characters')
        return v

    @validator('stage')
    def validate_stage(cls, v):
        valid_stages = ['student', 'junior', 'mid-level', 'senior', 'lead', 'manager', 'architect', 'other']
        if v and v not in valid_stages:
            raise ValueError(f'Stage must be one of: {", ".join(valid_stages)}')
        return v


class ProfileResponse(BaseModel):
    id: str
    username: str
    full_name: Optional[str]
    bio: Optional[str]
    company: Optional[str]
    location: Optional[str]
    website: Optional[str]
    interests: Optional[List[str]]
    stage: Optional[str]
    avatar_url: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AvatarUploadResponse(BaseModel):
    avatar_url: str
    message: str
