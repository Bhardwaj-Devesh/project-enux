-- Add RLS policies for storage buckets

-- Enable RLS on storage.objects if not already enabled
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;

-- Policies for public-enux bucket

-- Allow anyone to read files from public-enux bucket
DROP POLICY IF EXISTS "Anyone can read public files" ON storage.objects;
CREATE POLICY "Anyone can read public files"
ON storage.objects
FOR SELECT
USING (bucket_id = 'public-enux');

-- Allow authenticated users to upload files to public-enux bucket
DROP POLICY IF EXISTS "Authenticated users can upload files" ON storage.objects;
CREATE POLICY "Authenticated users can upload files"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'public-enux');

-- Allow users to update and delete their own files in public-enux bucket
DROP POLICY IF EXISTS "Users can update their own files" ON storage.objects;
CREATE POLICY "Users can update their own files"
ON storage.objects
FOR UPDATE
TO authenticated
USING (bucket_id = 'public-enux' AND (auth.uid() = owner OR auth.uid() IN (
  SELECT author_id FROM playbooks p
  WHERE p.id::text = (storage.foldername(name))[1]
)));

DROP POLICY IF EXISTS "Users can delete their own files" ON storage.objects;
CREATE POLICY "Users can delete their own files"
ON storage.objects
FOR DELETE
TO authenticated
USING (bucket_id = 'public-enux' AND (auth.uid() = owner OR auth.uid() IN (
  SELECT author_id FROM playbooks p
  WHERE p.id::text = (storage.foldername(name))[1]
)));

-- Policies for private-enux bucket

-- Allow users to read their own files from private-enux bucket
DROP POLICY IF EXISTS "Users can read their own private files" ON storage.objects;
CREATE POLICY "Users can read their own private files"
ON storage.objects
FOR SELECT
TO authenticated
USING (bucket_id = 'private-enux' AND (auth.uid() = owner OR auth.uid() IN (
  SELECT author_id FROM playbooks p
  WHERE p.id::text = (storage.foldername(name))[1]
)));

-- Allow authenticated users to upload files to private-enux bucket
DROP POLICY IF EXISTS "Authenticated users can upload private files" ON storage.objects;
CREATE POLICY "Authenticated users can upload private files"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'private-enux');

-- Allow users to update and delete their own files in private-enux bucket
DROP POLICY IF EXISTS "Users can update their own private files" ON storage.objects;
CREATE POLICY "Users can update their own private files"
ON storage.objects
FOR UPDATE
TO authenticated
USING (bucket_id = 'private-enux' AND (auth.uid() = owner OR auth.uid() IN (
  SELECT author_id FROM playbooks p
  WHERE p.id::text = (storage.foldername(name))[1]
)));

DROP POLICY IF EXISTS "Users can delete their own private files" ON storage.objects;
CREATE POLICY "Users can delete their own private files"
ON storage.objects
FOR DELETE
TO authenticated
USING (bucket_id = 'private-enux' AND (auth.uid() = owner OR auth.uid() IN (
  SELECT author_id FROM playbooks p
  WHERE p.id::text = (storage.foldername(name))[1]
)));