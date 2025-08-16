# 🔧 Fix Vector Search Issue

## **Problem Analysis**
The error `'created_at'` occurs because the database function `match_playbooks` doesn't return the `created_at` and `updated_at` fields, but our code expects them.

## **Root Cause**
The database function `match_playbooks` in Supabase needs to be updated to include these fields in its return table definition.

## **Solution Steps**

### **Step 1: Update Database Function in Supabase**

1. **Go to your Supabase Dashboard**
2. **Navigate to SQL Editor**
3. **Run this SQL script:**

```sql
-- Update the match_playbooks function to include created_at and updated_at fields
CREATE OR REPLACE FUNCTION match_playbooks(
    query_embedding vector(768),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    title TEXT,
    description TEXT,
    tags TEXT[],
    stage TEXT,
    owner_id UUID,
    version TEXT,
    files JSONB,
    summary TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.title,
        p.description,
        p.tags,
        p.stage,
        p.owner_id,
        p.version,
        p.files,
        p.summary,
        p.created_at,
        p.updated_at,
        1 - (p.vector_embedding <=> query_embedding) as similarity
    FROM playbooks p
    WHERE p.vector_embedding IS NOT NULL
    AND 1 - (p.vector_embedding <=> query_embedding) > match_threshold
    ORDER BY p.vector_embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
```

### **Step 2: Test the Fix**

After running the SQL script, test the vector search:

```bash
# Test with curl
curl "http://localhost:8000/api/v1/playbooks/search/vector?query=sales%20strategy&limit=5"

# Or use the test script
python test_vector_search.py
```

### **Step 3: Expected Results**

After the fix, you should see:
- ✅ No more `'created_at'` errors
- ✅ Vector search returns playbook IDs with similarity scores
- ✅ All required fields are present in the response

## **Temporary Workaround (Already Implemented)**

If you can't update the database function immediately, the code has been updated to handle missing datetime fields gracefully by:
- Using `result.get("created_at")` instead of `result["created_at"]`
- Providing fallback datetime values when fields are missing

## **Debug Information**

The updated code now includes debug logging to show:
- What fields are actually returned by the database function
- The structure of the first result

This will help identify any remaining issues.

## **Verification**

After applying the fix, the vector search should work correctly and return:

```json
[
  {
    "playbook": {
      "id": "6c697cd3-8356-4434-8b22-6d221339a1cd",
      "title": "Sales Strategies",
      "description": "Go-to-market strategy for early-stage startups",
      "tags": ["sales", "strategy", "startup"],
      "stage": "seed",
      "owner_id": "d4df2f6b-f995-44bf-8f49-61dd8399b3ba",
      "version": "v1",
      "files": {"sales.pdf": "https://..."},
      "created_at": "2025-08-16T04:08:14.429224Z",
      "updated_at": "2025-08-16T04:08:14.429224Z",
      "summary": "This playbook outlines five strategies...",
      "vector_embedding": [0.058341533, -0.07390659, ...]
    },
    "similarity_score": 0.85
  }
]
```

## **Next Steps**

1. **Run the SQL script in Supabase**
2. **Test the vector search API**
3. **Verify all fields are present**
4. **Remove debug logging if everything works**

The vector search should now work correctly! 🎯
