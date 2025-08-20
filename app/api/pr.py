"""
Pull Request API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import Optional, List, Dict, Any
from app.models.pr import (
    CreatePullRequestRequest, PullRequestResponse, PullRequestListRequest,
    PullRequestListResponse, DiffResponse, MergeResponse, ConflictResponse,
    PullRequestEvent, PlaybookVersionResponse, CreatePullRequestResponse,
    UpdatePullRequestRequest, PullRequestStats, PlaybookPRInfo, DiffFormat,
    PRStatus
)
from app.services.pr_service import pr_service
from app.api.dependencies import get_current_user
from app.models.auth import TokenData
from app.services.supabase_service import supabase_service

router = APIRouter(prefix="/pull-requests", tags=["Pull Requests"])


@router.post("/playbooks/{playbook_id}/pull-requests", response_model=CreatePullRequestResponse)
async def create_pull_request(
    playbook_id: str = Path(..., description="Target playbook ID"),
    request: CreatePullRequestRequest = None,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Create a new pull request for a playbook
    
    - **playbook_id**: Target playbook ID
    - **title**: PR title (1-200 characters)
    - **description**: Optional PR description (max 2000 characters)
    - **new_blog_text**: New blog content
    - **base_version_id**: Base version ID for conflict detection
    """
    try:
        result = await pr_service.create_pull_request(
            playbook_id=playbook_id,
            author_id=current_user.user_id,
            request=request
        )
        return result
    except Exception as e:
        if "Base version is outdated" in str(e):
            raise HTTPException(status_code=409, detail=str(e))
        elif "Playbook not found" in str(e):
            raise HTTPException(status_code=404, detail="Playbook not found")
        else:
            raise HTTPException(status_code=400, detail=str(e))


@router.get("/playbooks/{playbook_id}/pull-requests", response_model=PullRequestListResponse)
async def list_pull_requests(
    playbook_id: str = Path(..., description="Playbook ID"),
    status: Optional[PRStatus] = Query(None, description="Filter by PR status"),
    limit: int = Query(20, ge=1, le=100, description="Number of PRs to return"),
    offset: int = Query(0, ge=0, description="Number of PRs to skip"),
    current_user: TokenData = Depends(get_current_user)
):
    """
    List pull requests for a playbook
    
    - **playbook_id**: Playbook ID
    - **status**: Optional filter by PR status (OPEN, MERGED, DECLINED, CLOSED)
    - **limit**: Number of PRs to return (1-100)
    - **offset**: Number of PRs to skip for pagination
    """
    try:
        request = PullRequestListRequest(status=status, limit=limit, offset=offset)
        result = await pr_service.list_pull_requests(playbook_id, request)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{pr_id}", response_model=PullRequestResponse)
async def get_pull_request(
    pr_id: str = Path(..., description="Pull request ID"),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get pull request details by ID
    
    - **pr_id**: Pull request ID
    """
    try:
        pr = await pr_service.get_pull_request(pr_id)
        if not pr:
            raise HTTPException(status_code=404, detail="Pull request not found")
        return pr
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{pr_id}/diff", response_model=DiffResponse)
async def get_pull_request_diff(
    pr_id: str = Path(..., description="Pull request ID"),
    format: DiffFormat = Query(DiffFormat.UNIFIED, description="Diff format"),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get diff for a pull request
    
    - **pr_id**: Pull request ID
    - **format**: Diff format (unified, side-by-side, html)
    """
    try:
        diff = await pr_service.get_pull_request_diff(pr_id, format)
        if not diff:
            raise HTTPException(status_code=404, detail="Pull request not found")
        return diff
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{pr_id}/merge", response_model=MergeResponse)
async def merge_pull_request(
    pr_id: str = Path(..., description="Pull request ID"),
    merge_message: str = Query(..., min_length=1, max_length=500, description="Merge commit message"),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Merge a pull request (owner only)
    
    - **pr_id**: Pull request ID
    - **merge_message**: Merge commit message (1-500 characters)
    """
    try:
        result = await pr_service.merge_pull_request(
            pr_id=pr_id,
            merged_by=current_user.user_id,
            merge_message=merge_message
        )
        return result
    except Exception as e:
        if "Only playbook owner can merge" in str(e):
            raise HTTPException(status_code=403, detail="Only playbook owner can merge pull requests")
        elif "Pull request not found" in str(e):
            raise HTTPException(status_code=404, detail="Pull request not found")
        elif "Pull request is not open" in str(e):
            raise HTTPException(status_code=400, detail="Pull request is not open")
        elif "Merge conflicts detected" in str(e):
            raise HTTPException(status_code=409, detail="Merge conflicts detected. Manual resolution required.")
        else:
            raise HTTPException(status_code=400, detail=str(e))


@router.post("/{pr_id}/decline")
async def decline_pull_request(
    pr_id: str = Path(..., description="Pull request ID"),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Decline a pull request (owner only)
    
    - **pr_id**: Pull request ID
    """
    try:
        result = await pr_service.decline_pull_request(pr_id, current_user.user_id)
        return result
    except Exception as e:
        if "Only playbook owner can decline" in str(e):
            raise HTTPException(status_code=403, detail="Only playbook owner can decline pull requests")
        elif "Pull request not found" in str(e):
            raise HTTPException(status_code=404, detail="Pull request not found")
        elif "Pull request is not open" in str(e):
            raise HTTPException(status_code=400, detail="Pull request is not open")
        else:
            raise HTTPException(status_code=400, detail=str(e))


@router.post("/{pr_id}/close")
async def close_pull_request(
    pr_id: str = Path(..., description="Pull request ID"),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Close a pull request (author or owner)
    
    - **pr_id**: Pull request ID
    """
    try:
        result = await pr_service.close_pull_request(pr_id, current_user.user_id)
        return result
    except Exception as e:
        if "Only author or playbook owner can close" in str(e):
            raise HTTPException(status_code=403, detail="Only author or playbook owner can close pull requests")
        elif "Pull request not found" in str(e):
            raise HTTPException(status_code=404, detail="Pull request not found")
        elif "Pull request is not open" in str(e):
            raise HTTPException(status_code=400, detail="Pull request is not open")
        else:
            raise HTTPException(status_code=400, detail=str(e))


@router.get("/playbooks/{playbook_id}/stats", response_model=PullRequestStats)
async def get_pull_request_stats(
    playbook_id: str = Path(..., description="Playbook ID"),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get pull request statistics for a playbook
    
    - **playbook_id**: Playbook ID
    """
    try:
        stats = await pr_service.get_pull_request_stats(playbook_id)
        return stats
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/playbooks/{playbook_id}/info", response_model=PlaybookPRInfo)
async def get_playbook_pr_info(
    playbook_id: str = Path(..., description="Playbook ID"),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get PR information for a playbook
    
    - **playbook_id**: Playbook ID
    """
    try:
        info = await pr_service.get_playbook_pr_info(playbook_id, current_user.user_id)
        return info
    except Exception as e:
        if "Playbook not found" in str(e):
            raise HTTPException(status_code=404, detail="Playbook not found")
        else:
            raise HTTPException(status_code=400, detail=str(e))


@router.get("/playbooks/{playbook_id}/versions", response_model=List[PlaybookVersionResponse])
async def get_playbook_versions(
    playbook_id: str = Path(..., description="Playbook ID"),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get all versions of a playbook
    
    - **playbook_id**: Playbook ID
    """
    try:
        # This method needs to be added to the PR service
        # For now, we'll return a placeholder
        raise HTTPException(status_code=501, detail="Not implemented yet")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Additional utility endpoints

@router.get("/user/{user_id}/pull-requests", response_model=PullRequestListResponse)
async def get_user_pull_requests(
    user_id: str = Path(..., description="User ID"),
    status: Optional[PRStatus] = Query(None, description="Filter by PR status"),
    limit: int = Query(20, ge=1, le=100, description="Number of PRs to return"),
    offset: int = Query(0, ge=0, description="Number of PRs to skip"),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get pull requests created by a user
    
    - **user_id**: User ID
    - **status**: Optional filter by PR status
    - **limit**: Number of PRs to return (1-100)
    - **offset**: Number of PRs to skip for pagination
    """
    try:
        # This would need to be implemented in the service
        # For now, we'll return a placeholder
        raise HTTPException(status_code=501, detail="Not implemented yet")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{pr_id}/events", response_model=List[PullRequestEvent])
async def get_pull_request_events(
    pr_id: str = Path(..., description="Pull request ID"),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get events for a pull request
    
    - **pr_id**: Pull request ID
    """
    try:
        # This would need to be implemented in the service
        # For now, we'll return a placeholder
        raise HTTPException(status_code=501, detail="Not implemented yet")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/test-pr-notifications", response_model=Dict[str, Any])
async def test_pr_notifications(
    current_user: TokenData = Depends(get_current_user)
):
    """Test endpoint to verify PR notifications functionality"""
    try:
        # Test PR merge notification
        test_result = await supabase_service.create_pr_merge_notification(
            pr_id="test-pr-id",
            playbook_id="test-playbook-id", 
            merged_by=current_user.user_id,
            pr_author_id=current_user.user_id
        )
        
        return {
            "success": True,
            "message": "PR notification test completed",
            "test_result": test_result
        }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"PR notification test failed: {str(e)}",
            "error_type": type(e).__name__
        }
