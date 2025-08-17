# Fork Functionality Guide

## Overview

The fork functionality allows users to create their own copy of any playbook (except their own) and work on it independently. This enables collaboration, experimentation, and contribution workflows similar to Git repositories.

## Key Features

### 1. Fork Creation
- **Endpoint**: `POST /playbooks/fork`
- **Authentication**: Required
- **Request Body**:
  ```json
  {
    "playbook_id": "uuid-of-playbook-to-fork"
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "new_playbook_id": "uuid-of-new-fork",
    "new_playbook_url": "/user-playbooks/uuid",
    "message": "Successfully forked playbook 'Title'"
  }
  ```

### 2. Fork Information
- **Endpoint**: `GET /playbooks/{playbook_id}/fork-info`
- **Authentication**: Optional
- **Response**:
  ```json
  {
    "playbook_id": "uuid",
    "playbook_title": "Title",
    "total_forks": 5,
    "recent_forks": [...],
    "user_fork": {
      "fork_id": "uuid",
      "forked_at": "2024-01-01T00:00:00Z",
      "version": "v1",
      "status": "active"
    },
    "can_fork": true,
    "is_owner": false
  }
  ```

### 3. Fork Management

#### Get User Forks
- **Endpoint**: `GET /playbooks/user/forks`
- **Authentication**: Required
- **Response**: List of all forks created by the user

#### Get Forked Playbook
- **Endpoint**: `GET /playbooks/user-playbooks/{fork_id}`
- **Authentication**: Optional
- **Response**: Detailed information about a specific fork

#### Get Fork Files
- **Endpoint**: `GET /playbooks/user-playbooks/{fork_id}/files`
- **Authentication**: Optional
- **Response**: List of all files in the fork

### 4. File Management in Forks

#### Upload File to Fork
- **Endpoint**: `POST /playbooks/user-playbooks/{fork_id}/files`
- **Authentication**: Required
- **Form Data**:
  - `file`: The file to upload
  - `file_path` (optional): Custom path for the file

#### Download Fork
- **Endpoint**: `GET /playbooks/user-playbooks/{fork_id}/download`
- **Authentication**: Required
- **Response**: ZIP file containing all fork files

### 5. Version Synchronization

#### Check Sync Status
- **Endpoint**: `GET /playbooks/user-playbooks/{fork_id}/sync-status`
- **Authentication**: Required
- **Response**:
  ```json
  {
    "fork_id": "uuid",
    "original_playbook_id": "uuid",
    "original_playbook_title": "Title",
    "fork_version": 1,
    "original_version": 3,
    "is_behind": true,
    "versions_behind": 2,
    "sync_needed": true
  }
  ```

#### Sync Fork
- **Endpoint**: `POST /playbooks/user-playbooks/{fork_id}/sync`
- **Authentication**: Required
- **Response**:
  ```json
  {
    "message": "Successfully synced fork with original playbook version 3",
    "fork_version": 3,
    "original_version": 3,
    "sync_needed": false,
    "files_copied": 2
  }
  ```

### 6. Fork Deletion
- **Endpoint**: `DELETE /playbooks/user-playbooks/{fork_id}`
- **Authentication**: Required
- **Response**:
  ```json
  {
    "message": "Fork deleted successfully",
    "deleted_fork_id": "uuid"
  }
  ```

## Database Schema

### User Playbooks Table
```sql
CREATE TABLE user_playbooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    original_playbook_id UUID REFERENCES playbooks(id) ON DELETE CASCADE,
    forked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version TEXT DEFAULT 'v1',
    license TEXT,
    status TEXT DEFAULT 'active',
    base_version INT DEFAULT 1,
    last_sync_version INT DEFAULT 1,
    UNIQUE(user_id, original_playbook_id)
);
```

### User Playbook Files Table
```sql
CREATE TABLE user_playbook_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_playbook_id UUID REFERENCES user_playbooks(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_modified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version TEXT DEFAULT 'v1',
    version_created INT DEFAULT 1,
    is_active BOOLEAN DEFAULT true
);
```

## Workflow Examples

### 1. Basic Fork Workflow

```python
# 1. Create a fork
fork_response = requests.post(
    f"{BASE_URL}/playbooks/fork",
    json={"playbook_id": "original-playbook-id"},
    headers={"Authorization": f"Bearer {token}"}
)
fork_id = fork_response.json()["new_playbook_id"]

# 2. Upload a new file to the fork
with open("new_file.md", "rb") as f:
    files = {"file": ("new_file.md", f, "text/markdown")}
    response = requests.post(
        f"{BASE_URL}/playbooks/user-playbooks/{fork_id}/files",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )

# 3. Check if fork is behind original
sync_status = requests.get(
    f"{BASE_URL}/playbooks/user-playbooks/{fork_id}/sync-status",
    headers={"Authorization": f"Bearer {token}"}
).json()

if sync_status["sync_needed"]:
    # 4. Sync with original
    requests.post(
        f"{BASE_URL}/playbooks/user-playbooks/{fork_id}/sync",
        headers={"Authorization": f"Bearer {token}"}
    )
```

### 2. Pull Request Workflow

```python
# 1. Create a fork and make changes
fork_id = create_fork(original_playbook_id)

# 2. Upload modified files
upload_files_to_fork(fork_id, modified_files)

# 3. Create pull request
pr_data = {
    "fork_id": fork_id,
    "title": "Add new feature",
    "description": "This PR adds a new feature to the playbook",
    "commit_message": "feat: add new feature"
}
pr_response = requests.post(
    f"{BASE_URL}/pull-requests/",
    json=pr_data,
    headers={"Authorization": f"Bearer {token}"}
)
```

## Security and Permissions

### Fork Creation Rules
1. **Cannot fork own playbook**: Users cannot fork playbooks they own
2. **One fork per user**: Each user can only have one fork of a specific playbook
3. **Authentication required**: Fork creation requires valid authentication

### Access Control
1. **Fork ownership**: Only the fork owner can modify, sync, or delete their fork
2. **File access**: Fork files are accessible to the fork owner
3. **Public visibility**: Fork information is publicly visible but modifications require ownership

### Data Integrity
1. **Version tracking**: Forks track which version of the original they were created from
2. **File copying**: All files are copied to the fork's storage location
3. **Sync safety**: Syncing only updates files, doesn't overwrite user modifications

## Error Handling

### Common Error Responses

#### 400 Bad Request
- Trying to fork your own playbook
- Invalid playbook ID

#### 403 Forbidden
- Not authorized to access/modify a fork
- Not the fork owner

#### 404 Not Found
- Playbook doesn't exist
- Fork doesn't exist

#### 409 Conflict
- User already has a fork of this playbook

#### 500 Internal Server Error
- Database errors
- Storage errors
- File processing errors

## Best Practices

### For Fork Owners
1. **Regular syncing**: Keep your fork up to date with the original
2. **Clear documentation**: Document your changes and improvements
3. **Pull requests**: Use pull requests to contribute back to the original

### For Original Playbook Owners
1. **Monitor forks**: Check who has forked your playbook
2. **Review pull requests**: Consider contributions from forks
3. **Version management**: Use proper versioning for your playbook

### For Developers
1. **Error handling**: Always handle potential errors in fork operations
2. **User feedback**: Provide clear feedback for fork operations
3. **Performance**: Consider the impact of file copying on performance

## Testing

Run the comprehensive test suite:

```bash
python test_fork_functionality.py
```

This will test:
- Fork creation and validation
- File management in forks
- Sync functionality
- Error handling
- Security permissions
- Pull request integration

## Troubleshooting

### Common Issues

1. **Fork creation fails**
   - Check if user already has a fork
   - Verify playbook exists
   - Ensure user is not trying to fork their own playbook

2. **File upload fails**
   - Check file size limits
   - Verify file type is supported
   - Ensure user owns the fork

3. **Sync fails**
   - Check if fork is already up to date
   - Verify original playbook still exists
   - Check storage permissions

4. **Download fails**
   - Verify fork exists
   - Check user permissions
   - Ensure files are accessible

### Debug Information

Enable debug logging to get detailed information about fork operations:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

1. **Branch support**: Allow multiple branches within a fork
2. **Merge conflicts**: Handle merge conflicts in pull requests
3. **Fork templates**: Pre-configured fork templates
4. **Collaborative forks**: Allow multiple users to work on the same fork
5. **Fork analytics**: Track fork usage and popularity
