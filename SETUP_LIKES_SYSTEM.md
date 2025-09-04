# 🎮 Game Likes System Setup Instructions

This document provides step-by-step instructions to set up the likes system for the AI Game Studio.

## 📋 Prerequisites

- Access to your Supabase project dashboard
- Admin access to create tables and functions

## 🗄️ Database Setup

### Step 1: Create Tables

Go to your Supabase dashboard → SQL Editor and run the following SQL commands:

```sql
-- Table 1: Game Statistics (aggregate data for each game)
CREATE TABLE IF NOT EXISTS public.game_statistics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    game_id UUID NOT NULL REFERENCES public.user_data(id) ON DELETE CASCADE,
    likes_count INTEGER DEFAULT 0 NOT NULL,
    plays_count INTEGER DEFAULT 0 NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Ensure one stats record per game
    UNIQUE(game_id)
);

-- Table 2: Game Likes (individual user likes tracking)
CREATE TABLE IF NOT EXISTS public.game_likes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    game_id UUID NOT NULL REFERENCES public.user_data(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Prevent duplicate likes from same user for same game
    UNIQUE(game_id, user_id)
);
```

### Step 2: Create Indexes

```sql
-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_game_statistics_game_id ON public.game_statistics(game_id);
CREATE INDEX IF NOT EXISTS idx_game_statistics_likes_count ON public.game_statistics(likes_count DESC);
CREATE INDEX IF NOT EXISTS idx_game_likes_game_id ON public.game_likes(game_id);
CREATE INDEX IF NOT EXISTS idx_game_likes_user_id ON public.game_likes(user_id);
```

### Step 3: Create Functions and Triggers

```sql
-- Function to update game statistics when likes change
CREATE OR REPLACE FUNCTION update_game_likes_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        -- User liked a game
        INSERT INTO public.game_statistics (game_id, likes_count)
        VALUES (NEW.game_id, 1)
        ON CONFLICT (game_id)
        DO UPDATE SET 
            likes_count = game_statistics.likes_count + 1,
            updated_at = NOW();
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        -- User unliked a game
        UPDATE public.game_statistics 
        SET 
            likes_count = GREATEST(0, likes_count - 1),
            updated_at = NOW()
        WHERE game_id = OLD.game_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update likes count
DROP TRIGGER IF EXISTS trigger_update_likes_count ON public.game_likes;
CREATE TRIGGER trigger_update_likes_count
    AFTER INSERT OR DELETE ON public.game_likes
    FOR EACH ROW EXECUTE FUNCTION update_game_likes_count();
```

### Step 4: Set Up Row Level Security (RLS)

```sql
-- Enable RLS
ALTER TABLE public.game_statistics ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.game_likes ENABLE ROW LEVEL SECURITY;

-- Policies for game_statistics (read-only for all, write for service role)
CREATE POLICY "Allow public read access to game statistics" ON public.game_statistics
    FOR SELECT USING (true);

CREATE POLICY "Allow service role full access to game statistics" ON public.game_statistics
    FOR ALL USING (auth.role() = 'service_role');

-- Policies for game_likes
CREATE POLICY "Allow users to read all game likes" ON public.game_likes
    FOR SELECT USING (true);

CREATE POLICY "Allow users to insert their own likes" ON public.game_likes
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Allow users to delete their own likes" ON public.game_likes
    FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Allow service role full access to game likes" ON public.game_likes
    FOR ALL USING (auth.role() = 'service_role');
```

### Step 5: Initialize Data (Optional)

```sql
-- Initial data migration (creates stats for existing games)
INSERT INTO public.game_statistics (game_id, likes_count, plays_count)
SELECT 
    id as game_id,
    0 as likes_count,
    FLOOR(RANDOM() * 50 + 10)::INTEGER as plays_count -- Random play counts for existing games
FROM public.user_data 
WHERE data_type = 'html_game'
ON CONFLICT (game_id) DO NOTHING;
```

## ✅ Verification

After running the SQL commands, verify the setup:

1. **Check Tables Created**:
   ```sql
   SELECT table_name FROM information_schema.tables 
   WHERE table_schema = 'public' 
   AND table_name IN ('game_statistics', 'game_likes');
   ```

2. **Check Policies**:
   ```sql
   SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
   FROM pg_policies 
   WHERE tablename IN ('game_statistics', 'game_likes');
   ```

3. **Test Data**:
   ```sql
   SELECT * FROM public.game_statistics LIMIT 5;
   SELECT * FROM public.game_likes LIMIT 5;
   ```

## 🚀 Features Enabled

Once setup is complete, the following features will be available:

- ❤️ **Like/Unlike Games**: Users can like and unlike community games
- 📊 **Real-time Statistics**: Automatic tracking of likes and play counts
- 🔥 **Trending Games**: Games sorted by popularity (likes)
- 🎯 **User Personalization**: Users see their like status for each game
- 📈 **Rating System**: Dynamic ratings based on like counts

## 🔧 Troubleshooting

- **Permission Errors**: Ensure you're running SQL commands as a Supabase admin
- **RLS Issues**: Check that service role key is properly configured in `.env`
- **Missing Data**: Run the initialization query in Step 5 to populate statistics for existing games

## 🎉 Ready to Use!

After completing the setup, restart your Flask application to use the new likes system!
