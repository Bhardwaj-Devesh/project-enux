-- Fork Functionality Database Setup
-- Additional tables needed for fork functionality
-- Run this in your Supabase SQL editor AFTER the main setup.sql

-- Create user_playbooks table for storing forked playbooks
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

-- Create user_playbook_files table for storing files in forked playbooks
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

-- Create playbook_files table for original playbook files (if not exists)
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

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_playbooks_user_id 
ON user_playbooks(user_id);

CREATE INDEX IF NOT EXISTS idx_user_playbooks_original_playbook_id 
ON user_playbooks(original_playbook_id);

CREATE INDEX IF NOT EXISTS idx_user_playbooks_forked_at 
ON user_playbooks(forked_at DESC);

CREATE INDEX IF NOT EXISTS idx_user_playbook_files_user_playbook_id 
ON user_playbook_files(user_playbook_id);

CREATE INDEX IF NOT EXISTS idx_user_playbook_files_file_type 
ON user_playbook_files(file_type);

CREATE INDEX IF NOT EXISTS idx_playbook_files_playbook_id 
ON playbook_files(playbook_id);

-- Create trigger to update last_updated_at for user_playbooks
CREATE TRIGGER update_user_playbooks_updated_at 
    BEFORE UPDATE ON user_playbooks 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create trigger to update last_modified_at for user_playbook_files
CREATE TRIGGER update_user_playbook_files_modified_at 
    BEFORE UPDATE ON user_playbook_files 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create trigger to update last_modified_at for playbook_files
CREATE TRIGGER update_playbook_files_modified_at 
    BEFORE UPDATE ON playbook_files 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security policies for user_playbooks
ALTER TABLE user_playbooks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own playbook forks" ON user_playbooks
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own playbook forks" ON user_playbooks
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own playbook forks" ON user_playbooks
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own playbook forks" ON user_playbooks
    FOR DELETE USING (auth.uid() = user_id);

-- Row Level Security policies for user_playbook_files
ALTER TABLE user_playbook_files ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own playbook files" ON user_playbook_files
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM user_playbooks up 
            WHERE up.id = user_playbook_files.user_playbook_id 
            AND up.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can insert own playbook files" ON user_playbook_files
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM user_playbooks up 
            WHERE up.id = user_playbook_files.user_playbook_id 
            AND up.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can update own playbook files" ON user_playbook_files
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM user_playbooks up 
            WHERE up.id = user_playbook_files.user_playbook_id 
            AND up.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete own playbook files" ON user_playbook_files
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM user_playbooks up 
            WHERE up.id = user_playbook_files.user_playbook_id 
            AND up.user_id = auth.uid()
        )
    );

-- Row Level Security policies for playbook_files
ALTER TABLE playbook_files ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view all playbook files" ON playbook_files
    FOR SELECT USING (true);

CREATE POLICY "Users can insert playbook files" ON playbook_files
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM playbooks p 
            WHERE p.id = playbook_files.playbook_id 
            AND p.owner_id = auth.uid()
        )
    );

CREATE POLICY "Users can update own playbook files" ON playbook_files
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM playbooks p 
            WHERE p.id = playbook_files.playbook_id 
            AND p.owner_id = auth.uid()
        )
    );

CREATE POLICY "Users can delete own playbook files" ON playbook_files
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM playbooks p 
            WHERE p.id = playbook_files.playbook_id 
            AND p.owner_id = auth.uid()
        )
    );

-- Grant permissions
GRANT ALL ON user_playbooks TO anon, authenticated;
GRANT ALL ON user_playbook_files TO anon, authenticated;
GRANT ALL ON playbook_files TO anon, authenticated;