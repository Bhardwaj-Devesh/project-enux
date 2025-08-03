# Vector Database Implementation

This document describes the vector database implementation for storing and searching file embeddings using Google's Gemini embedding API.

## Overview

The vector database functionality allows you to:
- Store file embeddings in a PostgreSQL database using the pgvector extension
- Search for similar files using vector similarity
- Retrieve file vectors for specific playbooks
- Delete file vectors when playbooks are deleted

## Architecture

### Components

1. **VectorService** (`app/services/vector_service.py`)
   - Handles all vector database operations
   - Creates embeddings using Google's Gemini API
   - Stores and retrieves vectors from Supabase

2. **Database Schema** (`database/setup.sql`)
   - `file_vectors` table for storing individual file embeddings
   - Vector similarity search functions
   - Proper indexing for performance

3. **API Endpoints** (`app/api/playbooks.py`)
   - `/playbooks/search/files` - Search files using vector similarity
   - `/{playbook_id}/files` - Get file vectors for a specific playbook

## Database Schema

### file_vectors Table

```sql
CREATE TABLE file_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    playbook_id UUID REFERENCES playbooks(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    embedding vector(768) NOT NULL,
    file_size INTEGER NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Indexes

- `idx_file_vectors_playbook_id` - For filtering by playbook
- `idx_file_vectors_filename` - For filtering by filename
- `idx_file_vectors_content_type` - For filtering by content type
- `idx_file_vectors_embedding` - Vector similarity index using IVFFlat

### Search Functions

- `search_file_vectors(query_embedding, match_threshold, match_count)` - Search for similar files
- `match_playbooks(query_embedding, match_threshold, match_count)` - Search for similar playbooks

## Usage

### Uploading Files with Vector Storage

When you upload a playbook with files, the system:

1. Extracts text content from each file
2. Creates embeddings using Google's Gemini API
3. Stores vectors in the `file_vectors` table
4. Creates the playbook in the database
5. Processes files with AI in the background

```python
# Example upload flow
files_for_vector_storage = []
for file_info in uploaded_files:
    text_content = await ai_service.extract_text_from_file(
        file_content, file_info.filename, file_info.content_type
    )
    files_for_vector_storage.append({
        "filename": file_info.filename,
        "content": text_content,
        "content_type": file_info.content_type
    })

# Store in vector database
vector_storage_result = await vector_service.store_file_vectors(
    files_for_vector_storage, playbook_id
)
```

### Searching Files

```python
# Search for similar files
results = await vector_service.search_similar_files("business strategy", limit=10)
```

### Getting File Vectors

```python
# Get all file vectors for a playbook
file_vectors = await vector_service.get_file_vectors_by_playbook(playbook_id)
```

## API Endpoints

### Search Files
```
GET /playbooks/search/files?query=your_search_query&limit=10
```

Response:
```json
[
  {
    "id": "uuid",
    "playbook_id": "uuid",
    "filename": "document.pdf",
    "content_type": "application/pdf",
    "file_size": 1024,
    "metadata": {...},
    "similarity": 0.85
  }
]
```

### Get Playbook Files
```
GET /playbooks/{playbook_id}/files
```

Response:
```json
[
  {
    "id": "uuid",
    "playbook_id": "uuid",
    "filename": "document.pdf",
    "content_type": "application/pdf",
    "embedding": [0.1, 0.2, ...],
    "file_size": 1024,
    "metadata": {...},
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

## Configuration

### Environment Variables

```env
GOOGLE_API_KEY=your_google_api_key
VECTOR_DIMENSION=768
```

### Settings

```python
# app/config.py
vector_dimension: int = 768  # Gemini embedding dimension
```

## Best Practices

### 1. Embedding Normalization

All embeddings are normalized to unit vectors for better similarity calculations:

```python
def _normalize_embedding(self, embedding: List[float]) -> List[float]:
    embedding_array = np.array(embedding)
    norm = np.linalg.norm(embedding_array)
    if norm > 0:
        normalized = embedding_array / norm
        return normalized.tolist()
    return embedding
```

### 2. Error Handling

The service includes comprehensive error handling:

```python
try:
    embedding = await self.create_file_embedding(content, filename, content_type)
except Exception as e:
    print(f"Error creating embedding for {filename}: {str(e)}")
    return [0.0] * settings.vector_dimension  # Fallback
```

### 3. Content Limiting

Text content is limited to avoid token limits:

```python
embedding_text = f"File: {filename}\nType: {content_type}\nContent: {file_content[:6000]}"
```

### 4. Metadata Storage

Additional metadata is stored for debugging and analysis:

```python
metadata = {
    "original_filename": file_info['filename'],
    "content_preview": file_info['content'][:200] + "..." if len(file_info['content']) > 200 else file_info['content']
}
```

## Debugging

### 1. Check Vector Storage

```python
# Test vector creation
embedding = await vector_service.create_file_embedding(
    "test content", "test.txt", "text/plain"
)
print(f"Embedding dimension: {len(embedding)}")
print(f"Embedding norm: {np.linalg.norm(np.array(embedding))}")
```

### 2. Check Database Connection

```python
# Test database operations
result = await vector_service.get_file_vectors_by_playbook("test-id")
print(f"Found {len(result)} file vectors")
```

### 3. Run Tests

```bash
# Run vector service tests
python -m pytest tests/test_vector_service.py -v
```

### 4. Monitor Logs

Check for these log messages:
- "Error creating embedding for {filename}: {error}"
- "Error storing vectors in database: {error}"
- "Warning: Vector storage failed for playbook {id}: {error}"

## Performance Considerations

### 1. Batch Processing

For large numbers of files, consider batching:

```python
# Process files in batches
batch_size = 10
for i in range(0, len(files), batch_size):
    batch = files[i:i + batch_size]
    await vector_service.store_file_vectors(batch, playbook_id)
```

### 2. Index Optimization

The vector index uses IVFFlat with 100 lists for good performance:

```sql
CREATE INDEX idx_file_vectors_embedding 
ON file_vectors USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

### 3. Memory Management

Embeddings are processed one at a time to avoid memory issues with large files.

## Troubleshooting

### Common Issues

1. **Embedding Creation Fails**
   - Check Google API key configuration
   - Verify text content is not too long
   - Check API rate limits

2. **Database Connection Issues**
   - Verify Supabase connection
   - Check pgvector extension is enabled
   - Verify table permissions

3. **Search Returns No Results**
   - Check similarity threshold (default: 0.7)
   - Verify embeddings are stored correctly
   - Check query embedding creation

### Debug Commands

```python
# Test embedding creation
python -c "
import asyncio
from app.services.vector_service import vector_service
async def test():
    embedding = await vector_service.create_file_embedding('test', 'test.txt', 'text/plain')
    print(f'Embedding: {len(embedding)} dimensions')
asyncio.run(test())
"

# Test database connection
python -c "
import asyncio
from app.services.vector_service import vector_service
async def test():
    result = await vector_service.get_file_vectors_by_playbook('test')
    print(f'Found {len(result)} vectors')
asyncio.run(test())
"
```

## Future Enhancements

1. **Batch Embedding Creation** - Process multiple files simultaneously
2. **Caching** - Cache frequently accessed embeddings
3. **Compression** - Compress embeddings for storage efficiency
4. **Analytics** - Track embedding quality and search performance
5. **Multi-modal** - Support for image and audio embeddings 
