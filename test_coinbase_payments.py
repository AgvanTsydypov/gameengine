#!/usr/bin/env python3
"""
Test script for Coinbase Commerce payments debugging
"""
import os
import sys
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_coinbase_webhook_accessibility():
    """Test if the Coinbase webhook endpoint is accessible"""
    base_url = os.getenv('BASE_URL')
    
    # If BASE_URL is not set, try to determine from other environment variables
    if not base_url:
        # Check if we're running on a known platform
        if os.getenv('RENDER_SERVICE_NAME'):
            base_url = f"https://{os.getenv('RENDER_SERVICE_NAME')}.onrender.com"
        elif os.getenv('RAILWAY_PROJECT_NAME'):
            base_url = f"https://{os.getenv('RAILWAY_PROJECT_NAME')}.railway.app"
        elif os.getenv('FLASK_ENV') == 'production':
            # Production default
            base_url = 'https://glitchpeach.com'
            print(f"ℹ️ BASE_URL not set, using production default: {base_url}")
        else:
            # Default to localhost for development
            base_url = 'http://localhost:5000'
            print(f"⚠️ BASE_URL not set, using development default: {base_url}")
    
    # Remove trailing slash if present to avoid double slash
    base_url = base_url.rstrip('/')
    webhook_url = f"{base_url}/test_coinbase_webhook"
    
    print("=" * 60)
    print("Testing Coinbase Webhook Accessibility")
    print("=" * 60)
    print(f"Testing URL: {webhook_url}")
    
    try:
        # Test GET request
        response = requests.get(webhook_url, timeout=10)
        print(f"GET {webhook_url}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 404:
            print("❌ Webhook endpoint not found (404)")
            print("This could mean:")
            print("  1. The updated code hasn't been deployed yet")
            print("  2. The route isn't properly registered")
            print("  3. There's a routing issue in the application")
            print("👉 Solution: Deploy the updated app.py with the new webhook routes")
            return False
        elif response.status_code == 200:
            try:
                print(f"Response: {response.json()}")
            except:
                print(f"Response: {response.text[:200]}...")
        else:
            print(f"Unexpected status code: {response.status_code}")
            try:
                print(f"Response: {response.text[:200]}...")
            except:
                pass
        
        # Only test POST if GET was successful
        if response.status_code == 200:
            # Test POST request (simulate webhook)
            test_payload = {
                "type": "charge:confirmed",
                "data": {
                    "id": "test-charge-id",
                    "status": "COMPLETED"
                }
            }
            
            response = requests.post(
                webhook_url, 
                json=test_payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            print(f"\nPOST {webhook_url}")
            print(f"Status Code: {response.status_code}")
            try:
                print(f"Response: {response.json()}")
            except:
                print(f"Response: {response.text[:200]}...")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"Error testing webhook: {e}")
        return False

def check_environment_variables():
    """Check if all required environment variables are set"""
    print("\n" + "=" * 60)
    print("Checking Environment Variables")
    print("=" * 60)
    
    required_vars = [
        'COINBASE_COMMERCE_API_KEY',
        'COINBASE_COMMERCE_WEBHOOK_SECRET',
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'SUPABASE_SERVICE_ROLE_KEY'
    ]
    
    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * 10}...{value[-4:] if len(value) > 4 else '***'}")
        else:
            print(f"❌ {var}: NOT SET")
            all_set = False
    
    return all_set

def test_coinbase_api():
    """Test basic Coinbase Commerce API connectivity"""
    print("\n" + "=" * 60)
    print("Testing Coinbase Commerce API")
    print("=" * 60)
    
    api_key = os.getenv('COINBASE_COMMERCE_API_KEY')
    if not api_key:
        print("❌ COINBASE_COMMERCE_API_KEY not set")
        return False
    
    try:
        from coinbase_commerce.client import Client
        client = Client(api_key=api_key)
        
        # Try to list charges (this will validate API key)
        charges = client.charge.list()
        print(f"✅ Successfully connected to Coinbase Commerce API")
        print(f"Total charges found: {len(charges.data)}")
        
        # Show recent charges
        if charges.data:
            print("\nRecent charges:")
            for charge in charges.data[:3]:  # Show first 3
                print(f"  - {charge.id}: {charge.name} ({getattr(charge, 'status', 'N/A')})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to Coinbase Commerce API: {e}")
        return False

def test_supabase_connection():
    """Test Supabase database connectivity"""
    print("\n" + "=" * 60)
    print("Testing Supabase Connection")
    print("=" * 60)
    
    try:
        # Import the supabase manager from the app
        sys.path.append('/Users/agmac/Desktop/app')
        from supabase_client import SupabaseManager
        
        supabase_manager = SupabaseManager()
        
        if supabase_manager.is_connected():
            print("✅ Successfully connected to Supabase")
            
            # Test some basic operations
            try:
                # Try to get a test user (this will verify database access)
                test_user = supabase_manager.get_user_by_email("test@example.com")
                print(f"Test query successful (test user found: {bool(test_user)})")
                return True
            except Exception as e:
                print(f"⚠️ Connected but query failed: {e}")
                return False
        else:
            print("❌ Failed to connect to Supabase")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Supabase: {e}")
        return False

def check_payment_record(charge_id):
    """Check if a specific payment record exists in the database"""
    print(f"\n" + "=" * 60)
    print(f"Checking Payment Record: {charge_id}")
    print("=" * 60)
    
    try:
        sys.path.append('/Users/agmac/Desktop/app')
        from supabase_client import SupabaseManager
        
        supabase_manager = SupabaseManager()
        payment_record = supabase_manager.get_payment_by_id(charge_id)
        
        if payment_record:
            print("✅ Payment record found in database:")
            for key, value in payment_record.items():
                print(f"  {key}: {value}")
            return True
        else:
            print("❌ Payment record not found in database")
            return False
            
    except Exception as e:
        print(f"❌ Error checking payment record: {e}")
        return False

def main():
    """Run all tests"""
    print("Coinbase Commerce Payment Debug Tool")
    print("=" * 60)
    
    results = []
    
    # Run all tests
    results.append(("Environment Variables", check_environment_variables()))
    results.append(("Coinbase API", test_coinbase_api()))
    results.append(("Supabase Connection", test_supabase_connection()))
    results.append(("Webhook Accessibility", test_coinbase_webhook_accessibility()))
    
    # Test specific charge if provided
    if len(sys.argv) > 1:
        charge_id = sys.argv[1]
        results.append((f"Payment Record ({charge_id})", check_payment_record(charge_id)))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 All tests passed! Your Coinbase payment setup looks good.")
    else:
        print("\n⚠️ Some tests failed. Please fix the issues above.")
    
    print("\nNext steps:")
    print("1. Make a test payment with Coinbase Commerce")
    print("2. Check the webhook logs in your app")
    print("3. Use the manual verification endpoint if needed:")
    print("   POST /verify_payment/<charge_id>")
    
    return all_passed

if __name__ == "__main__":
    main()
