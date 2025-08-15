#!/usr/bin/env python3
"""
SwagMedia New Admin Functions Testing Suite
Tests the new administrative endpoints for warnings, user removal, and emergency state
"""

import requests
import json
import sys
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://localhost:8001/api"
ADMIN_CREDENTIALS = {"login": "admin", "password": "admin123"}

class NewAdminFunctionsTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        self.test_user_id = None
        
    def log_test(self, test_name, success, message, data=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if data and not success:
            print(f"   Data: {json.dumps(data, indent=2)}")
    
    def authenticate_admin(self):
        """Authenticate as admin user"""
        print("\n=== Admin Authentication ===")
        
        try:
            response = self.session.post(f"{BASE_URL}/login", json=ADMIN_CREDENTIALS)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user" in data:
                    self.admin_token = data["access_token"]
                    user = data["user"]
                    
                    if user.get("admin_level", 0) >= 1:
                        self.log_test("Admin Authentication", True, f"Successfully authenticated as admin")
                        self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
                        return True
                    else:
                        self.log_test("Admin Authentication", False, "User is not admin", user)
                else:
                    self.log_test("Admin Authentication", False, "Missing access_token or user in response", data)
            else:
                self.log_test("Admin Authentication", False, f"Login failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Exception during login: {str(e)}")
        
        return False
    
    def get_test_user(self):
        """Get a test user for admin operations"""
        print("\n=== Getting Test User ===")
        
        try:
            # Get list of users
            response = self.session.get(f"{BASE_URL}/admin/users")
            if response.status_code != 200:
                self.log_test("Get Test User", False, f"Failed to get users: {response.status_code}")
                return None
            
            users = response.json()
            if not users:
                self.log_test("Get Test User", False, "No users found")
                return None
            
            # Find a non-admin user for testing
            test_user = None
            for user in users:
                if user.get("admin_level", 0) == 0 and user.get("is_approved", False):
                    test_user = user
                    break
            
            if test_user:
                self.test_user_id = test_user["id"]
                self.log_test("Get Test User", True, f"Found test user: {test_user.get('nickname', 'Unknown')} (ID: {self.test_user_id})")
                return test_user
            else:
                self.log_test("Get Test User", False, "No suitable non-admin user found for testing")
                return None
                
        except Exception as e:
            self.log_test("Get Test User", False, f"Exception: {str(e)}")
            return None
    
    def test_user_warning_system(self):
        """Test POST /api/admin/users/{user_id}/warning - Warning system"""
        print("\n=== Testing Warning System ===")
        
        if not self.test_user_id:
            self.log_test("Warning System", False, "No test user available")
            return
        
        try:
            # Get user's current warning count
            users_response = self.session.get(f"{BASE_URL}/admin/users")
            if users_response.status_code != 200:
                self.log_test("Warning System - Get Current Warnings", False, "Failed to get users")
                return
            
            users = users_response.json()
            test_user = next((u for u in users if u["id"] == self.test_user_id), None)
            if not test_user:
                self.log_test("Warning System", False, "Test user not found")
                return
            
            original_warnings = test_user.get("warnings", 0)
            
            # Test giving a warning
            warning_data = {
                "reason": "Тестовое предупреждение - нарушение правил сообщества"
            }
            
            response = self.session.post(f"{BASE_URL}/admin/users/{self.test_user_id}/warning", json=warning_data)
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Warning API Call", True, f"Warning issued successfully: {result.get('message', '')}")
                
                # Verify warning count increased
                expected_warnings = original_warnings + 1
                if result.get("warnings_count") == expected_warnings:
                    self.log_test("Warning Count Update", True, f"Warning count correctly increased to {expected_warnings}")
                else:
                    self.log_test("Warning Count Update", False, f"Expected {expected_warnings}, got {result.get('warnings_count')}")
                
                # Verify reason is included in response
                if result.get("reason") == warning_data["reason"]:
                    self.log_test("Warning Reason Storage", True, "Warning reason correctly stored")
                else:
                    self.log_test("Warning Reason Storage", False, f"Expected '{warning_data['reason']}', got '{result.get('reason')}'")
                
                # Check if notification was created (verify in database by checking user's warnings)
                updated_users_response = self.session.get(f"{BASE_URL}/admin/users")
                if updated_users_response.status_code == 200:
                    updated_users = updated_users_response.json()
                    updated_user = next((u for u in updated_users if u["id"] == self.test_user_id), None)
                    
                    if updated_user and updated_user.get("warnings") == expected_warnings:
                        self.log_test("Warning Database Update", True, f"User warnings correctly updated in database to {expected_warnings}")
                        
                        # Test notification creation by checking if user has notifications
                        # We can't directly access user notifications, but we can infer from the API response
                        if "уведомление" in result.get("message", "").lower() or "notification" in result.get("message", "").lower():
                            self.log_test("Warning Notification Creation", True, "Notification creation confirmed")
                        else:
                            # Check if we can get notifications for this user (admin can see all notifications)
                            notifications_response = self.session.get(f"{BASE_URL}/notifications")
                            if notifications_response.status_code == 200:
                                notifications = notifications_response.json()
                                warning_notification = None
                                for notif in notifications:
                                    if (notif.get("user_id") == self.test_user_id and 
                                        "предупреждение" in notif.get("message", "").lower()):
                                        warning_notification = notif
                                        break
                                
                                if warning_notification:
                                    self.log_test("Warning Notification Creation", True, "Warning notification found in database")
                                else:
                                    self.log_test("Warning Notification Creation", False, "Warning notification not found")
                            else:
                                self.log_test("Warning Notification Creation", False, "Could not verify notification creation")
                    else:
                        self.log_test("Warning Database Update", False, f"User warnings not updated correctly in database")
                else:
                    self.log_test("Warning Database Update", False, "Failed to verify database update")
                    
            else:
                self.log_test("Warning API Call", False, f"API call failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Warning System", False, f"Exception: {str(e)}")
    
    def test_remove_from_media(self):
        """Test POST /api/admin/users/{user_id}/remove-from-media - Complete user removal"""
        print("\n=== Testing Remove From Media ===")
        
        # Create a new test user specifically for deletion testing
        try:
            # First create a test application
            test_app_data = {
                "nickname": f"test_delete_user_{datetime.now().strftime('%H%M%S')}",
                "login": f"test_delete_{datetime.now().strftime('%H%M%S')}",
                "password": "testpassword123",
                "vk_link": "https://vk.com/test_delete_user",
                "channel_link": "https://t.me/test_delete_channel"
            }
            
            # Register the test user
            register_response = self.session.post(f"{BASE_URL}/register", json=test_app_data)
            if register_response.status_code != 200:
                self.log_test("Remove From Media - Create Test User", False, f"Failed to create test user: {register_response.status_code}")
                return
            
            app_data = register_response.json()
            app_id = app_data.get("id")
            
            if not app_id:
                self.log_test("Remove From Media - Create Test User", False, "No application ID returned")
                return
            
            # Approve the application to create a user
            approve_response = self.session.post(f"{BASE_URL}/admin/applications/{app_id}/approve")
            if approve_response.status_code != 200:
                self.log_test("Remove From Media - Approve Test User", False, f"Failed to approve test user: {approve_response.status_code}")
                return
            
            # Get the created user ID
            users_response = self.session.get(f"{BASE_URL}/admin/users")
            if users_response.status_code != 200:
                self.log_test("Remove From Media - Find Test User", False, "Failed to get users")
                return
            
            users = users_response.json()
            test_user = next((u for u in users if u.get("login") == test_app_data["login"]), None)
            
            if not test_user:
                self.log_test("Remove From Media - Find Test User", False, "Test user not found after approval")
                return
            
            delete_user_id = test_user["id"]
            delete_user_nickname = test_user["nickname"]
            
            self.log_test("Remove From Media - Setup", True, f"Created test user for deletion: {delete_user_nickname}")
            
            # Now test the removal
            response = self.session.post(f"{BASE_URL}/admin/users/{delete_user_id}/remove-from-media")
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Remove From Media API Call", True, f"User removal successful: {result.get('message', '')}")
                
                # Verify user was completely removed
                verify_users_response = self.session.get(f"{BASE_URL}/admin/users")
                if verify_users_response.status_code == 200:
                    verify_users = verify_users_response.json()
                    deleted_user = next((u for u in verify_users if u["id"] == delete_user_id), None)
                    
                    if deleted_user is None:
                        self.log_test("User Complete Removal", True, "User completely removed from database")
                    else:
                        self.log_test("User Complete Removal", False, "User still exists in database after removal")
                    
                    # Verify removed_user_id in response
                    if result.get("removed_user_id") == delete_user_id:
                        self.log_test("Removal Response Verification", True, "Correct user ID returned in removal response")
                    else:
                        self.log_test("Removal Response Verification", False, f"Expected {delete_user_id}, got {result.get('removed_user_id')}")
                else:
                    self.log_test("User Complete Removal", False, "Failed to verify user removal")
                    
            else:
                self.log_test("Remove From Media API Call", False, f"API call failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Remove From Media", False, f"Exception: {str(e)}")
    
    def test_emergency_state(self):
        """Test POST /api/admin/users/{user_id}/emergency-state - Emergency state blocking"""
        print("\n=== Testing Emergency State ===")
        
        if not self.test_user_id:
            self.log_test("Emergency State", False, "No test user available")
            return
        
        try:
            # Get user's current state
            users_response = self.session.get(f"{BASE_URL}/admin/users")
            if users_response.status_code != 200:
                self.log_test("Emergency State - Get User State", False, "Failed to get users")
                return
            
            users = users_response.json()
            test_user = next((u for u in users if u["id"] == self.test_user_id), None)
            if not test_user:
                self.log_test("Emergency State", False, "Test user not found")
                return
            
            user_nickname = test_user.get("nickname", "Unknown")
            user_ip = test_user.get("registration_ip")
            
            # Test emergency state
            emergency_data = {
                "days": 7,  # Block for 7 days
                "reason": "Тестовое ЧС - серьезное нарушение правил платформы"
            }
            
            response = self.session.post(f"{BASE_URL}/admin/users/{self.test_user_id}/emergency-state", json=emergency_data)
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Emergency State API Call", True, f"Emergency state set successfully: {result.get('message', '')}")
                
                # Verify response data
                if result.get("user_id") == self.test_user_id:
                    self.log_test("Emergency State User ID", True, "Correct user ID in response")
                else:
                    self.log_test("Emergency State User ID", False, f"Expected {self.test_user_id}, got {result.get('user_id')}")
                
                if result.get("reason") == emergency_data["reason"]:
                    self.log_test("Emergency State Reason", True, "Reason correctly stored")
                else:
                    self.log_test("Emergency State Reason", False, f"Expected '{emergency_data['reason']}', got '{result.get('reason')}'")
                
                # Verify blocking period
                blocked_until = result.get("blocked_until")
                if blocked_until:
                    try:
                        blocked_date = datetime.fromisoformat(blocked_until.replace('Z', '+00:00'))
                        expected_date = datetime.utcnow() + timedelta(days=emergency_data["days"])
                        time_diff = abs((blocked_date - expected_date).total_seconds())
                        
                        if time_diff < 300:  # Allow 5 minutes difference
                            self.log_test("Emergency State Duration", True, f"Blocking period correctly set for {emergency_data['days']} days")
                        else:
                            self.log_test("Emergency State Duration", False, f"Blocking period incorrect. Expected ~{expected_date}, got {blocked_date}")
                    except Exception as date_e:
                        self.log_test("Emergency State Duration", False, f"Failed to parse blocked_until date: {date_e}")
                else:
                    self.log_test("Emergency State Duration", False, "No blocked_until date in response")
                
                # Verify IP blocking status
                ip_blocked = result.get("ip_blocked", False)
                blocked_ip = result.get("blocked_ip")
                
                if user_ip:
                    if ip_blocked and blocked_ip == user_ip:
                        self.log_test("Emergency State IP Blocking", True, f"IP {blocked_ip} correctly blocked")
                    else:
                        self.log_test("Emergency State IP Blocking", False, f"IP blocking failed. Expected {user_ip}, blocked: {ip_blocked}")
                else:
                    if not ip_blocked:
                        self.log_test("Emergency State IP Blocking", True, "No IP to block (user has no registration_ip)")
                    else:
                        self.log_test("Emergency State IP Blocking", False, "IP blocking reported but user has no registration_ip")
                
                # Verify user is blocked in database
                updated_users_response = self.session.get(f"{BASE_URL}/admin/users")
                if updated_users_response.status_code == 200:
                    updated_users = updated_users_response.json()
                    updated_user = next((u for u in updated_users if u["id"] == self.test_user_id), None)
                    
                    if updated_user:
                        if updated_user.get("blacklist_until") and not updated_user.get("is_approved", True):
                            self.log_test("Emergency State Database Update", True, "User correctly blocked in database")
                        else:
                            self.log_test("Emergency State Database Update", False, "User not properly blocked in database")
                    else:
                        self.log_test("Emergency State Database Update", False, "User not found after emergency state")
                else:
                    self.log_test("Emergency State Database Update", False, "Failed to verify database update")
                
                # Check blacklist for IP (if user had IP)
                if user_ip:
                    blacklist_response = self.session.get(f"{BASE_URL}/admin/blacklist")
                    if blacklist_response.status_code == 200:
                        blacklist_data = blacklist_response.json()
                        blacklisted_ips = blacklist_data.get("blacklisted_ips", [])
                        
                        ip_found = any(ip_entry.get("ip_address") == user_ip for ip_entry in blacklisted_ips)
                        if ip_found:
                            self.log_test("Emergency State IP Blacklist", True, f"IP {user_ip} found in blacklist")
                        else:
                            self.log_test("Emergency State IP Blacklist", False, f"IP {user_ip} not found in blacklist")
                    else:
                        self.log_test("Emergency State IP Blacklist", False, "Failed to check blacklist")
                
                # Check notification creation
                notifications_response = self.session.get(f"{BASE_URL}/notifications")
                if notifications_response.status_code == 200:
                    notifications = notifications_response.json()
                    emergency_notification = None
                    for notif in notifications:
                        if (notif.get("user_id") == self.test_user_id and 
                            "чрезвычайное" in notif.get("message", "").lower()):
                            emergency_notification = notif
                            break
                    
                    if emergency_notification:
                        self.log_test("Emergency State Notification", True, "Emergency state notification created")
                    else:
                        self.log_test("Emergency State Notification", False, "Emergency state notification not found")
                else:
                    self.log_test("Emergency State Notification", False, "Failed to check notifications")
                    
            else:
                self.log_test("Emergency State API Call", False, f"API call failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Emergency State", False, f"Exception: {str(e)}")
    
    def test_admin_authorization(self):
        """Test that all new endpoints require admin privileges"""
        print("\n=== Testing Admin Authorization ===")
        
        # Create a session without admin token
        non_admin_session = requests.Session()
        
        if not self.test_user_id:
            self.log_test("Admin Authorization", False, "No test user available")
            return
        
        endpoints_to_test = [
            (f"/admin/users/{self.test_user_id}/warning", {"reason": "test"}),
            (f"/admin/users/{self.test_user_id}/remove-from-media", {}),
            (f"/admin/users/{self.test_user_id}/emergency-state", {"days": 1, "reason": "test"})
        ]
        
        for endpoint, data in endpoints_to_test:
            try:
                response = non_admin_session.post(f"{BASE_URL}{endpoint}", json=data)
                
                if response.status_code == 401:
                    self.log_test(f"Admin Auth - {endpoint.split('/')[-1]}", True, "Correctly requires authentication")
                elif response.status_code == 403:
                    self.log_test(f"Admin Auth - {endpoint.split('/')[-1]}", True, "Correctly requires admin privileges")
                else:
                    self.log_test(f"Admin Auth - {endpoint.split('/')[-1]}", False, f"Expected 401/403, got {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Admin Auth - {endpoint.split('/')[-1]}", False, f"Exception: {str(e)}")
    
    def test_input_validation(self):
        """Test input validation for new endpoints"""
        print("\n=== Testing Input Validation ===")
        
        if not self.test_user_id:
            self.log_test("Input Validation", False, "No test user available")
            return
        
        try:
            # Test 1: Warning with empty reason
            response = self.session.post(f"{BASE_URL}/admin/users/{self.test_user_id}/warning", json={"reason": ""})
            if response.status_code == 422:
                self.log_test("Warning Empty Reason Validation", True, "Empty reason correctly rejected")
            else:
                self.log_test("Warning Empty Reason Validation", False, f"Expected 422, got {response.status_code}")
            
            # Test 2: Emergency state with invalid days (too high)
            response = self.session.post(f"{BASE_URL}/admin/users/{self.test_user_id}/emergency-state", 
                                       json={"days": 500, "reason": "test"})
            if response.status_code == 422:
                self.log_test("Emergency State Days Validation (High)", True, "Days > 365 correctly rejected")
            else:
                self.log_test("Emergency State Days Validation (High)", False, f"Expected 422, got {response.status_code}")
            
            # Test 3: Emergency state with invalid days (too low)
            response = self.session.post(f"{BASE_URL}/admin/users/{self.test_user_id}/emergency-state", 
                                       json={"days": 0, "reason": "test"})
            if response.status_code == 422:
                self.log_test("Emergency State Days Validation (Low)", True, "Days < 1 correctly rejected")
            else:
                self.log_test("Emergency State Days Validation (Low)", False, f"Expected 422, got {response.status_code}")
            
            # Test 4: Invalid user ID
            response = self.session.post(f"{BASE_URL}/admin/users/invalid-user-id/warning", 
                                       json={"reason": "test"})
            if response.status_code == 404:
                self.log_test("Invalid User ID Validation", True, "Invalid user ID correctly rejected")
            else:
                self.log_test("Invalid User ID Validation", False, f"Expected 404, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Input Validation", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all new admin function tests"""
        print("🚀 Starting SwagMedia New Admin Functions Tests")
        print(f"Testing against: {BASE_URL}")
        print("=" * 60)
        
        # Authenticate as admin
        if not self.authenticate_admin():
            print("❌ Failed to authenticate as admin. Cannot proceed with tests.")
            return False
        
        # Get test user
        test_user = self.get_test_user()
        if not test_user:
            print("❌ No test user available. Cannot proceed with user-specific tests.")
            # Still run authorization tests
            self.test_admin_authorization()
            self.test_input_validation()
        else:
            # Run all tests
            self.test_user_warning_system()
            self.test_emergency_state()
            self.test_remove_from_media()  # Run this last as it deletes a user
            self.test_admin_authorization()
            self.test_input_validation()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 NEW ADMIN FUNCTIONS TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  ❌ {result['test']}: {result['message']}")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = NewAdminFunctionsTester()
    success = tester.run_all_tests()
    
    if not success:
        sys.exit(1)
    else:
        print("\n🎉 All new admin function tests passed!")