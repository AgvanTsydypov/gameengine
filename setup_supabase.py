#!/usr/bin/env python3
"""
Supabase Setup and Testing Script
Helps diagnose and fix Supabase authentication issues
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_environment():
    """Check if all required environment variables are set"""
    logger.info("🔍 Checking environment variables...")
    
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            # Show partial key for security
            if 'KEY' in var:
                display_value = value[:10] + '...' + value[-4:] if len(value) > 14 else value
            else:
                display_value = value
            logger.info(f"  ✅ {var}: {display_value}")
    
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        logger.error("Please create a .env file with:")
        logger.error("SUPABASE_URL=https://your-project-id.supabase.co")
        logger.error("SUPABASE_KEY=your-anon-key-here")
        return False
    
    logger.info("✅ All environment variables are set")
    return True

def test_connection():
    """Test connection to Supabase"""
    logger.info("🔗 Testing Supabase connection...")
    
    try:
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        
        client = create_client(url, key)
        
        # Test basic connection by attempting to get auth user (will fail but should connect)
        try:
            client.auth.get_user()
            logger.info("✅ Supabase connection successful")
            return client
        except Exception as e:
            if "401" in str(e) or "unauthorized" in str(e).lower():
                logger.info("✅ Supabase connection successful (expected auth error)")
                return client
            else:
                raise e
                
    except Exception as e:
        logger.error(f"❌ Supabase connection failed: {e}")
        return None

def test_registration(client):
    """Test user registration"""
    logger.info("👤 Testing user registration...")
    
    test_email = "test@example.com"
    test_password = "testpassword123"
    
    try:
        # Try to sign up a test user
        response = client.auth.sign_up({
            "email": test_email,
            "password": test_password
        })
        
        logger.info(f"Registration response: {response}")
        
        if response.user:
            logger.info("✅ User registration works")
            
            # Clean up: sign out
            try:
                client.auth.sign_out()
            except:
                pass
                
            return True
        else:
            logger.error("❌ Registration failed - no user in response")
            return False
            
    except Exception as e:
        logger.error(f"❌ Registration test failed: {e}")
        logger.error(f"Exception type: {type(e)}")
        
        # Check if it's a specific error we can help with
        error_str = str(e).lower()
        if "email already registered" in error_str:
            logger.info("💡 This might be normal - test email already exists")
        elif "database error" in error_str:
            logger.error("💡 Database error - check your Supabase schema setup")
            logger.error("Run the SQL from supabase_schema_fix.sql in your Supabase SQL Editor")
        elif "email not confirmed" in error_str:
            logger.error("💡 Email confirmation required")
            logger.error("Go to Supabase > Authentication > Settings and disable email confirmations for development")
        
        return False

def check_auth_settings():
    """Provide guidance on auth settings"""
    logger.info("⚙️  Authentication Settings Checklist:")
    logger.info("   Go to your Supabase dashboard > Authentication > Settings")
    logger.info("   The app now automatically uses the correct URLs based on FLASK_ENV:")
    logger.info("   ")
    logger.info("   For DEVELOPMENT (FLASK_ENV=development):")
    logger.info("   1. ✅ Site URL: http://localhost:8888")
    logger.info("   2. ✅ Auto Confirm: Enable for development")
    logger.info("   3. ✅ Email Confirmations: Disable for development") 
    logger.info("   4. ✅ Phone Confirmations: Disable for development")
    logger.info("   5. ✅ Redirect URLs: Add http://localhost:8888/callback")
    logger.info("   ")
    logger.info("   For PRODUCTION (FLASK_ENV=production):")
    logger.info("   1. ✅ Site URL: https://glitchpeach.com")
    logger.info("   2. ✅ Auto Confirm: Disable (enable email confirmations)")
    logger.info("   3. ✅ Email Confirmations: Enable")
    logger.info("   4. ✅ Phone Confirmations: Disable")
    logger.info("   5. ✅ Redirect URLs: Add https://glitchpeach.com/callback")
    logger.info("   ")
    logger.info("   💡 The email confirmation redirect URL is now automatically")
    logger.info("      determined by the FLASK_ENV environment variable!")

def check_database_schema():
    """Check if database schema is set up correctly"""
    logger.info("📊 Database Schema Checklist:")
    logger.info("   Run this SQL in Supabase > SQL Editor:")
    logger.info("   - Execute the contents of supabase_schema_fix.sql")
    logger.info("   - This will clean up any old triggers and set up the correct schema")

def main():
    """Main setup and testing function"""
    logger.info("🚀 Supabase Setup and Testing")
    logger.info("=" * 50)
    
    # Step 1: Check environment
    if not check_environment():
        sys.exit(1)
    
    # Step 2: Test connection
    client = test_connection()
    if not client:
        sys.exit(1)
    
    # Step 3: Provide setup guidance
    check_auth_settings()
    check_database_schema()
    
    # Step 4: Test registration
    if test_registration(client):
        logger.info("🎉 Supabase setup appears to be working!")
    else:
        logger.error("❌ Issues found with registration")
        logger.info("💡 Try the following:")
        logger.info("   1. Run supabase_schema_fix.sql in Supabase SQL Editor")
        logger.info("   2. Check Authentication settings in Supabase dashboard")
        logger.info("   3. Ensure your .env file has correct values")
    
    logger.info("=" * 50)
    logger.info("Setup check complete!")

if __name__ == "__main__":
    main()
