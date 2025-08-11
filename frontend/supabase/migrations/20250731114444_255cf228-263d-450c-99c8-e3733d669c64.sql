-- Update database schema to match the requirements

-- First, let's update the existing tables to better match the schema

-- Update profiles table to include stage and interests
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS stage TEXT DEFAULT 'Ideation',
ADD COLUMN IF NOT EXISTS interests TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS last_login TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS recommender_suggestions JSONB DEFAULT '[]';

-- Update playbooks table with additional fields
ALTER TABLE public.playbooks 
ADD COLUMN IF NOT EXISTS structure JSONB DEFAULT '{"files": [], "folders": []}',
ADD COLUMN IF NOT EXISTS stage TEXT DEFAULT 'MVP';

-- Create commits table for version tracking
CREATE TABLE IF NOT EXISTS public.commits (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  repo_id UUID REFERENCES public.playbooks(id) ON DELETE CASCADE,
  author_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
  file_id UUID,
  version_from TEXT,
  version_to TEXT,
  commit_type TEXT DEFAULT 'Content Update',
  diff_summary TEXT,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create file_versions table
CREATE TABLE IF NOT EXISTS public.file_versions (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  file_id UUID REFERENCES public.playbook_assets(id) ON DELETE CASCADE,
  version_id TEXT NOT NULL,
  committed_by UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
  storage_path TEXT,
  diff_summary TEXT,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Update playbook_assets to include version tracking
ALTER TABLE public.playbook_assets 
ADD COLUMN IF NOT EXISTS current_version TEXT DEFAULT 'v1',
ADD COLUMN IF NOT EXISTS versions TEXT[] DEFAULT '{"v1"}';

-- Create tags table for better tag management
CREATE TABLE IF NOT EXISTS public.tags (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Create playbook_tags junction table
CREATE TABLE IF NOT EXISTS public.playbook_tags (
  id UUID NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
  playbook_id UUID REFERENCES public.playbooks(id) ON DELETE CASCADE,
  tag_id UUID REFERENCES public.tags(id) ON DELETE CASCADE,
  UNIQUE(playbook_id, tag_id)
);

-- Enable RLS on new tables
ALTER TABLE public.commits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.file_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.playbook_tags ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for commits
CREATE POLICY "Commits viewable for accessible playbooks" ON public.commits
FOR SELECT USING (is_playbook_accessible(repo_id, auth.uid()));

CREATE POLICY "Users can create commits for own playbooks" ON public.commits
FOR INSERT WITH CHECK (
  EXISTS (
    SELECT 1 FROM public.playbooks 
    WHERE id = repo_id AND author_id = auth.uid()
  )
);

-- Create RLS policies for file_versions
CREATE POLICY "File versions follow asset accessibility" ON public.file_versions
FOR SELECT USING (
  EXISTS (
    SELECT 1 FROM public.playbook_assets pa
    JOIN public.playbooks p ON pa.playbook_id = p.id
    WHERE pa.id = file_id 
    AND (p.visibility = 'public' OR p.author_id = auth.uid())
  )
);

CREATE POLICY "Users can create versions for own assets" ON public.file_versions
FOR INSERT WITH CHECK (
  EXISTS (
    SELECT 1 FROM public.playbook_assets pa
    JOIN public.playbooks p ON pa.playbook_id = p.id
    WHERE pa.id = file_id AND p.author_id = auth.uid()
  )
);

-- Create RLS policies for tags
CREATE POLICY "Tags are publicly viewable" ON public.tags
FOR SELECT USING (true);

CREATE POLICY "Authenticated users can create tags" ON public.tags
FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

-- Create RLS policies for playbook_tags
CREATE POLICY "Playbook tags are publicly viewable" ON public.playbook_tags
FOR SELECT USING (true);

CREATE POLICY "Users can tag own playbooks" ON public.playbook_tags
FOR ALL USING (
  EXISTS (
    SELECT 1 FROM public.playbooks 
    WHERE id = playbook_id AND author_id = auth.uid()
  )
);

-- Insert sample tags
INSERT INTO public.tags (name) VALUES 
('GTM'), ('Finance'), ('Marketing'), ('Sales'), ('Product Launch'), 
('Business Strategy'), ('Fundraising'), ('MVP'), ('Growth'), 
('Customer Acquisition'), ('Early Stage'), ('Operations'), 
('Hiring'), ('Legal'), ('Analytics');

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_commits_repo_id ON public.commits(repo_id);
CREATE INDEX IF NOT EXISTS idx_file_versions_file_id ON public.file_versions(file_id);
CREATE INDEX IF NOT EXISTS idx_playbook_tags_playbook_id ON public.playbook_tags(playbook_id);
CREATE INDEX IF NOT EXISTS idx_playbook_tags_tag_id ON public.playbook_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_profiles_stage ON public.profiles(stage);
CREATE INDEX IF NOT EXISTS idx_playbooks_stage ON public.playbooks(stage);