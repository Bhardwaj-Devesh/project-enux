from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class PlaybookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    blog_content: Optional[str] = Field(None, description="Markdown blog content")
    stage: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = Field(default_factory=list)
    version: str = Field(default="v1", max_length=20)


import json
from typing import Union

class PlaybookResponse(BaseModel):
    id: str
    title: str
    description: str
    blog_content: Optional[str] = None
    tags: List[str]
    stage: Optional[str]
    owner_id: str
    version: str
    files: Dict[str, str]
    created_at: datetime
    updated_at: datetime
    summary: Optional[str] = None
    vector_embedding: Optional[List[float]] = None
    star_count: int = 0
    view_count: int = 0
    
    @classmethod
    def from_orm(cls, obj):
        """Custom from_orm method to handle vector_embedding conversion"""
        data = obj.__dict__ if hasattr(obj, '__dict__') else obj
        
        # Convert vector_embedding from string to list if needed
        if 'vector_embedding' in data and data['vector_embedding'] is not None:
            if isinstance(data['vector_embedding'], str):
                try:
                    data['vector_embedding'] = json.loads(data['vector_embedding'])
                except (json.JSONDecodeError, TypeError):
                    data['vector_embedding'] = None
        
        return cls(**data)
    
    class Config:
        from_attributes = True


class PlaybookWithForkInfo(BaseModel):
    """Enhanced playbook response with fork information"""
    id: str
    title: str
    description: str
    blog_content: Optional[str] = None
    tags: List[str]
    stage: Optional[str]
    owner_id: str
    version: str
    files: Dict[str, str]
    created_at: datetime
    updated_at: datetime
    summary: Optional[str] = None
    vector_embedding: Optional[List[float]] = None
    star_count: int = 0
    view_count: int = 0
    fork_count: int = 0
    is_fork: bool = False
    forked_at: Optional[datetime] = None
    original_playbook_id: Optional[str] = None
    
    class Config:
        from_attributes = True


class PlaybookForkInfo(BaseModel):
    """Information about a playbook fork"""
    id: str
    user_id: str
    original_playbook_id: str
    forked_at: datetime
    version: str
    


class PlaybookDetailedResponse(BaseModel):
    """Detailed playbook response with fork information"""
    id: str
    title: str
    description: str
    blog_content: Optional[str] = None
    tags: List[str]
    stage: Optional[str]
    owner_id: str
    version: str
    files: Dict[str, str]
    created_at: datetime
    updated_at: datetime
    summary: Optional[str] = None
    vector_embedding: Optional[List[float]] = None
    star_count: int = 0
    view_count: int = 0
    fork_count: int = 0
    current_version_id: Optional[str] = None
    # forks: List[PlaybookForkInfo] = []
    
    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    """Notification response for fork events and PR events"""
    id: str
    type: str  # "fork", "pr_merged", "pr_declined", "pr_closed", etc.
    title: str
    message: str
    playbook_id: str
    playbook_title: str
    user_id: str
    user_email: str
    user_full_name: str
    fork_id: Optional[str] = None
    pr_id: Optional[str] = None
    is_read: bool = False
    read_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class PlaybookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
    blog_content: Optional[str] = Field(None, description="Markdown blog content")
    stage: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = None
    version: Optional[str] = Field(None, max_length=20)


class PlaybookSearch(BaseModel):
    query: str = Field(..., min_length=1)
    limit: Optional[int] = Field(10, ge=1, le=100)
    offset: Optional[int] = Field(0, ge=0)
    tags: Optional[List[str]] = None
    stage: Optional[str] = None


class PlaybookSearchResult(BaseModel):
    playbook: PlaybookResponse
    similarity_score: float


class FileUpload(BaseModel):
    filename: str
    content_type: str
    size: int
    file_path: str


class PlaybookUploadResponse(BaseModel):
    playbook: PlaybookResponse
    files: List[FileUpload]
    processing_status: str
    message: str


class ProcessingStatus(BaseModel):
    status: str  # "processing", "completed", "failed"
    message: str
    progress: Optional[float] = None
    summary: Optional[str] = None
    extracted_tags: Optional[List[str]] = None
    vector_embedding: Optional[List[float]] = None 


class PlaybookForkRequest(BaseModel):
    playbook_id: str = Field(..., description="UUID of the playbook to fork")


class PlaybookStarRequest(BaseModel):
    playbook_id: str = Field(..., description="UUID of the playbook to star/unstar")


class PlaybookStarResponse(BaseModel):
    playbook_id: str
    starred: bool
    star_count: int
    message: str


class PlaybookViewRequest(BaseModel):
    playbook_id: str = Field(..., description="UUID of the playbook being viewed")


class PlaybookViewResponse(BaseModel):
    playbook_id: str
    view_count: int
    message: str


class PopularPlaybookResponse(BaseModel):
    playbook_id: str
    title: str
    description: str
    star_count: int
    view_count: int
    created_at: datetime


class MarkNotificationsReadRequest(BaseModel):
    notification_ids: List[str] = Field(..., description="List of notification IDs to mark as read")


class MarkNotificationsReadResponse(BaseModel):
    updated_count: int
    message: str


class MarkAllNotificationsReadResponse(BaseModel):
    updated_count: int
    message: str


class NotificationCountResponse(BaseModel):
    unread_count: int
    total_count: int


class PlaybookForkResponse(BaseModel):
    status: str
    new_playbook_id: str
    new_playbook_url: str
    message: Optional[str] = None


class UserPlaybookResponse(BaseModel):
    id: str
    user_id: str
    original_playbook_id: str
    forked_at: datetime
    last_updated_at: datetime
    version: str
    license: Optional[str]
    status: str
    original_playbook: Optional[PlaybookResponse] = None
    
    class Config:
        from_attributes = True


class PlaybookFileCreate(BaseModel):
    playbook_id: str = Field(..., description="UUID of the playbook")
    file_name: str = Field(..., min_length=1, max_length=255, description="Name of the file")
    file_type: str = Field(..., description="Type of file (md, pdf, csv, docx, txt)")
    storage_path: str = Field(..., description="Path to file in storage")
    tags: Optional[List[str]] = Field(default_factory=list)
    uploaded_by: Optional[str] = Field(None, description="UUID of user who uploaded the file")


class PlaybookFileResponse(BaseModel):
    id: str
    playbook_id: str
    file_name: str
    file_type: str
    storage_path: str
    tags: List[str]
    uploaded_by: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class PlaybookFileUpdate(BaseModel):
    file_name: Optional[str] = Field(None, min_length=1, max_length=255)
    file_type: Optional[str] = None
    storage_path: Optional[str] = None
    tags: Optional[List[str]] = None
