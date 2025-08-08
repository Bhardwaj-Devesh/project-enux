-- PR Workflow Database Schema Updates
-- Run this in your Supabase SQL editor after the existing setup

-- ==========================================
-- PLAYBOOKS: add latest_version for sync checks
-- ==========================================
ALTER TABLE playbooks
ADD COLUMN IF NOT EXISTS latest_version INT DEFAULT 1;

-- ==========================================
-- PLAYBOOK_FILES: add checksum for change detection
-- ==========================================
ALTER TABLE playbook_files
ADD COLUMN IF NOT EXISTS checksum TEXT,
ADD COLUMN IF NOT EXISTS version INT DEFAULT 1;

-- ==========================================
-- USER_PLAYBOOKS (FORKS): add base_version for fork-behind-master checks
-- ==========================================
ALTER TABLE user_playbooks
ADD COLUMN IF NOT EXISTS base_version INT DEFAULT 1, -- master version at fork time
ADD COLUMN IF NOT EXISTS last_sync_version INT DEFAULT 1; -- last synced master version

-- ==========================================
-- USER_PLAYBOOK_FILES: add checksum and version for change detection
-- ==========================================
ALTER TABLE user_playbook_files
ADD COLUMN IF NOT EXISTS checksum TEXT,
ADD COLUMN IF NOT EXISTS version INT DEFAULT 1;

-- ==========================================
-- PULL_REQUESTS: main PR table
-- ==========================================
CREATE TABLE IF NOT EXISTS pull_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fork_id UUID REFERENCES user_playbooks(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    target_playbook_id UUID REFERENCES playbooks(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    commit_message TEXT,
    status TEXT DEFAULT 'open' CHECK (status IN ('open', 'closed', 'merged', 'draft')),
    file_changes JSONB DEFAULT '[]',
    summary TEXT, -- Gemini-generated title
    change_summary TEXT, -- Gemini-generated description
    diff_summary TEXT, -- Gemini per-file diff summary
    risk_flags TEXT[] DEFAULT '{}',
    merge_checklist TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    merged_at TIMESTAMP WITH TIME ZONE,
    closed_at TIMESTAMP WITH TIME ZONE
);

-- ==========================================
-- PULL_REQUEST_FILES: per-file diffs and analysis
-- ==========================================
CREATE TABLE IF NOT EXISTS pull_request_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pr_id UUID REFERENCES pull_requests(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    change_type TEXT NOT NULL CHECK (change_type IN ('added', 'modified', 'deleted')),
    main_file_id UUID, -- references playbook_files(id) if exists
    fork_file_id UUID, -- references user_playbook_files(id) if exists
    diff_text TEXT, -- raw unified diff
    diff_summary TEXT, -- LLM-generated summary
    risk_flags TEXT[] DEFAULT '{}',
    confidence DECIMAL(3,2), -- AI confidence score 0.00-1.00
    checksum_old TEXT,
    checksum_new TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==========================================
-- INDEXES for performance
-- ==========================================
CREATE INDEX IF NOT EXISTS idx_pull_requests_fork_id ON pull_requests(fork_id);
CREATE INDEX IF NOT EXISTS idx_pull_requests_user_id ON pull_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_pull_requests_target_playbook_id ON pull_requests(target_playbook_id);
CREATE INDEX IF NOT EXISTS idx_pull_requests_status ON pull_requests(status);
CREATE INDEX IF NOT EXISTS idx_pull_requests_created_at ON pull_requests(created_at);

CREATE INDEX IF NOT EXISTS idx_pull_request_files_pr_id ON pull_request_files(pr_id);
CREATE INDEX IF NOT EXISTS idx_pull_request_files_file_path ON pull_request_files(file_path);
CREATE INDEX IF NOT EXISTS idx_pull_request_files_change_type ON pull_request_files(change_type);

CREATE INDEX IF NOT EXISTS idx_playbook_files_checksum ON playbook_files(checksum);
CREATE INDEX IF NOT EXISTS idx_user_playbook_files_checksum ON user_playbook_files(checksum);
CREATE INDEX IF NOT EXISTS idx_playbooks_latest_version ON playbooks(latest_version);

-- ==========================================
-- RLS POLICIES (if needed)
-- ==========================================

-- Pull requests are viewable by the creator and playbook owner
ALTER TABLE pull_requests ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own pull requests" ON pull_requests
    FOR SELECT USING (auth.uid()::text = user_id);

CREATE POLICY "Playbook owners can view pull requests to their playbooks" ON pull_requests
    FOR SELECT USING (
        auth.uid()::text IN (
            SELECT owner_id FROM playbooks WHERE id = target_playbook_id
        )
    );

CREATE POLICY "Users can create pull requests" ON pull_requests
    FOR INSERT WITH CHECK (auth.uid()::text = user_id);

-- Pull request files inherit permissions from their parent PR
ALTER TABLE pull_request_files ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Pull request files are viewable with their PR" ON pull_request_files
    FOR SELECT USING (
        pr_id IN (
            SELECT id FROM pull_requests 
            WHERE auth.uid()::text = user_id 
               OR auth.uid()::text IN (
                   SELECT owner_id FROM playbooks WHERE id = target_playbook_id
               )
        )
    );

-- ==========================================
-- TRIGGER to update updated_at timestamp
-- ==========================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_pull_requests_updated_at 
    BEFORE UPDATE ON pull_requests 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==========================================
-- COMMENTS for documentation
-- ==========================================
COMMENT ON TABLE pull_requests IS 'Pull requests for proposing changes from forks to original playbooks';
COMMENT ON TABLE pull_request_files IS 'Individual file changes within pull requests with AI-generated analysis';

COMMENT ON COLUMN pull_requests.file_changes IS 'JSONB array of file change summaries for quick access';
COMMENT ON COLUMN pull_requests.summary IS 'AI-generated PR title';
COMMENT ON COLUMN pull_requests.change_summary IS 'AI-generated PR description';
COMMENT ON COLUMN pull_requests.diff_summary IS 'AI-generated summary of all file changes';
COMMENT ON COLUMN pull_requests.risk_flags IS 'Array of AI-identified risk categories';
COMMENT ON COLUMN pull_requests.merge_checklist IS 'AI-generated merge checklist items';

COMMENT ON COLUMN pull_request_files.confidence IS 'AI confidence score for the analysis (0.00-1.00)';
COMMENT ON COLUMN pull_request_files.change_type IS 'Type of change: added, modified, or deleted';
COMMENT ON COLUMN pull_request_files.diff_text IS 'Raw unified diff output';
COMMENT ON COLUMN pull_request_files.diff_summary IS 'AI-generated natural language summary of the change';