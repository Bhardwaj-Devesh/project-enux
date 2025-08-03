# Playbook API Setup Guide

This guide will help you set up the complete Playbook API system with Supabase, Google Gemini, and vector search capabilities.

## Prerequisites

- Python 3.8+
- Supabase account
- Google API key (for Gemini)
- Git

## Step 1: Clone and Setup Project

```bash
# Clone the repository (if not already done)
git clone <repository-url>
cd project-enux

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Supabase Setup

### 2.1 Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Note down your project URL and API keys

### 2.2 Setup Database

**Option A: Using SQL Editor (Recommended)**
1. Go to your Supabase dashboard
2. Navigate to SQL Editor
3. Copy and paste the contents of `database/setup.sql`
4. Run the script

**Option B: Using Setup Script**
```bash
# Set environment variables first
export SUPABASE_URL="your_supabase_url"
export SUPABASE_SERVICE_ROLE_KEY="your_service_role_key"

# Run setup script
python scripts/setup_database.py
```

### 2.3 Create Storage Bucket

1. Go to Storage in your Supabase dashboard
2. Create a new bucket named `playbooks`
3. Set it to public (for file access)

## Step 3: Google Gemini Setup

### 3.1 Get Google API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Note down your API key

### 3.2 Environment Configuration

1. Copy the environment template:
```bash
cp env.example .env
```

2. Edit `.env` with your credentials:
```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Google Gemini Configuration
GOOGLE_API_KEY=your_google_api_key
GEMINI_MODEL=gemini-pro

# Application Configuration
SECRET_KEY=your_secret_key_for_jwt
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Storage Configuration
STORAGE_BUCKET_NAME=playbooks
MAX_FILE_SIZE=10485760

# Vector Database Configuration
VECTOR_DIMENSION=768
```

## Step 4: Run the Application

```bash
# Start the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Step 5: Test the API

### 5.1 Using the Example Script

```bash
# Run the example upload script
python examples/upload_playbook.py
```

### 5.2 Using curl

```bash
# Register a user
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "full_name": "Test User"
  }'

# Login
curl -X POST "http://localhost:8000/api/v1/auth/login-json" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }'

# Upload a playbook (replace YOUR_TOKEN with the access token from login)
curl -X POST "http://localhost:8000/api/v1/playbooks/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "title=GTM Strategy v1" \
  -F "description=Go-to-market strategy for startups" \
  -F "stage=pre-seed" \
  -F "tags=[\"GTM\", \"marketing\"]" \
  -F "files=@/path/to/your/file.pdf"
```

### 5.3 Using Python Requests

```python
import requests

# Base URL
base_url = "http://localhost:8000/api/v1"

# Register
response = requests.post(f"{base_url}/auth/register", json={
    "email": "test@example.com",
    "password": "testpassword123",
    "full_name": "Test User"
})

# Login
response = requests.post(f"{base_url}/auth/login-json", json={
    "email": "test@example.com",
    "password": "testpassword123"
})

token = response.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# Upload playbook
with open("your_file.pdf", "rb") as f:
    response = requests.post(
        f"{base_url}/playbooks/upload",
        headers=headers,
        data={
            "title": "GTM Strategy v1",
            "description": "Go-to-market strategy for startups",
            "stage": "pre-seed"
        },
        files={"files": f}
    )

print(response.json())
```

## Step 6: Run Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_playbooks.py

# Run with coverage
pytest --cov=app tests/
```

## API Endpoints Overview

### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login with form data
- `POST /api/v1/auth/login-json` - Login with JSON
- `GET /api/v1/auth/me` - Get current user info

### Playbooks
- `POST /api/v1/playbooks/upload` - Upload new playbook
- `GET /api/v1/playbooks/` - List all playbooks
- `GET /api/v1/playbooks/{id}` - Get specific playbook
- `PUT /api/v1/playbooks/{id}` - Update playbook
- `DELETE /api/v1/playbooks/{id}` - Delete playbook
- `GET /api/v1/playbooks/search/vector` - Vector similarity search
- `GET /api/v1/playbooks/search/text` - Text search
- `GET /api/v1/playbooks/{id}/status` - Get processing status

## Features

### ✅ Implemented
- User authentication with JWT tokens
- File upload and storage in Supabase
- AI-powered content analysis (Google Gemini)
- Automatic tag extraction
- Stage classification
- Vector embeddings for semantic search (768 dimensions)
- Text-based search with filters
- Background AI processing
- File type validation
- Error handling and logging

### 🔄 Processing Flow
1. User uploads playbook with files
2. Files are stored in Supabase Storage
3. Playbook metadata is saved to database
4. AI processing starts in background:
   - Extract text from all files
   - Generate summary using Gemini
   - Extract relevant tags
   - Classify recommended stage
   - Create vector embeddings (768 dimensions)
5. Results are stored in database
6. User can search using text or vector similarity

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check your Supabase URL and API keys
   - Ensure the database is properly set up

2. **File Upload Errors**
   - Check file size limits
   - Verify file types are allowed
   - Ensure storage bucket exists

3. **AI Processing Errors**
   - Verify Google API key is valid
   - Check API rate limits
   - Ensure sufficient credits

4. **Vector Search Not Working**
   - Verify pgvector extension is enabled
   - Check vector dimension matches (768)
   - Ensure embeddings are being created

### Debug Mode

```bash
# Run with debug logging
uvicorn app.main:app --reload --log-level debug
```

### Check Logs

```bash
# View application logs
tail -f logs/app.log
```

## Production Deployment

### Environment Variables
- Set `SECRET_KEY` to a strong random string
- Configure proper CORS origins
- Set appropriate file size limits
- Use production database credentials

### Security Considerations
- Enable HTTPS
- Configure proper CORS policies
- Set up rate limiting
- Use environment-specific configurations
- Enable logging and monitoring

### Scaling
- Use Redis for session management
- Implement caching for search results
- Consider CDN for file delivery
- Monitor API usage and costs

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation at `/docs`
3. Check the test files for usage examples
4. Review the example scripts

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request 
