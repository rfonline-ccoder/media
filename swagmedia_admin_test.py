#!/usr/bin/env python3
"""
SwagMedia Critical Admin Functions Testing Suite
Tests the specific administrative functions mentioned in the review request:
1. POST /api/admin/users/{user_id}/remove-from-media - Complete user removal from DB
2. POST /api/admin/users/{user_id}/emergency-state - IP and user blocking for specified days  
3. POST /api/admin/users/{user_id}/unblacklist - Remove IP and account blocking
4. POST /api/admin/users/{user_id}/warning - Issue warnings with auto-block on 3rd warning
5. MySQL database connection verification
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import time

# Configuration from review request
BASE_URL = "https://request-tracker-11.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"login": "admin", "password": "admin123"}

class SwagMediaAdminTester:
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
    
    def test_database_connection(self):
        """Test MySQL database connection and basic functionality"""
        print("\n=== Testing MySQL Database Connection ===")
        
        try:
            # Test health endpoint
            response = self.session.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                health_data = response.json()
                self.log_test("Health Check", True, f"Server responding: {health_data.get('message', 'OK')}")
            else:
                self.log_test("Health Check", False, f"Health check failed: {response.status_code}")
                return
            
            # Test admin login to verify database connectivity
            login_response = self.session.post(f"{BASE_URL}/login", json=ADMIN_CREDENTIALS)
            if login_response.status_code == 200:
                login_data = login_response.json()
                if "access_token" in login_data:
                    self.admin_token = login_data["access_token"]
                    self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
                    self.log_test("Admin Authentication", True, "Successfully authenticated as admin")
                    
                    # Test database access by getting users
                    users_response = self.session.get(f"{BASE_URL}/admin/users")
                    if users_response.status_code == 200:
                        users = users_response.json()
                        self.log_test("Database Access", True, f"Successfully accessed user data: {len(users)} users found")
                        
                        # Verify admin user exists in database
                        admin_user = next((u for u in users if u.get("login") == "admin"), None)
                        if admin_user:
                            self.log_test("Admin User in DB", True, f"Admin user found with ID: {admin_user['id']}")
                        else:
                            self.log_test("Admin User in DB", False, "Admin user not found in database")
                    else:
                        self.log_test("Database Access", False, f"Failed to access user data: {users_response.status_code}")
                else:
                    self.log_test("Admin Authentication", False, "No access token in login response")
            else:
                self.log_test("Admin Authentication", False, f"Admin login failed: {login_response.status_code} - {login_response.text}")
                
        except Exception as e:
            self.log_test("Database Connection", False, f"Exception during database test: {str(e)}")
    
    def test_preview_system_status(self):
        """Test the preview system status endpoint"""
        print("\n=== Testing Preview System Status ===")
        
        if not self.admin_token:
            self.log_test("Preview System Status", False, "No admin token available")
            return
        
        try:
            # Test user previews endpoint
            response = self.session.get(f"{BASE_URL}/user/previews")
            if response.status_code == 200:
                preview_data = response.json()
                required_fields = ["previews_used", "preview_limit", "previews_remaining", "is_blacklisted"]
                
                if all(field in preview_data for field in required_fields):
                    self.log_test("Preview Status API", True, f"Preview system working: {preview_data['previews_used']}/{preview_data['preview_limit']} used")
                else:
                    missing = [f for f in required_fields if f not in preview_data]
                    self.log_test("Preview Status API", False, f"Missing fields: {missing}", preview_data)
            else:
                self.log_test("Preview Status API", False, f"Preview status failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Preview System Status", False, f"Exception: {str(e)}")
    
    def test_blacklist_management(self):
        """Test blacklist management endpoints"""
        print("\n=== Testing Blacklist Management ===")
        
        if not self.admin_token:
            self.log_test("Blacklist Management", False, "No admin token available")
            return
        
        try:
            # Test blacklist endpoint
            response = self.session.get(f"{BASE_URL}/admin/blacklist")
            if response.status_code == 200:
                blacklist_data = response.json()
                
                if "ip_blacklist" in blacklist_data and "blacklisted_users" in blacklist_data:
                    ip_count = len(blacklist_data["ip_blacklist"])
                    user_count = len(blacklist_data["blacklisted_users"])
                    self.log_test("Blacklist API", True, f"Blacklist accessible: {ip_count} IPs, {user_count} users blocked")
                    
                    # Store blacklist data for later tests
                    self.blacklist_data = blacklist_data
                else:
                    self.log_test("Blacklist API", False, "Invalid blacklist response structure", blacklist_data)
            else:
                self.log_test("Blacklist API", False, f"Blacklist access failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Blacklist Management", False, f"Exception: {str(e)}")
    
    def create_test_user(self):
        """Create a test user for admin function testing"""
        print("\n=== Creating Test User ===")
        
        if not self.admin_token:
            self.log_test("Test User Creation", False, "No admin token available")
            return None
        
        try:
            # First create a registration application
            timestamp = datetime.now().strftime("%H%M%S")
            test_data = {
                "nickname": f"testuser_{timestamp}",
                "login": f"testlogin_{timestamp}",
                "password": "testpassword123",
                "vk_link": f"https://vk.com/testuser_{timestamp}",
                "channel_link": f"https://t.me/testchannel_{timestamp}"
            }
            
            # Remove auth header temporarily for registration
            auth_header = self.session.headers.pop("Authorization", None)
            
            register_response = self.session.post(f"{BASE_URL}/register", json=test_data)
            
            # Restore auth header
            if auth_header:
                self.session.headers["Authorization"] = auth_header
            
            if register_response.status_code == 200:
                self.log_test("Test User Registration", True, "Test user registration submitted")
                
                # Get applications to find our test application
                apps_response = self.session.get(f"{BASE_URL}/admin/applications")
                if apps_response.status_code == 200:
                    applications = apps_response.json()
                    test_app = next((app for app in applications if app.get("login") == test_data["login"]), None)
                    
                    if test_app:
                        app_id = test_app["id"]
                        
                        # Approve the application to create the user
                        approve_response = self.session.post(f"{BASE_URL}/admin/applications/{app_id}/approve", 
                                                           json={"media_type": 0})
                        
                        if approve_response.status_code == 200:
                            self.log_test("Test User Approval", True, "Test user application approved")
                            
                            # Get the created user
                            users_response = self.session.get(f"{BASE_URL}/admin/users")
                            if users_response.status_code == 200:
                                users = users_response.json()
                                test_user = next((u for u in users if u.get("login") == test_data["login"]), None)
                                
                                if test_user:
                                    self.test_user_id = test_user["id"]
                                    self.log_test("Test User Creation Complete", True, f"Test user created with ID: {self.test_user_id}")
                                    return test_user
                                else:
                                    self.log_test("Test User Creation Complete", False, "Test user not found after approval")
                            else:
                                self.log_test("Test User Creation Complete", False, "Failed to retrieve users after approval")
                        else:
                            self.log_test("Test User Approval", False, f"Application approval failed: {approve_response.status_code}")
                    else:
                        self.log_test("Test User Registration", False, "Test application not found")
                else:
                    self.log_test("Test User Registration", False, "Failed to retrieve applications")
            else:
                self.log_test("Test User Registration", False, f"Registration failed: {register_response.status_code} - {register_response.text}")
                
        except Exception as e:
            self.log_test("Test User Creation", False, f"Exception: {str(e)}")
        
        return None
    
    def test_warning_system(self):
        """Test the warning system with auto-block on 3rd warning"""
        print("\n=== Testing Warning System ===")
        
        if not self.admin_token:
            self.log_test("Warning System", False, "No admin token available")
            return
        
        if not self.test_user_id:
            self.log_test("Warning System", False, "No test user available")
            return
        
        try:
            # Test giving warnings
            for warning_num in range(1, 4):  # Give 3 warnings
                warning_data = {
                    "reason": f"Test warning #{warning_num} - rule violation"
                }
                
                response = self.session.post(f"{BASE_URL}/admin/users/{self.test_user_id}/warning", json=warning_data)
                
                if response.status_code == 200:
                    result = response.json()
                    warnings_count = result.get("warnings_count", 0)
                    auto_blocked = result.get("auto_blocked", False)
                    
                    if warning_num < 3:
                        if warnings_count == warning_num and not auto_blocked:
                            self.log_test(f"Warning #{warning_num}", True, f"Warning issued successfully: {warnings_count}/3")
                        else:
                            self.log_test(f"Warning #{warning_num}", False, f"Unexpected warning result: count={warnings_count}, blocked={auto_blocked}")
                    else:  # 3rd warning should trigger auto-block
                        if warnings_count == 3 and auto_blocked:
                            blocked_until = result.get("blocked_until")
                            self.log_test("Auto-Block on 3rd Warning", True, f"User automatically blocked until {blocked_until}")
                        else:
                            self.log_test("Auto-Block on 3rd Warning", False, f"Auto-block failed: count={warnings_count}, blocked={auto_blocked}")
                else:
                    self.log_test(f"Warning #{warning_num}", False, f"Warning API failed: {response.status_code} - {response.text}")
                    break
                
                # Small delay between warnings
                time.sleep(1)
                
        except Exception as e:
            self.log_test("Warning System", False, f"Exception: {str(e)}")
    
    def test_emergency_state(self):
        """Test emergency state (ЧС) function"""
        print("\n=== Testing Emergency State (ЧС) Function ===")
        
        if not self.admin_token:
            self.log_test("Emergency State", False, "No admin token available")
            return
        
        # Create a fresh test user for this test
        test_user = self.create_test_user()
        if not test_user:
            self.log_test("Emergency State", False, "Failed to create test user for ЧС test")
            return
        
        emergency_user_id = test_user["id"]
        
        try:
            # Test emergency state with 7 days block
            emergency_data = {
                "days": 7,
                "reason": "Test emergency state - serious platform violation"
            }
            
            response = self.session.post(f"{BASE_URL}/admin/users/{emergency_user_id}/emergency-state", json=emergency_data)
            
            if response.status_code == 200:
                result = response.json()
                
                # Check response structure
                required_fields = ["message", "user_id", "blocked_until", "reason", "ip_blocked"]
                if all(field in result for field in required_fields):
                    blocked_until = result.get("blocked_until")
                    ip_blocked = result.get("ip_blocked")
                    blocked_ip = result.get("blocked_ip")
                    
                    self.log_test("Emergency State API", True, f"ЧС issued successfully for {emergency_data['days']} days")
                    
                    # Verify user is blocked in database
                    users_response = self.session.get(f"{BASE_URL}/admin/users")
                    if users_response.status_code == 200:
                        users = users_response.json()
                        blocked_user = next((u for u in users if u["id"] == emergency_user_id), None)
                        
                        if blocked_user:
                            if blocked_user.get("blacklist_until") and not blocked_user.get("is_approved", True):
                                self.log_test("Emergency State User Block", True, "User correctly blocked in database")
                            else:
                                self.log_test("Emergency State User Block", False, f"User not properly blocked: blacklist_until={blocked_user.get('blacklist_until')}, is_approved={blocked_user.get('is_approved')}")
                        else:
                            self.log_test("Emergency State User Block", False, "User not found after ЧС")
                    
                    # Verify IP is in blacklist
                    blacklist_response = self.session.get(f"{BASE_URL}/admin/blacklist")
                    if blacklist_response.status_code == 200:
                        blacklist_data = blacklist_response.json()
                        ip_blacklist = blacklist_data.get("ip_blacklist", [])
                        
                        # Check if our user's IP is in blacklist
                        user_ip_blocked = any(entry.get("reason", "").startswith("ЧС:") for entry in ip_blacklist)
                        if user_ip_blocked:
                            self.log_test("Emergency State IP Block", True, "IP correctly added to blacklist")
                        else:
                            self.log_test("Emergency State IP Block", False, "IP not found in blacklist")
                    
                else:
                    missing = [f for f in required_fields if f not in result]
                    self.log_test("Emergency State API", False, f"Missing response fields: {missing}", result)
            else:
                self.log_test("Emergency State API", False, f"ЧС API failed: {response.status_code} - {response.text}")
            
            # Test invalid days validation
            invalid_data = {"days": 400, "reason": "Test invalid days"}  # > 365 should fail
            invalid_response = self.session.post(f"{BASE_URL}/admin/users/{emergency_user_id}/emergency-state", json=invalid_data)
            
            if invalid_response.status_code == 422:
                self.log_test("Emergency State Validation", True, "Invalid days (>365) correctly rejected")
            else:
                self.log_test("Emergency State Validation", False, f"Expected 422 for invalid days, got {invalid_response.status_code}")
                
        except Exception as e:
            self.log_test("Emergency State", False, f"Exception: {str(e)}")
    
    def test_unblacklist_function(self):
        """Test unblacklist function"""
        print("\n=== Testing Unblacklist Function ===")
        
        if not self.admin_token:
            self.log_test("Unblacklist Function", False, "No admin token available")
            return
        
        try:
            # Get blacklisted users
            blacklist_response = self.session.get(f"{BASE_URL}/admin/blacklist")
            if blacklist_response.status_code != 200:
                self.log_test("Unblacklist Function", False, "Failed to get blacklist")
                return
            
            blacklist_data = blacklist_response.json()
            blacklisted_users = blacklist_data.get("blacklisted_users", [])
            
            if not blacklisted_users:
                self.log_test("Unblacklist Function", False, "No blacklisted users to test unblacklist with")
                return
            
            # Use the first blacklisted user for testing
            test_blocked_user = blacklisted_users[0]
            blocked_user_id = test_blocked_user["id"]
            
            # Test unblacklist
            response = self.session.post(f"{BASE_URL}/admin/users/{blocked_user_id}/unblacklist")
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Unblacklist API", True, f"Unblacklist successful: {result.get('message', '')}")
                
                # Verify user is unblocked
                users_response = self.session.get(f"{BASE_URL}/admin/users")
                if users_response.status_code == 200:
                    users = users_response.json()
                    unblocked_user = next((u for u in users if u["id"] == blocked_user_id), None)
                    
                    if unblocked_user:
                        if not unblocked_user.get("blacklist_until") and unblocked_user.get("is_approved", False):
                            self.log_test("Unblacklist Verification", True, "User successfully unblocked and approved")
                        else:
                            self.log_test("Unblacklist Verification", False, f"User not properly unblocked: blacklist_until={unblocked_user.get('blacklist_until')}, is_approved={unblocked_user.get('is_approved')}")
                    else:
                        self.log_test("Unblacklist Verification", False, "User not found after unblacklist")
                
                # Test reset previews function while we're here
                reset_response = self.session.post(f"{BASE_URL}/admin/users/{blocked_user_id}/reset-previews")
                if reset_response.status_code == 200:
                    self.log_test("Reset Previews", True, "Preview reset successful")
                else:
                    self.log_test("Reset Previews", False, f"Preview reset failed: {reset_response.status_code}")
                    
            else:
                self.log_test("Unblacklist API", False, f"Unblacklist failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Unblacklist Function", False, f"Exception: {str(e)}")
    
    def test_remove_from_media(self):
        """Test complete user removal from database"""
        print("\n=== Testing Remove From Media Function ===")
        
        if not self.admin_token:
            self.log_test("Remove From Media", False, "No admin token available")
            return
        
        # Create a fresh test user for removal
        test_user = self.create_test_user()
        if not test_user:
            self.log_test("Remove From Media", False, "Failed to create test user for removal")
            return
        
        removal_user_id = test_user["id"]
        user_nickname = test_user["nickname"]
        
        try:
            # First verify user exists
            users_response = self.session.get(f"{BASE_URL}/admin/users")
            if users_response.status_code == 200:
                users = users_response.json()
                user_exists = any(u["id"] == removal_user_id for u in users)
                
                if user_exists:
                    self.log_test("Pre-Removal User Check", True, f"User {user_nickname} exists before removal")
                    
                    # Test removal
                    response = self.session.post(f"{BASE_URL}/admin/users/{removal_user_id}/remove-from-media")
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        if "полностью удален" in result.get("message", "") or "removed" in result.get("message", ""):
                            self.log_test("Remove From Media API", True, f"User removal successful: {result.get('message', '')}")
                            
                            # Verify user is completely gone from database
                            verify_response = self.session.get(f"{BASE_URL}/admin/users")
                            if verify_response.status_code == 200:
                                updated_users = verify_response.json()
                                user_still_exists = any(u["id"] == removal_user_id for u in updated_users)
                                
                                if not user_still_exists:
                                    self.log_test("Complete User Removal", True, "User completely removed from database")
                                else:
                                    self.log_test("Complete User Removal", False, "User still exists in database after removal")
                            else:
                                self.log_test("Complete User Removal", False, "Failed to verify user removal")
                        else:
                            self.log_test("Remove From Media API", False, f"Unexpected response: {result}")
                    else:
                        self.log_test("Remove From Media API", False, f"Removal failed: {response.status_code} - {response.text}")
                else:
                    self.log_test("Pre-Removal User Check", False, "Test user not found before removal")
            else:
                self.log_test("Pre-Removal User Check", False, "Failed to get users list")
                
        except Exception as e:
            self.log_test("Remove From Media", False, f"Exception: {str(e)}")
    
    def test_media_access_system(self):
        """Test media access system with previews"""
        print("\n=== Testing Media Access System ===")
        
        if not self.admin_token:
            self.log_test("Media Access System", False, "No admin token available")
            return
        
        try:
            # Get media list to find a paid media user
            media_response = self.session.get(f"{BASE_URL}/media-list")
            if media_response.status_code == 200:
                media_list = media_response.json()
                
                # Find a paid media user
                paid_media_user = None
                for media in media_list:
                    if media.get("media_type") == "Платное":
                        paid_media_user = media
                        break
                
                if paid_media_user:
                    media_user_id = paid_media_user["id"]
                    
                    # Test accessing paid media (should use preview system for free users)
                    access_response = self.session.post(f"{BASE_URL}/media/{media_user_id}/access")
                    
                    if access_response.status_code == 200:
                        access_data = access_response.json()
                        access_type = access_data.get("access_type")
                        
                        if access_type in ["preview", "full"]:
                            self.log_test("Media Access API", True, f"Media access working: {access_type} access granted")
                            
                            if access_type == "preview":
                                previews_remaining = access_data.get("previews_remaining", 0)
                                self.log_test("Preview System", True, f"Preview system working: {previews_remaining} previews remaining")
                        else:
                            self.log_test("Media Access API", False, f"Unexpected access type: {access_type}")
                    else:
                        self.log_test("Media Access API", False, f"Media access failed: {access_response.status_code} - {access_response.text}")
                else:
                    self.log_test("Media Access System", False, "No paid media users found to test with")
            else:
                self.log_test("Media Access System", False, f"Failed to get media list: {media_response.status_code}")
                
        except Exception as e:
            self.log_test("Media Access System", False, f"Exception: {str(e)}")
    
    def run_critical_admin_tests(self):
        """Run all critical admin function tests"""
        print("🚨 Starting SwagMedia Critical Admin Functions Testing")
        print("Testing the specific functions mentioned in review request:")
        print("1. Database connection verification")
        print("2. Warning system with auto-block")
        print("3. Emergency state (ЧС) function")
        print("4. Unblacklist function")
        print("5. Complete user removal")
        print(f"Testing against: {BASE_URL}")
        print("=" * 80)
        
        # Run tests in logical order
        self.test_database_connection()
        
        if self.admin_token:
            self.test_preview_system_status()
            self.test_blacklist_management()
            self.test_media_access_system()
            
            # Create test user for admin function testing
            test_user = self.create_test_user()
            
            if test_user:
                self.test_warning_system()
            
            self.test_emergency_state()
            self.test_unblacklist_function()
            self.test_remove_from_media()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 CRITICAL ADMIN FUNCTIONS TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Categorize results by function
        functions = {
            "Database Connection": [],
            "Warning System": [],
            "Emergency State": [],
            "Unblacklist": [],
            "Remove From Media": [],
            "Preview System": [],
            "Other": []
        }
        
        for result in self.test_results:
            test_name = result["test"]
            categorized = False
            
            for func_name in functions.keys():
                if func_name.lower().replace(" ", "") in test_name.lower().replace(" ", ""):
                    functions[func_name].append(result)
                    categorized = True
                    break
            
            if not categorized:
                functions["Other"].append(result)
        
        print("\n🔍 RESULTS BY FUNCTION:")
        for func_name, results in functions.items():
            if results:
                func_passed = sum(1 for r in results if r["success"])
                func_total = len(results)
                status = "✅" if func_passed == func_total else "❌"
                print(f"  {status} {func_name}: {func_passed}/{func_total} tests passed")
        
        if failed_tests > 0:
            print("\n🚨 FAILED TESTS DETAILS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  ❌ {result['test']}: {result['message']}")
        
        print("\n" + "=" * 80)
        
        # Specific review request validation
        critical_functions = [
            "remove-from-media",
            "emergency-state", 
            "unblacklist",
            "warning"
        ]
        
        critical_results = {}
        for func in critical_functions:
            func_tests = [r for r in self.test_results if func.replace("-", "").lower() in r["test"].lower().replace(" ", "")]
            if func_tests:
                critical_results[func] = all(r["success"] for r in func_tests)
            else:
                critical_results[func] = False
        
        print("🎯 REVIEW REQUEST VALIDATION:")
        for func, success in critical_results.items():
            status = "✅ WORKING" if success else "❌ ISSUES"
            print(f"  {status}: {func}")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = SwagMediaAdminTester()
    success = tester.run_critical_admin_tests()
    
    if not success:
        print("\n⚠️  Some critical admin functions have issues!")
        sys.exit(1)
    else:
        print("\n🎉 All critical admin functions are working correctly!")