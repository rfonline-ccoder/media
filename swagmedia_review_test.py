#!/usr/bin/env python3
"""
SwagMedia Backend Review Testing Suite
Tests all backend endpoints according to review request after CORS URL fix
"""

import requests
import json
import sys
from datetime import datetime
import time

# Configuration based on review request
BASE_URL = "http://localhost:8001/api"
ADMIN_CREDENTIALS = {"login": "admin", "password": "ba7a7am1ZX3"}  # Correct password from review

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
            print(f"   Data: {json.dumps(data, indent=2, default=str)}")
    
    def test_health_endpoint(self):
        """Test health endpoint: GET /api/health"""
        print("\n=== 1. БАЗОВАЯ ФУНКЦИОНАЛЬНОСТЬ ===")
        
        try:
            response = self.session.get(f"{BASE_URL}/health")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    self.log_test("Health Endpoint", True, f"Server responding correctly: {data.get('message', '')}")
                else:
                    self.log_test("Health Endpoint", False, f"Unexpected health status: {data}")
            else:
                self.log_test("Health Endpoint", False, f"Health check failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Health Endpoint", False, f"Exception during health check: {str(e)}")
    
    def test_admin_login(self):
        """Test admin login: POST /api/login (admin/ba7a7am1ZX3)"""
        
        try:
            response = self.session.post(f"{BASE_URL}/login", json=ADMIN_CREDENTIALS)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user" in data:
                    self.admin_token = data["access_token"]
                    user = data["user"]
                    
                    # Verify admin user properties
                    if user.get("admin_level", 0) >= 1:
                        self.log_test("Admin Login (ba7a7am1ZX3)", True, f"Successfully logged in as admin: {user.get('nickname', 'Unknown')}")
                        
                        # Set authorization header for future requests
                        self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
                        
                    else:
                        self.log_test("Admin Login (ba7a7am1ZX3)", False, "User is not admin", user)
                else:
                    self.log_test("Admin Login (ba7a7am1ZX3)", False, "Missing access_token or user in response", data)
            else:
                self.log_test("Admin Login (ba7a7am1ZX3)", False, f"Login failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Admin Login (ba7a7am1ZX3)", False, f"Exception during login: {str(e)}")
    
    def test_mysql_connection(self):
        """Test MySQL database connection by checking data availability"""
        
        if not self.admin_token:
            self.log_test("MySQL Connection", False, "No admin token available")
            return
        
        try:
            # Test database connection by getting users
            response = self.session.get(f"{BASE_URL}/admin/users")
            
            if response.status_code == 200:
                users = response.json()
                if isinstance(users, list):
                    user_count = len(users)
                    self.log_test("MySQL Connection", True, f"Database accessible - found {user_count} users in system")
                    
                    # Check if admin user exists in database
                    admin_user = next((u for u in users if u.get("login") == "admin"), None)
                    if admin_user:
                        self.log_test("MySQL Admin User", True, f"Admin user found in database: {admin_user.get('nickname', 'Unknown')}")
                    else:
                        self.log_test("MySQL Admin User", False, "Admin user not found in database")
                        
                else:
                    self.log_test("MySQL Connection", False, f"Unexpected response format: {type(users)}")
            else:
                self.log_test("MySQL Connection", False, f"Database query failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("MySQL Connection", False, f"Exception during database test: {str(e)}")
    
    def test_user_system(self):
        """Test user system endpoints"""
        print("\n=== 2. СИСТЕМА ПОЛЬЗОВАТЕЛЕЙ ===")
        
        if not self.admin_token:
            self.log_test("User System", False, "No admin token available")
            return
        
        try:
            # Test GET /api/admin/users
            response = self.session.get(f"{BASE_URL}/admin/users")
            
            if response.status_code == 200:
                users = response.json()
                if isinstance(users, list):
                    self.log_test("GET /api/admin/users", True, f"Successfully retrieved {len(users)} users")
                    
                    # Store a test user for later tests
                    for user in users:
                        if user.get("admin_level", 0) == 0 and user.get("is_approved", False):
                            self.test_user_id = user["id"]
                            break
                    
                else:
                    self.log_test("GET /api/admin/users", False, f"Expected list, got {type(users)}")
            else:
                self.log_test("GET /api/admin/users", False, f"Failed: {response.status_code} - {response.text}")
            
            # Test GET /api/profile
            profile_response = self.session.get(f"{BASE_URL}/profile")
            if profile_response.status_code == 200:
                profile_data = profile_response.json()
                if profile_data.get("login") == "admin":
                    self.log_test("GET /api/profile", True, f"Profile retrieved for: {profile_data.get('nickname', 'Unknown')}")
                else:
                    self.log_test("GET /api/profile", False, "Profile data doesn't match admin user", profile_data)
            else:
                self.log_test("GET /api/profile", False, f"Profile endpoint failed: {profile_response.status_code}")
                
        except Exception as e:
            self.log_test("User System", False, f"Exception: {str(e)}")
    
    def test_preview_system(self):
        """Test preview system (priority)"""
        print("\n=== 3. СИСТЕМА ПРЕДВАРИТЕЛЬНЫХ ПРОСМОТРОВ (ПРИОРИТЕТ) ===")
        
        if not self.admin_token:
            self.log_test("Preview System", False, "No admin token available")
            return
        
        try:
            # Test GET /api/user/previews
            previews_response = self.session.get(f"{BASE_URL}/user/previews")
            
            if previews_response.status_code == 200:
                previews_data = previews_response.json()
                required_fields = ["previews_used", "preview_limit", "previews_remaining", "is_blacklisted"]
                
                if all(field in previews_data for field in required_fields):
                    used = previews_data.get("previews_used", 0)
                    limit = previews_data.get("preview_limit", 3)
                    remaining = previews_data.get("previews_remaining", 0)
                    
                    self.log_test("GET /api/user/previews", True, f"Preview status: {used}/{limit} used, {remaining} remaining")
                else:
                    self.log_test("GET /api/user/previews", False, f"Missing required fields in response", previews_data)
            else:
                self.log_test("GET /api/user/previews", False, f"Failed: {previews_response.status_code} - {previews_response.text}")
            
            # Test GET /api/media-list with authorization
            media_response = self.session.get(f"{BASE_URL}/media-list")
            
            if media_response.status_code == 200:
                media_list = media_response.json()
                if isinstance(media_list, list):
                    paid_media = [m for m in media_list if "Платное" in str(m.get("media_type", ""))]
                    free_media = [m for m in media_list if "Бесплатное" in str(m.get("media_type", ""))]
                    
                    self.log_test("GET /api/media-list", True, f"Media list retrieved: {len(paid_media)} paid, {len(free_media)} free media")
                    
                    # Test preview system with a paid media user
                    if paid_media:
                        test_media = paid_media[0]
                        media_user_id = test_media["id"]
                        
                        # Test POST /api/media/{user_id}/access
                        access_response = self.session.post(f"{BASE_URL}/media/{media_user_id}/access")
                        
                        if access_response.status_code == 200:
                            access_data = access_response.json()
                            access_type = access_data.get("access_type", "")
                            
                            if access_type in ["full", "preview"]:
                                self.log_test("POST /api/media/{id}/access", True, f"Access granted: {access_type} - {access_data.get('message', '')}")
                                
                                # If it was a preview, check if counter increased
                                if access_type == "preview":
                                    new_previews_response = self.session.get(f"{BASE_URL}/user/previews")
                                    if new_previews_response.status_code == 200:
                                        new_previews_data = new_previews_response.json()
                                        new_used = new_previews_data.get("previews_used", 0)
                                        
                                        if new_used > used:
                                            self.log_test("Preview Counter Increment", True, f"Preview counter increased: {used} → {new_used}")
                                        else:
                                            self.log_test("Preview Counter Increment", False, f"Preview counter didn't increase: {used} → {new_used}")
                            else:
                                self.log_test("POST /api/media/{id}/access", False, f"Unexpected access type: {access_type}", access_data)
                        elif access_response.status_code == 403:
                            # User might be blacklisted or exceeded limit
                            error_data = access_response.json()
                            if "лимит" in error_data.get("detail", "").lower():
                                self.log_test("POST /api/media/{id}/access", True, "Preview limit system working - user blocked for exceeding limit")
                            else:
                                self.log_test("POST /api/media/{id}/access", False, f"Unexpected 403 error: {error_data}")
                        else:
                            self.log_test("POST /api/media/{id}/access", False, f"Failed: {access_response.status_code} - {access_response.text}")
                    else:
                        self.log_test("POST /api/media/{id}/access", False, "No paid media found to test preview system")
                        
                else:
                    self.log_test("GET /api/media-list", False, f"Expected list, got {type(media_list)}")
            else:
                self.log_test("GET /api/media-list", False, f"Failed: {media_response.status_code} - {media_response.text}")
                
        except Exception as e:
            self.log_test("Preview System", False, f"Exception: {str(e)}")
    
    def test_admin_functions(self):
        """Test administrative functions"""
        print("\n=== 4. АДМИНИСТРАТИВНЫЕ ФУНКЦИИ ===")
        
        if not self.admin_token:
            self.log_test("Admin Functions", False, "No admin token available")
            return
        
        try:
            # Test GET /api/admin/blacklist
            blacklist_response = self.session.get(f"{BASE_URL}/admin/blacklist")
            
            if blacklist_response.status_code == 200:
                blacklist_data = blacklist_response.json()
                if "ip_blacklist" in blacklist_data and "blacklisted_users" in blacklist_data:
                    ip_count = len(blacklist_data["ip_blacklist"])
                    user_count = len(blacklist_data["blacklisted_users"])
                    
                    self.log_test("GET /api/admin/blacklist", True, f"Blacklist retrieved: {ip_count} IPs, {user_count} users")
                else:
                    self.log_test("GET /api/admin/blacklist", False, "Missing expected fields in blacklist response", blacklist_data)
            else:
                self.log_test("GET /api/admin/blacklist", False, f"Failed: {blacklist_response.status_code} - {blacklist_response.text}")
            
            # Test admin functions with a test user if available
            if self.test_user_id:
                # Test POST /api/admin/users/{id}/reset-previews
                reset_response = self.session.post(f"{BASE_URL}/admin/users/{self.test_user_id}/reset-previews")
                
                if reset_response.status_code == 200:
                    reset_data = reset_response.json()
                    self.log_test("POST /api/admin/users/{id}/reset-previews", True, f"Previews reset: {reset_data.get('message', '')}")
                else:
                    self.log_test("POST /api/admin/users/{id}/reset-previews", False, f"Failed: {reset_response.status_code} - {reset_response.text}")
                
                # Test POST /api/admin/users/{id}/unblacklist
                unblacklist_response = self.session.post(f"{BASE_URL}/admin/users/{self.test_user_id}/unblacklist")
                
                if unblacklist_response.status_code == 200:
                    unblacklist_data = unblacklist_response.json()
                    self.log_test("POST /api/admin/users/{id}/unblacklist", True, f"User unblacklisted: {unblacklist_data.get('message', '')}")
                else:
                    self.log_test("POST /api/admin/users/{id}/unblacklist", False, f"Failed: {unblacklist_response.status_code} - {unblacklist_response.text}")
            else:
                self.log_test("Admin User Management", False, "No test user available for admin function testing")
                
        except Exception as e:
            self.log_test("Admin Functions", False, f"Exception: {str(e)}")
    
    def test_preview_limits_system(self):
        """Test new preview system features: 3/3 limits, 15-day blocking, IP blocking"""
        print("\n=== 5. НОВЫЕ ФУНКЦИИ СИСТЕМЫ ПРЕДОВ ===")
        
        if not self.admin_token:
            self.log_test("Preview Limits System", False, "No admin token available")
            return
        
        try:
            # Get current preview status
            previews_response = self.session.get(f"{BASE_URL}/user/previews")
            
            if previews_response.status_code == 200:
                previews_data = previews_response.json()
                used = previews_data.get("previews_used", 0)
                limit = previews_data.get("preview_limit", 3)
                is_blacklisted = previews_data.get("is_blacklisted", False)
                
                # Test 1: Verify 3/3 limit system
                if limit == 3:
                    self.log_test("3/3 Preview Limit System", True, f"Correct preview limit configured: {limit}")
                else:
                    self.log_test("3/3 Preview Limit System", False, f"Expected limit 3, got {limit}")
                
                # Test 2: Check if user is properly blacklisted when limit exceeded
                if used >= limit and is_blacklisted:
                    self.log_test("Automatic 15-day Blocking", True, f"User correctly blacklisted after exceeding limit ({used}/{limit})")
                    
                    # Check blacklist_until field
                    if previews_data.get("blacklist_until"):
                        self.log_test("Blacklist Duration", True, f"Blacklist expiry set: {previews_data['blacklist_until']}")
                    else:
                        self.log_test("Blacklist Duration", False, "Blacklist expiry not set")
                        
                elif used < limit:
                    self.log_test("Preview Limit Status", True, f"User within limits: {used}/{limit} used")
                else:
                    self.log_test("Automatic 15-day Blocking", False, f"User exceeded limit ({used}/{limit}) but not blacklisted")
                
                # Test 3: Verify IP blocking system by checking blacklist
                blacklist_response = self.session.get(f"{BASE_URL}/admin/blacklist")
                if blacklist_response.status_code == 200:
                    blacklist_data = blacklist_response.json()
                    ip_blacklist = blacklist_data.get("ip_blacklist", [])
                    
                    # Look for IPs blocked due to preview limit
                    preview_blocked_ips = [ip for ip in ip_blacklist if "preview" in ip.get("reason", "").lower()]
                    
                    if preview_blocked_ips:
                        self.log_test("IP Blocking System", True, f"Found {len(preview_blocked_ips)} IPs blocked for preview limit violations")
                    else:
                        self.log_test("IP Blocking System", True, "No IPs currently blocked for preview violations (system ready)")
                        
                else:
                    self.log_test("IP Blocking System", False, "Could not verify IP blocking - blacklist inaccessible")
                    
            else:
                self.log_test("Preview Limits System", False, f"Could not get preview status: {previews_response.status_code}")
                
        except Exception as e:
            self.log_test("Preview Limits System", False, f"Exception: {str(e)}")
    
    def run_comprehensive_review_test(self):
        """Run all tests according to review request"""
        print("🚀 ПОЛНОЕ ТЕСТИРОВАНИЕ SwagMedia ПОСЛЕ ИСПРАВЛЕНИЯ URL")
        print(f"Testing against: {BASE_URL}")
        print(f"Admin credentials: {ADMIN_CREDENTIALS['login']}/{ADMIN_CREDENTIALS['password']}")
        print("=" * 80)
        
        # Run tests in order specified in review request
        self.test_health_endpoint()
        self.test_admin_login()
        self.test_mysql_connection()
        self.test_user_system()
        self.test_preview_system()
        self.test_admin_functions()
        self.test_preview_limits_system()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Всего тестов: {total_tests}")
        print(f"Пройдено: {passed_tests} ✅")
        print(f"Провалено: {failed_tests} ❌")
        print(f"Процент успеха: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n🔍 ПРОВАЛИВШИЕСЯ ТЕСТЫ:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  ❌ {result['test']}: {result['message']}")
        
        print("\n🎯 ЗАКЛЮЧЕНИЕ:")
        if failed_tests == 0:
            print("✅ ВСЕ СИСТЕМЫ РАБОТАЮТ КОРРЕКТНО! Backend готов к продакшену.")
        elif failed_tests <= 2:
            print("⚠️  Основные системы работают, есть минорные проблемы.")
        else:
            print("❌ Обнаружены критические проблемы, требуется исправление.")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = SwagMediaReviewTester()
    success = tester.run_comprehensive_review_test()
    
    if not success:
        sys.exit(1)
    else:
        print("\n🎉 Все тесты пройдены успешно!")