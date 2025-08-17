# Profile Update API Documentation

## Overview

The profile update API (`PUT /profiles/me`) allows users to update their profile information. The API automatically fetches the user's ID and username from the authentication token, so these fields should not be included in the request payload.

## Endpoint

```
PUT /profiles/me
```

## Authentication

This endpoint requires authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

## Request Payload

The request payload should only contain profile fields. The `user_id` and `username` are automatically fetched from the authentication token.

### Expected Payload Format

```json
{
  "full_name": "Devesh Bhardwaj",
  "bio": "I am a disco dancer ta ta ta tannana",
  "company": "Hiwipay",
  "location": "Mumbai",
  "website": "",
  "interests": ["reading"],
  "stage": "",
  "avatar_url": null
}
```

### Field Descriptions

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `full_name` | string | No | User's full name | Max 100 characters |
| `bio` | string | No | User's biography | Max 500 characters |
| `company` | string | No | User's company | Max 100 characters |
| `location` | string | No | User's location | Max 100 characters |
| `website` | string (URL) | No | User's website URL | Must be valid URL |
| `interests` | array of strings | No | User's interests | Max 10 interests, each max 50 chars |
| `stage` | string | No | Career stage | Must be one of: student, junior, mid-level, senior, lead, manager, architect, other |
| `avatar_url` | string | No | URL to user's avatar | No validation |

## Response

### Success Response (200 OK)

```json
{
  "id": "user-uuid-from-token",
  "username": "username-from-token",
  "full_name": "Devesh Bhardwaj",
  "bio": "I am a disco dancer ta ta ta tannana",
  "company": "Hiwipay",
  "location": "Mumbai",
  "website": "",
  "interests": ["reading"],
  "stage": "",
  "avatar_url": null,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Error Responses

- **401 Unauthorized**: Invalid or missing authentication token
- **422 Unprocessable Entity**: Invalid payload format or validation errors
- **500 Internal Server Error**: Server error

## Important Notes

1. **Authentication Required**: The user must be authenticated to use this endpoint
2. **User ID and Username**: These are automatically fetched from the JWT token and should not be included in the payload
3. **Create or Update**: If no profile exists for the user, one will be created. If a profile exists, it will be updated
4. **Partial Updates**: Only the fields provided in the payload will be updated. Other fields will remain unchanged
5. **Username Generation**: For new profiles, the username is automatically generated from the user's email address

## Example Usage

### cURL Example

```bash
curl -X PUT "http://localhost:8000/profiles/me" \
  -H "Authorization: Bearer your_jwt_token_here" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Devesh Bhardwaj",
    "bio": "I am a disco dancer ta ta ta tannana",
    "company": "Hiwipay",
    "location": "Mumbai",
    "website": "",
    "interests": ["reading"],
    "stage": "",
    "avatar_url": null
  }'
```

### Python Example

```python
import requests

# Login to get token
login_response = requests.post("http://localhost:8000/auth/login", json={
    "email": "user@example.com",
    "password": "password123"
})
token = login_response.json()["access_token"]

# Update profile
profile_data = {
    "full_name": "Devesh Bhardwaj",
    "bio": "I am a disco dancer ta ta ta tannana",
    "company": "Hiwipay",
    "location": "Mumbai",
    "website": "",
    "interests": ["reading"],
    "stage": "",
    "avatar_url": None
}

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

response = requests.put("http://localhost:8000/profiles/me", 
                       json=profile_data, 
                       headers=headers)

if response.status_code == 200:
    profile = response.json()
    print(f"Profile updated: {profile['full_name']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```
