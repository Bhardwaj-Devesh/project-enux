# Fork with New Playbook Implementation

## Overview

This document describes the implementation of enhanced fork functionality that creates a new playbook record in the `playbooks` table when forking, in addition to the existing user playbook tracking.

## Changes Made

### 1. Database Schema Updates

#### New Migration: `database/add_forked_playbook_id.sql`
- Added `forked_playbook_id` field to `user_playbooks` table
- This field stores the ID of the new playbook created during forking
- Added index for better performance
- Added foreign key constraint to `playbooks` table

### 2. API Changes

#### Updated `/fork` Endpoint (`app/api/playbooks.py`)

**New Steps in Fork Process:**

1. **Step 1-5**: Existing validation and version retrieval
2. **Step 6**: Create new playbook record in `playbooks` table
   - Copies all fields from original playbook
   - Sets `owner_id` to forking user's ID
   - Uses latest version from step 5
   - Preserves AI-generated content (summary, tags, vector_embedding)
3. **Step 7**: Create user playbook entry with link to new playbook
4. **Step 8**: Copy files to both new playbook and fork tracking
5. **Step 9**: Create notification
6. **Step 10**: Return new playbook URL

**Key Changes:**
- New playbook creation with all original fields
- File copying to new playbook record
- Updated response to return new playbook ID
- URL generation points to new playbook instead of user playbook

### 3. Service Layer Updates

#### New Method: `copy_playbook_files_to_new_playbook`
**Location**: `app/services/supabase_service.py`

**Purpose**: Copy files from original playbook to new playbook record

**Features:**
- Downloads original files from storage
- Uploads to new location with user-specific path
- Creates entries in `playbook_files` table
- Handles timestamp fields gracefully
- Preserves file metadata

#### Updated Method: `create_user_playbook_fork`
**Changes:**
- Added `forked_playbook_id` parameter
- Links user playbook entry to new playbook record
- Maintains backward compatibility

### 4. File Structure

```
playbook/{user_id}/v1/{filename}
```

Files are stored in user-specific directories to avoid conflicts and maintain organization.

## Benefits

### 1. Complete Playbook Independence
- Forked playbooks are now full playbook records
- Can be managed like any other playbook
- Full access to all playbook features

### 2. Better User Experience
- Direct access to forked playbooks via `/playbooks/{id}`
- Consistent API interface
- No need for special fork-specific endpoints

### 3. Enhanced Tracking
- Maintains fork relationship via `user_playbooks` table
- Preserves original playbook reference
- Enables sync functionality

### 4. Improved File Management
- Files are properly organized by user
- No storage conflicts
- Clear ownership structure

## Database Schema

### Updated Tables

#### `user_playbooks`
```sql
CREATE TABLE user_playbooks (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    original_playbook_id UUID REFERENCES playbooks(id),
    forked_playbook_id UUID REFERENCES playbooks(id), -- NEW FIELD
    forked_at TIMESTAMP WITH TIME ZONE,
    last_updated_at TIMESTAMP WITH TIME ZONE,
    version TEXT,
    license TEXT,
    status TEXT
);
```

#### `playbooks` (unchanged)
- New playbook records are created here during forking
- All standard playbook fields are preserved

## API Response Changes

### Before
```json
{
    "status": "success",
    "new_playbook_id": "user_playbook_uuid",
    "new_playbook_url": "/user-playbooks/{user_playbook_id}",
    "message": "Successfully forked playbook"
}
```

### After
```json
{
    "status": "success",
    "new_playbook_id": "new_playbook_uuid",
    "new_playbook_url": "/playbooks/{new_playbook_id}",
    "message": "Successfully forked playbook"
}
```

## Testing

### Test Script: `test_fork_with_new_playbook.py`
Comprehensive test that verifies:
1. Authentication
2. Playbook discovery
3. Fork creation
4. New playbook verification
5. User playbook listing
6. Fork information retrieval

## Migration Steps

1. **Run Database Migration**:
   ```sql
   -- Execute database/add_forked_playbook_id.sql
   ```

2. **Deploy Code Changes**:
   - Update `app/api/playbooks.py`
   - Update `app/services/supabase_service.py`

3. **Test Functionality**:
   ```bash
   python test_fork_with_new_playbook.py
   ```

## Backward Compatibility

- Existing fork functionality continues to work
- User playbook entries are preserved
- No breaking changes to existing APIs
- Gradual migration possible

## Future Enhancements

1. **Sync Functionality**: Update sync to work with new playbook records
2. **Fork History**: Track multiple forks of the same playbook
3. **Merge Functionality**: Enable merging changes back to original
4. **Fork Analytics**: Track fork usage and popularity

## Error Handling

- Graceful handling of missing database columns
- Fallback mechanisms for timestamp fields
- Comprehensive error messages
- Transaction rollback on failure

## Performance Considerations

- File copying is done asynchronously
- Storage operations are optimized
- Database indexes for efficient queries
- Minimal impact on existing operations
