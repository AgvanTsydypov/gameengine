-- Public Supabase Storage Setup for Game Files (No RLS)
-- Execute this command in the SQL Editor in your Supabase dashboard

-- Create a public storage bucket for game files (no RLS restrictions)
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
  'game-files',
  'game-files',
  true,  -- Make bucket public so games can be accessed
  16777216,  -- 16MB file size limit
  ARRAY['text/html', 'text/plain']  -- Only allow HTML files
);

-- Note: This creates a public bucket without RLS policies
-- Files will be accessible to anyone with the URL
-- This is simpler but less secure - suitable for public game files
