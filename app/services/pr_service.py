"""
Pull Request service for managing playbook pull requests
"""

import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.models.pr import (
    CreatePullRequestRequest, PullRequestResponse, PullRequestListRequest,
    PullRequestListResponse, DiffResponse, MergeResponse, ConflictResponse,
    PullRequestEvent, PlaybookVersionResponse, CreatePullRequestResponse,
    UpdatePullRequestRequest, PullRequestStats, PlaybookPRInfo, DiffFormat
)
from app.models.pr import PRStatus
from app.services.supabase_service import supabase_service
from app.services.diff_service import diff_service


class PRService:
    """Service for managing pull requests"""
    
    def __init__(self):
        """Initialize PR service"""
        pass
    
    async def create_pull_request(
        self, 
        playbook_id: str, 
        author_id: str, 
        request: CreatePullRequestRequest
    ) -> CreatePullRequestResponse:
        """Create a new pull request"""
        # Validate playbook exists
        playbook = await supabase_service.get_playbook(playbook_id)
        if not playbook:
            raise Exception("Playbook not found")
        
        # Validate base version
        base_version = await self._get_playbook_version(request.base_version_id)
        if not base_version:
            raise Exception("Base version not found")
        
        # Check if base version is still current
        if playbook.get('current_version_id') != request.base_version_id:
            raise Exception(f"Base version is outdated. Current version: {playbook.get('current_version_id')}")
        
        # Generate diff
        unified_diff = diff_service.generate_unified_diff(
            base_version['blog_text'], 
            request.new_blog_text
        )
        
        # Create PR
        pr_data = {
            "id": str(uuid.uuid4()),
            "playbook_id": playbook_id,
            "author_id": author_id,
            "base_version_id": request.base_version_id,
            "title": request.title,
            "description": request.description,
            "old_blog_text": base_version['blog_text'],
            "new_blog_text": request.new_blog_text,
            "unified_diff": unified_diff,
            "status": "OPEN",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Insert into database
        response = supabase_service.client.table("pull_requests").insert(pr_data).execute()
        if not response.data:
            raise Exception("Failed to create pull request")
        
        pr_record = response.data[0]
        
        # Create event
        await self._create_pr_event(pr_record['id'], 'created', author_id)
        
        # Create notification for playbook owner
        try:
            await supabase_service.create_pr_created_notification(
                pr_id=pr_record['id'],
                playbook_id=playbook_id,
                pr_author_id=author_id
            )
        except Exception as notification_error:
            print(f"⚠️ Failed to create PR creation notification: {notification_error}")
        
        # Get enhanced PR response
        pr_response = await self._get_enhanced_pr_response(pr_record)
        
        return CreatePullRequestResponse(
            pull_request=pr_response,
            message=f"Pull request '{request.title}' created successfully"
        )
    
    async def get_pull_request(self, pr_id: str) -> Optional[PullRequestResponse]:
        """Get pull request by ID"""
        response = supabase_service.client.table("pull_requests").select("*").eq("id", pr_id).execute()
        if not response.data:
            return None
        
        pr_record = response.data[0]
        return await self._get_enhanced_pr_response(pr_record)
    
    async def list_pull_requests(
        self,
        playbook_id: str, 
        request: PullRequestListRequest
    ) -> PullRequestListResponse:
        """List pull requests for a playbook"""
        query = supabase_service.client.table("pull_requests").select("*").eq("playbook_id", playbook_id)
        
        if request.status:
            query = query.eq("status", request.status.value)
        
        # Get total count
        count_response = query.execute()
        total_count = len(count_response.data)
        
        # Apply pagination
        query = query.order("created_at", desc=True).range(request.offset, request.offset + request.limit - 1)
        response = query.execute()
        
        # Enhance PRs with additional data
        enhanced_prs = []
        for pr_record in response.data:
            enhanced_pr = await self._get_enhanced_pr_response(pr_record)
            enhanced_prs.append(enhanced_pr)
        
        return PullRequestListResponse(
            pull_requests=enhanced_prs,
            total_count=total_count,
            has_more=request.offset + request.limit < total_count
        )
    
    async def get_pull_request_diff(
        self, 
        pr_id: str, 
        format: DiffFormat = DiffFormat.UNIFIED
    ) -> Optional[DiffResponse]:
        """Get diff for a pull request"""
        pr = await self.get_pull_request(pr_id)
        if not pr:
            return None
        
        unified_diff = diff_service.generate_unified_diff(
            pr.old_blog_text, 
            pr.new_blog_text
        )
        
        side_by_side_diff = None
        html_diff = None
        
        if format == DiffFormat.SIDE_BY_SIDE:
            side_by_side_diff = diff_service.generate_side_by_side_diff(
                pr.old_blog_text, 
                pr.new_blog_text
            )
        elif format == DiffFormat.HTML:
            html_diff = diff_service.generate_html_diff(
                pr.old_blog_text, 
                pr.new_blog_text
            )
        
        return DiffResponse(
            unified_diff=unified_diff,
            side_by_side_diff=side_by_side_diff,
            html_diff=html_diff,
            format=format
        )
    
    async def merge_pull_request(
        self, 
        pr_id: str, 
        merged_by: str, 
        merge_message: str
    ) -> MergeResponse:
        """Merge a pull request"""
        # Get PR
        pr = await self.get_pull_request(pr_id)
        if not pr:
            raise Exception("Pull request not found")
        
        if pr.status != PRStatus.OPEN:
            raise Exception("Pull request is not open")
        
        # Check if user is playbook owner
        playbook = await supabase_service.get_playbook(pr.playbook_id)
        if not playbook or playbook['owner_id'] != merged_by:
            raise Exception("Only playbook owner can merge pull requests")
        
        # Use database function for merge
        response = supabase_service.client.rpc(
            "merge_pull_request",
            {
                "p_pr_id": pr_id,
                "p_merge_message": merge_message,
                "p_merged_by": merged_by
            }
        ).execute()
        
        if not response.data:
            raise Exception("Failed to merge pull request")
        
        # Debug: Log the response structure
        print(f"DEBUG: Response data type: {type(response.data)}")
        print(f"DEBUG: Response data: {response.data}")
        
        result = response.data
        
        # Create event
        await self._create_pr_event(pr_id, 'merged', merged_by, {
            "new_version_id": result['new_version_id'],
            "merge_message": merge_message
        })
        
        # Create notification for PR author
        try:
            await supabase_service.create_pr_merge_notification(
                pr_id=pr_id,
                playbook_id=pr.playbook_id,
                merged_by=merged_by,
                pr_author_id=pr.author_id
            )
        except Exception as notification_error:
            print(f"⚠️ Failed to create merge notification: {notification_error}")
        
        return MergeResponse(
            status="MERGED",
            new_version_id=result['new_version_id'],
            version_number=result['version_number'],
            message=merge_message
        )
    
    async def decline_pull_request(self, pr_id: str, declined_by: str) -> Dict[str, Any]:
        """Decline a pull request"""
        # Get PR
        pr = await self.get_pull_request(pr_id)
        if not pr:
            raise Exception("Pull request not found")
        
        if pr.status != PRStatus.OPEN:
            raise Exception("Pull request is not open")
        
        # Check if user is playbook owner
        playbook = await supabase_service.get_playbook(pr.playbook_id)
        if not playbook or playbook['owner_id'] != declined_by:
            raise Exception("Only playbook owner can decline pull requests")
        
        # Update PR status
        response = supabase_service.client.table("pull_requests").update({
            "status": "DECLINED",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", pr_id).execute()
        
        if not response.data:
            raise Exception("Failed to decline pull request")
        
        # Create event
        await self._create_pr_event(pr_id, 'declined', declined_by)
        
        # Create notification for PR author
        try:
            await supabase_service.create_pr_decline_notification(
                pr_id=pr_id,
                playbook_id=pr.playbook_id,
                declined_by=declined_by,
                pr_author_id=pr.author_id
            )
        except Exception as notification_error:
            print(f"⚠️ Failed to create decline notification: {notification_error}")
        
        return {"status": "DECLINED"}
    
    async def close_pull_request(self, pr_id: str, closed_by: str) -> Dict[str, Any]:
        """Close a pull request"""
        # Get PR
        pr = await self.get_pull_request(pr_id)
        if not pr:
            raise Exception("Pull request not found")
        
        if pr.status != PRStatus.OPEN:
            raise Exception("Pull request is not open")
        
        # Check if user is author or playbook owner
        playbook = await supabase_service.get_playbook(pr.playbook_id)
        if not playbook:
            raise Exception("Playbook not found")
        
        if pr.author_id != closed_by and playbook['owner_id'] != closed_by:
            raise Exception("Only author or playbook owner can close pull requests")
        
        # Update PR status
        response = supabase_service.client.table("pull_requests").update({
            "status": "CLOSED",
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", pr_id).execute()
        
        if not response.data:
            raise Exception("Failed to close pull request")
        
        # Create event
        await self._create_pr_event(pr_id, 'closed', closed_by)
        
        # Create notification for PR author (only if closed by someone else)
        try:
            await supabase_service.create_pr_close_notification(
                pr_id=pr_id,
                playbook_id=pr.playbook_id,
                closed_by=closed_by,
                pr_author_id=pr.author_id
            )
        except Exception as notification_error:
            print(f"⚠️ Failed to create close notification: {notification_error}")
        
        return {"status": "CLOSED"}
    
    async def get_pull_request_stats(self, playbook_id: str) -> PullRequestStats:
        """Get pull request statistics for a playbook"""
        response = supabase_service.client.table("pull_requests").select("status").eq("playbook_id", playbook_id).execute()
        
        stats = {
            "total_prs": 0,
            "open_prs": 0,
            "merged_prs": 0,
            "declined_prs": 0,
            "closed_prs": 0
        }
        
        for pr in response.data:
            stats["total_prs"] += 1
            status = pr["status"]
            if status == "OPEN":
                stats["open_prs"] += 1
            elif status == "MERGED":
                stats["merged_prs"] += 1
            elif status == "DECLINED":
                stats["declined_prs"] += 1
            elif status == "CLOSED":
                stats["closed_prs"] += 1
        
        return PullRequestStats(**stats)
    
    async def get_playbook_pr_info(self, playbook_id: str, user_id: str) -> PlaybookPRInfo:
        """Get PR information for a playbook"""
        playbook = await supabase_service.get_playbook(playbook_id)
        if not playbook:
            raise Exception("Playbook not found")
        
        current_version = await self._get_playbook_version(playbook['current_version_id'])
        stats = await self.get_pull_request_stats(playbook_id)
        
        is_owner = playbook['owner_id'] == user_id
        
        return PlaybookPRInfo(
            playbook_id=playbook_id,
            playbook_title=playbook['title'],
            current_version_id=playbook['current_version_id'],
            current_version_number=current_version['version_number'] if current_version else 1,
            total_prs=stats.total_prs,
            open_prs=stats.open_prs,
            can_create_pr=not is_owner,
            is_owner=is_owner
        )
    
    # Private helper methods
    
    async def _get_playbook_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        """Get playbook version by ID"""
        response = supabase_service.client.table("playbook_versions").select("*").eq("id", version_id).execute()
        return response.data[0] if response.data else None
    
    async def _get_enhanced_pr_response(self, pr_record: Dict[str, Any]) -> PullRequestResponse:
        """Get enhanced PR response with additional data"""
        # Get author name
        author_name = None
        if pr_record['author_id']:
            user = await supabase_service.get_user_by_id(pr_record['author_id'])
            if user:
                author_name = user.get('full_name') or user.get('email')
        
        # Get playbook title
        playbook_title = None
        if pr_record['playbook_id']:
            playbook = await supabase_service.get_playbook(pr_record['playbook_id'])
            if playbook:
                playbook_title = playbook['title']
        
        # Get version numbers
        base_version_number = None
        new_version_number = None
        
        if pr_record['base_version_id']:
            base_version = await self._get_playbook_version(pr_record['base_version_id'])
            if base_version:
                base_version_number = base_version['version_number']
        
        if pr_record['new_version_id']:
            new_version = await self._get_playbook_version(pr_record['new_version_id'])
            if new_version:
                new_version_number = new_version['version_number']
        
        return PullRequestResponse(
            id=pr_record['id'],
            playbook_id=pr_record['playbook_id'],
            author_id=pr_record['author_id'],
            base_version_id=pr_record['base_version_id'],
            title=pr_record['title'],
            description=pr_record['description'],
            old_blog_text=pr_record['old_blog_text'],
            new_blog_text=pr_record['new_blog_text'],
            unified_diff=pr_record['unified_diff'],
            status=PRStatus(pr_record['status']),
            created_at=datetime.fromisoformat(pr_record['created_at']),
            updated_at=datetime.fromisoformat(pr_record['updated_at']),
            merged_at=datetime.fromisoformat(pr_record['merged_at']) if pr_record['merged_at'] else None,
            merged_by=pr_record['merged_by'],
            merge_message=pr_record['merge_message'],
            new_version_id=pr_record['new_version_id'],
            author_name=author_name,
            playbook_title=playbook_title,
            base_version_number=base_version_number,
            new_version_number=new_version_number
        )
    
    async def _create_pr_event(self, pr_id: str, event_type: str, actor_id: str, metadata: Dict[str, Any] = None):
        """Create a pull request event"""
        event_data = {
            "id": str(uuid.uuid4()),
            "pr_id": pr_id,
            "event_type": event_type,
            "actor_id": actor_id,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat()
        }
        
        supabase_service.client.table("pull_request_events").insert(event_data).execute()


# Global instance
pr_service = PRService()
