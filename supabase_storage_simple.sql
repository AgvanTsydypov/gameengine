-- Simple Supabase Storage Setup for Game Files
-- Execute this command in the SQL Editor in your Supabase dashboard

-- Create the storage bucket for game files
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'game-files',
  'game-files',
  true,  -- Make bucket public so games can be accessed
  16777216,  -- 16MB file size limit
  ARRAY['text/html', 'text/plain']  -- Only allow HTML files
);

-- After running this, go to your Supabase Dashboard:
-- 1. Navigate to Storage > game-files bucket
-- 2. Go to the "Policies" tab
-- 3. Add the following policies:

-- Policy 1: "Users can upload their own game files"
-- - Operation: INSERT
-- - Target roles: authenticated
-- - USING expression: bucket_id = 'game-files'
-- - WITH CHECK expression: bucket_id = 'game-files' AND auth.uid()::text = (storage.foldername(name))[2]

-- Policy 2: "Users can view their own game files"
-- - Operation: SELECT  
-- - Target roles: authenticated
-- - USING expression: bucket_id = 'game-files' AND auth.uid()::text = (storage.foldername(name))[2]

-- Policy 3: "Users can delete their own game files"
-- - Operation: DELETE
-- - Target roles: authenticated  
-- - USING expression: bucket_id = 'game-files' AND auth.uid()::text = (storage.foldername(name))[2]

-- Policy 4: "Public can view game files"
-- - Operation: SELECT
-- - Target roles: anon, authenticated
-- - USING expression: bucket_id = 'game-files'
