#!/usr/bin/env python3
"""
Test script for role-based access control implementation
"""

import requests
import json
import time
from datetime import datetime

# Base URL for the API
BASE_URL = "http://localhost:8000"

def test_authentication_flow():
    """Test the complete authentication flow"""
    print("🧪 Testing Role-Based Access Control Implementation")
    print("=" * 60)
    
    # Test 1: User Registration
    print("\n1. Testing User Registration")
    print("-" * 30)
    
    # Register admin user
    admin_data = {
        "username": "admin_user",
        "email": "admin@example.com",
        "password": "admin123",
        "full_name": "Admin User",
        "role": "admin"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=admin_data)
        if response.status_code == 200:
            admin_user = response.json()
            print(f"✅ Admin user created: {admin_user['username']} (ID: {admin_user['id']})")
        else:
            print(f"❌ Admin registration failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Admin registration error: {e}")
    
    # Register regular user
    user_data = {
        "username": "regular_user",
        "email": "user@example.com",
        "password": "user123",
        "full_name": "Regular User",
        "role": "user"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        if response.status_code == 200:
            regular_user = response.json()
            print(f"✅ Regular user created: {regular_user['username']} (ID: {regular_user['id']})")
        else:
            print(f"❌ User registration failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ User registration error: {e}")
    
    # Register creator user
    creator_data = {
        "username": "creator_user",
        "email": "creator@example.com",
        "password": "creator123",
        "full_name": "Creator User",
        "role": "creator"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=creator_data)
        if response.status_code == 200:
            creator_user = response.json()
            print(f"✅ Creator user created: {creator_user['username']} (ID: {creator_user['id']})")
        else:
            print(f"❌ Creator registration failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Creator registration error: {e}")
    
    # Test 2: User Login
    print("\n2. Testing User Login")
    print("-" * 30)
    
    tokens = {}
    
    # Login as admin
    try:
        login_data = {"username": "admin_user", "password": "admin123"}
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            admin_token = response.json()["access_token"]
            tokens["admin"] = admin_token
            print("✅ Admin login successful")
        else:
            print(f"❌ Admin login failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Admin login error: {e}")
    
    # Login as regular user
    try:
        login_data = {"username": "regular_user", "password": "user123"}
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            user_token = response.json()["access_token"]
            tokens["user"] = user_token
            print("✅ Regular user login successful")
        else:
            print(f"❌ User login failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ User login error: {e}")
    
    # Login as creator
    try:
        login_data = {"username": "creator_user", "password": "creator123"}
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            creator_token = response.json()["access_token"]
            tokens["creator"] = creator_token
            print("✅ Creator login successful")
        else:
            print(f"❌ Creator login failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Creator login error: {e}")
    
    # Test 3: Access Control - Workflow Operations
    print("\n3. Testing Workflow Access Control")
    print("-" * 30)
    
    # Create workflow as creator
    workflow_data = {
        "name": "Test Workflow",
        "description": "A test workflow for RBAC testing",
        "nodes": [
            {"id": "1", "type": "start", "data": {"label": "Start"}, "position": {"x": 100, "y": 100}},
            {"id": "2", "type": "end", "data": {"label": "End"}, "position": {"x": 300, "y": 100}}
        ],
        "edges": [{"id": "e1", "source": "1", "target": "2"}]
    }
    
    creator_workflow_id = None
    
    # Test creating workflow as creator (should succeed)
    try:
        headers = {"Authorization": f"Bearer {tokens['creator']}"}
        response = requests.post(f"{BASE_URL}/workflows", json=workflow_data, headers=headers)
        if response.status_code == 200:
            workflow = response.json()
            creator_workflow_id = workflow["id"]
            print(f"✅ Creator created workflow successfully (ID: {creator_workflow_id})")
        else:
            print(f"❌ Creator workflow creation failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Creator workflow creation error: {e}")
    
    # Test creating workflow as regular user (should fail)
    try:
        headers = {"Authorization": f"Bearer {tokens['user']}"}
        response = requests.post(f"{BASE_URL}/workflows", json=workflow_data, headers=headers)
        if response.status_code == 403:
            print("✅ Regular user correctly blocked from creating workflows")
        else:
            print(f"❌ Regular user should be blocked from creating workflows, got: {response.status_code}")
    except Exception as e:
        print(f"❌ Regular user workflow creation error: {e}")
    
    # Test viewing workflows as different users
    print("\n4. Testing Workflow Visibility")
    print("-" * 30)
    
    # Admin should see all workflows
    try:
        headers = {"Authorization": f"Bearer {tokens['admin']}"}
        response = requests.get(f"{BASE_URL}/workflows", headers=headers)
        if response.status_code == 200:
            workflows = response.json()
            print(f"✅ Admin can see {len(workflows)} workflows")
        else:
            print(f"❌ Admin workflow listing failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Admin workflow listing error: {e}")
    
    # Regular user should only see public workflows and their own
    try:
        headers = {"Authorization": f"Bearer {tokens['user']}"}
        response = requests.get(f"{BASE_URL}/workflows", headers=headers)
        if response.status_code == 200:
            workflows = response.json()
            print(f"✅ Regular user can see {len(workflows)} workflows")
        else:
            print(f"❌ User workflow listing failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ User workflow listing error: {e}")
    
    # Test 5: Schedule Operations
    print("\n5. Testing Schedule Access Control")
    print("-" * 30)
    
    if creator_workflow_id:
        schedule_data = {
            "name": "Test Schedule",
            "cron_expression": "0 9 * * *",  # Daily at 9 AM
            "is_active": True,
            "input_data": {"test": "data"}
        }
        
        # Creator should be able to create schedule
        try:
            headers = {"Authorization": f"Bearer {tokens['creator']}"}
            response = requests.post(f"{BASE_URL}/workflows/{creator_workflow_id}/schedules", 
                                   json=schedule_data, headers=headers)
            if response.status_code == 200:
                schedule = response.json()
                print(f"✅ Creator created schedule successfully (ID: {schedule['id']})")
            else:
                print(f"❌ Creator schedule creation failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Creator schedule creation error: {e}")
        
        # Regular user should not be able to create schedule
        try:
            headers = {"Authorization": f"Bearer {tokens['user']}"}
            response = requests.post(f"{BASE_URL}/workflows/{creator_workflow_id}/schedules", 
                                   json=schedule_data, headers=headers)
            if response.status_code == 403:
                print("✅ Regular user correctly blocked from creating schedules")
            else:
                print(f"❌ Regular user should be blocked from creating schedules, got: {response.status_code}")
        except Exception as e:
            print(f"❌ User schedule creation error: {e}")
    
    # Test 6: Admin Operations
    print("\n6. Testing Admin Operations")
    print("-" * 30)
    
    # Admin should be able to list all users
    try:
        headers = {"Authorization": f"Bearer {tokens['admin']}"}
        response = requests.get(f"{BASE_URL}/admin/users", headers=headers)
        if response.status_code == 200:
            users = response.json()
            print(f"✅ Admin can see {len(users)} users")
        else:
            print(f"❌ Admin user listing failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Admin user listing error: {e}")
    
    # Regular user should not be able to list users
    try:
        headers = {"Authorization": f"Bearer {tokens['user']}"}
        response = requests.get(f"{BASE_URL}/admin/users", headers=headers)
        if response.status_code == 403:
            print("✅ Regular user correctly blocked from admin operations")
        else:
            print(f"❌ Regular user should be blocked from admin operations, got: {response.status_code}")
    except Exception as e:
        print(f"❌ User admin operations error: {e}")
    
    # Test 7: Unauthenticated Access
    print("\n7. Testing Unauthenticated Access")
    print("-" * 30)
    
    # Try to access workflows without authentication
    try:
        response = requests.get(f"{BASE_URL}/workflows")
        if response.status_code == 401:
            print("✅ Unauthenticated access correctly blocked")
        else:
            print(f"❌ Unauthenticated access should be blocked, got: {response.status_code}")
    except Exception as e:
        print(f"❌ Unauthenticated access test error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Role-Based Access Control Testing Complete!")
    print("=" * 60)

if __name__ == "__main__":
    test_authentication_flow()