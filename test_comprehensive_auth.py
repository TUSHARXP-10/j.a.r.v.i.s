#!/usr/bin/env python3
"""
Comprehensive test script to verify role-based access control
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_role_based_access():
    """Test comprehensive role-based access control"""
    print("🧪 Testing Role-Based Access Control")
    print("=" * 45)
    
    # Test 1: Admin user login
    print("\n1. Testing Admin Login")
    admin_login = {"username": "admin_master", "password": "admin123"}
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=admin_login)
        if response.status_code == 200:
            result = response.json()
            admin_token = result.get("access_token")
            print(f"✅ Admin login successful")
        else:
            print(f"❌ Admin login failed: {response.text}")
            return
            
        # Test 2: Create a regular user (admin only)
        print("\n2. Testing User Creation (Admin Only)")
        headers = {"Authorization": f"Bearer {admin_token}"}
        user_data = {
            "username": "test_user",
            "email": "test@user.com",
            "password": "test123",
            "full_name": "Test User"
        }
        
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        if response.status_code == 200:
            test_user_id = response.json().get("user", {}).get("id")
            print(f"✅ Test user created with ID: {test_user_id}")
        elif response.status_code == 400 and "already registered" in response.text:
            # User already exists, get their ID
            response = requests.get(f"{BASE_URL}/admin/users", headers=headers)
            if response.status_code == 200:
                users = response.json()
                test_user = next((u for u in users if u["username"] == "test_user"), None)
                if test_user:
                    test_user_id = test_user["id"]
                    print(f"✅ Test user already exists with ID: {test_user_id}")
                else:
                    print(f"❌ Could not find test user")
                    return
            else:
                print(f"❌ Could not get users list: {response.text}")
                return
        else:
            print(f"❌ User creation failed: {response.text}")
            return
            
        # Test 3: Login as regular user
        print("\n3. Testing Regular User Login")
        regular_login = {"username": "test_user", "password": "test123"}
        response = requests.post(f"{BASE_URL}/auth/login", json=regular_login)
        
        if response.status_code == 200:
            result = response.json()
            regular_token = result.get("access_token")
            user_role = result.get("user", {}).get("role")
            print(f"✅ Regular user login successful (Role: {user_role})")
        else:
            print(f"❌ Regular user login failed: {response.text}")
            return
            
        # Test 4: Admin-only endpoint access
        print("\n4. Testing Admin-Only Endpoint Access")
        
        # Try to list all users as admin
        response = requests.get(f"{BASE_URL}/admin/users", headers=headers)
        if response.status_code == 200:
            users = response.json()
            print(f"✅ Admin can list all users: {len(users)} users found")
        else:
            print(f"❌ Admin user listing failed: {response.text}")
            
        # Try to list users as regular user (should fail)
        regular_headers = {"Authorization": f"Bearer {regular_token}"}
        response = requests.get(f"{BASE_URL}/admin/users", headers=regular_headers)
        if response.status_code == 403:
            print(f"✅ Regular user correctly denied access to admin endpoint")
        else:
            print(f"❌ Regular user should be denied admin access")
            
        # Test 5: Update user role (admin only)
        print("\n5. Testing Role Update (Admin Only)")
        
        # Admin should be able to update role
        response = requests.put(f"{BASE_URL}/admin/users/{test_user_id}/role?role=creator", headers=headers)
        if response.status_code == 200:
            print(f"✅ Admin successfully updated user role")
        else:
            print(f"❌ Admin role update failed: {response.text}")
            
        # Regular user should not be able to update role
        response = requests.put(f"{BASE_URL}/admin/users/{test_user_id}/role?role=creator", headers=regular_headers)
        if response.status_code == 403:
            print(f"✅ Regular user correctly denied role update")
        else:
            print(f"❌ Regular user should be denied role update")
            
        # Test 6: Workflow access control
        print("\n6. Testing Workflow Access Control")
        
        # Create a workflow as admin
        workflow_data = {
            "name": "Test Workflow",
            "description": "Testing access control",
            "nodes": [{
                "id": "1", 
                "type": "input", 
                "position": {"x": 100, "y": 100},
                "data": {"label": "Input"}
            }],
            "edges": []
        }
        
        response = requests.post(f"{BASE_URL}/workflows", json=workflow_data, headers=headers)
        if response.status_code == 200:
            workflow_id = response.json().get("id")
            print(f"✅ Admin created workflow with ID: {workflow_id}")
        else:
            print(f"❌ Workflow creation failed: {response.text}")
            return
            
        # Test workflow access as different users
        response = requests.get(f"{BASE_URL}/workflows", headers=headers)
        if response.status_code == 200:
            workflows = response.json()
            print(f"✅ Admin can see {len(workflows)} workflows")
        
        response = requests.get(f"{BASE_URL}/workflows", headers=regular_headers)
        if response.status_code == 200:
            workflows = response.json()
            print(f"✅ Regular user can see {len(workflows)} workflows")
            
        # Test 7: Schedule access control
        print("\n7. Testing Schedule Access Control")
        schedule_data = {
            "name": "Test Schedule",
            "cron_expression": "0 0 * * *",
            "is_active": False,
            "input_data": {}
        }
        
        # Admin should be able to create schedule
        response = requests.post(f"{BASE_URL}/workflows/{workflow_id}/schedules", 
                               json=schedule_data, headers=headers)
        if response.status_code == 200:
            schedule_id = response.json().get("id")
            print(f"✅ Admin created schedule with ID: {schedule_id}")
        else:
            print(f"❌ Schedule creation failed: {response.text}")
            
        # Regular user should be able to view schedules (if they have permission)
        response = requests.get(f"{BASE_URL}/workflows/{workflow_id}/schedules", 
                              headers=regular_headers)
        if response.status_code == 200:
            schedules = response.json()
            print(f"✅ Regular user can see {len(schedules)} schedules")
        else:
            print(f"❌ Schedule viewing failed: {response.text}")
            
        print("\n🎉 Role-based access control testing completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_role_based_access()