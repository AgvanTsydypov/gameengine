-- Nicknames System Schema for Supabase
-- This file contains the SQL commands to set up the nicknames system

-- Create user_nicknames table
CREATE TABLE IF NOT EXISTS user_nicknames (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    nickname VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id),
    UNIQUE(nickname)
);

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_nicknames_user_id ON user_nicknames(user_id);
CREATE INDEX IF NOT EXISTS idx_user_nicknames_nickname ON user_nicknames(nickname);

-- Enable Row Level Security (RLS)
ALTER TABLE user_nicknames ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
-- Users can view all nicknames (for display purposes)
CREATE POLICY "Users can view all nicknames" ON user_nicknames
    FOR SELECT USING (true);

-- Users can insert their own nickname
CREATE POLICY "Users can insert own nickname" ON user_nicknames
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Users can update their own nickname
CREATE POLICY "Users can update own nickname" ON user_nicknames
    FOR UPDATE USING (auth.uid() = user_id);

-- Users can delete their own nickname
CREATE POLICY "Users can delete own nickname" ON user_nicknames
    FOR DELETE USING (auth.uid() = user_id);

-- Service role can manage all nicknames (for server-side operations)
CREATE POLICY "Service role can manage all nicknames" ON user_nicknames
    FOR ALL USING (auth.role() = 'service_role');

-- Create function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_nickname_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update updated_at
DROP TRIGGER IF EXISTS update_user_nicknames_updated_at ON user_nicknames;
CREATE TRIGGER update_user_nicknames_updated_at
    BEFORE UPDATE ON user_nicknames
    FOR EACH ROW
    EXECUTE FUNCTION update_nickname_updated_at_column();

-- Grant necessary permissions
GRANT ALL ON user_nicknames TO authenticated;
GRANT ALL ON user_nicknames TO service_role;

-- Create a view for easy access to user data with nicknames
CREATE OR REPLACE VIEW user_data_with_nicknames AS
SELECT 
    ud.*,
    un.nickname,
    un.updated_at as nickname_updated_at
FROM user_data ud
LEFT JOIN user_nicknames un ON ud.user_id = un.user_id;

-- Grant permissions on the view
GRANT SELECT ON user_data_with_nicknames TO authenticated;
GRANT SELECT ON user_data_with_nicknames TO service_role;
