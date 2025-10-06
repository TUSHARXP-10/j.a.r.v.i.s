#!/usr/bin/env python3

import requests
import json

BASE_URL = "http://localhost:8000"

def update_user_role():
    """Update the admin_master user to admin role"""
    print("🛠️ Updating User Role")
    print("=" * 25)
    
    # Login as admin_master first
    print("\n1. Logging in as admin_master...")
    login_data = {"username": "admin_master", "password": "admin123"}
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Login status: {response.status_code}")
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            print("✅ Login successful")
            
            # Update role to admin
            print("\n2. Updating role to admin...")
            headers = {"Authorization": f"Bearer {token}"}
            role_data = {"role": "admin"}
            
            role_response = requests.put(
                f"{BASE_URL}/admin/users/1/role",
                json=role_data,
                headers=headers
            )
            print(f"Role update status: {role_response.status_code}")
            
            if role_response.status_code == 200:
                print("✅ Role updated to admin!")
            else:
                print(f"❌ Role update failed: {role_response.text}")
        else:
            print(f"❌ Login failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    update_user_role()