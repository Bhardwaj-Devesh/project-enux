-- Version Management Setup
-- Run this in your Supabase SQL editor after the existing setup

-- ==========================================
-- UPDATE PLAYBOOKS TABLE: Add proper version management
-- ==========================================
ALTER TABLE playbooks 
ADD COLUMN IF NOT EXISTS current_version INT DEFAULT 1;

-- Update existing records to have proper version numbers
UPDATE playbooks SET current_version = 1 WHERE current_version IS NULL;
UPDATE playbooks SET latest_version = 1 WHERE latest_version IS NULL;

-- ==========================================
-- UPDATE PLAYBOOK_FILES TABLE: Add version tracking
-- ==========================================
ALTER TABLE playbook_files 
ADD COLUMN IF NOT EXISTS version_created INT DEFAULT 1,
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;

-- Update existing records
UPDATE playbook_files SET version_created = 1 WHERE version_created IS NULL;
UPDATE playbook_files SET is_active = true WHERE is_active IS NULL;

-- ==========================================
-- UPDATE USER_PLAYBOOK_FILES TABLE: Add version tracking
-- ==========================================
ALTER TABLE user_playbook_files 
ADD COLUMN IF NOT EXISTS version_created INT DEFAULT 1,
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;

-- Update existing records
UPDATE user_playbook_files SET version_created = 1 WHERE version_created IS NULL;
UPDATE user_playbook_files SET is_active = true WHERE is_active IS NULL;

-- ==========================================
-- INDEXES for version management
-- ==========================================
CREATE INDEX IF NOT EXISTS idx_playbook_files_version_created 
ON playbook_files(playbook_id, version_created);

CREATE INDEX IF NOT EXISTS idx_playbook_files_active 
ON playbook_files(playbook_id, is_active) WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_user_playbook_files_version_created 
ON user_playbook_files(user_playbook_id, version_created);

CREATE INDEX IF NOT EXISTS idx_user_playbook_files_active 
ON user_playbook_files(user_playbook_id, is_active) WHERE is_active = true;

-- ==========================================
-- FUNCTIONS for version management
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
