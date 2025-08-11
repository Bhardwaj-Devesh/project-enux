# Supabase Storage Setup Guide

## Required Storage Buckets

This application requires the following Supabase storage buckets to function properly:

- `public-enux`: For storing public playbook files
- `private-enux`: For storing private playbook files

## Automatic Bucket Creation

The application includes a feature to automatically create these buckets. When you visit the Create Playbook page, the application will check if the required buckets exist. If they don't, you'll see a warning message with a button to attempt to create them.

Click the "Attempt to Create Required Buckets" button to create the missing buckets. This requires that your Supabase user has the necessary permissions to create storage buckets.

## Manual Bucket Creation

If automatic bucket creation fails (which is common due to Row Level Security policies), you'll need to create the buckets manually in the Supabase dashboard:

1. Log in to your Supabase dashboard
2. Navigate to the Storage section
3. Click "New Bucket"
4. Create a bucket named `public-enux` and set it as public
5. Create another bucket named `private-enux` and set it as private

## Storage Permissions

To allow users to upload files to these buckets, you need to set up appropriate Row Level Security (RLS) policies. Here's an example of RLS policies you might want to implement:

### For `public-enux` bucket:

```sql
-- Allow anyone to read files
CREATE POLICY "Anyone can read public files"
ON storage.objects
FOR SELECT
USING (bucket_id = 'public-enux');

-- Allow authenticated users to upload files
CREATE POLICY "Authenticated users can upload files"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'public-enux');

-- Allow users to update and delete their own files
CREATE POLICY "Users can update their own files"
ON storage.objects
FOR UPDATE
TO authenticated
USING (bucket_id = 'public-enux' AND owner = auth.uid());

CREATE POLICY "Users can delete their own files"
ON storage.objects
FOR DELETE
TO authenticated
USING (bucket_id = 'public-enux' AND owner = auth.uid());
```

### For `private-enux` bucket:

```sql
-- Allow users to read their own files
CREATE POLICY "Users can read their own private files"
ON storage.objects
FOR SELECT
TO authenticated
USING (bucket_id = 'private-enux' AND owner = auth.uid());

-- Allow authenticated users to upload files
CREATE POLICY "Authenticated users can upload private files"
ON storage.objects
FOR INSERT
TO authenticated
WITH CHECK (bucket_id = 'private-enux');

-- Allow users to update and delete their own files
CREATE POLICY "Users can update their own private files"
ON storage.objects
FOR UPDATE
TO authenticated
USING (bucket_id = 'private-enux' AND owner = auth.uid());

CREATE POLICY "Users can delete their own private files"
ON storage.objects
FOR DELETE
TO authenticated
USING (bucket_id = 'private-enux' AND owner = auth.uid());
```

## Troubleshooting

If you encounter permission issues when uploading files, check the following:

1. Ensure the required buckets exist
2. Verify that appropriate RLS policies are in place
3. Check that your user is authenticated
4. Look for errors in the browser console for more details

Common error messages and solutions:

- "Permission denied": This usually means your RLS policies are not correctly set up or your user doesn't have the required permissions.
- "Bucket not found": The specified bucket doesn't exist. Create it in the Supabase dashboard.
- "Invalid token": Your authentication token may have expired. Try signing out and back in.

## Additional Resources

- [Supabase Storage Documentation](https://supabase.com/docs/guides/storage)
- [Supabase RLS Documentation](https://supabase.com/docs/guides/auth/row-level-security)