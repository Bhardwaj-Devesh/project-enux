-- Update the match_playbooks function to include created_at and updated_at fields
-- Run this script in your Supabase SQL editor

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
