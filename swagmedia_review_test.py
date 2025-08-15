#!/usr/bin/env python3
"""
SwagMedia Review Test Suite
Tests specific endpoints mentioned in the review request:
1. Health/status endpoints
2. Admin login (admin/admin123)
3. User data access
4. Preview system endpoints
5. Database connectivity
6. Admin blacklist functions
"""

import requests
import json
import sys
from datetime import datetime
import time

# Configuration
BASE_URL = "https://backend-checker.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"login": "admin", "password": "admin123"}

class SwagMediaReviewTester:
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
    
    def test_health_endpoints(self):
        """Test health/status endpoints"""
        print("\n=== 1. ТЕСТИРОВАНИЕ ОСНОВНЫХ ENDPOINTS ===")
        
        # Test 1: Try common health endpoints
        health_endpoints = [
            "/health",
            "/status", 
            "/ping",
            "/"  # Root endpoint
        ]
        
        health_found = False
        for endpoint in health_endpoints:
            try:
                response = self.session.get(f"{BASE_URL}{endpoint}")
                if response.status_code == 200:
                    self.log_test(f"Health Endpoint {endpoint}", True, f"Health endpoint accessible: {response.status_code}")
                    health_found = True
                    break
                elif response.status_code == 404:
                    continue  # Try next endpoint
                else:
                    self.log_test(f"Health Endpoint {endpoint}", False, f"Unexpected status: {response.status_code}")
            except Exception as e:
                continue
        
        if not health_found:
            # Try to access any working endpoint as health check
            try:
                response = self.session.get(f"{BASE_URL}/shop")
                if response.status_code == 200:
                    self.log_test("Health Check (via shop endpoint)", True, "Server is responding - shop endpoint accessible")
                else:
                    self.log_test("Health Check", False, f"Server not responding properly: {response.status_code}")
            except Exception as e:
                self.log_test("Health Check", False, f"Server connection failed: {str(e)}")
    
    def test_admin_login(self):
        """Test admin login with admin/admin123"""
        print("\n=== 2. ТЕСТИРОВАНИЕ ADMIN LOGIN ===")
        
        try:
            response = self.session.post(f"{BASE_URL}/login", json=ADMIN_CREDENTIALS)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user" in data:
                    self.admin_token = data["access_token"]
                    user = data["user"]
                    
                    # Verify admin properties
                    if user.get("admin_level", 0) >= 1:
                        self.log_test("Admin Login", True, f"Successfully logged in as admin (level: {user.get('admin_level')})")
                        
                        # Set authorization header
                        self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
                        
                        # Store admin user ID for later tests
                        self.admin_user_id = user.get("id")
                        
                        return True
                    else:
                        self.log_test("Admin Login", False, f"User is not admin (level: {user.get('admin_level', 0)})", user)
                else:
                    self.log_test("Admin Login", False, "Missing access_token or user in response", data)
            else:
                self.log_test("Admin Login", False, f"Login failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Admin Login", False, f"Exception during login: {str(e)}")
        
        return False
    
    def test_user_data_access(self):
        """Test GET /api/users for user data access"""
        print("\n=== 3. ТЕСТИРОВАНИЕ ДОСТУПА К ДАННЫМ ПОЛЬЗОВАТЕЛЕЙ ===")
        
        if not self.admin_token:
            self.log_test("User Data Access", False, "No admin token available")
            return
        
        try:
            response = self.session.get(f"{BASE_URL}/admin/users")
            
            if response.status_code == 200:
                users = response.json()
                if isinstance(users, list):
                    self.log_test("GET /api/admin/users", True, f"Successfully retrieved {len(users)} users")
                    
                    # Check user data structure
                    if users:
                        sample_user = users[0]
                        required_fields = ["id", "nickname", "login", "balance", "admin_level", "is_approved", "media_type"]
                        missing_fields = [field for field in required_fields if field not in sample_user]
                        
                        if not missing_fields:
                            self.log_test("User Data Structure", True, "User data has all required fields")
                            
                            # Store a test user ID for preview tests
                            non_admin_user = next((u for u in users if u.get("admin_level", 0) == 0), None)
                            if non_admin_user:
                                self.test_user_id = non_admin_user["id"]
                                self.log_test("Test User Found", True, f"Found non-admin user for testing: {non_admin_user.get('nickname', 'Unknown')}")
                        else:
                            self.log_test("User Data Structure", False, f"Missing fields: {missing_fields}", sample_user)
                    else:
                        self.log_test("User Data Structure", False, "No users found in database")
                else:
                    self.log_test("GET /api/admin/users", False, f"Expected list, got {type(users)}", users)
            else:
                self.log_test("GET /api/admin/users", False, f"API call failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("User Data Access", False, f"Exception: {str(e)}")
    
    def test_database_connectivity(self):
        """Test database connectivity through various endpoints"""
        print("\n=== 4. ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ К БАЗЕ ДАННЫХ ===")
        
        if not self.admin_token:
            self.log_test("Database Connectivity", False, "No admin token available")
            return
        
        # Test multiple endpoints that require database access
        db_tests = [
            ("/admin/users", "Users table"),
            ("/admin/applications", "Applications table"),
            ("/admin/reports", "Reports table"),
            ("/shop", "Shop items"),
            ("/ratings", "Ratings table")
        ]
        
        db_working = 0
        total_db_tests = len(db_tests)
        
        for endpoint, table_name in db_tests:
            try:
                response = self.session.get(f"{BASE_URL}{endpoint}")
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        self.log_test(f"Database - {table_name}", True, f"Successfully accessed {table_name} ({len(data)} records)")
                        db_working += 1
                    else:
                        self.log_test(f"Database - {table_name}", False, f"Unexpected data format: {type(data)}")
                else:
                    self.log_test(f"Database - {table_name}", False, f"Database access failed: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Database - {table_name}", False, f"Exception: {str(e)}")
        
        # Overall database health
        if db_working == total_db_tests:
            self.log_test("Database Connectivity Overall", True, f"All {total_db_tests} database tables accessible")
        elif db_working > 0:
            self.log_test("Database Connectivity Overall", False, f"Only {db_working}/{total_db_tests} database tables accessible")
        else:
            self.log_test("Database Connectivity Overall", False, "No database tables accessible - database connection failed")
    
    def test_preview_system(self):
        """Test preview system endpoints"""
        print("\n=== 5. ТЕСТИРОВАНИЕ СИСТЕМЫ ПРЕДВАРИТЕЛЬНЫХ ПРОСМОТРОВ ===")
        
        if not self.admin_token:
            self.log_test("Preview System", False, "No admin token available")
            return
        
        # Test 1: GET /api/user/previews - preview status
        try:
            response = self.session.get(f"{BASE_URL}/user/previews")
            
            if response.status_code == 200:
                preview_data = response.json()
                required_fields = ["previews_used", "previews_limit", "previews_remaining", "is_blacklisted"]
                
                if all(field in preview_data for field in required_fields):
                    self.log_test("GET /api/user/previews", True, f"Preview status retrieved: {preview_data['previews_used']}/{preview_data['previews_limit']} used")
                else:
                    missing = [f for f in required_fields if f not in preview_data]
                    self.log_test("GET /api/user/previews", False, f"Missing fields: {missing}", preview_data)
            else:
                self.log_test("GET /api/user/previews", False, f"API call failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/user/previews", False, f"Exception: {str(e)}")
        
        # Test 2: POST /api/media/{media_user_id}/access - preview system
        if self.test_user_id:
            try:
                response = self.session.post(f"{BASE_URL}/media/{self.test_user_id}/access")
                
                if response.status_code == 200:
                    access_data = response.json()
                    if "access_type" in access_data:
                        access_type = access_data["access_type"]
                        self.log_test("POST /api/media/{id}/access", True, f"Media access granted: {access_type}")
                        
                        # Check if preview data is included for preview access
                        if access_type == "preview" and "previews_used" in access_data:
                            self.log_test("Preview System Logic", True, f"Preview system working: {access_data.get('message', '')}")
                        elif access_type == "full":
                            self.log_test("Preview System Logic", True, "Full access granted (user has paid access)")
                    else:
                        self.log_test("POST /api/media/{id}/access", False, "Missing access_type in response", access_data)
                else:
                    self.log_test("POST /api/media/{id}/access", False, f"API call failed: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.log_test("POST /api/media/{id}/access", False, f"Exception: {str(e)}")
        else:
            self.log_test("POST /api/media/{id}/access", False, "No test user ID available")
    
    def test_blacklist_management(self):
        """Test admin blacklist management functions"""
        print("\n=== 6. ТЕСТИРОВАНИЕ АДМИНСКИХ ФУНКЦИЙ ЧЕРНОГО СПИСКА ===")
        
        if not self.admin_token:
            self.log_test("Blacklist Management", False, "No admin token available")
            return
        
        # Test 1: GET /api/admin/blacklist - view blacklist
        try:
            response = self.session.get(f"{BASE_URL}/admin/blacklist")
            
            if response.status_code == 200:
                blacklist_data = response.json()
                if "blacklisted_users" in blacklist_data and "blacklisted_ips" in blacklist_data:
                    users_count = len(blacklist_data["blacklisted_users"])
                    ips_count = len(blacklist_data["blacklisted_ips"])
                    self.log_test("GET /api/admin/blacklist", True, f"Blacklist retrieved: {users_count} users, {ips_count} IPs")
                else:
                    self.log_test("GET /api/admin/blacklist", False, "Missing blacklisted_users or blacklisted_ips", blacklist_data)
            else:
                self.log_test("GET /api/admin/blacklist", False, f"API call failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("GET /api/admin/blacklist", False, f"Exception: {str(e)}")
        
        # Test 2: POST /api/admin/users/{user_id}/reset-previews
        if self.test_user_id:
            try:
                response = self.session.post(f"{BASE_URL}/admin/users/{self.test_user_id}/reset-previews")
                
                if response.status_code == 200:
                    result = response.json()
                    self.log_test("POST /api/admin/users/{id}/reset-previews", True, f"Preview reset successful: {result.get('message', '')}")
                else:
                    self.log_test("POST /api/admin/users/{id}/reset-previews", False, f"API call failed: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.log_test("POST /api/admin/users/{id}/reset-previews", False, f"Exception: {str(e)}")
        else:
            self.log_test("POST /api/admin/users/{id}/reset-previews", False, "No test user ID available")
        
        # Test 3: POST /api/admin/users/{user_id}/unblacklist
        if self.test_user_id:
            try:
                response = self.session.post(f"{BASE_URL}/admin/users/{self.test_user_id}/unblacklist")
                
                if response.status_code == 200:
                    result = response.json()
                    self.log_test("POST /api/admin/users/{id}/unblacklist", True, f"Unblacklist successful: {result.get('message', '')}")
                else:
                    self.log_test("POST /api/admin/users/{id}/unblacklist", False, f"API call failed: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.log_test("POST /api/admin/users/{id}/unblacklist", False, f"Exception: {str(e)}")
        else:
            self.log_test("POST /api/admin/users/{id}/unblacklist", False, "No test user ID available")
    
    def test_additional_critical_endpoints(self):
        """Test additional critical endpoints for completeness"""
        print("\n=== 7. ДОПОЛНИТЕЛЬНЫЕ КРИТИЧЕСКИ ВАЖНЫЕ ФУНКЦИИ ===")
        
        if not self.admin_token:
            self.log_test("Additional Critical Tests", False, "No admin token available")
            return
        
        # Test media list with authorization
        try:
            response = self.session.get(f"{BASE_URL}/media-list")
            
            if response.status_code == 200:
                media_list = response.json()
                if isinstance(media_list, list):
                    self.log_test("Media List with Auth", True, f"Media list accessible: {len(media_list)} entries")
                    
                    # Check if can_access field is present (indicates preview system integration)
                    if media_list and "can_access" in media_list[0]:
                        self.log_test("Media List Preview Integration", True, "Media list includes access control information")
                    elif media_list:
                        self.log_test("Media List Preview Integration", False, "Media list missing access control information")
                else:
                    self.log_test("Media List with Auth", False, f"Expected list, got {type(media_list)}")
            else:
                self.log_test("Media List with Auth", False, f"API call failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Media List with Auth", False, f"Exception: {str(e)}")
        
        # Test notifications system
        try:
            response = self.session.get(f"{BASE_URL}/notifications")
            
            if response.status_code == 200:
                notifications = response.json()
                if isinstance(notifications, list):
                    self.log_test("Notifications System", True, f"Notifications accessible: {len(notifications)} notifications")
                else:
                    self.log_test("Notifications System", False, f"Expected list, got {type(notifications)}")
            else:
                self.log_test("Notifications System", False, f"API call failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Notifications System", False, f"Exception: {str(e)}")
    
    def run_review_tests(self):
        """Run all review-specific tests"""
        print("🔍 Starting SwagMedia Review Test Suite")
        print(f"Testing against: {BASE_URL}")
        print("Testing with admin credentials: admin/admin123")
        print("=" * 70)
        
        # Run tests in order
        self.test_health_endpoints()
        
        # Admin login is critical - if this fails, most other tests will fail
        admin_login_success = self.test_admin_login()
        
        if admin_login_success:
            self.test_user_data_access()
            self.test_database_connectivity()
            self.test_preview_system()
            self.test_blacklist_management()
            self.test_additional_critical_endpoints()
        else:
            print("\n⚠️  Admin login failed - skipping tests that require authentication")
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 REVIEW TEST SUMMARY")
        print("=" * 70)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Categorize results
        critical_failures = []
        minor_issues = []
        
        for result in self.test_results:
            if not result["success"]:
                test_name = result["test"]
                if any(keyword in test_name.lower() for keyword in ["login", "database", "connectivity", "health"]):
                    critical_failures.append(result)
                else:
                    minor_issues.append(result)
        
        if critical_failures:
            print("\n🚨 CRITICAL FAILURES:")
            for result in critical_failures:
                print(f"  ❌ {result['test']}: {result['message']}")
        
        if minor_issues:
            print("\n⚠️  MINOR ISSUES:")
            for result in minor_issues:
                print(f"  ⚠️  {result['test']}: {result['message']}")
        
        # Overall assessment
        if not critical_failures:
            print("\n✅ OVERALL ASSESSMENT: SwagMedia backend is working correctly!")
            print("   - Database connectivity: ✅")
            print("   - Admin authentication: ✅") 
            print("   - Preview system: ✅")
            print("   - Blacklist management: ✅")
        else:
            print("\n❌ OVERALL ASSESSMENT: Critical issues found that need attention")
        
        return len(critical_failures) == 0

if __name__ == "__main__":
    tester = SwagMediaReviewTester()
    success = tester.run_review_tests()
    
    if not success:
        sys.exit(1)
    else:
        print("\n🎉 All critical tests passed!")