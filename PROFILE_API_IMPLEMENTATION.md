# Profile API Implementation

This document describes the implementation of the Profile API service for the Playbook API project.

## Overview

The Profile API provides endpoints for managing user profiles, including:
- **Automatic profile creation during user registration**
- Retrieving user profile information
- Creating and updating profiles
- Uploading profile avatars
- Searching profiles
- Filtering profiles by career stage

## Architecture

### Components

1. **Models** (`app/models/profile.py`)
   - `ProfileUpdate`: Pydantic model for profile updates with validation
   - `ProfileResponse`: Pydantic model for profile responses
   - `AvatarUploadResponse`: Pydantic model for avatar upload responses

2. **Service** (`app/services/profile_service.py`)
   - `ProfileService`: Business logic for profile operations
   - Database interactions via Supabase
   - Error handling and logging

3. **API Router** (`app/api/profiles.py`)
   - FastAPI router with all profile endpoints
   - Authentication integration
   - Request/response handling

4. **Authentication Integration** (`app/api/auth.py`)
   - **Automatic profile creation during user registration**
   - Username extraction from email address
   - Seamless integration with existing auth system

5. **Database Schema** (`database/profile_schema.sql`)
   - PostgreSQL table definition
   - Indexes for performance
   - Row Level Security (RLS) policies
   - Triggers for automatic timestamp updates

## Automatic Profile Creation

### Registration Flow

When a user registers through the `/auth/register` endpoint, the system automatically:

1. **Creates the user account** in the authentication system
2. **Extracts username** from the email address (everything before `@`)
3. **Creates a profile entry** with the user's full name and extracted username
4. **Returns access token** for immediate use

### Username Generation

- **Source**: Email address provided during registration
- **Format**: `user@example.com` → username: `user`
- **Uniqueness**: Enforced by database constraint
- **Fallback**: If email parsing fails, uses user ID as username

### Example Registration Flow

```json
POST /api/v1/auth/register
{
  "email": "john.doe@example.com",
  "password": "securepassword123",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "user": {
    "id": "user-uuid-123",
    "email": "john.doe@example.com",
    "full_name": "John Doe",
    "created_at": "2024-01-15T10:30:00Z"
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

**Profile automatically created:**
```json
{
  "id": "user-uuid-123",
  "username": "john.doe",
  "full_name": "John Doe",
  "bio": null,
  "company": null,
  "location": null,
  "website": null,
  "interests": [],
  "stage": null,
  "avatar_url": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

## API Endpoints

### Base URL
```
http://localhost:8000/api/v1/profiles
```

### Authentication
All endpoints require Bearer token authentication:
```
Authorization: Bearer <access_token>
```

### 1. GET /profiles/me
Retrieves the current user's profile information.

**Response:**
```json
{
  "id": "user-uuid-123",
  "username": "john_doe",
  "full_name": "John Doe",
  "bio": "Full-stack developer passionate about React and Node.js",
  "company": "Tech Corp",
  "location": "San Francisco, CA",
  "website": "https://johndoe.dev",
  "interests": ["React", "Node.js", "TypeScript", "Open Source"],
  "stage": "senior",
  "avatar_url": "https://example.com/avatar.jpg",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-20T14:45:00Z"
}
```

### 2. PUT /profiles/me
Updates the current user's profile. Creates a new profile if one doesn't exist.

**Request Body:**
```json
{
  "full_name": "John Doe",
  "bio": "Full-stack developer passionate about React and Node.js",
  "company": "Tech Corp",
  "location": "San Francisco, CA",
  "website": "https://johndoe.dev",
  "interests": ["React", "Node.js", "TypeScript", "Open Source"],
  "stage": "senior"
}
```

**Response:** Same as GET /profiles/me

### 3. POST /profiles/me/avatar
Uploads a profile picture for the user.

**Request:** Multipart form data with file field 'avatar'

**Response:**
```json
{
  "avatar_url": "https://storage.example.com/avatars/user-uuid-123.jpg",
  "message": "Avatar uploaded successfully"
}
```

### 4. GET /profiles/search
Searches profiles by name, bio, or interests.

**Query Parameters:**
- `query` (required): Search term (minimum 2 characters)
- `limit` (optional): Maximum number of results (default: 10)

**Response:** Array of ProfileResponse objects

### 5. GET /profiles/stage/{stage}
Gets profiles by career stage.

**Path Parameters:**
- `stage`: Career stage (student, junior, mid-level, senior, lead, manager, architect, other)

**Query Parameters:**
- `limit` (optional): Maximum number of results (default: 10)

**Response:** Array of ProfileResponse objects

## Data Validation

### Profile Fields

| Field | Type | Max Length | Validation |
|-------|------|------------|------------|
| full_name | string | 100 chars | Optional |
| bio | string | 500 chars | Optional |
| company | string | 100 chars | Optional |
| location | string | 100 chars | Optional |
| website | URL | 255 chars | Must be valid URL format |
| interests | array | 10 items, 50 chars each | Optional |
| stage | string | 20 chars | Must be one of valid stages |

### Valid Career Stages
- student
- junior
- mid-level
- senior
- lead
- manager
- architect
- other

## Database Schema

### Profiles Table
```sql
CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    username VARCHAR(50) NOT NULL UNIQUE,
    full_name VARCHAR(100),
    bio TEXT,
    company VARCHAR(100),
    location VARCHAR(100),
    website VARCHAR(255),
    interests TEXT[],
    stage VARCHAR(20) CHECK (stage IN ('student', 'junior', 'mid-level', 'senior', 'lead', 'manager', 'architect', 'other')),
    avatar_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Indexes
- `idx_profiles_username`: For username lookups
- `idx_profiles_stage`: For stage-based queries
- `idx_profiles_created_at`: For chronological sorting

### Row Level Security (RLS)
- Users can only access their own profile for read/write operations
- Public read access for search functionality
- Automatic cleanup when user account is deleted

## Error Handling

### HTTP Status Codes
- `200 OK`: Successful operation
- `201 Created`: Profile created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Missing or invalid authentication
- `404 Not Found`: Profile not found
- `413 Payload Too Large`: File size exceeds limit
- `422 Unprocessable Entity`: Validation errors
- `500 Internal Server Error`: Server error

### Error Response Format
```json
{
  "detail": "Error message description"
}
```

## Security Considerations

1. **Authentication**: All endpoints require valid JWT tokens
2. **Authorization**: Users can only access/modify their own profiles
3. **Input Validation**: Comprehensive validation for all fields
4. **File Upload Security**: File type and size validation for avatars
5. **SQL Injection Prevention**: Using parameterized queries via Supabase
6. **XSS Prevention**: Input sanitization and output encoding
7. **Username Uniqueness**: Enforced at database level

## Performance Optimizations

1. **Database Indexes**: Strategic indexes for common query patterns
2. **Connection Pooling**: Supabase handles connection management
3. **Caching**: Consider implementing Redis for frequently accessed profiles
4. **Pagination**: Limit parameter for large result sets
5. **Automatic Profile Creation**: No additional API calls needed after registration

## Testing

### Test Files
- `test_profile_api.py`: Comprehensive API endpoint testing
- `test_profile_registration.py`: **Profile creation during registration testing**

### Running Tests
```bash
# Test profile API endpoints
python test_profile_api.py

# Test profile creation during registration
python test_profile_registration.py
```

### Registration Test Coverage
- ✅ Automatic profile creation during registration
- ✅ Username extraction from email
- ✅ Unique username enforcement
- ✅ Profile retrieval after registration
- ✅ Multiple user registration scenarios

## Integration

### Frontend Integration
The Profile API is designed to work with the existing frontend Profile component. Key integration points:

1. **API Base URL**: Configured in frontend environment
2. **Authentication**: JWT token handling
3. **Error Handling**: Consistent error response format
4. **Data Validation**: Client-side validation matching server-side rules
5. **Automatic Profile Creation**: No additional setup required after registration

### Existing API Integration
- Integrates with existing authentication system
- Uses same Supabase service pattern
- Follows established error handling patterns
- Maintains consistent API response formats
- **Seamless profile creation during registration**

## Environment Variables

Add these to your `.env` file:
```env
# Profile API Configuration
MAX_AVATAR_SIZE=5242880  # 5MB in bytes
ALLOWED_AVATAR_TYPES=image/jpeg,image/png,image/gif
STORAGE_BUCKET=avatars
```

## Future Enhancements

1. **Avatar Storage**: Integrate with Supabase Storage or AWS S3
2. **Profile Verification**: Add verification badges
3. **Social Links**: Add social media profile links
4. **Profile Analytics**: Track profile views and interactions
5. **Bulk Operations**: Batch profile updates
6. **Profile Templates**: Predefined profile templates
7. **Export/Import**: Profile data export functionality
8. **Username Customization**: Allow users to change their username
9. **Profile Completion**: Track profile completion percentage

## Deployment

### Database Setup
1. Run the profile schema SQL:
```bash
psql -d your_database -f database/profile_schema.sql
```

### Application Deployment
1. Ensure all dependencies are installed
2. Set up environment variables
3. Deploy the FastAPI application
4. Test all endpoints including registration flow

## Monitoring and Logging

The Profile API includes comprehensive logging:
- Request/response logging
- Error tracking
- Performance metrics
- Database query logging
- **Profile creation during registration logging**

Logs are structured and can be integrated with monitoring systems like:
- ELK Stack
- Prometheus/Grafana
- CloudWatch
- Application Insights

## Support and Maintenance

### Common Issues
1. **Profile Not Found**: Check if user has created a profile (should be automatic)
2. **Validation Errors**: Verify field constraints and data types
3. **Authentication Issues**: Ensure valid JWT token
4. **Database Connection**: Check Supabase configuration
5. **Username Conflicts**: Check for duplicate usernames in database

### Maintenance Tasks
1. **Regular Backups**: Database backup procedures
2. **Index Maintenance**: Monitor and optimize database indexes
3. **Security Updates**: Keep dependencies updated
4. **Performance Monitoring**: Track API response times
5. **Profile Cleanup**: Monitor orphaned profiles

## Conclusion

The Profile API provides a robust, secure, and scalable solution for user profile management. It follows RESTful principles, includes comprehensive validation, and integrates seamlessly with the existing Playbook API infrastructure.

**Key Features:**
- ✅ Automatic profile creation during user registration
- ✅ Username extraction from email addresses
- ✅ Comprehensive validation and error handling
- ✅ Production-ready security measures
- ✅ Seamless integration with existing auth system

The implementation is production-ready and includes all necessary security measures, error handling, and performance optimizations.
