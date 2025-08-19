"""
Pydantic models for Pull Request workflow
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class PRStatus(str, Enum):
    """Pull request status enum"""
    OPEN = "OPEN"
    MERGED = "MERGED"
    DECLINED = "DECLINED"
    CLOSED = "CLOSED"


class DiffFormat(str, Enum):
    """Diff format enum"""
    UNIFIED = "unified"
    SIDE_BY_SIDE = "side-by-side"
    HTML = "html"


class CreatePullRequestRequest(BaseModel):
    """Request to create a new pull request"""
    title: str = Field(..., min_length=1, max_length=200, description="PR title")
    description: Optional[str] = Field(None, max_length=2000, description="PR description")
    new_blog_text: str = Field(..., description="New blog content")
    base_version_id: str = Field(..., description="Base version ID for conflict detection")


class MergePullRequestRequest(BaseModel):
    """Request to merge a pull request"""
    message: str = Field(..., min_length=1, max_length=500, description="Merge commit message")


class PullRequestResponse(BaseModel):
    """Response model for pull request operations"""
    id: str
    playbook_id: str
    author_id: str
    base_version_id: str
    title: str
    description: Optional[str]
    old_blog_text: str
    new_blog_text: str
    unified_diff: Optional[str]
    status: PRStatus
    created_at: datetime
    updated_at: datetime
    merged_at: Optional[datetime]
    merged_by: Optional[str]
    merge_message: Optional[str]
    new_version_id: Optional[str]
    
    # Additional fields for UI
    author_name: Optional[str] = None
    playbook_title: Optional[str] = None
    base_version_number: Optional[int] = None
    new_version_number: Optional[int] = None


class PullRequestListRequest(BaseModel):
    """Request parameters for listing pull requests"""
    status: Optional[PRStatus] = None
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class PullRequestListResponse(BaseModel):
    """Response for listing pull requests"""
    pull_requests: List[PullRequestResponse]
    total_count: int
    has_more: bool


class DiffResponse(BaseModel):
    """Response for diff operations"""
    unified_diff: str
    side_by_side_diff: Optional[Dict[str, Any]] = None
    html_diff: Optional[str] = None
    format: DiffFormat


class PullRequestDetailResponse(BaseModel):
    """Detailed pull request response with diff"""
    pull_request: PullRequestResponse
    diff: Optional[DiffResponse] = None


class MergeResponse(BaseModel):
    """Response for merge operations"""
    status: str
    new_version_id: str
    version_number: int
    message: str


class ConflictResponse(BaseModel):
    """Response for merge conflicts"""
    has_conflicts: bool = True
    conflicts: List[Dict[str, Any]]
    current_version_id: str
    base_version_id: str
    message: str


class PullRequestEvent(BaseModel):
    """Pull request event model"""
    id: str
    pr_id: str
    event_type: str
    actor_id: str
    actor_name: Optional[str] = None
    metadata: Dict[str, Any]
    created_at: datetime


class PlaybookVersionResponse(BaseModel):
    """Response model for playbook versions"""
    id: str
    playbook_id: str
    version_number: int
    blog_text: str
    content_hash: str
    source: str
    pr_id: Optional[str]
    created_by: str
    created_at: datetime
    created_by_name: Optional[str] = None


class CreatePullRequestResponse(BaseModel):
    """Response for creating a pull request"""
    pull_request: PullRequestResponse
    message: str


class UpdatePullRequestRequest(BaseModel):
    """Request to update a pull request"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    new_blog_text: Optional[str] = None


class PullRequestStats(BaseModel):
    """Pull request statistics"""
    total_prs: int
    open_prs: int
    merged_prs: int
    declined_prs: int
    closed_prs: int


class PlaybookPRInfo(BaseModel):
    """Information about PRs for a playbook"""
    playbook_id: str
    playbook_title: str
    current_version_id: str
    current_version_number: int
    total_prs: int
    open_prs: int
    can_create_pr: bool
    is_owner: bool


# Validation models
class PullRequestFilters(BaseModel):
    """Filters for pull request queries"""
    status: Optional[PRStatus] = None
    author_id: Optional[str] = None
    playbook_id: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


class PullRequestSort(BaseModel):
    """Sorting options for pull requests"""
    field: str = Field("created_at", pattern="^(created_at|updated_at|title|status)$")
    order: str = Field("desc", pattern="^(asc|desc)$")


# Utility models for internal operations
class DiffHunk(BaseModel):
    """Represents a diff hunk"""
    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    content: List[str]


class DiffResult(BaseModel):
    """Result of diff operation"""
    hunks: List[DiffHunk]
    unified_diff: str
    has_changes: bool
    lines_added: int
    lines_removed: int


class MergeResult(BaseModel):
    """Result of merge operation"""
    success: bool
    new_version_id: Optional[str] = None
    version_number: Optional[int] = None
    conflicts: Optional[List[Dict[str, Any]]] = None
    message: str
