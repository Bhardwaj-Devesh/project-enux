# 🔧 Vector Similarity NaN Fix

## **Problem Analysis**

The error `ValueError: Out of range float values are not JSON compliant` occurs because:

1. **Database Function Returns NaN**: The `match_playbooks` function returns `'NaN'` as a similarity score
2. **JSON Serialization Fails**: FastAPI cannot serialize `NaN` values to JSON
3. **Root Cause**: Vector similarity calculation fails due to edge cases (null vectors, zero magnitude, etc.)

## **Debug Information**

From the logs:
```
🔍 Debug - First result fields: ['id', 'title', 'description', 'tags', 'stage', 'owner_id', 'version', 'files', 'summary', 'similarity']
'similarity': 'NaN'
```

**Missing Fields**: Notice that `created_at` and `updated_at` are still missing from the database function response.

## **Root Causes**

### **1. NaN Similarity Calculation**
- Vector embeddings might be null or have zero magnitude
- Cosine similarity calculation fails when vectors are invalid
- Database function doesn't handle edge cases

### **2. Missing DateTime Fields**
- Database function still doesn't return `created_at` and `updated_at`
- Code handles this with fallbacks, but it's not ideal

## **✅ Fixes Applied**

### **1. Service Layer Fix (Immediate)**
- Added `math.isnan()` checks for NaN values
- Convert NaN to 0.0 similarity score
- Handle both string 'NaN' and float NaN
- Added comprehensive error handling

### **2. Database Function Fix (Recommended)**
- Updated function to handle edge cases
- Added CASE statements for null vectors
- Used COALESCE and NULLIF for NaN handling
- Added proper vector validation

## **Code Changes**

### **Service Layer (`app/services/supabase_service.py`)**
```python
# Handle NaN similarity scores
similarity = result["similarity"]
if similarity == 'NaN' or (isinstance(similarity, float) and math.isnan(similarity)):
    similarity = 0.0  # Default to 0 similarity for NaN values
elif isinstance(similarity, str):
    try:
        similarity = float(similarity)
        if math.isnan(similarity):
            similarity = 0.0
    except (ValueError, TypeError):
        similarity = 0.0
```

### **Database Function (`fix_vector_similarity.sql`)**
```sql
CASE 
    WHEN p.vector_embedding IS NULL THEN 0.0
    WHEN array_length(p.vector_embedding, 1) = 0 THEN 0.0
    WHEN query_embedding IS NULL THEN 0.0
    WHEN array_length(query_embedding, 1) = 0 THEN 0.0
    ELSE 
        COALESCE(
            NULLIF(1 - (p.vector_embedding <=> query_embedding), 'NaN'::float),
            0.0
        )
END as similarity
```

## **Testing Steps**

### **1. Test Current Fix**
```bash
# Test the immediate fix
python test_current_fix.py
```

### **2. Apply Database Fix**
1. Go to Supabase Dashboard > SQL Editor
2. Run the SQL from `fix_vector_similarity.sql`
3. Test again

### **3. Expected Results**
- ✅ No more JSON serialization errors
- ✅ Similarity scores are valid numbers (0.0 to 1.0)
- ✅ Vector search returns playbook IDs with scores
- ✅ All required fields are present

## **Verification**

After applying both fixes, the response should be:
```json
[
  {
    "playbook": {
      "id": "41e4b3cd-f9c4-4fd2-8ed9-0ad27e380d76",
      "title": "GTM Strategy v1",
      "description": "Go-to-market strategy for early-stage startups",
      "tags": ["GTM", "Strategy", "Early-Stage", "Startups"],
      "stage": "pre-seed",
      "owner_id": "be8c2067-d2c9-43ca-8b2f-f6019ded04ab",
      "version": "v1",
      "files": {"file.pdf": "https://..."},
      "created_at": "2025-08-16T04:08:14.429224Z",
      "updated_at": "2025-08-16T04:08:14.429224Z",
      "summary": "Based on the analysis...",
      "vector_embedding": [0.058341533, -0.07390659, ...]
    },
    "similarity_score": 0.85  // Valid number, not NaN
  }
]
```

## **Next Steps**

1. **Immediate**: The service layer fix should resolve the JSON error
2. **Database**: Run the SQL script to fix the root cause
3. **Verify**: Test with various queries to ensure stability
4. **Monitor**: Watch for any remaining edge cases

The vector search should now work correctly without NaN errors! 🎯
