#!/usr/bin/env python3
"""
Script to create an admin user
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def create_admin_user():
    """Create an admin user by registering and then updating role"""
    print("🛠️ Creating Admin User")
    print("=" * 30)
    
    # First, register a user
    print("\n1. Registering user...")
    register_data = {
        "username": "admin_master",
        "email": "admin@master.com", 
        "password": "admin123",
        "full_name": "Admin Master"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        print(f"Register status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            user_id = result.get("user", {}).get("id")
            print(f"✅ User registered with ID: {user_id}")
            
            # Now login to get admin token
            print("\n2. Logging in as admin_master...")
            login_data = {"username": "admin_master", "password": "admin123"}
            login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
            
            if login_response.status_code == 200:
                admin_token = login_response.json().get("access_token")
                print(f"✅ Admin token obtained")
                
                # Update the new user's role to admin
                print(f"\n3. Updating user {user_id} role to admin...")
                headers = {"Authorization": f"Bearer {admin_token}"}
                role_data = {"role": "admin"}
                
                role_response = requests.put(
                    f"{BASE_URL}/admin/users/{user_id}/role",
                    json=role_data,
                    headers=headers
                )
                print(f"Role update status: {role_response.status_code}")
                
                if role_response.status_code == 200:
                    print("✅ Admin user created successfully!")
                    
                    # Test the new admin login
                    print("\n4. Testing new admin login...")
                    new_login = {"username": "admin_master", "password": "admin123"}
                    new_response = requests.post(f"{BASE_URL}/auth/login", json=new_login)
                    
                    if new_response.status_code == 200:
                        new_token = new_response.json().get("access_token")
                        print(f"✅ New admin token: {new_token[:30]}...")
                        return new_token
                    else:
                        print(f"❌ New admin login failed: {new_response.text}")
                else:
                    print(f"❌ Role update failed: {role_response.text}")
            else:
                print(f"❌ Admin login failed: {login_response.text}")
        else:
            print(f"❌ Registration failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    create_admin_user()