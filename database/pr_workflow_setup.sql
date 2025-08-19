-- Pull Request Workflow Database Setup
-- Run this in your Supabase SQL editor

-- ==========================================
-- 1. PULL REQUESTS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS pull_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    playbook_id UUID REFERENCES playbooks(id) ON DELETE CASCADE,
    author_id UUID REFERENCES users(id) ON DELETE CASCADE,
    base_version_id UUID REFERENCES playbook_versions(id),
    title TEXT NOT NULL,
    description TEXT,
    old_blog_text TEXT NOT NULL,
    new_blog_text TEXT NOT NULL,
    unified_diff TEXT,
    status TEXT DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'MERGED', 'DECLINED', 'CLOSED')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    merged_at TIMESTAMP WITH TIME ZONE,
    merged_by UUID REFERENCES users(id),
    merge_message TEXT,
    new_version_id UUID REFERENCES playbook_versions(id)
);

-- ==========================================
-- 2. PLAYBOOK VERSIONS TABLE (if not exists)
-- ==========================================
CREATE TABLE IF NOT EXISTS playbook_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    playbook_id UUID REFERENCES playbooks(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    blog_text TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    source TEXT DEFAULT 'manual' CHECK (source IN ('manual', 'pr_merge', 'import')),
    pr_id UUID REFERENCES pull_requests(id),
    created_by UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(playbook_id, version_number)
);

-- ==========================================
-- 3. PULL REQUEST EVENTS TABLE
-- ==========================================
CREATE TABLE IF NOT EXISTS pull_request_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pr_id UUID REFERENCES pull_requests(id) ON DELETE CASCADE,
    event_type TEXT NOT NULL CHECK (event_type IN ('created', 'merged', 'declined', 'closed', 'reopened')),
    actor_id UUID REFERENCES users(id) ON DELETE CASCADE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==========================================
-- 4. INDEXES FOR PERFORMANCE
-- ==========================================
CREATE INDEX IF NOT EXISTS idx_pull_requests_playbook_id ON pull_requests(playbook_id);
CREATE INDEX IF NOT EXISTS idx_pull_requests_author_id ON pull_requests(author_id);
CREATE INDEX IF NOT EXISTS idx_pull_requests_status ON pull_requests(status);
CREATE INDEX IF NOT EXISTS idx_pull_requests_created_at ON pull_requests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pull_requests_base_version_id ON pull_requests(base_version_id);

CREATE INDEX IF NOT EXISTS idx_playbook_versions_playbook_id ON playbook_versions(playbook_id);
CREATE INDEX IF NOT EXISTS idx_playbook_versions_version_number ON playbook_versions(playbook_id, version_number DESC);
CREATE INDEX IF NOT EXISTS idx_playbook_versions_content_hash ON playbook_versions(content_hash);

CREATE INDEX IF NOT EXISTS idx_pull_request_events_pr_id ON pull_request_events(pr_id);
CREATE INDEX IF NOT EXISTS idx_pull_request_events_created_at ON pull_request_events(created_at DESC);

-- ==========================================
-- 5. TRIGGERS FOR UPDATED_AT COLUMNS
-- ==========================================
CREATE TRIGGER update_pull_requests_updated_at 
    BEFORE UPDATE ON pull_requests 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==========================================
-- 6. FUNCTIONS FOR PR OPERATIONS
-- ==========================================

-- Function to get next version number for a playbook
CREATE OR REPLACE FUNCTION get_next_version_number(p_playbook_id UUID)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    next_version INTEGER;
BEGIN
    SELECT COALESCE(MAX(version_number), 0) + 1
    INTO next_version
    FROM playbook_versions
    WHERE playbook_id = p_playbook_id;
    
    RETURN next_version;
END;
$$;

-- Function to create a new playbook version
CREATE OR REPLACE FUNCTION create_playbook_version(
    p_playbook_id UUID,
    p_blog_text TEXT,
    p_source TEXT DEFAULT 'manual',
    p_pr_id UUID DEFAULT NULL,
    p_created_by UUID DEFAULT NULL
)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
    new_version_id UUID;
    new_version_number INTEGER;
    content_hash TEXT;
BEGIN
    -- Get next version number
    new_version_number := get_next_version_number(p_playbook_id);
    
    -- Generate content hash
    content_hash := encode(sha256(p_blog_text::bytea), 'hex');
    
    -- Create new version
    INSERT INTO playbook_versions (
        id, playbook_id, version_number, blog_text, content_hash, 
        source, pr_id, created_by
    ) VALUES (
        gen_random_uuid(), p_playbook_id, new_version_number, p_blog_text, content_hash,
        p_source, p_pr_id, p_created_by
    ) RETURNING id INTO new_version_id;
    
    -- Update playbook's current version
    UPDATE playbooks 
    SET current_version_id = new_version_id,
        updated_at = NOW()
    WHERE id = p_playbook_id;
    
    RETURN new_version_id;
END;
$$;

-- Function to merge a pull request
CREATE OR REPLACE FUNCTION merge_pull_request(
    p_pr_id UUID,
    p_merge_message TEXT,
    p_merged_by UUID
)
RETURNS JSONB
LANGUAGE plpgsql
AS $$
DECLARE
    pr_record RECORD;
    v_new_version_id UUID;
    result JSONB;
BEGIN
    -- Get PR details
    SELECT * INTO pr_record
    FROM pull_requests
    WHERE id = p_pr_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Pull request not found';
    END IF;
    
    IF pr_record.status != 'OPEN' THEN
        RAISE EXCEPTION 'Pull request is not open';
    END IF;
    
    -- Create new version
    v_new_version_id := create_playbook_version(
        pr_record.playbook_id,
        pr_record.new_blog_text,
        'pr_merge',
        p_pr_id,
        p_merged_by
    );
    
    -- Update PR status
    UPDATE pull_requests
    SET status = 'MERGED',
        merged_at = NOW(),
        merged_by = p_merged_by,
        merge_message = p_merge_message,
        new_version_id = v_new_version_id,
        updated_at = NOW()
    WHERE id = p_pr_id;
    
    -- Update playbook's blog_content with the new content
    UPDATE playbooks
    SET blog_content = pr_record.new_blog_text,
        updated_at = NOW()
    WHERE id = pr_record.playbook_id;
    
    -- Create event
    INSERT INTO pull_request_events (pr_id, event_type, actor_id, metadata)
    VALUES (p_pr_id, 'merged', p_merged_by, 
            jsonb_build_object('new_version_id', v_new_version_id, 'merge_message', p_merge_message));
    
    -- Return result
    SELECT jsonb_build_object(
        'status', 'MERGED',
        'new_version_id', v_new_version_id,
        'version_number', (SELECT version_number FROM playbook_versions WHERE id = v_new_version_id)
    ) INTO result;
    
    RETURN result;
END;
$$;

-- ==========================================
-- 7. ROW LEVEL SECURITY (RLS)
-- ==========================================
ALTER TABLE pull_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE playbook_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE pull_request_events ENABLE ROW LEVEL SECURITY;

-- Pull requests policies
CREATE POLICY "Users can view all pull requests" ON pull_requests
    FOR SELECT USING (true);

CREATE POLICY "Users can create pull requests" ON pull_requests
    FOR INSERT WITH CHECK (auth.uid()::text = author_id::text);

CREATE POLICY "Playbook owners can update pull requests" ON pull_requests
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM playbooks p 
            WHERE p.id = pull_requests.playbook_id 
            AND p.owner_id::text = auth.uid()::text
        )
    );

-- Playbook versions policies
CREATE POLICY "Users can view all playbook versions" ON playbook_versions
    FOR SELECT USING (true);

CREATE POLICY "Users can create playbook versions" ON playbook_versions
    FOR INSERT WITH CHECK (true);

-- Pull request events policies
CREATE POLICY "Users can view all pull request events" ON pull_request_events
    FOR SELECT USING (true);

CREATE POLICY "System can create pull request events" ON pull_request_events
    FOR INSERT WITH CHECK (true);

-- ==========================================
-- 8. GRANT PERMISSIONS
-- ==========================================
GRANT ALL ON pull_requests TO anon, authenticated;
GRANT ALL ON playbook_versions TO anon, authenticated;
GRANT ALL ON pull_request_events TO anon, authenticated;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;

-- ==========================================
-- 9. UPDATE EXISTING PLAYBOOKS
-- ==========================================
-- Add current_version_id column to playbooks if it doesn't exist
ALTER TABLE playbooks 
ADD COLUMN IF NOT EXISTS current_version_id UUID REFERENCES playbook_versions(id);

-- Create initial versions for existing playbooks
DO $$
DECLARE
    playbook_record RECORD;
    initial_version_id UUID;
BEGIN
    FOR playbook_record IN SELECT id, blog_content FROM playbooks WHERE current_version_id IS NULL
    LOOP
        -- Create initial version
        INSERT INTO playbook_versions (
            id, playbook_id, version_number, blog_text, content_hash, 
            source, created_by
        ) VALUES (
            gen_random_uuid(), 
            playbook_record.id, 
            1, 
            COALESCE(playbook_record.blog_content, ''),
            encode(sha256(COALESCE(playbook_record.blog_content, '')::bytea), 'hex'),
            'manual',
            (SELECT owner_id FROM playbooks WHERE id = playbook_record.id)
        ) RETURNING id INTO initial_version_id;
        
        -- Update playbook with current version
        UPDATE playbooks 
        SET current_version_id = initial_version_id
        WHERE id = playbook_record.id;
    END LOOP;
END $$;

-- ==========================================
-- COMPLETE SETUP MESSAGE
-- ==========================================
DO $$
BEGIN
    RAISE NOTICE 'Pull Request workflow database setup completed successfully!';
    RAISE NOTICE 'Tables created: pull_requests, playbook_versions, pull_request_events';
    RAISE NOTICE 'Functions created: get_next_version_number, create_playbook_version, merge_pull_request';
    RAISE NOTICE 'RLS policies and permissions configured';
END $$;
