"""
Pull Request service for handling the complete PR creation workflow
"""

import hashlib
import json
import difflib
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import uuid

from app.models.pr import (
    PRCreateRequest, PRResponse, FileChangeRequest, PRPreview, 
    SyncStatus, FileChangeAnalysis, PRAnalysis, ChangeType
)
from app.services.supabase_service import supabase_service
from app.services.gemini_service import gemini_service


class PRService:
    """Service for handling Pull Request workflow"""
    
    def __init__(self):
        """Initialize PR service"""
        pass
    
    async def create_pull_request(
        self, 
        pr_request: PRCreateRequest, 
        user_id: str
    ) -> PRResponse:
        """
        Main PR creation workflow orchestrator
        
        Steps:
        1. Validate & authorize
        2. Load versions & check sync status
        3. Normalize input & compute checksums
        4. Generate diffs
        5. AI analysis (per-file and overall)
        6. Persist PR and files
        7. Return PR preview
        """
        
        # Step 1: Validate & authorize
        await self._validate_and_authorize(pr_request.fork_id, user_id)
        
        # Step 2: Load versions & check sync
        sync_status = await self._check_sync_status(pr_request.fork_id)
        if sync_status.is_behind:
            raise Exception(f"Fork is behind master. Please sync first. "
                          f"Master version: {sync_status.master_latest_version}, "
                          f"Fork base: {sync_status.base_version}")
        
        # Step 3: Normalize input & compute checksums
        normalized_changes = await self._normalize_file_changes(
            pr_request.fork_id, pr_request.file_changes
        )
        
        # Step 4: Generate diffs
        diff_results = await self._generate_diffs(
            pr_request.fork_id, normalized_changes
        )
        
        # Step 5: AI analysis
        file_analyses = []
        for diff_result in diff_results:
            analysis = await gemini_service.analyze_file_change(
                file_path=diff_result['file_path'],
                main_content=diff_result.get('main_content'),
                fork_content=diff_result.get('fork_content'),
                user_content=diff_result.get('user_content', ''),
                change_type=diff_result['change_type']
            )
            file_analyses.append(analysis)
        
        # Overall PR analysis
        pr_analysis = await gemini_service.analyze_pr_overall(
            file_analyses=file_analyses,
            commit_message=pr_request.commit_message,
            pr_title=pr_request.title,
            pr_description=pr_request.description or ""
        )
        
        # Step 6: Persist PR
        pr_response = await self._persist_pull_request(
            pr_request=pr_request,
            user_id=user_id,
            diff_results=diff_results,
            file_analyses=file_analyses,
            pr_analysis=pr_analysis
        )
        
        return pr_response
    
    async def get_pull_request(self, pr_id: str, user_id: str) -> PRResponse:
        """Get pull request details with authorization check"""
        
        # Get PR from database
        pr_data = await supabase_service.get_pull_request(pr_id)
        if not pr_data:
            raise Exception("Pull request not found")
        
        # Simple authorization check (user owns PR)
        if pr_data['user_id'] != user_id:
            raise Exception("Not authorized to view this pull request")
        
        # Get file details (not needed for basic response but available for future use)
        file_details = await supabase_service.get_pull_request_files(pr_id)
        
        return self._convert_to_pr_response(pr_data)
    
    async def check_sync_status(self, fork_id: str, user_id: str) -> SyncStatus:
        """Check if fork is behind master and needs sync"""
        
        # Validate ownership
        await self._validate_and_authorize(fork_id, user_id)
        
        return await self._check_sync_status(fork_id)
    
    async def sync_fork(self, fork_id: str, user_id: str) -> Dict[str, Any]:
        """Sync fork with master when behind"""
        
        # Validate ownership
        await self._validate_and_authorize(fork_id, user_id)
        
        sync_status = await self._check_sync_status(fork_id)
        if not sync_status.is_behind:
            return {
                "success": True,
                "message": "Fork is already up to date",
                "synced_files": []
            }
        
        # Perform sync
        return await self._perform_fork_sync(fork_id, sync_status)
    
    async def list_pull_requests(
        self,
        user_id: Optional[str] = None,
        playbook_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[PRResponse]:
        """List pull requests with filters"""
        
        prs_data = await supabase_service.list_pull_requests(
            playbook_id=playbook_id,
            user_id=user_id,
            status=status,
            limit=limit,
            offset=offset
        )
        
        return [self._convert_to_pr_response(pr_data) for pr_data in prs_data]
    
    async def list_pull_requests_for_owner(
        self,
        owner_id: str,
        playbook_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[PRResponse]:
        """List pull requests targeting playbooks owned by user"""
        
        # Get playbooks owned by user
        owned_playbooks = await supabase_service.list_playbooks(owner_id=owner_id)
        owned_playbook_ids = [pb['id'] for pb in owned_playbooks]
        
        if not owned_playbook_ids:
            return []
        
        # Get PRs targeting owned playbooks
        all_prs = []
        for playbook_id_owned in owned_playbook_ids:
            if playbook_id and playbook_id_owned != playbook_id:
                continue  # Skip if filtering by specific playbook
            
            prs_data = await supabase_service.list_pull_requests(
                playbook_id=playbook_id_owned,
                status=status,
                limit=limit,
                offset=offset
            )
            all_prs.extend(prs_data)
        
        # Remove duplicates and sort
        unique_prs = {pr['id']: pr for pr in all_prs}.values()
        sorted_prs = sorted(unique_prs, key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Apply pagination
        paginated = sorted_prs[offset:offset + limit]
        
        return [self._convert_to_pr_response(pr_data) for pr_data in paginated]
    
    # ========================================
    # Private helper methods
    # ========================================
    
    def _convert_to_pr_response(self, pr_data: Dict[str, Any]) -> PRResponse:
        """Convert database PR data to PRResponse model"""
        from datetime import datetime
        
        # Parse timestamps if they're strings
        created_at = pr_data['created_at']
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            
        updated_at = pr_data['updated_at']
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
            
        merged_at = pr_data.get('merged_at')
        if merged_at and isinstance(merged_at, str):
            merged_at = datetime.fromisoformat(merged_at.replace('Z', '+00:00'))
            
        closed_at = pr_data.get('closed_at')
        if closed_at and isinstance(closed_at, str):
            closed_at = datetime.fromisoformat(closed_at.replace('Z', '+00:00'))
        
        return PRResponse(
            id=pr_data['id'],
            fork_id=pr_data['fork_id'],
            user_id=pr_data['user_id'],
            target_playbook_id=pr_data['target_playbook_id'],
            title=pr_data['title'],
            description=pr_data.get('description'),
            commit_message=pr_data['commit_message'],
            status=pr_data['status'],
            file_changes=pr_data['file_changes'],
            summary=pr_data.get('summary'),
            change_summary=pr_data.get('change_summary'),
            diff_summary=pr_data.get('diff_summary'),
            risk_flags=pr_data.get('risk_flags', []),
            merge_checklist=pr_data.get('merge_checklist', []),
            created_at=created_at,
            updated_at=updated_at,
            merged_at=merged_at,
            closed_at=closed_at
        )
    
    async def _validate_and_authorize(self, fork_id: str, user_id: str) -> Dict[str, Any]:
        """Validate fork exists and user owns it"""
        
        fork_data = await supabase_service.get_user_playbook(fork_id)
        if not fork_data:
            raise Exception("Fork not found")
        
        if fork_data['user_id'] != user_id:
            raise Exception("Not authorized to access this fork")
        
        return fork_data
    
    async def _check_sync_status(self, fork_id: str) -> SyncStatus:
        """Check if fork is behind master"""
        
        # Get fork info from user_playbooks table
        fork_data = await supabase_service.get_user_playbook(fork_id)
        
        # Get master playbook info  
        master_playbook = await supabase_service.get_playbook(fork_data['original_playbook_id'])
        
        base_version = fork_data.get('base_version', 1)
        last_sync_version = fork_data.get('last_sync_version', 1)
        master_latest_version = master_playbook.get('latest_version', 1)
        
        is_behind = last_sync_version < master_latest_version
        
        files_to_sync = []
        if is_behind:
            # Get files that changed in master since last sync
            files_to_sync = await self._get_changed_files_since_version(
                fork_data['original_playbook_id'], 
                last_sync_version
            )
        
        return SyncStatus(
            fork_id=fork_id,
            is_behind=is_behind,
            base_version=base_version,
            master_latest_version=master_latest_version,
            last_sync_version=last_sync_version,
            files_to_sync=files_to_sync,
            conflicts=[]  # TODO: Implement conflict detection
        )
    
    async def _normalize_file_changes(
        self, 
        fork_id: str, 
        file_changes: List[FileChangeRequest]
    ) -> List[Dict[str, Any]]:
        """Normalize file changes and compute checksums"""
        
        normalized = []
        
        for change in file_changes:
            # Compute checksum for new content
            checksum_new = None
            if change.content:
                checksum_new = hashlib.md5(change.content.encode('utf-8')).hexdigest()
            
            # Get existing file info if it exists
            existing_file = await self._get_fork_file_by_path(fork_id, change.file_path)
            checksum_old = existing_file.get('checksum') if existing_file else None
            
            normalized.append({
                'file_path': change.file_path,
                'content': change.content,
                'change_type': change.change_type,
                'checksum_old': checksum_old,
                'checksum_new': checksum_new,
                'existing_file': existing_file
            })
        
        return normalized
    
    async def _generate_diffs(
        self, 
        fork_id: str, 
        normalized_changes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate diffs for all file changes"""
        
        diff_results = []
        
        # Get fork and master info
        fork_data = await supabase_service.get_user_playbook(fork_id)
        master_playbook_id = fork_data['original_playbook_id']
        
        for change in normalized_changes:
            file_path = change['file_path']
            
            # Get master file content
            master_file = await self._get_master_file_by_path(master_playbook_id, file_path)
            main_content = await self._get_file_content(master_file) if master_file else None
            
            # Get current fork file content
            fork_content = await self._get_file_content(change['existing_file']) if change['existing_file'] else None
            
            # Generate diff
            diff_text = self._compute_diff(
                main_content or "",
                change.get('content', ''),
                file_path
            )
            
            diff_results.append({
                'file_path': file_path,
                'change_type': change['change_type'],
                'main_content': main_content,
                'fork_content': fork_content,
                'user_content': change.get('content', ''),
                'diff_text': diff_text,
                'checksum_old': change['checksum_old'],
                'checksum_new': change['checksum_new'],
                'main_file_id': master_file.get('id') if master_file else None,
                'fork_file_id': change['existing_file'].get('id') if change['existing_file'] else None
            })
        
        return diff_results
    
    def _compute_diff(self, content_a: str, content_b: str, file_path: str) -> str:
        """Compute unified diff between two content strings"""
        
        if not content_a and not content_b:
            return "No changes"
        
        lines_a = content_a.splitlines(keepends=True)
        lines_b = content_b.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            lines_a, 
            lines_b,
            fromfile=f"master/{file_path}",
            tofile=f"fork/{file_path}",
            lineterm=""
        )
        
        return ''.join(diff)
    
    async def _persist_pull_request(
        self,
        pr_request: PRCreateRequest,
        user_id: str,
        diff_results: List[Dict[str, Any]],
        file_analyses: List[FileChangeAnalysis],
        pr_analysis: PRAnalysis
    ) -> PRResponse:
        """Persist PR and file details to database"""
        
        # Get fork and target info
        fork_data = await supabase_service.get_user_playbook(pr_request.fork_id)
        target_playbook_id = fork_data['original_playbook_id']
        
        # Aggregate risk flags
        all_risk_flags = []
        for analysis in file_analyses:
            all_risk_flags.extend(analysis.risk_flags)
        risk_flags = list(set(all_risk_flags))  # Remove duplicates
        
        # Create file changes array for comprehensive schema
        file_changes_array = []
        for i, diff_result in enumerate(diff_results):
            analysis = file_analyses[i] if i < len(file_analyses) else None
            file_changes_array.append({
                'file_path': diff_result['file_path'],
                'change_type': diff_result['change_type'],
                'changelog': analysis.changelog if analysis else "File changed",
                'risk_flags': analysis.risk_flags if analysis else [],
                'confidence': analysis.confidence if analysis else 0.6,
                'diff_text': diff_result.get('diff_text', ''),
                'checksum_old': diff_result.get('checksum_old', ''),
                'checksum_new': diff_result.get('checksum_new', '')
            })
        
        # Create PR record using comprehensive schema
        pr_data = {
            'fork_id': pr_request.fork_id,  # References user_playbooks id
            'user_id': user_id,
            'target_playbook_id': target_playbook_id,
            'title': pr_request.title,
            'description': pr_request.description,
            'commit_message': pr_request.commit_message,
            'status': 'open',
            'file_changes': file_changes_array,  # JSONB array
            'summary': pr_analysis.pr_title,
            'change_summary': pr_analysis.pr_description,
            'diff_summary': self._create_diff_summary(file_analyses),
            'risk_flags': risk_flags,
            'merge_checklist': pr_analysis.merge_checklist
        }
        
        # Insert PR
        pr_record = await supabase_service.create_pull_request(pr_data)
        pr_id = pr_record['id']
        
        # Insert PR files using comprehensive schema
        for i, diff_result in enumerate(diff_results):
            analysis = file_analyses[i] if i < len(file_analyses) else None
            
            file_data = {
                'pr_id': pr_id,
                'file_path': diff_result['file_path'],
                'change_type': diff_result['change_type'],
                'main_file_id': diff_result.get('main_file_id'),
                'fork_file_id': diff_result.get('fork_file_id'),
                'diff_text': diff_result.get('diff_text', ''),
                'diff_summary': analysis.changelog if analysis else "File changed",
                'risk_flags': analysis.risk_flags if analysis else [],
                'confidence': analysis.confidence if analysis else 0.8,
                'checksum_old': diff_result.get('checksum_old', ''),
                'checksum_new': diff_result.get('checksum_new', '')
            }
            
            await supabase_service.create_pull_request_file(file_data)
        
        return self._convert_to_pr_response(pr_record)
    
    def _create_diff_summary(self, file_analyses: List[FileChangeAnalysis]) -> str:
        """Create combined diff summary from file analyses"""
        summaries = []
        for analysis in file_analyses:
            summaries.append(f"• {analysis.file_path}: {analysis.changelog}")
        return "\n".join(summaries)
    
    async def _get_fork_file_by_path(self, fork_id: str, file_path: str) -> Optional[Dict[str, Any]]:
        """Get fork file by path"""
        try:
            return await supabase_service.get_user_playbook_file_by_path(fork_id, file_path)
        except:
            return None
    
    async def _get_master_file_by_path(self, playbook_id: str, file_path: str) -> Optional[Dict[str, Any]]:
        """Get master file by path (using file_name)"""
        try:
            return await supabase_service.get_playbook_file_by_name(playbook_id, file_path)
        except:
            return None
    
    async def _get_file_content(self, file_record: Dict[str, Any]) -> Optional[str]:
        """Get file content from storage"""
        if not file_record:
            return None
        
        try:
            # Determine bucket based on file type
            if 'user_playbook_id' in file_record:
                bucket = 'user-playbooks'
            else:
                bucket = 'playbooks'
            
            # Download file content
            file_content = supabase_service.client.storage.from_(bucket).download(
                file_record['storage_path']
            )
            
            # Try to decode as text
            if isinstance(file_content, bytes):
                return file_content.decode('utf-8')
            return str(file_content)
            
        except Exception as e:
            print(f"Failed to get file content: {e}")
            return None
    
    async def _get_changed_files_since_version(
        self, 
        playbook_id: str, 
        since_version: int
    ) -> List[Dict[str, Any]]:
        """Get files that changed in master since given version"""
        # TODO: Implement version-based file tracking
        # For now, return empty list
        return []
    
    async def _perform_fork_sync(
        self, 
        fork_id: str, 
        sync_status: SyncStatus
    ) -> Dict[str, Any]:
        """Perform actual fork synchronization"""
        # TODO: Implement 3-way merge logic
        # For now, return mock success
        return {
            "success": True,
            "message": "Sync functionality coming soon",
            "synced_files": []
        }


# Global instance
pr_service = PRService()