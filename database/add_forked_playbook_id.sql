-- Add forked_playbook_id field to user_playbooks table
-- This field will store the ID of the new playbook created during forking

-- Add the new column
ALTER TABLE user_playbooks 
ADD COLUMN IF NOT EXISTS forked_playbook_id UUID REFERENCES playbooks(id) ON DELETE CASCADE;

-- Add index for better performance
CREATE INDEX IF NOT EXISTS idx_user_playbooks_forked_playbook_id 
ON user_playbooks(forked_playbook_id);

-- Add comment to document the field
COMMENT ON COLUMN user_playbooks.forked_playbook_id IS 'ID of the new playbook created when forking (different from original_playbook_id)';
