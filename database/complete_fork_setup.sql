-- Complete Fork Functionality Database Setup
-- This script ensures all necessary tables and columns exist for fork functionality
-- Run this in your Supabase SQL editor

-- ==========================================
-- 1. ENSURE USERS TABLE EXISTS
-- ==========================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    hashed_password TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==========================================
-- 2. ENSURE PLAYBOOKS TABLE EXISTS
-- ==========================================
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

-- Add version management columns if they don't exist
ALTER TABLE playbooks 
ADD COLUMN IF NOT EXISTS latest_version INT DEFAULT 1,
ADD COLUMN IF NOT EXISTS current_version INT DEFAULT 1;

-- ==========================================
-- 3. ENSURE USER_PLAYBOOKS TABLE EXISTS
-- ==========================================
CREATE TABLE IF NOT EXISTS user_playbooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    original_playbook_id UUID REFERENCES playbooks(id) ON DELETE CASCADE,
    forked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version TEXT DEFAULT 'v1',
    license TEXT,
    status TEXT DEFAULT 'active',
    UNIQUE(user_id, original_playbook_id) -- Prevent duplicate forks
);

-- Add version management columns if they don't exist
ALTER TABLE user_playbooks 
ADD COLUMN IF NOT EXISTS base_version INT DEFAULT 1,
ADD COLUMN IF NOT EXISTS last_sync_version INT DEFAULT 1;

-- ==========================================
-- 4. ENSURE PLAYBOOK_FILES TABLE EXISTS
-- ==========================================
CREATE TABLE IF NOT EXISTS playbook_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    playbook_id UUID REFERENCES playbooks(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    file_size INTEGER,
    content_type TEXT,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_modified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Add version management columns if they don't exist
ALTER TABLE playbook_files 
ADD COLUMN IF NOT EXISTS checksum TEXT,
ADD COLUMN IF NOT EXISTS version INT DEFAULT 1,
ADD COLUMN IF NOT EXISTS version_created INT DEFAULT 1,
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;

-- ==========================================
-- 5. ENSURE USER_PLAYBOOK_FILES TABLE EXISTS
-- ==========================================
CREATE TABLE IF NOT EXISTS user_playbook_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_playbook_id UUID REFERENCES user_playbooks(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL, -- Relative path within the playbook
    file_type TEXT NOT NULL,
    storage_path TEXT NOT NULL, -- Full storage URL/path
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_modified_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version TEXT DEFAULT 'v1'
);

-- Add version management columns if they don't exist
ALTER TABLE user_playbook_files 
ADD COLUMN IF NOT EXISTS checksum TEXT,
ADD COLUMN IF NOT EXISTS version INT DEFAULT 1,
ADD COLUMN IF NOT EXISTS version_created INT DEFAULT 1,
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;

-- ==========================================
-- 6. CREATE INDEXES FOR PERFORMANCE
-- ==========================================

-- Users table indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Playbooks table indexes
CREATE INDEX IF NOT EXISTS idx_playbooks_owner_id ON playbooks(owner_id);
CREATE INDEX IF NOT EXISTS idx_playbooks_latest_version ON playbooks(latest_version);
CREATE INDEX IF NOT EXISTS idx_playbooks_current_version ON playbooks(current_version);

-- User playbooks table indexes
CREATE INDEX IF NOT EXISTS idx_user_playbooks_user_id ON user_playbooks(user_id);
CREATE INDEX IF NOT EXISTS idx_user_playbooks_original_playbook_id ON user_playbooks(original_playbook_id);
CREATE INDEX IF NOT EXISTS idx_user_playbooks_forked_at ON user_playbooks(forked_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_playbooks_base_version ON user_playbooks(base_version);
CREATE INDEX IF NOT EXISTS idx_user_playbooks_last_sync_version ON user_playbooks(last_sync_version);

-- Playbook files table indexes
CREATE INDEX IF NOT EXISTS idx_playbook_files_playbook_id ON playbook_files(playbook_id);
CREATE INDEX IF NOT EXISTS idx_playbook_files_checksum ON playbook_files(checksum);
CREATE INDEX IF NOT EXISTS idx_playbook_files_version_created ON playbook_files(playbook_id, version_created);
CREATE INDEX IF NOT EXISTS idx_playbook_files_active ON playbook_files(playbook_id, is_active) WHERE is_active = true;

-- User playbook files table indexes
CREATE INDEX IF NOT EXISTS idx_user_playbook_files_user_playbook_id ON user_playbook_files(user_playbook_id);
CREATE INDEX IF NOT EXISTS idx_user_playbook_files_file_type ON user_playbook_files(file_type);
CREATE INDEX IF NOT EXISTS idx_user_playbook_files_checksum ON user_playbook_files(checksum);
CREATE INDEX IF NOT EXISTS idx_user_playbook_files_version_created ON user_playbook_files(user_playbook_id, version_created);
CREATE INDEX IF NOT EXISTS idx_user_playbook_files_active ON user_playbook_files(user_playbook_id, is_active) WHERE is_active = true;

-- ==========================================
-- 7. CREATE TRIGGERS FOR UPDATED_AT COLUMNS
-- ==========================================

-- Create the update_updated_at_column function if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_playbooks_updated_at ON playbooks;
CREATE TRIGGER update_playbooks_updated_at 
    BEFORE UPDATE ON playbooks 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_playbooks_updated_at ON user_playbooks;
CREATE TRIGGER update_user_playbooks_updated_at 
    BEFORE UPDATE ON user_playbooks 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_playbook_files_modified_at ON playbook_files;
CREATE TRIGGER update_playbook_files_modified_at 
    BEFORE UPDATE ON playbook_files 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_user_playbook_files_modified_at ON user_playbook_files;
CREATE TRIGGER update_user_playbook_files_modified_at 
    BEFORE UPDATE ON user_playbook_files 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==========================================
-- 8. CREATE VERSION MANAGEMENT FUNCTIONS
-- ==========================================

-- Function to get files for a specific version
CREATE OR REPLACE FUNCTION get_playbook_files_for_version(
    p_playbook_id UUID,
    p_version INT
)
RETURNS TABLE (
    id UUID,
    file_name TEXT,
    file_type TEXT,
    storage_path TEXT,
    version_created INT,
    is_active BOOLEAN
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pf.id,
        pf.file_name,
        pf.file_type,
        pf.storage_path,
        pf.version_created,
        pf.is_active
    FROM playbook_files pf
    WHERE pf.playbook_id = p_playbook_id
    AND pf.version_created <= p_version
    AND pf.is_active = true
    ORDER BY pf.file_name;
END;
$$;

-- Function to get user playbook files for a specific version
CREATE OR REPLACE FUNCTION get_user_playbook_files_for_version(
    p_user_playbook_id UUID,
    p_version INT
)
RETURNS TABLE (
    id UUID,
    file_path TEXT,
    file_type TEXT,
    storage_path TEXT,
    version_created INT,
    is_active BOOLEAN
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        upf.id,
        upf.file_path,
        upf.file_type,
        upf.storage_path,
        upf.version_created,
        upf.is_active
    FROM user_playbook_files upf
    WHERE upf.user_playbook_id = p_user_playbook_id
    AND upf.version_created <= p_version
    AND upf.is_active = true
    ORDER BY upf.file_path;
END;
$$;

-- ==========================================
-- 9. SET UP ROW LEVEL SECURITY (RLS)
-- ==========================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE playbooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_playbooks ENABLE ROW LEVEL SECURITY;
ALTER TABLE playbook_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_playbook_files ENABLE ROW LEVEL SECURITY;

-- Users table policies
DROP POLICY IF EXISTS "Users can view own profile" ON users;
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid()::text = id::text);

DROP POLICY IF EXISTS "Users can update own profile" ON users;
CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid()::text = id::text);

-- Playbooks table policies
DROP POLICY IF EXISTS "Users can view all playbooks" ON playbooks;
CREATE POLICY "Users can view all playbooks" ON playbooks
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Users can create own playbooks" ON playbooks;
CREATE POLICY "Users can create own playbooks" ON playbooks
    FOR INSERT WITH CHECK (auth.uid()::text = owner_id::text);

DROP POLICY IF EXISTS "Users can update own playbooks" ON playbooks;
CREATE POLICY "Users can update own playbooks" ON playbooks
    FOR UPDATE USING (auth.uid()::text = owner_id::text);

DROP POLICY IF EXISTS "Users can delete own playbooks" ON playbooks;
CREATE POLICY "Users can delete own playbooks" ON playbooks
    FOR DELETE USING (auth.uid()::text = owner_id::text);

-- User playbooks table policies
DROP POLICY IF EXISTS "Users can view own playbook forks" ON user_playbooks;
CREATE POLICY "Users can view own playbook forks" ON user_playbooks
    FOR SELECT USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Users can create own playbook forks" ON user_playbooks;
CREATE POLICY "Users can create own playbook forks" ON user_playbooks
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Users can update own playbook forks" ON user_playbooks;
CREATE POLICY "Users can update own playbook forks" ON user_playbooks
    FOR UPDATE USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Users can delete own playbook forks" ON user_playbooks;
CREATE POLICY "Users can delete own playbook forks" ON user_playbooks
    FOR DELETE USING (auth.uid()::text = user_id::text);

-- Playbook files table policies
DROP POLICY IF EXISTS "Users can view all playbook files" ON playbook_files;
CREATE POLICY "Users can view all playbook files" ON playbook_files
    FOR SELECT USING (true);

DROP POLICY IF EXISTS "Users can insert playbook files" ON playbook_files;
CREATE POLICY "Users can insert playbook files" ON playbook_files
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM playbooks p 
            WHERE p.id = playbook_files.playbook_id 
            AND p.owner_id::text = auth.uid()::text
        )
    );

DROP POLICY IF EXISTS "Users can update own playbook files" ON playbook_files;
CREATE POLICY "Users can update own playbook files" ON playbook_files
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM playbooks p 
            WHERE p.id = playbook_files.playbook_id 
            AND p.owner_id::text = auth.uid()::text
        )
    );

DROP POLICY IF EXISTS "Users can delete own playbook files" ON playbook_files;
CREATE POLICY "Users can delete own playbook files" ON playbook_files
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM playbooks p 
            WHERE p.id = playbook_files.playbook_id 
            AND p.owner_id::text = auth.uid()::text
        )
    );

-- User playbook files table policies
DROP POLICY IF EXISTS "Users can view own playbook files" ON user_playbook_files;
CREATE POLICY "Users can view own playbook files" ON user_playbook_files
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_playbooks up 
            WHERE up.id = user_playbook_files.user_playbook_id 
            AND up.user_id::text = auth.uid()::text
        )
    );

DROP POLICY IF EXISTS "Users can insert own playbook files" ON user_playbook_files;
CREATE POLICY "Users can insert own playbook files" ON user_playbook_files
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM user_playbooks up 
            WHERE up.id = user_playbook_files.user_playbook_id 
            AND up.user_id::text = auth.uid()::text
        )
    );

DROP POLICY IF EXISTS "Users can update own playbook files" ON user_playbook_files;
CREATE POLICY "Users can update own playbook files" ON user_playbook_files
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM user_playbooks up 
            WHERE up.id = user_playbook_files.user_playbook_id 
            AND up.user_id::text = auth.uid()::text
        )
    );

DROP POLICY IF EXISTS "Users can delete own playbook files" ON user_playbook_files;
CREATE POLICY "Users can delete own playbook files" ON user_playbook_files
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM user_playbooks up 
            WHERE up.id = user_playbook_files.user_playbook_id 
            AND up.user_id::text = auth.uid()::text
        )
    );

-- ==========================================
-- 10. GRANT PERMISSIONS
-- ==========================================
GRANT ALL ON users TO anon, authenticated;
GRANT ALL ON playbooks TO anon, authenticated;
GRANT ALL ON user_playbooks TO anon, authenticated;
GRANT ALL ON playbook_files TO anon, authenticated;
GRANT ALL ON user_playbook_files TO anon, authenticated;

-- Grant usage on sequences
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;

-- ==========================================
-- 11. UPDATE EXISTING RECORDS
-- ==========================================

-- Update existing playbooks to have proper version numbers
UPDATE playbooks SET current_version = 1 WHERE current_version IS NULL;
UPDATE playbooks SET latest_version = 1 WHERE latest_version IS NULL;

-- Update existing playbook files to have proper version tracking
UPDATE playbook_files SET version_created = 1 WHERE version_created IS NULL;
UPDATE playbook_files SET is_active = true WHERE is_active IS NULL;

-- Update existing user playbook files to have proper version tracking
UPDATE user_playbook_files SET version_created = 1 WHERE version_created IS NULL;
UPDATE user_playbook_files SET is_active = true WHERE is_active IS NULL;

-- ==========================================
-- COMPLETE SETUP MESSAGE
-- ==========================================
DO $$
BEGIN
    RAISE NOTICE 'Complete fork functionality database setup finished successfully!';
    RAISE NOTICE 'All tables, indexes, triggers, functions, and policies have been created.';
    RAISE NOTICE 'The fork functionality should now work properly.';
END $$;
