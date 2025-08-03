# Postman API Testing Guide

## 🚀 Quick Start

### 1. Start the Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Base URL
```
http://localhost:8000/api/v1
```

---

## 📤 Upload Playbook API (No Authentication Required)

### **Endpoint:** `POST /playbooks/upload`

### **URL:** `http://localhost:8000/api/v1/playbooks/upload`

### **Headers:**
```
Content-Type: multipart/form-data
```

### **Body (form-data):**

| Key | Type | Required | Value | Description |
|-----|------|----------|-------|-------------|
| `title` | Text | ✅ | `GTM Strategy v1` | Playbook title |
| `description` | Text | ✅ | `Go-to-market strategy for early-stage startups` | Playbook description |
| `stage` | Text | ❌ | `pre-seed` | Company stage (optional) |
| `tags` | Text | ❌ | `["GTM", "marketing", "strategy"]` | JSON array of tags |
| `version` | Text | ❌ | `v1` | Version (default: v1) |
| `owner_id` | Text | ❌ | `demo_user_123` | Owner ID (default: demo_user_123) |
| `files` | File | ✅ | `[file1.pdf, file2.md]` | One or more files |

---

## 📋 Postman Setup Instructions

### **Step 1: Create New Request**
1. Open Postman
2. Click "New" → "Request"
3. Set method to `POST`
4. Enter URL: `http://localhost:8000/api/v1/playbooks/upload`

### **Step 2: Set Headers**
- Click "Headers" tab
- Add: `Content-Type: multipart/form-data`

### **Step 3: Set Body**
1. Click "Body" tab
2. Select "form-data"
3. Add the following key-value pairs:

#### **Text Fields:**
```
title: GTM Strategy v1
description: Comprehensive go-to-market strategy for early-stage startups with focus on market research, positioning, and channel strategy.
stage: pre-seed
tags: ["GTM", "marketing", "strategy", "startup"]
version: v1
owner_id: demo_user_123
```

#### **File Fields:**
```
files: [Select your PDF/MD/CSV files]
```

**Note:** For multiple files, add multiple `files` keys with different files.

---

## 🧪 Test Examples

### **Example 1: Basic Upload**
```json
{
  "title": "GTM Strategy v1",
  "description": "Go-to-market strategy for early-stage startups",
  "stage": "pre-seed",
  "tags": ["GTM", "marketing"],
  "version": "v1",
  "owner_id": "demo_user_123",
  "files": [file1.pdf, file2.md]
}
```

### **Example 2: Minimal Upload**
```json
{
  "title": "Sales Playbook",
  "description": "Sales strategy and processes",
  "files": [sales_guide.pdf]
}
```

### **Example 3: Multiple Files**
```json
{
  "title": "Complete Business Plan",
  "description": "Full business plan with financial projections",
  "stage": "seed",
  "tags": ["business-plan", "finance", "strategy"],
  "files": [business_plan.pdf, financial_model.xlsx, market_research.md]
}
```

---

## 📁 Supported File Types

| File Type | Extension | Content-Type |
|-----------|-----------|--------------|
| PDF | `.pdf` | `application/pdf` |
| Markdown | `.md` | `text/markdown` |
| Text | `.txt` | `text/plain` |
| CSV | `.csv` | `text/csv` |
| Excel | `.xlsx` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| JSON | `.json` | `application/json` |
| ZIP | `.zip` | `application/zip` |

---

## 📊 Expected Response

### **Success Response (200):**
```json
{
  "playbook": {
    "id": "uuid-here",
    "title": "GTM Strategy v1",
    "description": "Go-to-market strategy for early-stage startups",
    "tags": ["GTM", "marketing"],
    "stage": "pre-seed",
    "owner_id": "demo_user_123",
    "version": "v1",
    "files": {
      "document.pdf": "https://supabase-url/storage/...",
      "guide.md": "https://supabase-url/storage/..."
    },
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "summary": null,
    "vector_embedding": null
  },
  "files": [
    {
      "filename": "document.pdf",
      "content_type": "application/pdf",
      "size": 1024000,
      "file_path": "uuid-here.pdf"
    }
  ],
  "processing_status": "processing",
  "message": "Playbook uploaded successfully. AI processing started in background."
}
```

### **Error Response (400/500):**
```json
{
  "detail": "Error message here"
}
```

---

## 🔍 Check Processing Status

### **Endpoint:** `GET /playbooks/{playbook_id}/status`

### **URL:** `http://localhost:8000/api/v1/playbooks/{playbook_id}/status`

### **Response:**
```json
{
  "status": "completed",
  "message": "AI processing completed successfully",
  "summary": "This playbook provides a comprehensive go-to-market strategy...",
  "extracted_tags": ["GTM", "marketing", "strategy"],
  "vector_embedding": [0.1, 0.2, 0.3, ...]
}
```

---

## 🧪 Sample Test Files

Create these sample files for testing:

### **1. sample.md**
```markdown
# GTM Strategy Playbook

## Overview
This playbook provides a comprehensive go-to-market strategy for early-stage startups.

## Key Components
- Market Research
- Product Positioning
- Channel Strategy
- Revenue Model

## Implementation Timeline
- Month 1-2: Market research and positioning
- Month 3-4: Channel setup and testing
- Month 5-6: Full launch and optimization
```

### **2. metrics.csv**
```csv
Metric,Target,Current,Status
Customer Acquisition Cost,$50,$75,Needs Improvement
Conversion Rate,5%,3.2%,Below Target
Monthly Recurring Revenue,$10K,$8.5K,On Track
```

### **3. config.json**
```json
{
  "playbook_info": {
    "title": "GTM Strategy v1",
    "version": "1.0",
    "tags": ["GTM", "marketing", "strategy"]
  },
  "target_audience": {
    "primary": "Early-stage SaaS startups"
  }
}
```

---

## 🚨 Common Issues & Solutions

### **1. File Size Too Large**
- **Error:** `Total file size exceeds 10485760 bytes`
- **Solution:** Reduce file size or increase `MAX_FILE_SIZE` in config

### **2. Invalid File Type**
- **Error:** `File type application/octet-stream not allowed`
- **Solution:** Use supported file types only

### **3. Missing Required Fields**
- **Error:** `Field required`
- **Solution:** Ensure `title`, `description`, and `files` are provided

### **4. Database Connection Error**
- **Error:** `Failed to create playbook`
- **Solution:** Check Supabase configuration in `.env` file

---

## 🔧 Environment Setup

Create a `.env` file in your project root:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Google Gemini Configuration
GOOGLE_API_KEY=your_google_api_key
GEMINI_MODEL=gemini-pro

# Application Configuration
SECRET_KEY=test_secret_key_for_development
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Storage Configuration
STORAGE_BUCKET_NAME=playbooks
MAX_FILE_SIZE=10485760

# Vector Database Configuration
VECTOR_DIMENSION=768
```

---

## 📝 Testing Checklist

- [ ] Server is running on `http://localhost:8000`
- [ ] Environment variables are set
- [ ] Supabase project is configured
- [ ] Storage bucket exists
- [ ] Test files are ready
- [ ] Postman request is configured correctly
- [ ] Files are under size limit
- [ ] File types are supported

---

## 🎯 Quick Test Command

```bash
# Test with curl (replace with your actual file path)
curl -X POST "http://localhost:8000/api/v1/playbooks/upload" \
  -F "title=Test Playbook" \
  -F "description=Test description" \
  -F "stage=pre-seed" \
  -F "tags=[\"test\", \"demo\"]" \
  -F "files=@/path/to/your/file.pdf"
``` 
