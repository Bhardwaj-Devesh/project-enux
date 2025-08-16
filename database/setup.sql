-- Playbook API Database Setup
-- Run this in your Supabase SQL editor

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    hashed_password TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create playbooks table
CREATE TABLE IF NOT EXISTS playbooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    blog_content TEXT,
    tags TEXT[] DEFAULT '{}',
    stage TEXT,
    owner_id UUID REFERENCES users(id) ON DELETE CASCADE,
    version TEXT DEFAULT 'v1',
    files JSONB DEFAULT '{}',
    summary TEXT,
    vector_embedding vector(768),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create file_vectors table for storing individual file embeddings
CREATE TABLE IF NOT EXISTS file_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    playbook_id UUID REFERENCES playbooks(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    content_type TEXT NOT NULL,
    embedding vector(768) NOT NULL,
    file_size INTEGER NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_playbooks_title_description 
ON playbooks USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '')));

CREATE INDEX IF NOT EXISTS idx_playbooks_tags 
ON playbooks USING gin(tags);

CREATE INDEX IF NOT EXISTS idx_playbooks_owner_id 
ON playbooks(owner_id);

CREATE INDEX IF NOT EXISTS idx_playbooks_stage 
ON playbooks(stage);

CREATE INDEX IF NOT EXISTS idx_playbooks_created_at 
ON playbooks(created_at DESC);

-- Create vector similarity index for playbooks
CREATE INDEX IF NOT EXISTS idx_playbooks_vector 
ON playbooks USING ivfflat (vector_embedding vector_cosine_ops) WITH (lists = 100);

-- Create indexes for file_vectors table
CREATE INDEX IF NOT EXISTS idx_file_vectors_playbook_id 
ON file_vectors(playbook_id);

CREATE INDEX IF NOT EXISTS idx_file_vectors_filename 
ON file_vectors(filename);

CREATE INDEX IF NOT EXISTS idx_file_vectors_content_type 
ON file_vectors(content_type);

-- Create vector similarity index for file_vectors
CREATE INDEX IF NOT EXISTS idx_file_vectors_embedding 
ON file_vectors USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create vector similarity search function for playbooks
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

-- Create vector similarity search function for file_vectors
CREATE OR REPLACE FUNCTION search_file_vectors(
    query_embedding vector(768),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    playbook_id UUID,
    filename TEXT,
    content_type TEXT,
    file_size INTEGER,
    metadata JSONB,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        fv.id,
        fv.playbook_id,
        fv.filename,
        fv.content_type,
        fv.file_size,
        fv.metadata,
        1 - (fv.embedding <=> query_embedding) as similarity
    FROM file_vectors fv
    WHERE fv.embedding IS NOT NULL
    AND 1 - (fv.embedding <=> query_embedding) > match_threshold
    ORDER BY fv.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_playbooks_updated_at 
    BEFORE UPDATE ON playbooks 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create RLS (Row Level Security) policies
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE playbooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE file_vectors ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY "Users can view own data" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can insert own data" ON users
    FOR INSERT WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update own data" ON users
    FOR UPDATE USING (auth.uid() = id);

-- Playbooks policies
CREATE POLICY "Users can view all playbooks" ON playbooks
    FOR SELECT USING (true);

CREATE POLICY "Users can insert own playbooks" ON playbooks
    FOR INSERT WITH CHECK (auth.uid() = owner_id);

CREATE POLICY "Users can update own playbooks" ON playbooks
    FOR UPDATE USING (auth.uid() = owner_id);

CREATE POLICY "Users can delete own playbooks" ON playbooks
    FOR DELETE USING (auth.uid() = owner_id);

-- File vectors policies
CREATE POLICY "Users can view all file vectors" ON file_vectors
    FOR SELECT USING (true);

CREATE POLICY "Users can insert file vectors" ON file_vectors
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Users can update file vectors" ON file_vectors
    FOR UPDATE USING (true);

CREATE POLICY "Users can delete file vectors" ON file_vectors
    FOR DELETE USING (true);

-- Insert sample data (optional)
INSERT INTO users (email, full_name) VALUES 
('demo@example.com', 'Demo User')
ON CONFLICT (email) DO NOTHING;

-- Create storage bucket (this needs to be done via Supabase dashboard or CLI)
-- supabase storage create playbooks

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO anon, authenticated; 
