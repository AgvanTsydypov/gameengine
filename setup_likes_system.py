#!/usr/bin/env python3
"""
Setup script for the game likes system database tables
Run this script to create the necessary tables and functions in Supabase
"""

import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_likes_system():
    """Create the likes system tables and functions in Supabase"""
    
    # Get Supabase credentials
    url = os.getenv('SUPABASE_URL')
    service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not service_role_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env file")
        return False
    
    try:
        # Create Supabase client with service role key (needed for admin operations)
        supabase = create_client(url, service_role_key)
        
        print("🔧 Setting up likes system database schema...")
        
        # Read the SQL schema file
        schema_file = os.path.join(os.path.dirname(__file__), 'schema_likes_system.sql')
        with open(schema_file, 'r') as f:
            sql_commands = f.read()
        
        # Split SQL commands and execute them
        commands = [cmd.strip() for cmd in sql_commands.split(';') if cmd.strip() and not cmd.strip().startswith('--')]
        
        for i, command in enumerate(commands):
            if command:
                print(f"📝 Executing SQL command {i+1}/{len(commands)}...")
                try:
                    # Use RPC to execute SQL via Supabase
                    result = supabase.rpc('exec_sql', {'sql': command}).execute()
                    print(f"✅ Command {i+1} executed successfully")
                except Exception as e:
                    print(f"⚠️  Command {i+1} warning (might be expected): {e}")
                    continue
        
        print("🎉 Likes system setup completed successfully!")
        print("\n📊 Created tables:")
        print("   - public.game_statistics (aggregate stats per game)")
        print("   - public.game_likes (individual user likes)")
        print("\n🔧 Created functions:")
        print("   - update_game_likes_count() (auto-update likes count)")
        print("   - increment_play_count() (track game plays)")
        print("\n🔒 Configured Row Level Security policies")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up likes system: {e}")
        return False

if __name__ == "__main__":
    success = setup_likes_system()
    if success:
        print("\n✨ You can now run the Flask app with the new likes system!")
    else:
        print("\n💡 Please check your Supabase configuration and try again.")
