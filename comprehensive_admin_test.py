#!/usr/bin/env python3
"""
Comprehensive test for new SwagMedia admin functions
Tests all three new endpoints with real data verification
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8001/api"
ADMIN_CREDENTIALS = {"login": "admin", "password": "admin123"}

def test_new_admin_functions():
    """Test all new admin functions comprehensively"""
    session = requests.Session()
    
    print("🔐 Authenticating as admin...")
    login_response = session.post(f"{BASE_URL}/login", json=ADMIN_CREDENTIALS)
    if login_response.status_code != 200:
        print(f"❌ Admin login failed: {login_response.status_code}")
        return False
    
    token = login_response.json()["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    print("✅ Admin authenticated successfully")
    
    # Get test user
    users_response = session.get(f"{BASE_URL}/admin/users")
    if users_response.status_code != 200:
        print("❌ Failed to get users")
        return False
    
    users = users_response.json()
    test_user = None
    for user in users:
        if user.get("admin_level", 0) == 0 and user.get("is_approved", False):
            test_user = user
            break
    
    if not test_user:
        print("❌ No test user found")
        return False
    
    user_id = test_user["id"]
    user_nickname = test_user["nickname"]
    print(f"👤 Using test user: {user_nickname} (ID: {user_id})")
    
    # Test 1: Warning System
    print("\n🚨 Testing Warning System...")
    original_warnings = test_user.get("warnings", 0)
    
    warning_data = {"reason": "Тестовое предупреждение - нарушение правил"}
    warning_response = session.post(f"{BASE_URL}/admin/users/{user_id}/warning", json=warning_data)
    
    if warning_response.status_code == 200:
        result = warning_response.json()
        print(f"✅ Warning issued: {result['message']}")
        print(f"✅ Warnings count: {original_warnings} → {result['warnings_count']}")
        
        # Verify in database
        updated_users = session.get(f"{BASE_URL}/admin/users").json()
        updated_user = next(u for u in updated_users if u["id"] == user_id)
        if updated_user["warnings"] == result["warnings_count"]:
            print("✅ Warning count verified in database")
        else:
            print("❌ Warning count mismatch in database")
    else:
        print(f"❌ Warning failed: {warning_response.status_code} - {warning_response.text}")
        return False
    
    # Test 2: Emergency State
    print("\n🚨 Testing Emergency State...")
    emergency_data = {"days": 5, "reason": "Тестовое ЧС - серьезное нарушение"}
    emergency_response = session.post(f"{BASE_URL}/admin/users/{user_id}/emergency-state", json=emergency_data)
    
    if emergency_response.status_code == 200:
        result = emergency_response.json()
        print(f"✅ Emergency state set: {result['message']}")
        print(f"✅ Blocked until: {result['blocked_until']}")
        print(f"✅ IP blocked: {result['ip_blocked']}")
        
        # Verify user is blocked
        updated_users = session.get(f"{BASE_URL}/admin/users").json()
        updated_user = next(u for u in updated_users if u["id"] == user_id)
        if updated_user["blacklist_until"] and not updated_user["is_approved"]:
            print("✅ User correctly blocked in database")
        else:
            print("❌ User not properly blocked in database")
        
        # Check blacklist
        blacklist_response = session.get(f"{BASE_URL}/admin/blacklist")
        if blacklist_response.status_code == 200:
            blacklist = blacklist_response.json()
            print(f"✅ Blacklist contains {len(blacklist['blacklisted_users'])} users, {len(blacklist['blacklisted_ips'])} IPs")
        
    else:
        print(f"❌ Emergency state failed: {emergency_response.status_code} - {emergency_response.text}")
        return False
    
    # Test 3: Create a user for removal test
    print("\n🗑️ Testing User Removal...")
    
    # Create test application
    test_app = {
        "nickname": f"delete_test_{datetime.now().strftime('%H%M%S')}",
        "login": f"delete_login_{datetime.now().strftime('%H%M%S')}",
        "password": "testpassword123",
        "vk_link": "https://vk.com/delete_test",
        "channel_link": "https://t.me/delete_test"
    }
    
    register_response = session.post(f"{BASE_URL}/register", json=test_app)
    if register_response.status_code != 200:
        print(f"❌ Failed to create test user: {register_response.status_code}")
        return False
    
    app_id = register_response.json()["id"]
    
    # Approve application
    approve_response = session.post(f"{BASE_URL}/admin/applications/{app_id}/approve")
    if approve_response.status_code != 200:
        print(f"❌ Failed to approve test user: {approve_response.status_code}")
        return False
    
    # Find the created user
    users = session.get(f"{BASE_URL}/admin/users").json()
    delete_user = next((u for u in users if u.get("login") == test_app["login"]), None)
    
    if not delete_user:
        print("❌ Created user not found")
        return False
    
    delete_user_id = delete_user["id"]
    delete_nickname = delete_user["nickname"]
    print(f"👤 Created user for deletion: {delete_nickname}")
    
    # Remove user
    remove_response = session.post(f"{BASE_URL}/admin/users/{delete_user_id}/remove-from-media")
    if remove_response.status_code == 200:
        result = remove_response.json()
        print(f"✅ User removed: {result['message']}")
        
        # Verify user is gone
        users = session.get(f"{BASE_URL}/admin/users").json()
        if not any(u["id"] == delete_user_id for u in users):
            print("✅ User completely removed from database")
        else:
            print("❌ User still exists in database")
    else:
        print(f"❌ User removal failed: {remove_response.status_code} - {remove_response.text}")
        return False
    
    print("\n🎉 All new admin functions tested successfully!")
    return True

if __name__ == "__main__":
    success = test_new_admin_functions()
    if success:
        print("\n✅ COMPREHENSIVE TEST PASSED")
    else:
        print("\n❌ COMPREHENSIVE TEST FAILED")