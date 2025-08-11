from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class PlaybookCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=1000)
    stage: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = Field(default_factory=list)
    version: str = Field(default="v1", max_length=20)


class PlaybookResponse(BaseModel):
    id: str
    title: str
    description: str
    tags: List[str]
    stage: Optional[str]
    owner_id: str
    version: str
    files: Dict[str, str]
    created_at: datetime
    updated_at: datetime
    summary: Optional[str] = None
    vector_embedding: Optional[List[float]] = None
    
    class Config:
        from_attributes = True


class PlaybookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=1000)
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
    user_id: str = Field(..., description="UUID of the user creating the fork")


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
