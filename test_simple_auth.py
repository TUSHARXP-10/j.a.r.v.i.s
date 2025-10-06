#!/usr/bin/env python3
"""
Simple test script to verify authentication is working
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_simple_auth():
    """Test basic authentication flow"""
    print("🧪 Testing Simple Authentication")
    print("=" * 40)
    
    # Test login with admin user
    print("\n1. Testing Admin Login")
    login_data = {"username": "admin_master", "password": "admin123"}
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Login response status: {response.status_code}")
        print(f"Login response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            print(f"✅ Admin login successful, token: {token[:20]}...")
            
            # Test getting user info
            print("\n2. Testing Get User Info")
            headers = {"Authorization": f"Bearer {token}"}
            user_response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
            print(f"User info status: {user_response.status_code}")
            print(f"User info: {user_response.text}")
            
            if user_response.status_code == 200:
                user_data = user_response.json()
                print(f"✅ User info retrieved: {user_data['username']} (Role: {user_data['role']})")
                
                # Test workflow listing
                print("\n3. Testing Workflow Listing")
                workflow_response = requests.get(f"{BASE_URL}/workflows", headers=headers)
                print(f"Workflow listing status: {workflow_response.status_code}")
                if workflow_response.status_code == 200:
                    workflows = workflow_response.json()
                    print(f"✅ Workflows listed: {len(workflows)} workflows found")
                else:
                    print(f"❌ Workflow listing failed: {workflow_response.text}")
            else:
                print(f"❌ User info failed: {user_response.text}")
        else:
            print(f"❌ Admin login failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_simple_auth()