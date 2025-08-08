"""
Pydantic models for Pull Request workflow
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ChangeType(str, Enum):
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"


class PRStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"
    DRAFT = "draft"


class FileChangeRequest(BaseModel):
    """Individual file change in a PR request"""
    file_path: str = Field(..., description="Path to the file being changed")
    content: Optional[str] = Field(None, description="New file content (for text files)")
    change_type: ChangeType = Field(..., description="Type of change")


class PRCreateRequest(BaseModel):
    """Request to create a new pull request"""
    fork_id: str = Field(..., description="UUID of the user playbook (fork)")
    title: str = Field(..., min_length=1, max_length=200, description="PR title")
    description: Optional[str] = Field(None, description="PR description")
    commit_message: str = Field(..., min_length=1, description="Commit message describing changes")
    file_changes: List[FileChangeRequest] = Field(..., description="List of file changes")


class PRCreateFromZipRequest(BaseModel):
    """Request to create PR from uploaded ZIP file"""
    fork_id: str = Field(..., description="UUID of the user playbook (fork)")
    title: str = Field(..., min_length=1, max_length=200, description="PR title")
    description: Optional[str] = Field(None, description="PR description")
    commit_message: str = Field(..., min_length=1, description="Commit message describing changes")


class FileChangeAnalysis(BaseModel):
    """AI analysis of a single file change"""
    file_path: str
    changelog: str = Field(..., description="One-line summary of the change")
    risk_flags: List[str] = Field(default_factory=list, description="Identified risk categories")
    confidence: float = Field(..., ge=0.0, le=1.0, description="AI confidence score")


class PRAnalysis(BaseModel):
    """Overall AI analysis of the pull request"""
    pr_title: str = Field(..., description="AI-generated PR title")
    pr_description: str = Field(..., description="AI-generated PR description")
    high_risks: List[str] = Field(default_factory=list, description="High-risk items requiring attention")
    merge_checklist: List[str] = Field(default_factory=list, description="Suggested merge checklist")


class FileChangeDetail(BaseModel):
    """Detailed information about a file change"""
    id: str
    file_path: str
    change_type: ChangeType
    main_file_id: Optional[str]
    fork_file_id: Optional[str]
    diff_text: Optional[str]
    diff_summary: Optional[str]
    risk_flags: List[str]
    confidence: Optional[float]
    checksum_old: Optional[str]
    checksum_new: Optional[str]
    created_at: datetime


class PRResponse(BaseModel):
    """Response model for pull request operations - comprehensive schema"""
    id: str
    fork_id: str
    user_id: str
    target_playbook_id: str
    title: str
    description: Optional[str]
    commit_message: str
    status: PRStatus
    file_changes: List[Dict[str, Any]]  # JSONB array of file changes
    summary: Optional[str]  # AI-generated title
    change_summary: Optional[str]  # AI-generated description
    diff_summary: Optional[str]  # AI per-file diff summary
    risk_flags: List[str]
    merge_checklist: List[str]
    created_at: datetime
    updated_at: datetime
    merged_at: Optional[datetime]
    closed_at: Optional[datetime]
    
    # Related data
    file_details: Optional[List[FileChangeDetail]] = None
    
    class Config:
        from_attributes = True


class PRPreview(BaseModel):
    """Preview of a PR before creation"""
    title: str
    description: str
    target_playbook_id: str
    target_playbook_title: str
    fork_info: Dict[str, Any]
    file_changes_summary: List[Dict[str, str]]
    ai_analysis: Optional[PRAnalysis]
    sync_required: bool
    can_create: bool
    issues: List[str] = Field(default_factory=list)


class SyncStatus(BaseModel):
    """Status of fork synchronization"""
    fork_id: str
    is_behind: bool
    base_version: int
    master_latest_version: int
    last_sync_version: int
    files_to_sync: List[Dict[str, Any]] = Field(default_factory=list)
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)


class SyncRequest(BaseModel):
    """Request to sync a fork with master"""
    fork_id: str = Field(..., description="UUID of the user playbook (fork)")
    auto_resolve_conflicts: bool = Field(False, description="Automatically resolve non-conflicting changes")


class SyncResponse(BaseModel):
    """Response after fork synchronization"""
    fork_id: str
    success: bool
    synced_files: List[str]
    conflicts_resolved: List[str]
    remaining_conflicts: List[Dict[str, Any]]
    new_sync_version: int
    message: str


class PRListRequest(BaseModel):
    """Request parameters for listing pull requests"""
    playbook_id: Optional[str] = None
    user_id: Optional[str] = None
    status: Optional[PRStatus] = None
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class PRListResponse(BaseModel):
    """Response for listing pull requests"""
    pull_requests: List[PRResponse]
    total_count: int
    limit: int
    offset: int
    has_more: bool