# JWT Authentication Implementation

## Overview
This document outlines the implementation of JWT (JSON Web Token) authentication across all APIs in the project. The authentication system now provides secure token-based access control for all endpoints.

## Changes Made

### 1. Authentication Models (`app/models/auth.py`)
- **Added `UserResponseWithToken` model**: Combines user data with JWT token information
- **Enhanced response structure**: Register and login endpoints now return both user data and access token

### 2. Authentication API (`app/api/auth.py`)
- **Enhanced `/register` endpoint**: 
  - Now returns `UserResponseWithToken` instead of just `UserResponse`
  - Automatically generates and returns JWT token upon successful registration
  - Token includes user ID and email in payload
- **Enhanced `/login` and `/login-json` endpoints**:
  - Already return JWT tokens (no changes needed)
  - Consistent token format across all auth endpoints

### 3. Dependencies (`app/api/dependencies.py`)
- **Added `get_authenticated_user` function**: 
  - Required authentication for protected endpoints
  - Returns 401 Unauthorized if token is missing or invalid
- **Enhanced `get_optional_user` function**:
  - Optional authentication for public endpoints
  - Returns user data if token is valid, None otherwise
- **Improved error handling**: Better error messages and status codes

### 4. Playbooks API (`app/api/playbooks.py`)
- **Protected endpoints requiring authentication**:
  - `POST /upload` - Upload new playbook
  - `PUT /{playbook_id}` - Update playbook
  - `DELETE /{playbook_id}` - Delete playbook
  - `POST /fork` - Fork a playbook
  - `GET /user/forks` - Get user's forked playbooks
  - `GET /user-playbooks/{user_playbook_id}/download` - Download forked playbook
  - `POST /{playbook_id}/files` - Upload playbook file
  - `POST /{playbook_id}/files/metadata` - Create file metadata
  - `PUT /{playbook_id}/files/{file_id}` - Update playbook file
  - `DELETE /{playbook_id}/files/{file_id}` - Delete playbook file

- **Public endpoints with optional authentication**:
  - `GET /` - List playbooks (authenticated users see their own)
  - `GET /{playbook_id}` - Get specific playbook
  - `GET /search/vector` - Vector search
  - `GET /search/text` - Text search
  - `GET /{playbook_id}/status` - Get processing status
  - `GET /{playbook_id}/files` - Get playbook files

### 5. Pull Request API (`app/api/pr.py`)
- **All endpoints now require authentication**:
  - `POST /` - Create pull request
  - `POST /from-zip` - Create PR from ZIP
  - `GET /{pr_id}` - Get PR details
  - `GET /` - List PRs
  - `POST /{pr_id}/merge` - Merge PR
  - `POST /{pr_id}/close` - Close PR
  - `GET /forks/{fork_id}/sync-status` - Get sync status
  - `POST /forks/{fork_id}/sync` - Sync fork

### 6. Requirements (`requirements.txt`)
- **Added `bcrypt==4.0.1`**: Fixed version compatibility issue with passlib

## Authentication Flow

### 1. User Registration
```json
POST /api/v1/auth/register
{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe"
}

Response:
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 2. User Login
```json
POST /api/v1/auth/login-json
{
  "email": "user@example.com",
  "password": "securepassword"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 3. Using Protected Endpoints
```http
GET /api/v1/auth/me
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## Frontend Integration

### 1. Store Token in Session Storage
```javascript
// After successful login/registration
const response = await fetch('/api/v1/auth/login-json', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});

const data = await response.json();
sessionStorage.setItem('authToken', data.access_token);
sessionStorage.setItem('user', JSON.stringify(data.user));
```

### 2. Include Token in API Requests
```javascript
// For protected endpoints
const token = sessionStorage.getItem('authToken');
const response = await fetch('/api/v1/playbooks/', {
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
```

### 3. Handle Authentication Errors
```javascript
if (response.status === 401) {
  // Token expired or invalid
  sessionStorage.removeItem('authToken');
  sessionStorage.removeItem('user');
  // Redirect to login page
  window.location.href = '/login';
}
```

## Security Features

1. **JWT Token Expiration**: Tokens expire after 30 minutes (configurable)
2. **Secure Password Hashing**: Passwords are hashed using bcrypt
3. **Token Validation**: All protected endpoints validate JWT tokens
4. **User Authorization**: Endpoints check if user owns the resource
5. **Error Handling**: Proper HTTP status codes and error messages

## Testing

Run the test script to verify the authentication workflow:
```bash
python test_auth_workflow.py
```

This will test:
- User registration with token generation
- User login with token validation
- Protected endpoint access
- Invalid token rejection
- Playbooks API authentication

## Configuration

JWT settings can be configured in `app/config.py`:
- `secret_key`: JWT signing secret
- `algorithm`: JWT algorithm (HS256)
- `access_token_expire_minutes`: Token expiration time (30 minutes)

## Migration Notes

1. **Existing users**: Will need to re-register or use login endpoint to get tokens
2. **Frontend changes**: All API calls to protected endpoints must include Authorization header
3. **Session management**: Frontend should handle token storage and refresh logic
4. **Error handling**: Frontend should handle 401 responses appropriately

## Next Steps

1. Implement token refresh mechanism
2. Add role-based access control (RBAC)
3. Implement rate limiting for auth endpoints
4. Add password reset functionality
5. Implement email verification

