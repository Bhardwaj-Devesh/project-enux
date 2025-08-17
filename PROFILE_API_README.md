# Profile API - Quick Start Guide

This guide will help you get the Profile API up and running quickly.

## 🚀 Quick Start

### 1. Database Setup

First, set up the database schema:

```bash
# Run the profile schema setup
python scripts/setup_profile_schema.py
```

### 2. Start the API Server

```bash
# Start the FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Test the API

```bash
# Test profile API endpoints
python test_profile_api.py

# Test profile creation during registration
python test_profile_registration.py
```

## 🎯 Automatic Profile Creation

When a user registers through `/auth/register`, a profile is automatically created with:
- **Username**: Extracted from email (e.g., `john.doe@example.com` → `john.doe`)
- **Full Name**: From registration data
- **Unique Username**: Enforced at database level

No additional API calls needed after registration!

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/profiles/me` | Get current user's profile |
| PUT | `/api/v1/profiles/me` | Update current user's profile |
| POST | `/api/v1/profiles/me/avatar` | Upload profile avatar |
| GET | `/api/v1/profiles/search` | Search profiles |
| GET | `/api/v1/profiles/stage/{stage}` | Get profiles by career stage |

## 🔐 Authentication

All endpoints require Bearer token authentication:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8000/api/v1/profiles/me
```

## 📝 Example Usage

### Get Profile
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/v1/profiles/me
```

### Update Profile
```bash
curl -X PUT \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "full_name": "John Doe",
       "bio": "Full-stack developer",
       "company": "Tech Corp",
       "location": "San Francisco, CA",
       "website": "https://johndoe.dev",
       "interests": ["React", "Node.js"],
       "stage": "senior"
     }' \
     http://localhost:8000/api/v1/profiles/me
```

### Upload Avatar
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -F "avatar=@/path/to/your/image.jpg" \
     http://localhost:8000/api/v1/profiles/me/avatar
```

## 🗄️ Database Schema

The Profile API uses a PostgreSQL table with the following structure:

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
    stage VARCHAR(20),
    avatar_url VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 🔧 Configuration

Add these environment variables to your `.env` file:

```env
# Profile API Configuration
MAX_AVATAR_SIZE=5242880  # 5MB in bytes
ALLOWED_AVATAR_TYPES=image/jpeg,image/png,image/gif
STORAGE_BUCKET=avatars
```

## 📊 Validation Rules

| Field | Type | Max Length | Validation |
|-------|------|------------|------------|
| full_name | string | 100 chars | Optional |
| bio | string | 500 chars | Optional |
| company | string | 100 chars | Optional |
| location | string | 100 chars | Optional |
| website | URL | 255 chars | Must be valid URL |
| interests | array | 10 items, 50 chars each | Optional |
| stage | string | 20 chars | Must be valid stage |

### Valid Career Stages
- student
- junior
- mid-level
- senior
- lead
- manager
- architect
- other

## 🧪 Testing

The Profile API includes a comprehensive test suite:

```bash
# Run all tests
python test_profile_api.py

# Expected output:
# 🚀 Starting Profile API Tests...
# ✅ Authentication successful
# ✅ Profile retrieved successfully
# ✅ Profile updated successfully
# ✅ Partial profile update successful
# ✅ Validation error caught for invalid stage
# ✅ Search successful, found X profiles
# ✅ Stage search successful, found X senior profiles
# 🎉 All tests passed! Profile API is working correctly.
```

## 🔍 API Documentation

Once the server is running, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🚨 Error Handling

The API returns appropriate HTTP status codes:

- `200 OK`: Successful operation
- `201 Created`: Profile created
- `400 Bad Request`: Invalid request
- `401 Unauthorized`: Missing/invalid token
- `404 Not Found`: Profile not found
- `413 Payload Too Large`: File too large
- `422 Unprocessable Entity`: Validation errors
- `500 Internal Server Error`: Server error

## 🔒 Security Features

- JWT token authentication
- Row Level Security (RLS)
- Input validation and sanitization
- File upload security
- SQL injection prevention

## 📈 Performance

- Database indexes for common queries
- Connection pooling via Supabase
- Efficient query patterns
- Pagination support

## 🆘 Troubleshooting

### Common Issues

1. **Profile Not Found (404)**
   - User hasn't created a profile yet
   - Use PUT `/profiles/me` to create one

2. **Authentication Error (401)**
   - Check if JWT token is valid
   - Ensure token is in Authorization header

3. **Validation Error (422)**
   - Check field constraints
   - Verify data types and formats

4. **Database Connection Error**
   - Check Supabase configuration
   - Verify environment variables

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 Additional Resources

- [Full API Documentation](PROFILE_API_IMPLEMENTATION.md)
- [Database Schema](database/profile_schema.sql)
- [Test Suite](test_profile_api.py)
- [Setup Script](scripts/setup_profile_schema.py)

## 🤝 Contributing

1. Follow the existing code patterns
2. Add tests for new features
3. Update documentation
4. Ensure all tests pass

## 📄 License

This Profile API is part of the Playbook API project.
