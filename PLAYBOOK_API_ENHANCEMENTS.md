# Playbook API Enhancements

## Overview
This document summarizes the enhancements made to the playbook APIs to improve file organization, user experience, and provide better playbook management functionality.

## Changes Made

### 1. Updated File Upload Structure

**Problem**: Files were being uploaded with a simple UUID-based path structure, making it difficult to organize files by user and version.

**Solution**: Implemented a new folder structure: `playbook/{{user_id}}/version/filename`

**Changes**:
- **File**: `app/api/playbooks.py`
- **Function**: `upload_playbook()` (line ~120)
- **Old Structure**: `{file_id}{file_extension}`
- **New Structure**: `playbook/{current_user.user_id}/v1/{file_id}{file_extension}`

**Benefits**:
- Better organization by user
- Version control support
- Easier file management and cleanup
- Clear ownership structure

### 2. New API Endpoints

#### 2.1 GET /playbooks/my-playbooks
**Purpose**: Get all playbooks owned by the authenticated user (for "My Playbooks" functionality)

**Authentication**: Required
**Response**: `List[PlaybookResponse]`

**Features**:
- Returns only playbooks owned by the authenticated user
- Includes basic playbook information
- Supports pagination (limit, offset)

**Usage Example**:
```bash
GET /playbooks/my-playbooks?limit=10&offset=0
Authorization: Bearer <token>
```

#### 2.2 GET /playbooks/my-playbooks/detailed
**Purpose**: Get detailed information about all playbooks owned by the authenticated user

**Authentication**: Required
**Response**: `List[Dict[str, Any]]`

**Features**:
- Enhanced metadata including file counts
- Processing status information
- Summary and embedding status
- Better for dashboard/overview pages

**Response Structure**:
```json
[
  {
    "playbook": {
      "id": "...",
      "title": "...",
      "description": "...",
      // ... other playbook fields
    },
    "metadata": {
      "file_count": 5,
      "processing_status": "completed",
      "has_summary": true,
      "has_embedding": true,
      "created_at": "...",
      "updated_at": "..."
    }
  }
]
```

#### 2.3 GET /playbooks/{playbook_id}/details
**Purpose**: Get comprehensive details of a specific playbook

**Authentication**: Optional (provides different permissions based on authentication)
**Response**: `Dict[str, Any]`

**Features**:
- Complete playbook information
- File list and metadata
- Processing status and AI results
- User permissions and capabilities
- File vector information for search

**Response Structure**:
```json
{
  "playbook": {
    // Complete playbook information
  },
  "files": [
    // List of playbook files
  ],
  "file_vectors_count": 5,
  "processing_status": {
    "status": "completed",
    "message": "AI processing completed successfully",
    "has_summary": true,
    "has_embedding": true,
    "embedding_dimensions": 1536
  },
  "permissions": {
    "is_owner": true,
    "can_edit": true,
    "can_delete": true,
    "can_fork": false
  },
  "metadata": {
    "total_files": 5,
    "created_at": "...",
    "updated_at": "...",
    "version": "v1",
    "stage": "production",
    "tags": ["tag1", "tag2"]
  }
}
```

### 3. Enhanced Supabase Service

#### 3.1 New Method: `get_playbooks_by_user_detailed()`
**File**: `app/services/supabase_service.py`

**Purpose**: Get playbooks by user with detailed information including file counts and processing status

**Features**:
- Joins with playbook_files table to get file counts
- Calculates processing status based on AI results
- Includes metadata about summary and embedding status
- Optimized for performance with proper indexing

### 4. Updated Playbook File Upload

**File**: `app/api/playbooks.py`
**Function**: `upload_playbook_file()`

**Changes**:
- Updated to use new folder structure: `playbook/{user_id}/v1/{filename}`
- Maintains backward compatibility with existing file paths
- Preserves folder structure when custom file paths are provided

## API Endpoints Summary

### New Endpoints
| Method | Endpoint | Purpose | Auth Required |
|--------|----------|---------|---------------|
| GET | `/playbooks/my-playbooks` | Get user's playbooks | Yes |
| GET | `/playbooks/my-playbooks/detailed` | Get detailed user playbooks | Yes |
| GET | `/playbooks/{id}/details` | Get comprehensive playbook details | No |

### Updated Endpoints
| Method | Endpoint | Change |
|--------|----------|--------|
| POST | `/playbooks/upload` | New folder structure |
| POST | `/playbooks/{id}/files` | New folder structure |

## Testing

A comprehensive test script has been created: `test_playbook_apis.py`

**Test Coverage**:
- ✅ New folder structure verification
- ✅ My playbooks endpoint functionality
- ✅ Detailed playbooks endpoint
- ✅ Playbook details endpoint
- ✅ Authentication and permissions

**Run Tests**:
```bash
python test_playbook_apis.py
```

## Benefits

### For Users
1. **Better Organization**: Files are now organized by user and version
2. **My Playbooks**: Easy access to user's own playbooks
3. **Detailed Information**: Rich metadata for better decision making
4. **Permission Clarity**: Clear understanding of what actions are available

### For Developers
1. **Structured File Storage**: Predictable file paths for better management
2. **Enhanced APIs**: More comprehensive endpoints for different use cases
3. **Better Performance**: Optimized queries with proper joins
4. **Extensible Design**: Easy to add more metadata and features

### For System Administration
1. **User Isolation**: Files are clearly separated by user
2. **Version Control**: Support for multiple versions per user
3. **Cleanup Capability**: Easy to identify and remove user files
4. **Audit Trail**: Clear ownership and organization structure

## Migration Notes

### Existing Files
- Existing files will continue to work with the old path structure
- New uploads will use the new folder structure
- No immediate migration required for existing data

### Database Changes
- No database schema changes required
- Existing queries continue to work
- New methods provide enhanced functionality

### Storage Changes
- New files will be stored in the new folder structure
- Existing files remain in their current locations
- Consider implementing a migration script for existing files if needed

## Future Enhancements

1. **Version Management**: Support for multiple versions per playbook
2. **File Organization**: Support for subdirectories within playbooks
3. **Bulk Operations**: Batch operations for multiple playbooks
4. **Advanced Search**: Enhanced search with file content and metadata
5. **Collaboration**: Multi-user access and sharing capabilities

## Security Considerations

1. **User Isolation**: Files are properly isolated by user ID
2. **Authentication**: All sensitive endpoints require authentication
3. **Authorization**: Proper permission checks for all operations
4. **Input Validation**: All inputs are validated and sanitized
5. **Path Traversal**: Protected against path traversal attacks

## Performance Considerations

1. **Database Indexing**: Proper indexes on user_id and playbook_id
2. **Query Optimization**: Efficient joins and filtering
3. **Pagination**: All list endpoints support pagination
4. **Caching**: Consider implementing caching for frequently accessed data
5. **File Storage**: Efficient file organization reduces lookup time
