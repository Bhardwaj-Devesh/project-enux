from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form, Request
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
import uuid
import asyncio
from app.models.playbook import (
    PlaybookCreate, PlaybookResponse, PlaybookUpdate, 
    PlaybookSearch, PlaybookSearchResult, PlaybookUploadResponse,
    FileUpload, ProcessingStatus, PlaybookForkRequest, PlaybookForkResponse,
    UserPlaybookResponse, PlaybookFileCreate, PlaybookFileResponse, PlaybookFileUpdate,
    PlaybookWithForkInfo, PlaybookDetailedResponse, NotificationResponse,
    PlaybookStarRequest, PlaybookStarResponse, PlaybookViewRequest, PlaybookViewResponse,
    PopularPlaybookResponse, MarkNotificationsReadRequest, MarkNotificationsReadResponse,
    MarkAllNotificationsReadResponse, NotificationCountResponse
)
from app.models.auth import TokenData
from app.api.dependencies import get_current_user, get_optional_user, get_authenticated_user
from app.services.supabase_service import supabase_service
from app.services.ai_service import ai_service
from app.services.vector_service import vector_service
from app.services.download_service import download_service
from app.config import settings
import json
import io
from datetime import datetime


router = APIRouter(prefix="/playbooks", tags=["playbooks"])


def convert_vector_embedding(playbook_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert vector_embedding from string to list if needed"""
    if playbook_data.get('vector_embedding') and isinstance(playbook_data['vector_embedding'], str):
        try:
            playbook_data['vector_embedding'] = json.loads(playbook_data['vector_embedding'])
        except (json.JSONDecodeError, TypeError):
            playbook_data['vector_embedding'] = None
    return playbook_data


def ensure_datetime_fields(playbook_data: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure created_at and updated_at fields are valid datetime objects"""
    from datetime import datetime
    
    # Handle created_at
    if not playbook_data.get('created_at'):
        playbook_data['created_at'] = datetime.utcnow()
    elif isinstance(playbook_data['created_at'], str):
        try:
            playbook_data['created_at'] = datetime.fromisoformat(playbook_data['created_at'].replace('Z', '+00:00'))
        except (ValueError, TypeError):
            playbook_data['created_at'] = datetime.utcnow()
    
    # Handle updated_at
    if not playbook_data.get('updated_at'):
        playbook_data['updated_at'] = datetime.utcnow()
    elif isinstance(playbook_data['updated_at'], str):
        try:
            playbook_data['updated_at'] = datetime.fromisoformat(playbook_data['updated_at'].replace('Z', '+00:00'))
        except (ValueError, TypeError):
            playbook_data['updated_at'] = datetime.utcnow()
    
    return playbook_data


@router.post("/upload", response_model=PlaybookUploadResponse)
async def upload_playbook(
    title: str = Form(...),
    description: str = Form(...),
    blog_content: Optional[str] = Form(None),
    files: List[UploadFile] = File(...),
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Upload a new playbook with files (Authentication required)"""
    try:
        # Validate file size and type
        total_size = 0
        for file in files:
            total_size += len(await file.read())
            await file.seek(0)  # Reset file pointer
        
        if total_size > settings.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Total file size exceeds {settings.max_file_size} bytes"
            )
        
        # Create playbook data
        playbook_data = {
            "title": title,
            "description": description,
            "blog_content": blog_content,
            "tags": [],  # Will be calculated by LLM
            "version": "v1",  # Initial version
            "latest_version": 1,  # Initial version number
            "current_version": 1,  # Initial version number
            "owner_id": current_user.user_id,
            "files": {},
            "summary": None,
            "vector_embedding": None
        }
        
        # Upload files to storage and create playbook_files entries
        uploaded_files = []
        playbook_files_data = []
        files_with_content = []  # Store files with their content for AI processing
        
        for file in files:
            print(f"📁 Processing file: {file.filename} ({file.content_type})")
            
            if file.content_type not in settings.allowed_file_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type {file.content_type} not allowed"
                )
            
            # Generate unique file path with new structure: playbook/{{user_id}}/version/filename
            file_id = str(uuid.uuid4())
            file_extension = settings.file_extensions.get(file.content_type, "")
            # New folder structure: playbook/{{user_id}}/version/filename
            file_path = f"playbook/{current_user.user_id}/v1/{file_id}{file_extension}"
            
            # Read file content once and store it
            file_content = await file.read()
            print(f"📊 Read {len(file_content)} bytes from {file.filename}")
            
            # Upload to Supabase Storage
            file_url = await supabase_service.upload_file_to_storage(
                file_path, file_content, file.content_type
            )
            print(f"✅ Uploaded {file.filename} to storage")
            
            # Store file info for playbook
            playbook_data["files"][file.filename] = file_url
            uploaded_files.append(FileUpload(
                filename=file.filename,
                content_type=file.content_type,
                size=len(file_content),
                file_path=file_path
            ))
            
            # Store file with content for AI processing
            files_with_content.append({
                "file": file,
                "content": file_content,
                "filename": file.filename,
                "content_type": file.content_type
            })
            
            # Prepare data for playbook_files table
            file_type = file.content_type.split('/')[-1] if '/' in file.content_type else 'txt'
            playbook_files_data.append({
                "file_name": file.filename,
                "file_type": file_type,
                "storage_path": file_url,
                # "file_size": len(file_content),  # Temporarily removed due to missing column
                "uploaded_by": current_user.user_id,
                "version_created": 1,  # Initial version
                "is_active": True
            })
        
        # Extract text content from files for vector storage (using stored content)
        files_for_vector_storage = []
        for file_info in files_with_content:
            try:
                # Extract text content for embedding
                text_content = await ai_service.extract_text_from_file(
                    file_info["content"],
                    file_info["filename"],
                    file_info["content_type"]
                )
            
                files_for_vector_storage.append({
                    "filename": file_info["filename"],
                    "content": text_content,
                    "content_type": file_info["content_type"]
                })
                print(f"✅ Extracted text from {file_info['filename']} for vector storage")
            except Exception as e:
                print(f"⚠️ Failed to extract text from {file_info['filename']}: {e}")
                continue
        
        # Create playbook in database first to get the ID
        playbook = await supabase_service.create_playbook(playbook_data)
        
        if not playbook:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create playbook"
            )
        
        # Create playbook_files entries for all uploaded files
        # for file_data in playbook_files_data:
        #     file_data["playbook_id"] = playbook["id"]
        #     await supabase_service.create_playbook_file(file_data)
        
        # Process files with AI synchronously to get tags and summary (fast response)
        print(f"🚀 Starting synchronous AI processing for {len(files_with_content)} files...")
        
        # Prepare files for AI processing
        files_for_ai = []
        for file_info in files_with_content:
            try:
                files_for_ai.append({
                    "filename": file_info["filename"],
                    "content": file_info["content"],
                    "content_type": file_info["content_type"]
                })
                print(f"✅ Prepared {file_info['filename']} for AI processing")
            except Exception as e:
                print(f"⚠️ Failed to prepare {file_info['filename']}: {e}")
                continue
        
        # Process with AI to get tags, summary, and stage (synchronous - fast)
        ai_results = await ai_service.process_playbook_files(files_for_ai, title, description, blog_content)
        
        print(f"✅ Synchronous AI processing completed")
        print(f"📝 Summary: {ai_results['summary'][:100]}...")
        print(f"🏷️ Tags: {ai_results['tags']}")
        print(f"📈 Stage: {ai_results['stage']}")
        
        # Update playbook with AI results immediately (without embedding)
        update_data = {
            "summary": ai_results["summary"],
            "tags": ai_results["tags"],
            "stage": ai_results["stage"],
            "vector_embedding": None  # Will be updated in background
        }
        
        print(f"💾 Updating playbook {playbook['id']} with AI results...")
        updated_playbook = await supabase_service.update_playbook(playbook["id"], update_data)
        
        # Start background embedding processing
        print(f"🔄 Starting background embedding processing...")
        # Use the already extracted text from files_for_vector_storage
        all_text = ""
        for file_info in files_for_vector_storage:
            all_text += f"\n\n--- {file_info['filename']} ---\n{file_info['content']}"
        
        # Start background task for embedding
        asyncio.create_task(
            ai_service.process_playbook_embedding_background(
                playbook["id"], 
                title, 
                description, 
                all_text, 
                blog_content
            )
        )
        
        # Store individual file vectors for search functionality
        print(f"🔍 Storing file vectors for search...")
        try:
            vector_storage_result = await vector_service.store_file_vectors(
                files_for_vector_storage, 
                playbook["id"]
            )
            
            if vector_storage_result["success"]:
                print(f"✅ Stored vectors for {vector_storage_result['stored_count']} files")
            else:
                print(f"⚠️ Vector storage failed: {vector_storage_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"⚠️ Failed to store file vectors: {e}")
        
        # Convert vector_embedding from string to list if needed
        updated_playbook = convert_vector_embedding(updated_playbook)
        
        return PlaybookUploadResponse(
            playbook=PlaybookResponse(**updated_playbook),
            files=uploaded_files,
            processing_status="completed",
            message="Playbook uploaded successfully with AI insights. Vector embedding processing in background."
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def process_playbook_ai_with_content(playbook_id: str, files_with_content: List[Dict], title: str, description: str, blog_content: Optional[str] = None):
    """Process playbook files with AI in background using files with content already available"""
    try:
        print(f"🤖 Starting AI processing for playbook {playbook_id}")
        
        # Prepare files for AI processing using stored content
        files_for_ai = []
        for file_info in files_with_content:
            try:
                files_for_ai.append({
                    "filename": file_info["filename"],
                    "content": file_info["content"],
                    "content_type": file_info["content_type"]
                })
                print(f"✅ Prepared {file_info['filename']} for AI processing")
            except Exception as e:
                print(f"⚠️ Failed to prepare {file_info['filename']}: {e}")
                continue
        
        if not files_for_ai:
            print(f"❌ No files available for AI processing for playbook {playbook_id}")
            return
        
        print(f"📊 Processing {len(files_for_ai)} files with AI...")
        
        # Process with AI (include blog_content in processing)
        ai_results = await ai_service.process_playbook_files(files_for_ai, title, description, blog_content)
        
        print(f"✅ AI processing completed for playbook {playbook_id}")
        print(f"📝 Summary: {ai_results['summary'][:100]}...")
        print(f"🏷️ Tags: {ai_results['tags']}")
        print(f"📈 Stage: {ai_results['stage']}")
        print(f"🔢 Embedding dimensions: {len(ai_results['embedding'])}")
        
        # Update playbook with AI results
        update_data = {
            "summary": ai_results["summary"],
            "tags": ai_results["tags"],
            "stage": ai_results["stage"],
            "vector_embedding": ai_results["embedding"]
        }
        
        print(f"💾 Updating playbook {playbook_id} with AI results...")
        await supabase_service.update_playbook(playbook_id, update_data)
        print(f"✅ Playbook {playbook_id} updated successfully with vector embedding")
        
    except Exception as e:
        print(f"❌ Error processing playbook {playbook_id}: {str(e)}")
        # Try to update with error information
        try:
            error_update = {
                "summary": f"AI processing failed: {str(e)}",
                "tags": ["error", "processing-failed"],
                "stage": "unknown"
            }
            await supabase_service.update_playbook(playbook_id, error_update)
        except:
            pass


async def store_file_vectors_for_playbook(playbook_id: str, files_with_content: List[Dict]):
    """Store individual file vectors for search functionality"""
    print(f"🔍 Storing file vectors for search...")
    try:
        from app.services.vector_service import vector_service
        
        # Prepare files for vector storage
        files_for_vector_storage = []
        for file_info in files_with_content:
            try:
                text_content = await ai_service.extract_text_from_file(
                    file_info["content"],
                    file_info["filename"],
                    file_info["content_type"]
                )
                files_for_vector_storage.append({
                    "filename": file_info["filename"],
                    "content": text_content,
                    "content_type": file_info["content_type"]
                })
                print(f"✅ Extracted text from {file_info['filename']} for vector storage")
            except Exception as e:
                print(f"⚠️ Failed to extract text from {file_info['filename']}: {e}")
                continue
        
        # Store vectors for each file
        if files_for_vector_storage:
            await vector_service.store_file_vectors(playbook_id, files_for_vector_storage)
            print(f"✅ Stored vectors for {len(files_for_vector_storage)} files")
        else:
            print(f"⚠️ No files available for vector storage")
            
    except Exception as e:
        print(f"⚠️ Failed to store file vectors: {e}")
        # Continue processing even if vector storage fails


async def process_playbook_ai(playbook_id: str, files: List[FileUpload], title: str, description: str, blog_content: Optional[str] = None):
    """Process playbook files with AI in background (legacy function for when files need to be downloaded)"""
    try:
        print(f"🤖 Starting AI processing for playbook {playbook_id}")
        
        # Prepare files for AI processing
        files_for_ai = []
        for file_info in files:
            try:
                # Download file content for AI processing
                file_content = await supabase_service.client.storage.from_(
                    settings.storage_bucket_name
                ).download(file_info.file_path)
                
                files_for_ai.append({
                    "filename": file_info.filename,
                    "content": file_content,
                    "content_type": file_info.content_type
                })
                print(f"✅ Downloaded {file_info.filename} for AI processing")
            except Exception as e:
                print(f"⚠️ Failed to download {file_info.filename}: {e}")
                continue
        
        if not files_for_ai:
            print(f"❌ No files available for AI processing for playbook {playbook_id}")
            return
        
        print(f"📊 Processing {len(files_for_ai)} files with AI...")
        
        # Process with AI (include blog_content in processing)
        ai_results = await ai_service.process_playbook_files(files_for_ai, title, description, blog_content)
        
        print(f"✅ AI processing completed for playbook {playbook_id}")
        print(f"📝 Summary: {ai_results['summary'][:100]}...")
        print(f"🏷️ Tags: {ai_results['tags']}")
        print(f"📈 Stage: {ai_results['stage']}")
        print(f"🔢 Embedding dimensions: {len(ai_results['embedding'])}")
        
        # Update playbook with AI results
        update_data = {
            "summary": ai_results["summary"],
            "tags": ai_results["tags"],
            "stage": ai_results["stage"],
            "vector_embedding": ai_results["embedding"]
        }
        
        print(f"💾 Updating playbook {playbook_id} with AI results...")
        await supabase_service.update_playbook(playbook_id, update_data)
        print(f"✅ Playbook {playbook_id} updated successfully with vector embedding")
        
    except Exception as e:
        print(f"❌ Error processing playbook {playbook_id}: {str(e)}")
        # Try to update with error information
        try:
            error_update = {
                "summary": f"AI processing failed: {str(e)}",
                "tags": ["error", "processing-failed"],
                "stage": "unknown"
            }
            await supabase_service.update_playbook(playbook_id, error_update)
        except:
            pass


@router.get("/", response_model=List[PlaybookResponse])
async def get_playbooks(
    limit: int = 50,
    offset: int = 0,
    current_user: Optional[TokenData] = Depends(get_optional_user)
):
    """Get all playbooks (public, but authenticated users see their own playbooks)"""
    try:
        user_id = current_user.user_id if current_user else None
        playbooks = await supabase_service.get_playbooks(user_id, limit, offset)
        return [PlaybookResponse(**convert_vector_embedding(playbook)) for playbook in playbooks]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/my-playbooks", response_model=List[PlaybookResponse])
async def get_my_playbooks(
    limit: int = 50,
    offset: int = 0,
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Get playbooks owned by the current user"""
    try:
        user_id = current_user.user_id
        playbooks = await supabase_service.get_playbooks_by_user_detailed(user_id, limit, offset)
        
        # Remove vector_embedding from response to reduce payload size
        cleaned_playbooks = []
        for playbook in playbooks:
            # Create a copy without vector_embedding
            playbook_copy = playbook.copy()
            if 'vector_embedding' in playbook_copy:
                del playbook_copy['vector_embedding']
            cleaned_playbooks.append(PlaybookResponse(**playbook_copy))
        
        return cleaned_playbooks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/my-playbooks-enhanced", response_model=List[PlaybookWithForkInfo])
async def get_my_playbooks_enhanced(
    limit: int = 50,
    offset: int = 0,
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Get playbooks owned by the current user with fork information"""
    try:
        user_id = current_user.user_id
        playbooks = await supabase_service.get_playbooks_with_fork_info(user_id, limit, offset)
        
        # Remove vector_embedding from response to reduce payload size
        cleaned_playbooks = []
        for playbook in playbooks:
            # Create a copy without vector_embedding
            playbook_copy = playbook.copy()
            if 'vector_embedding' in playbook_copy:
                del playbook_copy['vector_embedding']
            cleaned_playbooks.append(PlaybookWithForkInfo(**playbook_copy))
        
        return cleaned_playbooks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/my-forks", response_model=List[PlaybookWithForkInfo])
async def get_my_forks(
    limit: int = 50,
    offset: int = 0,
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Get playbooks forked by the current user"""
    try:
        user_id = current_user.user_id
        forked_playbooks = await supabase_service.get_user_playbooks_with_fork_info(user_id, limit, offset)
        
        # Remove vector_embedding from response to reduce payload size
        cleaned_playbooks = []
        for playbook in forked_playbooks:
            # Create a copy without vector_embedding
            playbook_copy = playbook.copy()
            if 'vector_embedding' in playbook_copy:
                del playbook_copy['vector_embedding']
            cleaned_playbooks.append(PlaybookWithForkInfo(**playbook_copy))
        
        return cleaned_playbooks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/my-playbooks-combined", response_model=List[PlaybookWithForkInfo])
async def get_my_playbooks_combined(
    limit: int = 50,
    offset: int = 0,
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Get both owned and forked playbooks for the current user"""
    try:
        user_id = current_user.user_id
        combined_playbooks = await supabase_service.get_combined_user_playbooks(user_id, limit, offset)
        
        # Remove vector_embedding from response to reduce payload size
        cleaned_playbooks = []
        for playbook in combined_playbooks:
            # Create a copy without vector_embedding
            playbook_copy = playbook.copy()
            if 'vector_embedding' in playbook_copy:
                del playbook_copy['vector_embedding']
            cleaned_playbooks.append(PlaybookWithForkInfo(**playbook_copy))
        
        return cleaned_playbooks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    limit: int = 20,
    offset: int = 0,
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Get notifications for the current user (fork events on their playbooks)"""
    try:
        user_id = current_user.user_id
        notifications = await supabase_service.get_user_notifications(user_id, limit, offset)
        
        # Filter out any notifications with missing required fields
        valid_notifications = []
        for notification in notifications:
            try:
                # Validate that all required fields are present
                if all([
                    notification.get('playbook_id'),
                    notification.get('playbook_title'),
                    notification.get('user_id'),
                    notification.get('user_email'),
                    notification.get('user_full_name')
                ]):
                    valid_notifications.append(NotificationResponse(**notification))
                else:
                    print(f"Skipping invalid notification: {notification}")
            except Exception as validation_error:
                print(f"Validation error for notification: {validation_error}")
                continue
        
        return valid_notifications
    except Exception as e:
        print(f"Error in get_notifications endpoint: {str(e)}")
        # Return empty list instead of error to prevent API failure
        return []


@router.get("/notifications/count", response_model=NotificationCountResponse)
async def get_notification_count(
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Get notification count for the current user"""
    try:
        user_id = current_user.user_id
        count_data = await supabase_service.get_notification_count(user_id)
        
        return NotificationCountResponse(**count_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/popular", response_model=List[PopularPlaybookResponse])
async def get_popular_playbooks(
    limit: int = 10,
    current_user: Optional[TokenData] = Depends(get_optional_user)
):
    """Get most popular playbooks"""
    try:
        popular_playbooks = await supabase_service.get_popular_playbooks(limit)
        
        # Transform the response to match PopularPlaybookResponse model
        response_playbooks = []
        for playbook_data in popular_playbooks:
            popular_response = PopularPlaybookResponse(
                playbook_id=playbook_data['id'],
                title=playbook_data['title'],
                description=playbook_data['description'],
                star_count=playbook_data['star_count'],
                view_count=playbook_data['view_count'],
                created_at=playbook_data['created_at']
            )
            response_playbooks.append(popular_response)
        
        return response_playbooks
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/{playbook_id}")
async def get_playbook(
    playbook_id: str,
    current_user: Optional[TokenData] = Depends(get_optional_user),
    request: Request = None
):
    """Get a specific playbook"""
    try:
        playbook = await supabase_service.get_playbook(playbook_id)
        if not playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook not found"
            )
        
        # Record view (in background to avoid blocking the response)
        try:
            # Record the view asynchronously
            import asyncio
            asyncio.create_task(
                supabase_service.record_playbook_view(
                    playbook_id=playbook_id,
                    user_id=current_user.user_id if current_user else None
                )
            )
        except Exception as view_error:
            # Don't fail the request if view recording fails
            print(f"Warning: Failed to record view for playbook {playbook_id}: {view_error}")
        
        # Convert and exclude vector_embedding from response
        playbook_data = convert_vector_embedding(playbook)
        if 'vector_embedding' in playbook_data:
            del playbook_data['vector_embedding']
        
        return playbook_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{playbook_id}/detailed", response_model=PlaybookDetailedResponse)
async def get_playbook_detailed(playbook_id: str):
    """Get a specific playbook with detailed fork information"""
    try:
        playbook = await supabase_service.get_playbook_detailed(playbook_id)
        if not playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook not found"
            )
        
        # Convert and exclude vector_embedding from response
        playbook_data = convert_vector_embedding(playbook)
        if 'vector_embedding' in playbook_data:
            del playbook_data['vector_embedding']
        
        return PlaybookDetailedResponse(**playbook_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{playbook_id}/forks")
async def get_playbook_forks(
    playbook_id: str,
    limit: int = 20,
    offset: int = 0
):
    """Get list of users who forked a specific playbook"""
    try:
        # Verify playbook exists
        playbook = await supabase_service.get_playbook(playbook_id)
        if not playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook not found"
            )
        
        # Get fork information
        forks = await supabase_service.get_playbook_forks(playbook_id, limit, offset)
        
        # Transform the response
        fork_list = []
        for fork in forks:
            user_info = fork.get('users', {}) or {}
            # Only include forks with valid user data
            if user_info.get('id') and user_info.get('email'):
                fork_info = {
                    'user_id': user_info.get('id'),
                    'user_email': user_info.get('email'),
                    'user_full_name': user_info.get('full_name') or user_info.get('email'),
                    'forked_at': fork['forked_at'],
                    'version': fork['version']
                }
                fork_list.append(fork_info)
        
        return {
            'playbook_id': playbook_id,
            'playbook_title': playbook['title'],
            'total_forks': len(fork_list),
            'forks': fork_list
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{playbook_id}", response_model=PlaybookResponse)
async def update_playbook(
    playbook_id: str,
    playbook_update: PlaybookUpdate,
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Update a playbook"""
    try:
        # Check if user owns the playbook
        playbook = await supabase_service.get_playbook(playbook_id)
        if not playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook not found"
            )
        
        if playbook["owner_id"] != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this playbook"
            )
        
        # Update playbook
        update_data = playbook_update.dict(exclude_unset=True)
        updated_playbook = await supabase_service.update_playbook(playbook_id, update_data)
        
        if not updated_playbook:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update playbook"
            )
        
        return PlaybookResponse(**convert_vector_embedding(updated_playbook))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{playbook_id}")
async def delete_playbook(
    playbook_id: str,
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Delete a playbook"""
    try:
        # Check if user owns the playbook
        playbook = await supabase_service.get_playbook(playbook_id)
        if not playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook not found"
            )
        
        if playbook["owner_id"] != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this playbook"
            )
        
        # Delete files from storage
        for file_path in playbook["files"].values():
            await supabase_service.delete_file_from_storage(file_path)
        
        # Delete file vectors from vector database
        await vector_service.delete_file_vectors(playbook_id)
        
        # Delete playbook from database
        await supabase_service.delete_playbook(playbook_id)
        
        return {"message": "Playbook deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/search/vector", response_model=List[PlaybookSearchResult])
async def search_playbooks_vector(
    query: str,
    limit: int = 10,
    current_user: Optional[TokenData] = Depends(get_optional_user)
):
    """Search playbooks using vector similarity"""
    try:
        print(f"🔍 Starting vector search for query: '{query}'")
        
        # Create embedding for query
        print("📊 Creating query embedding...")
        query_embedding = await ai_service.create_embedding(query)
        print(f"✅ Query embedding created with {len(query_embedding)} dimensions")
        
        # Search using vector similarity
        print("🔍 Searching playbooks using vector similarity...")
        results = await supabase_service.search_playbooks_vector(query_embedding, limit)
        print(f"✅ Found {len(results)} results")
        
        # Transform results
        search_results = []
        for result in results:
            try:
                # Ensure all required fields are present and valid
                playbook_data = convert_vector_embedding(result["playbook"])
                playbook_data = ensure_datetime_fields(playbook_data)
                
                search_results.append(PlaybookSearchResult(
                    playbook=PlaybookResponse(**playbook_data),
                    similarity_score=result["similarity"]
                ))
            except Exception as e:
                print(f"⚠️ Error processing search result: {e}")
                continue
        
        print(f"🎯 Returning {len(search_results)} processed results")
        return search_results
        
    except Exception as e:
        print(f"❌ Vector search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Vector search failed: {str(e)}"
        )


@router.get("/search/text", response_model=List[PlaybookResponse])
async def search_playbooks_text(
    query: str,
    tags: Optional[str] = None,  # Comma-separated tags
    stage: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
    current_user: Optional[TokenData] = Depends(get_optional_user)
):
    """Search playbooks using text search"""
    try:
        # Parse tags
        parsed_tags = None
        if tags:
            parsed_tags = [tag.strip() for tag in tags.split(",")]
        
        # Search using text
        results = await supabase_service.search_playbooks_text(
            query, parsed_tags, stage, limit, offset
        )
        
        return [PlaybookResponse(**convert_vector_embedding(playbook)) for playbook in results]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{playbook_id}/status", response_model=ProcessingStatus)
async def get_playbook_processing_status(playbook_id: str):
    """Get the processing status of a playbook"""
    try:
        playbook = await supabase_service.get_playbook(playbook_id)
        if not playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook not found"
            )
        
        # Determine status based on AI processing results
        if playbook.get("summary") and playbook.get("vector_embedding"):
            status = "completed"
            message = "AI processing completed successfully"
        elif playbook.get("summary") or playbook.get("vector_embedding"):
            status = "processing"
            message = "AI processing in progress"
        else:
            status = "processing"
            message = "AI processing started"
        
        # Convert vector_embedding if it's a string
        vector_embedding = playbook.get("vector_embedding")
        if vector_embedding and isinstance(vector_embedding, str):
            try:
                vector_embedding = json.loads(vector_embedding)
            except (json.JSONDecodeError, TypeError):
                vector_embedding = None
        
        return ProcessingStatus(
            status=status,
            message=message,
            summary=playbook.get("summary"),
            extracted_tags=playbook.get("tags"),
            vector_embedding=vector_embedding
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/search/files", response_model=List[Dict[str, Any]])
async def search_files_vector(
    query: str,
    limit: int = 10,
    current_user: Optional[TokenData] = Depends(get_optional_user)
):
    """Search files using vector similarity"""
    try:
        # Search files using vector similarity
        results = await vector_service.search_similar_files(query, limit)
        
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{playbook_id}/files", response_model=List[Dict[str, Any]])
async def get_playbook_files_vector(playbook_id: str):
    """Get all vector records for files in a specific playbook"""
    try:
        # Get file vectors for the playbook
        file_vectors = await vector_service.get_file_vectors_by_playbook(playbook_id)
        
        return file_vectors
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{playbook_id}/embedding-status")
async def get_playbook_embedding_status(playbook_id: str):
    """Get the embedding status of a playbook for debugging"""
    try:
        # Get playbook information
        playbook = await supabase_service.get_playbook(playbook_id)
        if not playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook not found"
            )
        
        # Get file vectors
        file_vectors = await vector_service.get_file_vectors_by_playbook(playbook_id)
        
        # Convert vector_embedding if it's a string
        vector_embedding = playbook.get("vector_embedding")
        if vector_embedding and isinstance(vector_embedding, str):
            try:
                vector_embedding = json.loads(vector_embedding)
            except (json.JSONDecodeError, TypeError):
                vector_embedding = None
        
        return {
            "playbook_id": playbook_id,
            "has_playbook_embedding": vector_embedding is not None,
            "playbook_embedding_dimensions": len(vector_embedding) if vector_embedding else 0,
            "file_vectors_count": len(file_vectors),
            "summary": playbook.get("summary"),
            "tags": playbook.get("tags"),
            "stage": playbook.get("stage"),
            "ai_processing_complete": bool(playbook.get("summary") and vector_embedding)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{playbook_id}/reprocess-ai")
async def reprocess_playbook_ai(
    playbook_id: str,
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Manually trigger AI processing for a playbook (for debugging)"""
    try:
        # Get playbook information
        playbook = await supabase_service.get_playbook(playbook_id)
        if not playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook not found"
            )
        
        # Check if user owns the playbook
        if playbook["owner_id"] != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to reprocess this playbook"
            )
        
        # Get playbook files
        playbook_files = await supabase_service.get_playbook_files(playbook_id)
        if not playbook_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No files found for this playbook"
            )
        
        # Prepare files for AI processing
        files_for_ai = []
        for file_data in playbook_files:
            try:
                # Download file content from storage
                file_content = supabase_service.client.storage.from_(
                    settings.storage_bucket_name
                ).download(file_data["storage_path"])
                
                files_for_ai.append({
                    "filename": file_data["file_name"],
                    "content": file_content,
                    "content_type": file_data["file_type"]
                })
            except Exception as e:
                print(f"⚠️ Failed to download {file_data['file_name']}: {e}")
                continue
        
        if not files_for_ai:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No files could be downloaded for AI processing"
            )
        
        # Process with AI
        ai_results = await ai_service.process_playbook_files(
            files_for_ai, 
            playbook["title"], 
            playbook["description"],
            playbook.get("blog_content")
        )
        
        # Update playbook with AI results
        update_data = {
            "summary": ai_results["summary"],
            "tags": ai_results["tags"],
            "stage": ai_results["stage"],
            "vector_embedding": ai_results["embedding"]
        }
        
        await supabase_service.update_playbook(playbook_id, update_data)
        
        return {
            "message": "AI processing completed successfully",
            "playbook_id": playbook_id,
            "summary": ai_results["summary"],
            "tags": ai_results["tags"],
            "stage": ai_results["stage"],
            "embedding_dimensions": len(ai_results["embedding"])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reprocess playbook: {str(e)}"
        )


@router.post("/fork", response_model=PlaybookForkResponse)
async def fork_playbook(
    fork_request: PlaybookForkRequest,
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Fork a playbook to user's workspace"""
    try:
        # Step 1: Validate input and get user ID from authentication
        user_id = current_user.user_id
        playbook_id = fork_request.playbook_id
        
        print(f"🍴 Forking playbook {playbook_id} for user: {user_id}")
        
        # Step 2: Validate original playbook exists
        original_playbook = await supabase_service.get_playbook(playbook_id)
        if not original_playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Original playbook not found"
            )
        
        # Step 3: Check if user is trying to fork their own playbook
        if original_playbook["owner_id"] == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot fork your own playbook"
            )
        
        # Step 4: Check if user already forked this playbook
        existing_forks = await supabase_service.get_user_playbooks(user_id)
        for fork in existing_forks:
            if fork['original_playbook_id'] == playbook_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="You have already forked this playbook"
                )
        
        # Step 5: Get latest version for forking
        from app.services.version_service import version_service
        latest_version = await version_service.get_latest_version_for_fork(playbook_id)
        
        # Step 6: Create new playbook record in playbooks table
        new_playbook_data = {
            "title": original_playbook["title"],
            "description": original_playbook["description"],
            "blog_content": original_playbook.get("blog_content"),
            "tags": original_playbook.get("tags", []),
            "stage": original_playbook.get("stage"),
            "owner_id": user_id,  # New owner is the forking user
            "version": f"v{latest_version}",  # Use the latest version from step 5
            "files": {},  # Will be populated with copied files
            "summary": original_playbook.get("summary"),
            # "vector_embedding": original_playbook.get("vector_embedding"),
            "is_fork": True,
            "original_playbook_id": playbook_id
        }
        
        # Create the new playbook record
        new_playbook = await supabase_service.create_playbook(new_playbook_data)
        
        if not new_playbook:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create new playbook record"
            )
        
        print(f"✅ Created new playbook record with ID: {new_playbook['id']}")
        
        # Step 7: Create new user playbook entry with version info
        user_playbook = await supabase_service.create_user_playbook_fork(
            user_id=user_id,
            original_playbook_id=new_playbook['id'],
            base_version=latest_version,  # Fork from latest version
            license=original_playbook.get('license')
        )
        
        if not user_playbook:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create playbook fork"
            )
        
        # Step 8: Copy files to both new playbook and user_playbook_files with version tracking
        original_files = await version_service.get_version_files(playbook_id, latest_version)
        
        if original_files:
            # Copy files to the new playbook record
            copied_playbook_files = await supabase_service.copy_playbook_files_to_new_playbook(
                new_playbook_id=new_playbook['id'],
                original_files=original_files,
                user_id=user_id
            )
            print(f"✅ Copied {len(copied_playbook_files)} files to new playbook")
            
            # Update the new playbook with files information
            files_dict = {}
            for file_data in copied_playbook_files:
                files_dict[file_data['file_name']] = file_data['storage_path']
            
            # Update playbook with files information
            await supabase_service.update_playbook(new_playbook['id'], {
                "files": files_dict
            })
            
            # Copy files to user_playbook_files for fork tracking
            copied_fork_files = await supabase_service.copy_playbook_files_with_version(
                user_playbook_id=user_playbook['id'],
                original_files=original_files,
                version_number=1  # Start with version 1 for fork
            )
            print(f"✅ Copied {len(copied_fork_files)} files to fork tracking")
        else:
            print("⚠️ No files found to copy to fork")
        
        # Step 9: Create notification for original playbook owner
        try:
            await supabase_service.create_fork_notification(
                original_playbook_id=playbook_id,
                forking_user_id=user_id,
                fork_id=user_playbook['id']
            )
        except Exception as notification_error:
            print(f"⚠️ Failed to create fork notification: {notification_error}")
            # Don't fail the fork if notification fails
        
        # Step 10: Generate playbook URL for redirect (use new playbook ID)
        new_playbook_url = f"/playbooks/{new_playbook['id']}"
        
        print(f"✅ Successfully forked playbook '{original_playbook['title']}' to {new_playbook_url}")
        
        return PlaybookForkResponse(
            status="success",
            new_playbook_id=new_playbook['id'],  # Return the new playbook ID
            new_playbook_url=new_playbook_url,
            message=f"Successfully forked playbook '{original_playbook['title']}'"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Fork error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fork playbook: {str(e)}"
        )


@router.get("/user/forks", response_model=List[UserPlaybookResponse])
async def get_user_playbook_forks(
    limit: int = 50,
    offset: int = 0,
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Get all playbook forks for a specific user"""
    try:
        # Use current authenticated user's ID
        user_id = current_user.user_id
        
        user_playbooks = await supabase_service.get_user_playbooks(user_id, limit, offset)
        
        # Transform response to match UserPlaybookResponse model
        response_data = []
        for up in user_playbooks:
            original_playbook = up.get('playbooks')
            response_data.append(UserPlaybookResponse(
                id=up['id'],
                user_id=up['user_id'],
                original_playbook_id=up['original_playbook_id'],
                forked_at=up['forked_at'],
                last_updated_at=up['last_updated_at'],
                version=up['version'],
                license=up.get('license'),
                status=up['status'],
                original_playbook=PlaybookResponse(
                    id=original_playbook['id'],
                    title=original_playbook['title'],
                    description=original_playbook['description'],
                    tags=original_playbook.get('tags', []),
                    stage=original_playbook.get('stage'),
                    owner_id="",  # Not needed for this context
                    version=original_playbook['version'],
                    files={},  # Files will be fetched separately if needed
                    created_at=original_playbook['created_at'],
                    updated_at=original_playbook['created_at']  # Use created_at as fallback
                ) if original_playbook else None
            ))
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user playbook forks: {str(e)}"
        )


@router.get("/user-playbooks/{user_playbook_id}", response_model=UserPlaybookResponse)
async def get_user_playbook(
    user_playbook_id: str,
    current_user: Optional[TokenData] = Depends(get_optional_user)
):
    """Get a specific user playbook fork by ID"""
    try:
        user_playbook = await supabase_service.get_user_playbook(user_playbook_id)
        
        if not user_playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User playbook not found"
            )
        
        original_playbook = user_playbook.get('playbooks')
        
        return UserPlaybookResponse(
            id=user_playbook['id'],
            user_id=user_playbook['user_id'],
            original_playbook_id=user_playbook['original_playbook_id'],
            forked_at=user_playbook['forked_at'],
            last_updated_at=user_playbook['last_updated_at'],
            version=user_playbook['version'],
            license=user_playbook.get('license'),
            status=user_playbook['status'],
            original_playbook=PlaybookResponse(
                id=original_playbook['id'],
                title=original_playbook['title'],
                description=original_playbook['description'],
                tags=original_playbook.get('tags', []),
                stage=original_playbook.get('stage'),
                owner_id="",  # Not needed for this context
                version=original_playbook['version'],
                files={},  # Files will be fetched separately if needed
                created_at=original_playbook['created_at'],
                updated_at=original_playbook['created_at']  # Use created_at as fallback
            ) if original_playbook else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user playbook: {str(e)}"
        )


@router.get("/user-playbooks/{user_playbook_id}/files", response_model=List[Dict[str, Any]])
async def get_user_playbook_files(
    user_playbook_id: str,
    current_user: Optional[TokenData] = Depends(get_optional_user)
):
    """Get all files associated with a user playbook"""
    try:
        # First check if user playbook exists
        user_playbook = await supabase_service.get_user_playbook(user_playbook_id)
        if not user_playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User playbook not found"
            )
        
        # Get files for the user playbook
        files = await supabase_service.get_user_playbook_files(user_playbook_id)
        
        # Transform files to include additional metadata
        file_list = []
        for file_data in files:
            file_info = {
                "id": file_data['id'],
                "file_path": file_data['file_path'],
                "file_type": file_data['file_type'],
                "storage_path": file_data['storage_path'],
                "uploaded_at": file_data['uploaded_at'],
                "last_modified_at": file_data['last_modified_at'],
                "version": file_data['version'],
                "download_url": file_data['storage_path']  # Can be used directly for download
            }
            file_list.append(file_info)
        
        return file_list
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user playbook files: {str(e)}"
        )


@router.get("/{playbook_id}/download")
async def download_original_playbook(
    playbook_id: str,
    current_user: Optional[TokenData] = Depends(get_optional_user)
):
    """Download original playbook as ZIP file"""
    try:
        # Get playbook information
        playbook_info = await download_service.get_playbook_info(playbook_id, source="original")
        
        if not playbook_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook not found"
            )
        
        # Create ZIP file
        zip_buffer = await download_service.create_playbook_zip(
            playbook_id=playbook_id,
            source="original",
            playbook_title=playbook_info.get('title', 'Unknown_Playbook')
        )
        
        # Generate filename
        filename = download_service.generate_zip_filename(
            playbook_title=playbook_info.get('title', 'Unknown_Playbook'),
            source="original"
        )
        
        # Return ZIP file as streaming response
        return StreamingResponse(
            iter([zip_buffer.read()]),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download playbook: {str(e)}"
        )


@router.get("/user-playbooks/{user_playbook_id}/download")
async def download_forked_playbook(
    user_playbook_id: str,
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Download forked playbook as ZIP file"""
    try:
        # Get user playbook information
        user_playbook_info = await download_service.get_playbook_info(user_playbook_id, source="forked")
        
        if not user_playbook_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User playbook not found"
            )
        
        # Check if user owns this fork
        if user_playbook_info.get('user_id') != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to download this playbook"
            )
        
        # Get original playbook title if available
        playbook_title = "Forked_Playbook"
        if user_playbook_info.get('playbooks'):
            playbook_title = user_playbook_info['playbooks'].get('title', 'Forked_Playbook')
        elif user_playbook_info.get('original_playbook'):
            playbook_title = user_playbook_info['original_playbook'].get('title', 'Forked_Playbook')
        
        # Create ZIP file
        zip_buffer = await download_service.create_playbook_zip(
            playbook_id=user_playbook_id,
            source="forked",
            playbook_title=playbook_title
        )
        
        # Generate filename
        filename = download_service.generate_zip_filename(
            playbook_title=playbook_title,
            source="forked"
        )
        
        # Return ZIP file as streaming response
        return StreamingResponse(
            iter([zip_buffer.read()]),
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download forked playbook: {str(e)}"
        )


@router.get("/{playbook_id}/download-info")
async def get_download_info(
    playbook_id: str,
    source: str = "original",
    current_user: Optional[TokenData] = Depends(get_optional_user)
):
    """Get download information for a playbook without actually downloading"""
    try:
        # Validate source parameter
        if source not in ["original", "forked"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source must be 'original' or 'forked'"
            )
        
        # Get playbook information
        playbook_info = await download_service.get_playbook_info(playbook_id, source=source)
        
        if not playbook_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook not found"
            )
        
        # For forked playbooks, check authorization
        if source == "forked" and current_user:
            if playbook_info.get('user_id') != current_user.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to access this playbook"
                )
        
        # Get file metadata
        files_metadata = await download_service.get_playbook_files_metadata(playbook_id, source)
        
        # Calculate total size (estimate)
        total_files = len(files_metadata)
        
        # Get playbook title
        if source == "original":
            playbook_title = playbook_info.get('title', 'Unknown_Playbook')
        else:
            playbook_title = "Forked_Playbook"
            if playbook_info.get('playbooks'):
                playbook_title = playbook_info['playbooks'].get('title', 'Forked_Playbook')
            elif playbook_info.get('original_playbook'):
                playbook_title = playbook_info['original_playbook'].get('title', 'Forked_Playbook')
        
        # Generate filename
        filename = download_service.generate_zip_filename(playbook_title, source)
        
        return {
            "playbook_id": playbook_id,
            "source": source,
            "title": playbook_title,
            "total_files": total_files,
            "estimated_filename": filename,
            "files": [
                {
                    "name": f.get('file_name' if source == 'original' else 'file_path', 'Unknown'),
                    "type": f.get('file_type', 'Unknown'),
                    "path": f.get('storage_path', '')
                }
                for f in files_metadata
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get download info: {str(e)}"
        )


# Playbook Files Management Endpoints

@router.post("/{playbook_id}/files", response_model=PlaybookFileResponse)
async def upload_playbook_file(
    playbook_id: str,
    file: UploadFile = File(...),
    file_path: Optional[str] = Form(None),
    tags: Optional[str] = Form("[]"),
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Upload a file to a playbook and create the database entry"""
    try:
        # Verify playbook exists
        playbook = await supabase_service.get_playbook(playbook_id)
        if not playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook not found"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Determine file type from extension, mapping to allowed database types
        file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else 'txt'
        
        # Database constraint only allows: 'md', 'pdf', 'csv', 'docx', 'txt'
        # Map other common types to txt
        type_mapping = {
            'md': 'md',
            'markdown': 'md',
            'pdf': 'pdf',
            'csv': 'csv',
            'docx': 'docx',
            'doc': 'docx',  # Map doc to docx
            'txt': 'txt',
            'py': 'txt',    # Map Python files to txt
            'python': 'txt',
            'json': 'txt',  # Map JSON to txt
            'yaml': 'txt',  # Map YAML to txt
            'yml': 'txt',
            'js': 'txt',    # Map JavaScript to txt
            'html': 'txt',  # Map HTML to txt
            'xml': 'txt',   # Map XML to txt
            'sql': 'txt',   # Map SQL to txt
            'sh': 'txt',    # Map shell scripts to txt
            'cfg': 'txt',   # Map config files to txt
            'conf': 'txt',
            'ini': 'txt',
            'log': 'txt'
        }
        
        file_type = type_mapping.get(file_extension, 'txt')  # Default fallback to txt
        
        # Generate storage path with new structure: playbook/{{user_id}}/version/filename
        if file_path:
            # Use provided file path (preserving folder structure)
            storage_path = f"playbook/{current_user.user_id}/v1/{file_path}"
            file_name = file_path
        else:
            # Use original filename with new folder structure
            storage_path = f"playbook/{current_user.user_id}/v1/{file.filename}"
            file_name = file.filename
        
        # Upload file to Supabase Storage
        await supabase_service.upload_playbook_file_to_storage(
            file_content=file_content,
            storage_path=storage_path,
            bucket="playbooks"
        )
        
        # Parse tags
        try:
            import json
            tags_list = json.loads(tags) if tags else []
        except:
            tags_list = []
        
        # Create database entry
        file_dict = {
            "playbook_id": playbook_id,
            "file_name": file_name,
            "file_type": file_type,
            "storage_path": storage_path,
            "tags": tags_list
        }
        
        # Set uploaded_by to current user if authenticated
        if current_user:
            file_dict["uploaded_by"] = current_user.user_id
        
        # Create the playbook file entry
        created_file = await supabase_service.create_playbook_file(file_dict)
        
        if not created_file:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create playbook file entry"
            )
        
        return PlaybookFileResponse(**created_file)
    
    except HTTPException:
        raise
    except Exception as e:
        # If database entry failed but file was uploaded, try to clean up
        try:
            if 'storage_path' in locals():
                await supabase_service.delete_file_from_storage(storage_path, "playbooks")
        except:
            pass  # Cleanup failed, but don't mask the original error
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload playbook file: {str(e)}"
        )


@router.post("/{playbook_id}/files/metadata", response_model=PlaybookFileResponse)
async def create_playbook_file_metadata(
    playbook_id: str,
    file_data: PlaybookFileCreate,
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Create a playbook file metadata entry (without uploading actual file)"""
    try:
        # Verify playbook exists
        playbook = await supabase_service.get_playbook(playbook_id)
        if not playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook not found"
            )
        
        # Ensure the playbook_id in the request matches the URL parameter
        file_dict = file_data.dict()
        file_dict["playbook_id"] = playbook_id
        
        # Set uploaded_by to current user if authenticated
        if current_user:
            file_dict["uploaded_by"] = current_user.user_id
        
        # Create the playbook file entry
        created_file = await supabase_service.create_playbook_file(file_dict)
        
        if not created_file:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create playbook file"
            )
        
        return PlaybookFileResponse(**created_file)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create playbook file: {str(e)}"
        )


@router.get("/{playbook_id}/files", response_model=List[PlaybookFileResponse])
async def get_playbook_files(
    playbook_id: str,
    current_user: Optional[TokenData] = Depends(get_optional_user)
):
    """Get all files for a playbook"""
    try:
        # Verify playbook exists
        playbook = await supabase_service.get_playbook(playbook_id)
        if not playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook not found"
            )
        
        # Get playbook files
        files = await supabase_service.get_playbook_files(playbook_id)
        
        return [PlaybookFileResponse(**file_data) for file_data in files]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get playbook files: {str(e)}"
        )


@router.get("/{playbook_id}/files/{file_id}", response_model=PlaybookFileResponse)
async def get_playbook_file(
    playbook_id: str,
    file_id: str,
    current_user: Optional[TokenData] = Depends(get_optional_user)
):
    """Get a specific playbook file"""
    try:
        # Get the file
        file_data = await supabase_service.get_playbook_file(file_id)
        
        if not file_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook file not found"
            )
        
        # Verify the file belongs to the specified playbook
        if file_data["playbook_id"] != playbook_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File does not belong to specified playbook"
            )
        
        return PlaybookFileResponse(**file_data)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get playbook file: {str(e)}"
        )


@router.put("/{playbook_id}/files/{file_id}", response_model=PlaybookFileResponse)
async def update_playbook_file(
    playbook_id: str,
    file_id: str,
    file_update: PlaybookFileUpdate,
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Update a playbook file entry"""
    try:
        # Get the existing file
        existing_file = await supabase_service.get_playbook_file(file_id)
        
        if not existing_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook file not found"
            )
        
        # Verify the file belongs to the specified playbook
        if existing_file["playbook_id"] != playbook_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File does not belong to specified playbook"
            )
        
        # Get the playbook to check ownership
        playbook = await supabase_service.get_playbook(playbook_id)
        if playbook["owner_id"] != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this playbook file"
            )
        
        # Update the file
        update_data = file_update.dict(exclude_unset=True)
        updated_file = await supabase_service.update_playbook_file(file_id, update_data)
        
        if not updated_file:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update playbook file"
            )
        
        return PlaybookFileResponse(**updated_file)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update playbook file: {str(e)}"
        )


@router.delete("/{playbook_id}/files/{file_id}")
async def delete_playbook_file(
    playbook_id: str,
    file_id: str,
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Delete a playbook file entry"""
    try:
        # Get the existing file
        existing_file = await supabase_service.get_playbook_file(file_id)
        
        if not existing_file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook file not found"
            )
        
        # Verify the file belongs to the specified playbook
        if existing_file["playbook_id"] != playbook_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File does not belong to specified playbook"
            )
        
        # Get the playbook to check ownership
        playbook = await supabase_service.get_playbook(playbook_id)
        if playbook["owner_id"] != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this playbook file"
            )
        
        # Delete the file entry
        await supabase_service.delete_playbook_file(file_id)
        
        return {"message": "Playbook file deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete playbook file: {str(e)}"
        )


@router.get("/{playbook_id}/fork-info")
async def get_playbook_fork_info(
    playbook_id: str,
    current_user: Optional[TokenData] = Depends(get_optional_user)
):
    """Get fork information for a specific playbook"""
    try:
        # Verify playbook exists
        playbook = await supabase_service.get_playbook(playbook_id)
        if not playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook not found"
            )
        
        # Get fork count
        fork_count = await supabase_service.get_playbook_fork_count(playbook_id)
        
        # Get recent forks (last 5)
        recent_forks = await supabase_service.get_playbook_forks(playbook_id, limit=5)
        
        # Check if current user has forked this playbook
        user_fork_info = None
        if current_user:
            user_forks = await supabase_service.get_user_playbooks(current_user.user_id)
            for fork in user_forks:
                if fork['original_playbook_id'] == playbook_id:
                    user_fork_info = {
                        'fork_id': fork['id'],
                        'forked_at': fork['forked_at'],
                        'version': fork['version'],
                        'status': fork['status']
                    }
                    break
        
        # Check if user can fork this playbook
        can_fork = True
        if current_user:
            # Can't fork own playbook
            if playbook['owner_id'] == current_user.user_id:
                can_fork = False
            # Can't fork if already forked
            elif user_fork_info:
                can_fork = False
        
        return {
            'playbook_id': playbook_id,
            'playbook_title': playbook['title'],
            'total_forks': fork_count,
            'recent_forks': recent_forks,
            'user_fork': user_fork_info,
            'can_fork': can_fork,
            'is_owner': current_user and playbook['owner_id'] == current_user.user_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/user-playbooks/{user_playbook_id}/sync")
async def sync_fork_with_original(
    user_playbook_id: str,
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Sync a fork with the latest version of the original playbook"""
    try:
        # Get user playbook
        user_playbook = await supabase_service.get_user_playbook(user_playbook_id)
        if not user_playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User playbook not found"
            )
        
        # Check if user owns this fork
        if user_playbook['user_id'] != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to sync this fork"
            )
        
        # Get original playbook
        original_playbook = await supabase_service.get_playbook(user_playbook['original_playbook_id'])
        if not original_playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Original playbook not found"
            )
        
        # Get current versions
        from app.services.version_service import version_service
        original_latest_version = await version_service.get_current_version(original_playbook['id'])
        fork_current_version = user_playbook.get('base_version', 1)
        
        # Check if sync is needed
        if fork_current_version >= original_latest_version:
            return {
                "message": "Fork is already up to date",
                "fork_version": fork_current_version,
                "original_version": original_latest_version,
                "sync_needed": False
            }
        
        # Get new files from original playbook
        new_files = await version_service.get_version_files(original_playbook['id'], original_latest_version)
        
        # Copy new files to fork
        if new_files:
            copied_files = await supabase_service.copy_playbook_files_with_version(
                user_playbook_id=user_playbook_id,
                original_files=new_files,
                version_number=original_latest_version
            )
        else:
            copied_files = []
        
        # Update fork version
        update_data = {
            'base_version': original_latest_version,
            'last_sync_version': original_latest_version,
            'last_updated_at': datetime.utcnow().isoformat()
        }
        
        updated_fork = await supabase_service.update_user_playbook(user_playbook_id, update_data)
        
        return {
            "message": f"Successfully synced fork with original playbook version {original_latest_version}",
            "fork_version": original_latest_version,
            "original_version": original_latest_version,
            "sync_needed": False,
            "files_copied": len(copied_files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync fork: {str(e)}"
        )


@router.get("/user-playbooks/{user_playbook_id}/sync-status")
async def get_fork_sync_status(
    user_playbook_id: str,
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Check if a fork is behind the original playbook"""
    try:
        # Get user playbook
        user_playbook = await supabase_service.get_user_playbook(user_playbook_id)
        if not user_playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User playbook not found"
            )
        
        # Check if user owns this fork
        if user_playbook['user_id'] != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this fork"
            )
        
        # Get original playbook
        original_playbook = await supabase_service.get_playbook(user_playbook['original_playbook_id'])
        if not original_playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Original playbook not found"
            )
        
        # Get current versions
        from app.services.version_service import version_service
        original_latest_version = await version_service.get_current_version(original_playbook['id'])
        fork_current_version = user_playbook.get('base_version', 1)
        
        # Check if fork is behind
        is_behind = fork_current_version < original_latest_version
        versions_behind = original_latest_version - fork_current_version if is_behind else 0
        
        return {
            "fork_id": user_playbook_id,
            "original_playbook_id": original_playbook['id'],
            "original_playbook_title": original_playbook['title'],
            "fork_version": fork_current_version,
            "original_version": original_latest_version,
            "is_behind": is_behind,
            "versions_behind": versions_behind,
            "sync_needed": is_behind
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sync status: {str(e)}"
        )


@router.delete("/user-playbooks/{user_playbook_id}")
async def delete_fork(
    user_playbook_id: str,
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Delete a fork"""
    try:
        # Get user playbook
        user_playbook = await supabase_service.get_user_playbook(user_playbook_id)
        if not user_playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User playbook not found"
            )
        
        # Check if user owns this fork
        if user_playbook['user_id'] != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this fork"
            )
        
        # Delete all files from storage
        user_playbook_files = await supabase_service.get_user_playbook_files(user_playbook_id)
        for file_data in user_playbook_files:
            try:
                # Extract file path from storage URL
                storage_path = file_data['storage_path']
                if storage_path.startswith('http'):
                    path_parts = storage_path.split('/')
                    bucket_index = next(i for i, part in enumerate(path_parts) if part == settings.storage_bucket_name)
                    file_path = '/'.join(path_parts[bucket_index + 1:])
                else:
                    file_path = storage_path
                
                # Delete from storage
                await supabase_service.delete_file_from_storage(file_path)
            except Exception as file_error:
                print(f"Warning: Failed to delete file {file_data.get('file_path')}: {file_error}")
        
        # Delete user playbook files from database
        await supabase_service.delete_user_playbook_files(user_playbook_id)
        
        # Delete user playbook entry
        await supabase_service.delete_user_playbook(user_playbook_id)
        
        return {
            "message": "Fork deleted successfully",
            "deleted_fork_id": user_playbook_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete fork: {str(e)}"
        )


@router.post("/user-playbooks/{user_playbook_id}/files")
async def upload_fork_file(
    user_playbook_id: str,
    file: UploadFile = File(...),
    file_path: Optional[str] = Form(None),
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Upload a file to a fork"""
    try:
        # Get user playbook
        user_playbook = await supabase_service.get_user_playbook(user_playbook_id)
        if not user_playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User playbook not found"
            )
        
        # Check if user owns this fork
        if user_playbook['user_id'] != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to upload files to this fork"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Determine file type from extension
        file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else 'txt'
        file_type = file_extension if file_extension in ['md', 'pdf', 'csv', 'docx', 'txt'] else 'txt'
        
        # Determine content type
        content_type_map = {
            'pdf': 'application/pdf',
            'md': 'text/markdown',
            'txt': 'text/plain',
            'csv': 'text/csv',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        content_type = content_type_map.get(file_extension, 'application/octet-stream')
        
        # Generate storage path
        if file_path:
            storage_path = f"user_playbooks/{user_playbook_id}/{file_path}"
            file_name = file_path
        else:
            storage_path = f"user_playbooks/{user_playbook_id}/{file.filename}"
            file_name = file.filename
        
        # Upload file to storage
        storage_url = await supabase_service.upload_file_to_storage(storage_path, file_content, content_type)
        
        # Create file entry in database
        file_data = {
            "id": str(uuid.uuid4()),
            "user_playbook_id": user_playbook_id,
            "file_path": file_name,  # Relative path within the playbook
            "file_type": file_type,
            "storage_path": storage_url,  # Full storage URL
            "version": "v1",
            "version_created": 1,
            "is_active": True
        }
        
        # Try to add timestamp fields if they exist
        try:
            file_data.update({
                "uploaded_at": datetime.utcnow().isoformat(),
                "last_modified_at": datetime.utcnow().isoformat()
            })
            
            response = supabase_service.client.table("user_playbook_files").insert(file_data).execute()
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create file entry"
                )
                
        except Exception as timestamp_error:
            # If timestamp columns don't exist, try without them
            print(f"Timestamp columns not available, trying without: {str(timestamp_error)}")
            
            # Remove timestamp fields and try again
            file_data.pop("uploaded_at", None)
            file_data.pop("last_modified_at", None)
            
            response = supabase_service.client.table("user_playbook_files").insert(file_data).execute()
            if not response.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create file entry"
                )
        
        return {
            "message": "File uploaded successfully",
            "file_id": response.data[0]['id'],
            "file_name": file_name,
            "file_type": file_type,
            "storage_url": storage_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


# Star and View Count Endpoints

@router.post("/{playbook_id}/star", response_model=PlaybookStarResponse)
async def star_playbook(
    playbook_id: str,
    star_request: PlaybookStarRequest,
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Star a playbook (simple approach - just increments count)"""
    try:
        # Verify playbook exists
        playbook = await supabase_service.get_playbook(playbook_id)
        if not playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook not found"
            )
        
        # Star the playbook
        result = await supabase_service.star_playbook(playbook_id, current_user.user_id)
        
        return PlaybookStarResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{playbook_id}/star", response_model=PlaybookStarResponse)
async def unstar_playbook(
    playbook_id: str,
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Unstar a playbook (simple approach - just decrements count)"""
    try:
        # Verify playbook exists
        playbook = await supabase_service.get_playbook(playbook_id)
        if not playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook not found"
            )
        
        # Unstar the playbook
        result = await supabase_service.unstar_playbook(playbook_id, current_user.user_id)
        
        return PlaybookStarResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{playbook_id}/view", response_model=PlaybookViewResponse)
async def record_playbook_view(
    playbook_id: str,
    view_request: PlaybookViewRequest,
    current_user: Optional[TokenData] = Depends(get_optional_user)
):
    """Record a view for a playbook"""
    try:
        # Verify playbook exists
        playbook = await supabase_service.get_playbook(playbook_id)
        if not playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook not found"
            )
        
        # Record the view
        result = await supabase_service.record_playbook_view(
            playbook_id=playbook_id,
            user_id=current_user.user_id if current_user else None
        )
        
        return PlaybookViewResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# Notification Management Endpoints

@router.post("/notifications/mark-read", response_model=MarkNotificationsReadResponse)
async def mark_notifications_read(
    request: MarkNotificationsReadRequest,
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Mark specific notifications as read"""
    try:
        user_id = current_user.user_id
        updated_count = await supabase_service.mark_notifications_read(
            user_id, request.notification_ids
        )
        
        return MarkNotificationsReadResponse(
            updated_count=updated_count,
            message=f"Successfully marked {updated_count} notifications as read"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/notifications/mark-all-read", response_model=MarkAllNotificationsReadResponse)
async def mark_all_notifications_read(
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Mark all notifications as read for the current user"""
    try:
        user_id = current_user.user_id
        updated_count = await supabase_service.mark_all_notifications_read(user_id)
        
        return MarkAllNotificationsReadResponse(
            updated_count=updated_count,
            message=f"Successfully marked all {updated_count} notifications as read"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: TokenData = Depends(get_authenticated_user)
):
    """Delete a specific notification"""
    try:
        user_id = current_user.user_id
        success = await supabase_service.delete_notification(user_id, notification_id)
        
        if success:
            return {"message": "Notification deleted successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found or access denied"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


