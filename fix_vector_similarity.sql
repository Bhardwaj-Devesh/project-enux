-- Fix the match_playbooks function to handle NaN similarity scores
-- Run this script in your Supabase SQL Editor

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
        -- Handle edge cases in similarity calculation
        CASE 
            WHEN p.vector_embedding IS NULL THEN 0.0
            WHEN array_length(p.vector_embedding, 1) = 0 THEN 0.0
            WHEN query_embedding IS NULL THEN 0.0
            WHEN array_length(query_embedding, 1) = 0 THEN 0.0
            ELSE 
                -- Use COALESCE to handle any remaining NaN values
                COALESCE(
                    NULLIF(1 - (p.vector_embedding <=> query_embedding), 'NaN'::float),
                    0.0
                )
        END as similarity
    FROM playbooks p
    WHERE p.vector_embedding IS NOT NULL
    AND array_length(p.vector_embedding, 1) > 0
    AND 1 - (p.vector_embedding <=> query_embedding) > match_threshold
    ORDER BY p.vector_embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
