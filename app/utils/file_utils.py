import os
import uuid
from typing import List, Dict, Any
from fastapi import UploadFile, HTTPException
from app.config import settings


def validate_file_type(file: UploadFile) -> bool:
    """Validate if file type is allowed"""
    return file.content_type in settings.allowed_file_types


def validate_file_size(file: UploadFile, max_size: int = None) -> bool:
    """Validate file size"""
    if max_size is None:
        max_size = settings.max_file_size
    
    # Read file to get size
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset to beginning
    
    return size <= max_size


def generate_file_path(filename: str, content_type: str) -> str:
    """Generate unique file path for storage"""
    file_id = str(uuid.uuid4())
    file_extension = settings.file_extensions.get(content_type, "")
    
    # Clean filename
    clean_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
    
    return f"{file_id}_{clean_filename}{file_extension}"


def get_file_extension(content_type: str) -> str:
    """Get file extension from content type"""
    return settings.file_extensions.get(content_type, "")


def is_text_file(content_type: str) -> bool:
    """Check if file is text-based"""
    text_types = [
        "text/plain",
        "text/markdown",
        "text/csv",
        "application/json",
        "application/xml",
        "text/xml",
        "text/html"
    ]
    return content_type in text_types


def is_spreadsheet_file(content_type: str) -> bool:
    """Check if file is a spreadsheet"""
    spreadsheet_types = [
        "text/csv",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel"
    ]
    return content_type in spreadsheet_types


def is_archive_file(content_type: str) -> bool:
    """Check if file is an archive"""
    archive_types = [
        "application/zip",
        "application/x-zip-compressed"
    ]
    return content_type in archive_types


async def validate_upload_files(files: List[UploadFile]) -> List[Dict[str, Any]]:
    """Validate uploaded files and return file info"""
    validated_files = []
    total_size = 0
    
    for file in files:
        # Validate file type
        if not validate_file_type(file):
            raise HTTPException(
                status_code=400,
                detail=f"File type {file.content_type} not allowed"
            )
        
        # Validate file size
        if not validate_file_size(file):
            raise HTTPException(
                status_code=413,
                detail=f"File {file.filename} exceeds maximum size"
            )
        
        # Calculate total size
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)
        total_size += file_size
        
        # Check total size limit
        if total_size > settings.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"Total file size exceeds {settings.max_file_size} bytes"
            )
        
        validated_files.append({
            "filename": file.filename,
            "content_type": file.content_type,
            "size": file_size,
            "file": file
        })
    
    return validated_files


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove or replace unsafe characters
    unsafe_chars = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename 
