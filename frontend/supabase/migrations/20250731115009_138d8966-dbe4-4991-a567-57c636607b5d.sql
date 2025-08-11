-- Insert sample data for testing

-- Insert sample profiles (users)
INSERT INTO public.profiles (id, username, full_name, bio, stage, interests, website, location, company, avatar_url) VALUES
(gen_random_uuid(), 'sarah_chen', 'Sarah Chen', 'Serial entrepreneur and GTM expert. Building tools for early-stage founders.', 'Growth', '{"GTM", "Marketing", "Sales"}', 'https://sarahchen.com', 'San Francisco, CA', 'GTM Labs', '/api/placeholder/40/40'),
(gen_random_uuid(), 'mike_johnson', 'Mike Johnson', 'Product leader turned founder. Passionate about user-centered design.', 'MVP', '{"Product Launch", "UX", "Analytics"}', 'https://mikej.dev', 'Austin, TX', 'ProductFlow', '/api/placeholder/40/40'),
(gen_random_uuid(), 'lisa_park', 'Lisa Park', 'Sales operations specialist helping startups scale their revenue engines.', 'Growth', '{"Sales", "Operations", "Analytics"}', 'https://lisapark.co', 'New York, NY', 'SalesScale', '/api/placeholder/40/40'),
(gen_random_uuid(), 'david_kim', 'David Kim', 'Content marketing strategist and former VC. Author of "Content that Converts".', 'Growth', '{"Marketing", "Content", "GTM"}', 'https://davidkim.blog', 'Seattle, WA', 'Content Labs', '/api/placeholder/40/40'),
(gen_random_uuid(), 'emily_rodriguez', 'Emily Rodriguez', 'Finance and fundraising expert. Helped 50+ startups raise over $100M.', 'Growth', '{"Finance", "Fundraising", "Legal"}', 'https://emilyrodriguez.vc', 'Boston, MA', 'Capital Advisors', '/api/placeholder/40/40');

-- Insert sample playbooks
DO $$
DECLARE
    user_sarah UUID;
    user_mike UUID;
    user_lisa UUID;
    user_david UUID;
    user_emily UUID;
    playbook_id UUID;
    tag_gtm UUID;
    tag_marketing UUID;
    tag_sales UUID;
    tag_product UUID;
    tag_finance UUID;
    tag_mvp UUID;
    tag_growth UUID;
    tag_early UUID;
BEGIN
    -- Get user IDs
    SELECT id INTO user_sarah FROM public.profiles WHERE username = 'sarah_chen';
    SELECT id INTO user_mike FROM public.profiles WHERE username = 'mike_johnson';
    SELECT id INTO user_lisa FROM public.profiles WHERE username = 'lisa_park';
    SELECT id INTO user_david FROM public.profiles WHERE username = 'david_kim';
    SELECT id INTO user_emily FROM public.profiles WHERE username = 'emily_rodriguez';
    
    -- Get tag IDs
    SELECT id INTO tag_gtm FROM public.tags WHERE name = 'GTM';
    SELECT id INTO tag_marketing FROM public.tags WHERE name = 'Marketing';
    SELECT id INTO tag_sales FROM public.tags WHERE name = 'Sales';
    SELECT id INTO tag_product FROM public.tags WHERE name = 'Product Launch';
    SELECT id INTO tag_finance FROM public.tags WHERE name = 'Finance';
    SELECT id INTO tag_mvp FROM public.tags WHERE name = 'MVP';
    SELECT id INTO tag_growth FROM public.tags WHERE name = 'Growth';
    SELECT id INTO tag_early FROM public.tags WHERE name = 'Early Stage';
    
    -- Insert GTM Launch Playbook
    INSERT INTO public.playbooks (id, title, description, author_id, visibility, license, stage, structure, stars_count, forks_count, created_at, updated_at)
    VALUES (
        gen_random_uuid(),
        'GTM Launch Playbook for Early-Stage Startups',
        'A comprehensive guide to launching your go-to-market strategy for early-stage startups. Includes templates, checklists, and proven frameworks.',
        user_sarah,
        'public',
        'CC-BY-SA',
        'MVP',
        '{"files": ["launch.md", "icp-template.xlsx", "timeline.pptx"], "folders": ["templates", "examples"]}',
        47,
        12,
        NOW() - INTERVAL '30 days',
        NOW() - INTERVAL '2 days'
    ) RETURNING id INTO playbook_id;
    
    -- Tag the GTM playbook
    INSERT INTO public.playbook_tags (playbook_id, tag_id) VALUES 
    (playbook_id, tag_gtm),
    (playbook_id, tag_marketing),
    (playbook_id, tag_early);
    
    -- Product Launch Checklist
    INSERT INTO public.playbooks (id, title, description, author_id, visibility, license, stage, structure, stars_count, forks_count, created_at, updated_at)
    VALUES (
        gen_random_uuid(),
        'Product Launch Checklist & Timeline',
        'Step-by-step checklist for launching your MVP with confidence. Covers pre-launch, launch day, and post-launch activities.',
        user_mike,
        'public',
        'MIT',
        'MVP',
        '{"files": ["checklist.md", "timeline.xlsx"], "folders": ["pre-launch", "post-launch"]}',
        34,
        8,
        NOW() - INTERVAL '25 days',
        NOW() - INTERVAL '5 days'
    ) RETURNING id INTO playbook_id;
    
    INSERT INTO public.playbook_tags (playbook_id, tag_id) VALUES 
    (playbook_id, tag_product),
    (playbook_id, tag_mvp);
    
    -- Sales Funnel Optimization
    INSERT INTO public.playbooks (id, title, description, author_id, visibility, license, stage, structure, stars_count, forks_count, created_at, updated_at)
    VALUES (
        gen_random_uuid(),
        'Sales Funnel Optimization for SaaS Startups',
        'Data-driven approach to optimizing your sales funnel from lead to close. Includes metrics, templates, and automation strategies.',
        user_lisa,
        'public',
        'CC-BY',
        'Growth',
        '{"files": ["funnel-guide.md", "metrics-dashboard.xlsx", "automation-flows.pptx"], "folders": ["templates", "tools"]}',
        62,
        15,
        NOW() - INTERVAL '40 days',
        NOW() - INTERVAL '1 day'
    ) RETURNING id INTO playbook_id;
    
    INSERT INTO public.playbook_tags (playbook_id, tag_id) VALUES 
    (playbook_id, tag_sales),
    (playbook_id, tag_growth);
    
    -- Content Marketing Guide
    INSERT INTO public.playbooks (id, title, description, author_id, visibility, license, stage, structure, stars_count, forks_count, created_at, updated_at)
    VALUES (
        gen_random_uuid(),
        'Content Marketing Guide for B2B SaaS',
        'Complete content marketing playbook covering strategy, creation, distribution, and measurement for B2B SaaS companies.',
        user_david,
        'public',
        'CC-BY-SA',
        'Growth',
        '{"files": ["content-strategy.md", "editorial-calendar.xlsx", "templates.zip"], "folders": ["blog-templates", "social-media"]}',
        89,
        23,
        NOW() - INTERVAL '60 days',
        NOW() - INTERVAL '3 days'
    ) RETURNING id INTO playbook_id;
    
    INSERT INTO public.playbook_tags (playbook_id, tag_id) VALUES 
    (playbook_id, tag_marketing),
    (playbook_id, tag_growth);
    
    -- Fundraising Playbook
    INSERT INTO public.playbooks (id, title, description, author_id, visibility, license, stage, structure, stars_count, forks_count, created_at, updated_at)
    VALUES (
        gen_random_uuid(),
        'Seed Fundraising Playbook',
        'Everything you need to raise your seed round: pitch deck templates, investor outreach strategies, and term sheet negotiation guides.',
        user_emily,
        'public',
        'CC-BY',
        'MVP',
        '{"files": ["pitch-deck-template.pptx", "investor-outreach.md", "term-sheet-guide.pdf"], "folders": ["templates", "examples", "legal"]}',
        156,
        42,
        NOW() - INTERVAL '90 days',
        NOW() - INTERVAL '7 days'
    ) RETURNING id INTO playbook_id;
    
    INSERT INTO public.playbook_tags (playbook_id, tag_id) VALUES 
    (playbook_id, tag_finance),
    (playbook_id, tag_early);
END $$;

-- Add some sample stars
INSERT INTO public.playbook_stars (playbook_id, user_id)
SELECT p.id, pr.id
FROM public.playbooks p
CROSS JOIN public.profiles pr
WHERE random() < 0.3; -- 30% chance each user stars each playbook

-- Update playbook stats based on actual stars
UPDATE public.playbooks 
SET stars_count = (
    SELECT COUNT(*) 
    FROM public.playbook_stars 
    WHERE playbook_id = playbooks.id
);

-- Add some sample commits for version history
INSERT INTO public.commits (repo_id, author_id, version_from, version_to, commit_type, diff_summary)
SELECT 
    p.id,
    p.author_id,
    'v' || (1 + floor(random() * 3))::text,
    'v' || (2 + floor(random() * 3))::text,
    CASE floor(random() * 4)
        WHEN 0 THEN 'Content Update'
        WHEN 1 THEN 'Template Addition'
        WHEN 2 THEN 'Structure Improvement'
        ELSE 'Bug Fix'
    END,
    CASE floor(random() * 5)
        WHEN 0 THEN 'Added new section on customer interviews'
        WHEN 1 THEN 'Updated templates with latest best practices'
        WHEN 2 THEN 'Fixed formatting issues in checklist'
        WHEN 3 THEN 'Enhanced metrics tracking section'
        ELSE 'Improved readability and structure'
    END
FROM public.playbooks p
WHERE random() < 0.7; -- 70% of playbooks have at least one commit