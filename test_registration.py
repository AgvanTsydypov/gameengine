#!/usr/bin/env python3
"""
Test script to verify duplicate email registration is properly handled
"""
import requests
import json
import time

def test_duplicate_registration():
    """Test that duplicate email registration is properly rejected"""
    base_url = "http://localhost:8888"
    
    # Test email and password
    test_email = "test@example.com"
    test_password = "testpassword123"
    
    print("🧪 Testing duplicate email registration...")
    
    # First registration attempt
    print(f"1️⃣ Attempting first registration with email: {test_email}")
    response1 = requests.post(f"{base_url}/register", data={
        'email': test_email,
        'password': test_password,
        'confirm_password': test_password
    }, headers={'X-Requested-With': 'XMLHttpRequest'})
    
    print(f"   Status Code: {response1.status_code}")
    print(f"   Response: {response1.text}")
    
    # Wait a moment
    time.sleep(1)
    
    # Second registration attempt with same email
    print(f"2️⃣ Attempting second registration with same email: {test_email}")
    response2 = requests.post(f"{base_url}/register", data={
        'email': test_email,
        'password': test_password,
        'confirm_password': test_password
    }, headers={'X-Requested-With': 'XMLHttpRequest'})
    
    print(f"   Status Code: {response2.status_code}")
    print(f"   Response: {response2.text}")
    
    # Check if second registration was properly rejected
    if response2.status_code == 400:
        try:
            data = response2.json()
            if 'error' in data and 'already registered' in data['error'].lower():
                print("✅ SUCCESS: Duplicate email registration properly rejected!")
                return True
            else:
                print(f"❌ FAIL: Unexpected error message: {data.get('error', 'No error message')}")
                return False
        except json.JSONDecodeError:
            print("❌ FAIL: Response is not valid JSON")
            return False
    else:
        print(f"❌ FAIL: Expected status 400, got {response2.status_code}")
        return False

if __name__ == "__main__":
    success = test_duplicate_registration()
    exit(0 if success else 1)
