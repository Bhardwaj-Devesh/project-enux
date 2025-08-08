"""
Pull Request API endpoints
"""

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from typing import List, Optional
import json
import tempfile
import zipfile
import os

from app.models.pr import (
    PRCreateRequest, PRCreateFromZipRequest, PRResponse, PRPreview,
    SyncStatus, SyncRequest, SyncResponse, PRListRequest, PRListResponse
)
from app.models.auth import TokenData
from app.api.dependencies import get_current_user
from app.services.pr_service import pr_service

router = APIRouter(prefix="/pull-requests", tags=["pull-requests"])


@router.post("/", response_model=PRResponse)
async def create_pull_request(
    pr_request: PRCreateRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Create a new pull request with file changes
    
    This endpoint handles the complete PR workflow:
    1. Validates and authorizes the request
    2. Checks if fork is behind master (requires sync if so)
    3. Generates diffs for all file changes
    4. Uses AI to analyze changes and generate summaries
    5. Persists the PR and returns preview
    """
    try:
        pr_response = await pr_service.create_pull_request(
            pr_request=pr_request,
            user_id=current_user.user_id
        )
        
        return pr_response
    
    except Exception as e:
        if "fork is behind" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        elif "not authorized" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create pull request: {str(e)}"
            )


@router.post("/from-zip", response_model=PRResponse)
async def create_pull_request_from_zip(
    fork_id: str = Form(...),
    title: str = Form(...),
    commit_message: str = Form(...),
    description: Optional[str] = Form(None),
    zip_file: UploadFile = File(...),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Create a pull request by uploading a ZIP file with changes
    
    The ZIP file should contain the updated files in their intended structure.
    Each file will be compared against the current fork version.
    """
    try:
        # Validate ZIP file
        if not zip_file.filename.endswith('.zip'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only ZIP files are allowed"
            )
        
        # Read and extract ZIP content
        zip_content = await zip_file.read()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "upload.zip")
            
            # Save ZIP file
            with open(zip_path, 'wb') as f:
                f.write(zip_content)
            
            # Extract and process files
            file_changes = []
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for file_path in zip_ref.namelist():
                    # Skip directories
                    if file_path.endswith('/'):
                        continue
                    
                    # Read file content
                    file_content = zip_ref.read(file_path).decode('utf-8')
                    
                    # Determine change type (for now, assume all are modifications)
                    # TODO: Implement more sophisticated change detection
                    file_changes.append({
                        "file_path": file_path,
                        "content": file_content,
                        "change_type": "modified"
                    })
        
        # Create PR request
        pr_request = PRCreateRequest(
            fork_id=fork_id,
            title=title,
            description=description,
            commit_message=commit_message,
            file_changes=file_changes
        )
        
        # Create PR
        pr_response = await pr_service.create_pull_request(
            pr_request=pr_request,
            user_id=current_user.user_id
        )
        
        return pr_response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create pull request from ZIP: {str(e)}"
        )


@router.get("/{pr_id}", response_model=PRResponse)
async def get_pull_request(
    pr_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get pull request details including file changes and AI analysis
    
    Users can view PRs they created or PRs targeting playbooks they own.
    """
    try:
        pr_response = await pr_service.get_pull_request(
            pr_id=pr_id,
            user_id=current_user.user_id
        )
        
        return pr_response
    
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "not authorized" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get pull request: {str(e)}"
            )


@router.get("/", response_model=PRListResponse)
async def list_pull_requests(
    playbook_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: TokenData = Depends(get_current_user)
):
    """
    List pull requests with optional filters
    
    Users see PRs they created and PRs targeting their playbooks.
    """
    try:
        # Get PRs created by user
        user_prs = await pr_service.list_pull_requests(
            user_id=current_user.user_id,
            playbook_id=playbook_id,
            status=status,
            limit=limit,
            offset=offset
        )
        
        # Get PRs targeting user's playbooks
        owned_prs = await pr_service.list_pull_requests_for_owner(
            owner_id=current_user.user_id,
            playbook_id=playbook_id,
            status=status,
            limit=limit,
            offset=offset
        )
        
        # Combine and deduplicate
        all_prs = user_prs + [pr for pr in owned_prs if pr not in user_prs]
        
        # Sort by created_at desc
        all_prs.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination to combined results
        paginated_prs = all_prs[offset:offset + limit]
        
        return PRListResponse(
            pull_requests=paginated_prs,
            total_count=len(all_prs),
            limit=limit,
            offset=offset,
            has_more=offset + limit < len(all_prs)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list pull requests: {str(e)}"
        )


@router.post("/{pr_id}/merge")
async def merge_pull_request(
    pr_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Merge a pull request (only by playbook owner)
    
    This applies all changes from the PR to the master playbook.
    """
    try:
        # TODO: Implement merge functionality
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Merge functionality coming soon"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to merge pull request: {str(e)}"
        )


@router.post("/{pr_id}/close")
async def close_pull_request(
    pr_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Close a pull request without merging
    
    Can be done by PR creator or playbook owner.
    """
    try:
        # TODO: Implement close functionality
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Close functionality coming soon"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to close pull request: {str(e)}"
        )


# Fork Sync Endpoints

@router.get("/forks/{fork_id}/sync-status", response_model=SyncStatus)
async def get_sync_status(
    fork_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Check if a fork is behind master and needs synchronization
    
    Returns version information and files that need updating.
    """
    try:
        sync_status = await pr_service.check_sync_status(
            fork_id=fork_id,
            user_id=current_user.user_id
        )
        
        return sync_status
    
    except Exception as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        elif "not authorized" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get sync status: {str(e)}"
            )


@router.post("/forks/{fork_id}/sync", response_model=SyncResponse)
async def sync_fork(
    fork_id: str,
    sync_request: SyncRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Synchronize a fork with the master playbook
    
    This updates the fork with changes from master since last sync.
    """
    try:
        # Validate fork_id matches request
        if sync_request.fork_id != fork_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fork ID in path and request body must match"
            )
        
        sync_result = await pr_service.sync_fork(
            fork_id=fork_id,
            user_id=current_user.user_id
        )
        
        return SyncResponse(
            fork_id=fork_id,
            success=sync_result["success"],
            synced_files=sync_result.get("synced_files", []),
            conflicts_resolved=sync_result.get("conflicts_resolved", []),
            remaining_conflicts=sync_result.get("remaining_conflicts", []),
            new_sync_version=sync_result.get("new_sync_version", 1),
            message=sync_result.get("message", "Sync completed")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync fork: {str(e)}"
        )