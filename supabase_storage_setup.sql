-- Supabase Storage Setup for Game Files
-- Execute these commands in the SQL Editor in your Supabase dashboard

-- 1. Create the storage bucket for game files
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'game-files',
  'game-files',
  true,  -- Make bucket public so games can be accessed
  16777216,  -- 16MB file size limit
  ARRAY['text/html', 'text/plain']  -- Only allow HTML files
);

-- 2. Create storage policies for the game-files bucket
-- Note: These policies will be created automatically by Supabase when you create the bucket
-- If you need to modify them, use the Supabase Dashboard > Storage > Policies section

-- Alternative: Create policies using the Supabase Dashboard
-- Go to Storage > game-files bucket > Policies and add these policies:

-- Policy 1: "Users can upload their own game files"
-- Operation: INSERT
-- Target roles: authenticated
-- USING expression: bucket_id = 'game-files'
-- WITH CHECK expression: bucket_id = 'game-files' AND auth.uid()::text = (storage.foldername(name))[2]

-- Policy 2: "Users can view their own game files" 
-- Operation: SELECT
-- Target roles: authenticated
-- USING expression: bucket_id = 'game-files' AND auth.uid()::text = (storage.foldername(name))[2]

-- Policy 3: "Users can delete their own game files"
-- Operation: DELETE  
-- Target roles: authenticated
-- USING expression: bucket_id = 'game-files' AND auth.uid()::text = (storage.foldername(name))[2]

-- Policy 4: "Public can view game files"
-- Operation: SELECT
-- Target roles: anon, authenticated
-- USING expression: bucket_id = 'game-files'

-- 3. Optional: Create a function to get public URL for a file
CREATE OR REPLACE FUNCTION get_game_file_url(file_path text)
RETURNS text AS $$
BEGIN
  RETURN (
    SELECT 
      CASE 
        WHEN file_path IS NOT NULL AND file_path != '' THEN
          (SELECT concat(settings.value, '/storage/v1/object/public/game-files/', file_path) 
           FROM auth.settings 
           WHERE key = 'api_url' 
           LIMIT 1)
        ELSE NULL
      END
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Note: After running this script, make sure to:
-- 1. Verify the bucket was created in the Storage section of your Supabase dashboard
-- 2. Test file uploads to ensure the policies work correctly
-- 3. Check that public URLs are accessible for game files
