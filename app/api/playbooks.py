from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
import uuid
import asyncio
from app.models.playbook import (
    PlaybookCreate, PlaybookResponse, PlaybookUpdate, 
    PlaybookSearch, PlaybookSearchResult, PlaybookUploadResponse,
    FileUpload, ProcessingStatus, PlaybookForkRequest, PlaybookForkResponse,
    UserPlaybookResponse
)
from app.models.auth import TokenData
from app.api.dependencies import get_current_user, get_optional_user
from app.services.supabase_service import supabase_service
from app.services.ai_service import ai_service
from app.services.vector_service import vector_service
from app.config import settings
import json


router = APIRouter(prefix="/playbooks", tags=["playbooks"])


@router.post("/upload", response_model=PlaybookUploadResponse)
async def upload_playbook(
    title: str = Form(...),
    description: str = Form(...),
    stage: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # JSON string
    version: str = Form("v1"),
    files: List[UploadFile] = File(...),
    owner_id: str = Form("demo_user_123")  # Default owner ID for testing
):
    """Upload a new playbook with files (No authentication required)"""
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
        
        # Parse tags
        parsed_tags = []
        if tags:
            try:
                parsed_tags = json.loads(tags)
            except json.JSONDecodeError:
                parsed_tags = [tag.strip() for tag in tags.split(",")]
        
        # Create playbook data
        playbook_data = {
            "title": title,
            "description": description,
            "stage": stage,
            "tags": parsed_tags,
            "version": version,
            "owner_id": owner_id,
            "files": {},
            "summary": None,
            "vector_embedding": None
        }
        
        # Upload files to storage
        uploaded_files = []
        for file in files:
            if file.content_type not in settings.allowed_file_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File type {file.content_type} not allowed"
                )
            
            # Generate unique file path
            file_id = str(uuid.uuid4())
            file_extension = settings.file_extensions.get(file.content_type, "")
            file_path = f"{file_id}{file_extension}"
            
            # Upload to Supabase Storage
            file_content = await file.read()
            file_url = await supabase_service.upload_file_to_storage(
                file_path, file_content, file.content_type
            )
            
            # Store file info
            playbook_data["files"][file.filename] = file_url
            uploaded_files.append(FileUpload(
                filename=file.filename,
                content_type=file.content_type,
                size=len(file_content),
                file_path=file_path
            ))
        
           # Extract text content from files for vector storage
            files_for_vector_storage = []
            for file_info in uploaded_files:
                # Download file content for vector processing
                file_content = supabase_service.client.storage.from_(
                    settings.storage_bucket_name
                ).download(file_info.file_path)
                
                # Extract text content for embedding
                text_content = await ai_service.extract_text_from_file(
                    file_content,
                    file_info.filename,
                    file_info.content_type
                )
            
            files_for_vector_storage.append({
                "filename": file_info.filename,
                "content": text_content,
                "content_type": file_info.content_type
            })
        
        # Create playbook in database first to get the ID
        playbook = await supabase_service.create_playbook(playbook_data)
        
        if not playbook:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create playbook"
            )
        
        # Store files in vector database
        vector_storage_result = await vector_service.store_file_vectors(
            files_for_vector_storage, 
            playbook["id"]
        )
        
        if not vector_storage_result["success"]:
            print(f"Warning: Vector storage failed for playbook {playbook['id']}: {vector_storage_result.get('error', 'Unknown error')}")
        
        # Process files with AI in background
        asyncio.create_task(process_playbook_ai(playbook["id"], uploaded_files, title, description))
        
        return PlaybookUploadResponse(
            playbook=PlaybookResponse(**playbook),
            files=uploaded_files,
            processing_status="processing",
            message="Playbook uploaded successfully. AI processing started in background."
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def process_playbook_ai(playbook_id: str, files: List[FileUpload], title: str, description: str):
    """Process playbook files with AI in background"""
    try:
        # Prepare files for AI processing
        files_for_ai = []
        for file_info in files:
            # Download file content for AI processing
            file_content = await supabase_service.client.storage.from_(
                settings.storage_bucket_name
            ).download(file_info.file_path)
            
            files_for_ai.append({
                "filename": file_info.filename,
                "content": file_content,
                "content_type": file_info.content_type
            })
        
        # Process with AI
        ai_results = await ai_service.process_playbook_files(files_for_ai, title, description)
        
        # Update playbook with AI results
        update_data = {
            "summary": ai_results["summary"],
            "tags": ai_results["tags"],
            "stage": ai_results["stage"],
            "vector_embedding": ai_results["embedding"]
        }
        
        await supabase_service.update_playbook(playbook_id, update_data)
        
    except Exception as e:
        print(f"Error processing playbook {playbook_id}: {str(e)}")


@router.get("/", response_model=List[PlaybookResponse])
async def get_playbooks(
    limit: int = 50,
    offset: int = 0,
    current_user: Optional[TokenData] = Depends(get_optional_user)
):
    """Get all playbooks"""
    try:
        user_id = current_user.user_id if current_user else None
        playbooks = await supabase_service.get_playbooks(user_id, limit, offset)
        return [PlaybookResponse(**playbook) for playbook in playbooks]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{playbook_id}", response_model=PlaybookResponse)
async def get_playbook(playbook_id: str):
    """Get a specific playbook"""
    try:
        playbook = await supabase_service.get_playbook(playbook_id)
        if not playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Playbook not found"
            )
        return PlaybookResponse(**playbook)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{playbook_id}", response_model=PlaybookResponse)
async def update_playbook(
    playbook_id: str,
    playbook_update: PlaybookUpdate,
    current_user: TokenData = Depends(get_current_user)
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
        
        return PlaybookResponse(**updated_playbook)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/{playbook_id}")
async def delete_playbook(
    playbook_id: str,
    current_user: TokenData = Depends(get_current_user)
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
        # Create embedding for query
        query_embedding = await ai_service.create_embedding(query)
        
        # Search using vector similarity
        results = await supabase_service.search_playbooks_vector(query_embedding, limit)
        
        return [
            PlaybookSearchResult(
                playbook=PlaybookResponse(**result["playbook"]),
                similarity_score=result["similarity"]
            )
            for result in results
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
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
        
        return [PlaybookResponse(**playbook) for playbook in results]
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
        
        return ProcessingStatus(
            status=status,
            message=message,
            summary=playbook.get("summary"),
            extracted_tags=playbook.get("tags"),
            vector_embedding=playbook.get("vector_embedding")
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


@router.post("/fork", response_model=PlaybookForkResponse)
async def fork_playbook(
    fork_request: PlaybookForkRequest,
    current_user: Optional[TokenData] = Depends(get_optional_user)
):
    """Fork a playbook to user's workspace"""
    try:
        # Step 1: Validate input
        # Validate user exists in database
        user_exists = await supabase_service.validate_user_exists(fork_request.user_id)
        if not user_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Validate original playbook exists
        original_playbook = await supabase_service.get_playbook(fork_request.playbook_id)
        if not original_playbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Original playbook not found"
            )
        
        # Check if user already forked this playbook
        existing_forks = await supabase_service.get_user_playbooks(fork_request.user_id)
        for fork in existing_forks:
            if fork['original_playbook_id'] == fork_request.playbook_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User has already forked this playbook"
                )
        
        # Step 2: Create new user playbook entry
        user_playbook = await supabase_service.create_user_playbook_fork(
            user_id=fork_request.user_id,
            original_playbook_id=fork_request.playbook_id,
            license=original_playbook.get('license')
        )
        
        if not user_playbook:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create playbook fork"
            )
        
        # Step 3: Copy files to user_playbook_files
        original_files = await supabase_service.get_playbook_files(fork_request.playbook_id)
        
        if original_files:
            copied_files = await supabase_service.copy_playbook_files(
                user_playbook_id=user_playbook['id'],
                original_files=original_files
            )
        
        # Generate playbook URL (you might want to adjust this based on your frontend routing)
        new_playbook_url = f"/user-playbooks/{user_playbook['id']}"
        
        return PlaybookForkResponse(
            status="success",
            new_playbook_id=user_playbook['id'],
            new_playbook_url=new_playbook_url,
            message=f"Successfully forked playbook '{original_playbook['title']}'"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fork playbook: {str(e)}"
        )


@router.get("/user/{user_id}/forks", response_model=List[UserPlaybookResponse])
async def get_user_playbook_forks(
    user_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: Optional[TokenData] = Depends(get_optional_user)
):
    """Get all playbook forks for a specific user"""
    try:
        # Validate user exists
        user_exists = await supabase_service.validate_user_exists(user_id)
        if not user_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
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

