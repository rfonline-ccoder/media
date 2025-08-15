#!/usr/bin/env python3
"""
SwagMedia Registration and Application System Testing
Focused testing for user registration, application approval, and admin management
Based on review request requirements
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuration
BASE_URL = "https://request-tracker-11.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"login": "admin", "password": "admin123"}

class RegistrationSystemTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        self.created_applications = []
        self.created_users = []
        
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
    
    def setup_admin_authentication(self):
        """Setup admin authentication for testing"""
        print("\n=== Setting up Admin Authentication ===")
        
        try:
            response = self.session.post(f"{BASE_URL}/login", json=ADMIN_CREDENTIALS)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user" in data:
                    self.admin_token = data["access_token"]
                    user = data["user"]
                    
                    if user.get("admin_level", 0) >= 1:
                        self.log_test("Admin Authentication", True, f"Successfully authenticated as admin: {user.get('nickname', 'Unknown')}")
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
    
    def test_database_connection(self):
        """Test database connection and existing data"""
        print("\n=== Testing Database Connection ===")
        
        try:
            # Test health endpoint
            response = self.session.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                self.log_test("API Health Check", True, "API is responding correctly")
            else:
                self.log_test("API Health Check", False, f"Health check failed: {response.status_code}")
            
            # Check existing users
            if self.admin_token:
                users_response = self.session.get(f"{BASE_URL}/admin/users")
                if users_response.status_code == 200:
                    users = users_response.json()
                    admin_users = [u for u in users if u.get("admin_level", 0) >= 1]
                    regular_users = [u for u in users if u.get("admin_level", 0) == 0]
                    
                    self.log_test("Database Users Check", True, 
                                f"Found {len(users)} total users: {len(admin_users)} admin(s), {len(regular_users)} regular user(s)")
                    
                    # Check if admin user exists
                    admin_user = next((u for u in users if u.get("login") == "admin"), None)
                    if admin_user:
                        self.log_test("Admin User Exists", True, f"Admin user found: {admin_user.get('nickname', 'Unknown')}")
                    else:
                        self.log_test("Admin User Exists", False, "Admin user not found in database")
                else:
                    self.log_test("Database Users Check", False, f"Failed to get users: {users_response.status_code}")
            
            # Check existing applications
            if self.admin_token:
                apps_response = self.session.get(f"{BASE_URL}/admin/applications")
                if apps_response.status_code == 200:
                    applications = apps_response.json()
                    pending_apps = [a for a in applications if a.get("status") == "pending"]
                    approved_apps = [a for a in applications if a.get("status") == "approved"]
                    rejected_apps = [a for a in applications if a.get("status") == "rejected"]
                    
                    self.log_test("Database Applications Check", True, 
                                f"Found {len(applications)} applications: {len(pending_apps)} pending, {len(approved_apps)} approved, {len(rejected_apps)} rejected")
                else:
                    self.log_test("Database Applications Check", False, f"Failed to get applications: {apps_response.status_code}")
                    
        except Exception as e:
            self.log_test("Database Connection", False, f"Exception: {str(e)}")
    
    def test_user_registration_process(self):
        """Test the complete user registration process"""
        print("\n=== Testing User Registration Process ===")
        
        # Create unique test data
        timestamp = datetime.now().strftime('%H%M%S')
        test_users = [
            {
                "nickname": f"TestUser1_{timestamp}",
                "login": f"testuser1_{timestamp}",
                "password": "testpassword123",
                "vk_link": "https://vk.com/testuser1",
                "channel_link": "https://t.me/testchannel1"
            },
            {
                "nickname": f"TestUser2_{timestamp}",
                "login": f"testuser2_{timestamp}",
                "password": "testpassword456",
                "vk_link": "https://vk.com/testuser2",
                "channel_link": "https://youtube.com/testchannel2"
            },
            {
                "nickname": f"TestUser3_{timestamp}",
                "login": f"testuser3_{timestamp}",
                "password": "testpassword789",
                "vk_link": "https://vk.com/testuser3",
                "channel_link": "https://instagram.com/testchannel3"
            }
        ]
        
        for i, user_data in enumerate(test_users, 1):
            try:
                # Step 1: Submit registration
                response = self.session.post(f"{BASE_URL}/register", json=user_data)
                
                if response.status_code == 200:
                    result = response.json()
                    if "заявка" in result.get("message", "").lower():
                        self.log_test(f"User {i} Registration Submission", True, 
                                    f"Registration submitted successfully: {result.get('message', '')}")
                        
                        # Wait a moment for database to process
                        time.sleep(1)
                        
                        # Step 2: Check if application appears in admin panel
                        if self.admin_token:
                            apps_response = self.session.get(f"{BASE_URL}/admin/applications")
                            if apps_response.status_code == 200:
                                applications = apps_response.json()
                                
                                # Find our application
                                our_app = None
                                for app in applications:
                                    if (app.get("login") == user_data["login"] and 
                                        app.get("nickname") == user_data["nickname"]):
                                        our_app = app
                                        break
                                
                                if our_app:
                                    self.log_test(f"User {i} Application in Admin Panel", True, 
                                                f"Application found in admin panel with status: {our_app.get('status', 'unknown')}")
                                    self.created_applications.append(our_app)
                                else:
                                    self.log_test(f"User {i} Application in Admin Panel", False, 
                                                "Application NOT found in admin panel - this is the reported issue!")
                            else:
                                self.log_test(f"User {i} Application Check", False, 
                                            f"Failed to get applications: {apps_response.status_code}")
                        else:
                            self.log_test(f"User {i} Application Check", False, "No admin token available")
                    else:
                        self.log_test(f"User {i} Registration Submission", False, 
                                    f"Unexpected response: {result}")
                else:
                    self.log_test(f"User {i} Registration Submission", False, 
                                f"Registration failed: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.log_test(f"User {i} Registration Process", False, f"Exception: {str(e)}")
    
    def test_application_approval_process(self):
        """Test the application approval process"""
        print("\n=== Testing Application Approval Process ===")
        
        if not self.admin_token:
            self.log_test("Application Approval", False, "No admin token available")
            return
        
        if not self.created_applications:
            self.log_test("Application Approval", False, "No applications to approve")
            return
        
        for i, application in enumerate(self.created_applications, 1):
            try:
                app_id = application["id"]
                
                # Step 1: Approve the application
                # Test with different media types
                media_type = 0 if i % 2 == 1 else 1  # Alternate between free (0) and paid (1)
                
                approve_response = self.session.post(
                    f"{BASE_URL}/admin/applications/{app_id}/approve",
                    params={"media_type": media_type}
                )
                
                if approve_response.status_code == 200:
                    result = approve_response.json()
                    self.log_test(f"Application {i} Approval", True, 
                                f"Application approved successfully: {result.get('message', '')}")
                    
                    # Wait for database to process
                    time.sleep(1)
                    
                    # Step 2: Check if user was created
                    users_response = self.session.get(f"{BASE_URL}/admin/users")
                    if users_response.status_code == 200:
                        users = users_response.json()
                        
                        # Find the created user
                        created_user = None
                        for user in users:
                            if (user.get("login") == application["login"] and 
                                user.get("nickname") == application["nickname"]):
                                created_user = user
                                break
                        
                        if created_user:
                            self.log_test(f"User {i} Creation Verification", True, 
                                        f"User created successfully with media_type: {created_user.get('media_type', 'unknown')}")
                            self.created_users.append(created_user)
                            
                            # Verify user properties
                            if created_user.get("is_approved") == True:
                                self.log_test(f"User {i} Approval Status", True, "User is marked as approved")
                            else:
                                self.log_test(f"User {i} Approval Status", False, "User is not marked as approved")
                            
                            if created_user.get("media_type") == media_type:
                                self.log_test(f"User {i} Media Type", True, f"Media type correctly set to {media_type}")
                            else:
                                self.log_test(f"User {i} Media Type", False, 
                                            f"Media type mismatch. Expected: {media_type}, Got: {created_user.get('media_type')}")
                        else:
                            self.log_test(f"User {i} Creation Verification", False, 
                                        "User was not created after application approval")
                    else:
                        self.log_test(f"User {i} Creation Check", False, 
                                    f"Failed to get users: {users_response.status_code}")
                    
                    # Step 3: Check application status was updated
                    apps_response = self.session.get(f"{BASE_URL}/admin/applications")
                    if apps_response.status_code == 200:
                        applications = apps_response.json()
                        updated_app = next((a for a in applications if a["id"] == app_id), None)
                        
                        if updated_app and updated_app.get("status") == "approved":
                            self.log_test(f"Application {i} Status Update", True, "Application status updated to 'approved'")
                        else:
                            self.log_test(f"Application {i} Status Update", False, 
                                        f"Application status not updated correctly. Status: {updated_app.get('status') if updated_app else 'not found'}")
                    else:
                        self.log_test(f"Application {i} Status Check", False, 
                                    f"Failed to check application status: {apps_response.status_code}")
                else:
                    self.log_test(f"Application {i} Approval", False, 
                                f"Approval failed: {approve_response.status_code} - {approve_response.text}")
                    
            except Exception as e:
                self.log_test(f"Application {i} Approval Process", False, f"Exception: {str(e)}")
    
    def test_user_login_after_approval(self):
        """Test that approved users can login"""
        print("\n=== Testing User Login After Approval ===")
        
        for i, user in enumerate(self.created_users, 1):
            try:
                # Find the original registration data
                original_app = None
                for app in self.created_applications:
                    if app["login"] == user["login"]:
                        original_app = app
                        break
                
                if not original_app:
                    self.log_test(f"User {i} Login Test", False, "Could not find original application data")
                    continue
                
                # Attempt to login
                login_data = {
                    "login": user["login"],
                    "password": original_app["password"]
                }
                
                # Create a new session for this test to avoid conflicts
                test_session = requests.Session()
                response = test_session.post(f"{BASE_URL}/login", json=login_data)
                
                if response.status_code == 200:
                    result = response.json()
                    if "access_token" in result and "user" in result:
                        returned_user = result["user"]
                        if returned_user.get("nickname") == user["nickname"]:
                            self.log_test(f"User {i} Login Success", True, 
                                        f"User can login successfully: {returned_user.get('nickname')}")
                            
                            # Test accessing protected endpoint
                            test_session.headers.update({"Authorization": f"Bearer {result['access_token']}"})
                            profile_response = test_session.get(f"{BASE_URL}/profile")
                            
                            if profile_response.status_code == 200:
                                profile_data = profile_response.json()
                                if profile_data.get("nickname") == user["nickname"]:
                                    self.log_test(f"User {i} Profile Access", True, "User can access protected endpoints")
                                else:
                                    self.log_test(f"User {i} Profile Access", False, "Profile data mismatch")
                            else:
                                self.log_test(f"User {i} Profile Access", False, 
                                            f"Profile access failed: {profile_response.status_code}")
                        else:
                            self.log_test(f"User {i} Login Success", False, "Login returned wrong user data")
                    else:
                        self.log_test(f"User {i} Login Success", False, "Login response missing required fields")
                else:
                    self.log_test(f"User {i} Login Success", False, 
                                f"Login failed: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.log_test(f"User {i} Login Test", False, f"Exception: {str(e)}")
    
    def test_admin_user_creation(self):
        """Test creating admin user with specific credentials if needed"""
        print("\n=== Testing Admin User Creation ===")
        
        if not self.admin_token:
            self.log_test("Admin User Creation", False, "No admin token available")
            return
        
        try:
            # Check if admin user with ba7a7am1ZX3 password exists
            users_response = self.session.get(f"{BASE_URL}/admin/users")
            if users_response.status_code == 200:
                users = users_response.json()
                
                # Look for admin user with specific login
                target_admin = next((u for u in users if u.get("login") == "admin"), None)
                
                if target_admin:
                    self.log_test("Target Admin User Check", True, 
                                f"Admin user 'admin' exists with nickname: {target_admin.get('nickname', 'Unknown')}")
                    
                    # Test login with the specific password mentioned in review request
                    test_session = requests.Session()
                    test_credentials = {"login": "admin", "password": "ba7a7am1ZX3"}
                    
                    test_response = test_session.post(f"{BASE_URL}/login", json=test_credentials)
                    if test_response.status_code == 200:
                        self.log_test("Admin ba7a7am1ZX3 Password", True, "Admin can login with ba7a7am1ZX3 password")
                    else:
                        self.log_test("Admin ba7a7am1ZX3 Password", False, 
                                    f"Admin cannot login with ba7a7am1ZX3 password: {test_response.status_code}")
                        
                        # Note: We cannot create a new admin user as that would require database manipulation
                        # The review request asks to create admin with ba7a7am1ZX3 if it doesn't exist
                        # But we can only test with existing credentials
                        self.log_test("Admin Password Update Needed", False, 
                                    "Admin user exists but password may need to be updated to ba7a7am1ZX3")
                else:
                    self.log_test("Target Admin User Check", False, "Admin user 'admin' not found")
            else:
                self.log_test("Admin User Creation", False, f"Failed to get users: {users_response.status_code}")
                
        except Exception as e:
            self.log_test("Admin User Creation", False, f"Exception: {str(e)}")
    
    def test_edge_cases(self):
        """Test edge cases and error conditions"""
        print("\n=== Testing Edge Cases ===")
        
        try:
            # Test 1: Duplicate registration
            timestamp = datetime.now().strftime('%H%M%S')
            duplicate_data = {
                "nickname": f"DuplicateTest_{timestamp}",
                "login": f"duplicatetest_{timestamp}",
                "password": "testpassword123",
                "vk_link": "https://vk.com/duplicatetest",
                "channel_link": "https://t.me/duplicatetest"
            }
            
            # First registration
            response1 = self.session.post(f"{BASE_URL}/register", json=duplicate_data)
            if response1.status_code == 200:
                # Second registration with same data
                response2 = self.session.post(f"{BASE_URL}/register", json=duplicate_data)
                if response2.status_code == 400:
                    error_data = response2.json()
                    if "занят" in str(error_data).lower():
                        self.log_test("Duplicate Registration Prevention", True, "Duplicate registration correctly prevented")
                    else:
                        self.log_test("Duplicate Registration Prevention", False, f"Wrong error message: {error_data}")
                else:
                    self.log_test("Duplicate Registration Prevention", False, 
                                f"Duplicate registration not prevented: {response2.status_code}")
            else:
                self.log_test("Duplicate Registration Test Setup", False, 
                            f"Initial registration failed: {response1.status_code}")
            
            # Test 2: Invalid application ID approval
            if self.admin_token:
                fake_app_id = "fake-application-id-12345"
                response = self.session.post(f"{BASE_URL}/admin/applications/{fake_app_id}/approve")
                
                if response.status_code == 404:
                    self.log_test("Invalid Application ID", True, "Invalid application ID correctly rejected")
                else:
                    self.log_test("Invalid Application ID", False, 
                                f"Expected 404, got {response.status_code}")
            
            # Test 3: Unauthenticated admin access
            unauth_session = requests.Session()
            response = unauth_session.get(f"{BASE_URL}/admin/applications")
            
            if response.status_code == 401:
                self.log_test("Unauthenticated Admin Access", True, "Admin endpoints properly protected")
            else:
                self.log_test("Unauthenticated Admin Access", False, 
                            f"Admin endpoints not properly protected: {response.status_code}")
                
        except Exception as e:
            self.log_test("Edge Cases", False, f"Exception: {str(e)}")
    
    def run_comprehensive_test(self):
        """Run all registration system tests"""
        print("🚀 Starting SwagMedia Registration System Tests")
        print(f"Testing against: {BASE_URL}")
        print("=" * 80)
        
        # Setup
        if not self.setup_admin_authentication():
            print("❌ Cannot proceed without admin authentication")
            return False
        
        # Run tests in logical order
        self.test_database_connection()
        self.test_user_registration_process()
        self.test_application_approval_process()
        self.test_user_login_after_approval()
        self.test_admin_user_creation()
        self.test_edge_cases()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 REGISTRATION SYSTEM TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Detailed results
        if failed_tests > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  ❌ {result['test']}: {result['message']}")
        
        # Key findings
        print("\n🔍 KEY FINDINGS:")
        registration_issues = [r for r in self.test_results if not r["success"] and "Application in Admin Panel" in r["test"]]
        if registration_issues:
            print("  🚨 CRITICAL: Applications not appearing in admin panel - this confirms the reported issue!")
        
        approval_issues = [r for r in self.test_results if not r["success"] and "Approval" in r["test"]]
        if approval_issues:
            print("  ⚠️  Issues found in application approval process")
        
        login_issues = [r for r in self.test_results if not r["success"] and "Login" in r["test"]]
        if login_issues:
            print("  ⚠️  Issues found in user login after approval")
        
        if not registration_issues and not approval_issues and not login_issues:
            print("  ✅ Registration and application system working correctly")
        
        print(f"\n📝 Created {len(self.created_applications)} test applications")
        print(f"📝 Created {len(self.created_users)} test users")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = RegistrationSystemTester()
    success = tester.run_comprehensive_test()
    
    if not success:
        sys.exit(1)
    else:
        print("\n🎉 All registration system tests passed!")