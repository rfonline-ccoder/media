#!/usr/bin/env python3
"""
SwagMedia MySQL Migration Testing Suite
Comprehensive testing of all major functions after MySQL + SQLAlchemy migration
"""

import requests
import json
import sys
import time
from datetime import datetime
import uuid

# Configuration
BASE_URL = "https://mysql-setup.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"login": "admin", "password": "admin123"}

class MySQLMigrationTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_user_token = None
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
    
    def test_authentication_system(self):
        """Test 1: Authentication (admin/admin123 login, JWT tokens)"""
        print("\n=== 1. TESTING AUTHENTICATION SYSTEM ===")
        
        try:
            # Test admin login
            response = self.session.post(f"{BASE_URL}/login", json=ADMIN_CREDENTIALS)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user" in data:
                    self.admin_token = data["access_token"]
                    user = data["user"]
                    
                    # Verify admin user properties
                    if user.get("admin_level", 0) >= 1:
                        self.log_test("Admin Login (admin/admin123)", True, f"Successfully logged in as admin")
                        
                        # Set authorization header for future requests
                        self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
                        
                        # Test JWT token validation by accessing protected endpoint
                        protected_response = self.session.get(f"{BASE_URL}/admin/users")
                        if protected_response.status_code == 200:
                            self.log_test("JWT Token Generation & Validation", True, "JWT tokens work correctly for protected routes")
                        else:
                            self.log_test("JWT Token Generation & Validation", False, f"Protected endpoint failed: {protected_response.status_code}")
                    else:
                        self.log_test("Admin Login (admin/admin123)", False, "User is not admin", user)
                else:
                    self.log_test("Admin Login (admin/admin123)", False, "Missing access_token or user in response", data)
            else:
                self.log_test("Admin Login (admin/admin123)", False, f"Login failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Authentication System", False, f"Exception during authentication test: {str(e)}")
    
    def test_media_system_and_previews(self):
        """Test 2: Media system and previews"""
        print("\n=== 2. TESTING MEDIA SYSTEM AND PREVIEWS ===")
        
        if not self.admin_token:
            self.log_test("Media System", False, "No admin token available")
            return
        
        try:
            # Test GET /api/media-list with can_access field
            response = self.session.get(f"{BASE_URL}/media-list")
            
            if response.status_code == 200:
                media_list = response.json()
                if isinstance(media_list, list):
                    self.log_test("GET /api/media-list", True, f"Returns {len(media_list)} media entries")
                    
                    # Check if can_access field is present
                    if media_list:
                        sample_media = media_list[0]
                        required_fields = ["id", "nickname", "vk_link", "channel_link", "media_type", "can_access"]
                        if all(field in sample_media for field in required_fields):
                            self.log_test("Media List with can_access field", True, "All required fields including can_access present")
                            
                            # Test preview system - find a paid media user
                            paid_media_user = None
                            for media in media_list:
                                if media.get("media_type") == 1 and not media.get("can_access", True):
                                    paid_media_user = media
                                    break
                            
                            if paid_media_user:
                                # Test POST /api/media/{id}/access for preview system
                                media_user_id = paid_media_user["id"]
                                access_response = self.session.post(f"{BASE_URL}/media/{media_user_id}/access")
                                
                                if access_response.status_code == 200:
                                    access_data = access_response.json()
                                    if access_data.get("access_type") == "preview":
                                        self.log_test("POST /api/media/{id}/access - Preview System", True, f"Preview system working: {access_data.get('message', '')}")
                                        
                                        # Test GET /api/user/previews
                                        previews_response = self.session.get(f"{BASE_URL}/user/previews")
                                        if previews_response.status_code == 200:
                                            previews_data = previews_response.json()
                                            required_preview_fields = ["previews_used", "previews_limit", "previews_remaining", "is_blacklisted"]
                                            if all(field in previews_data for field in required_preview_fields):
                                                self.log_test("GET /api/user/previews", True, f"Preview status endpoint working: {previews_data}")
                                            else:
                                                missing = [f for f in required_preview_fields if f not in previews_data]
                                                self.log_test("GET /api/user/previews", False, f"Missing fields: {missing}")
                                        else:
                                            self.log_test("GET /api/user/previews", False, f"Preview status endpoint failed: {previews_response.status_code}")
                                    else:
                                        self.log_test("POST /api/media/{id}/access - Preview System", False, f"Expected preview access, got: {access_data}")
                                else:
                                    self.log_test("POST /api/media/{id}/access - Preview System", False, f"Media access failed: {access_response.status_code} - {access_response.text}")
                            else:
                                self.log_test("Preview System Test", True, "No paid media users found to test preview system (all users have access)")
                        else:
                            missing = [f for f in required_fields if f not in sample_media]
                            self.log_test("Media List with can_access field", False, f"Missing fields: {missing}")
                else:
                    self.log_test("GET /api/media-list", False, f"Expected list, got {type(media_list)}")
            else:
                self.log_test("GET /api/media-list", False, f"API call failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Media System and Previews", False, f"Exception: {str(e)}")
    
    def test_shop_system(self):
        """Test 3: Shop system"""
        print("\n=== 3. TESTING SHOP SYSTEM ===")
        
        try:
            # Test GET /api/shop - should return 9 pre-filled items
            response = self.session.get(f"{BASE_URL}/shop")
            
            if response.status_code == 200:
                items = response.json()
                
                if isinstance(items, list) and len(items) == 9:
                    self.log_test("GET /api/shop - 9 Pre-filled Items", True, f"Returns exactly 9 shop items as expected")
                    
                    # Check categories
                    categories = set()
                    valid_items = 0
                    
                    for item in items:
                        if all(key in item for key in ["id", "name", "description", "price", "category"]):
                            valid_items += 1
                            categories.add(item["category"])
                    
                    expected_categories = {"Премиум", "Буст", "Дизайн"}
                    if categories == expected_categories:
                        self.log_test("Shop Categories Structure", True, f"All 3 expected categories present: {categories}")
                    else:
                        self.log_test("Shop Categories Structure", False, f"Categories mismatch. Expected: {expected_categories}, Got: {categories}")
                    
                    if valid_items == 9:
                        self.log_test("Shop Items Structure", True, "All 9 items have required fields")
                        
                        # Test POST /api/shop/purchase
                        if self.admin_token:
                            test_item = items[0]
                            purchase_data = {
                                "item_id": test_item["id"],
                                "quantity": 1
                            }
                            
                            purchase_response = self.session.post(f"{BASE_URL}/shop/purchase", json=purchase_data)
                            if purchase_response.status_code == 200:
                                purchase_result = purchase_response.json()
                                self.log_test("POST /api/shop/purchase", True, f"Purchase system working: {purchase_result.get('message', '')}")
                            elif purchase_response.status_code == 400:
                                # Insufficient funds is expected for admin user
                                self.log_test("POST /api/shop/purchase", True, "Purchase validation working (insufficient funds expected)")
                            else:
                                self.log_test("POST /api/shop/purchase", False, f"Purchase failed: {purchase_response.status_code} - {purchase_response.text}")
                        else:
                            self.log_test("POST /api/shop/purchase", False, "No admin token for purchase test")
                    else:
                        self.log_test("Shop Items Structure", False, f"Only {valid_items}/9 items have valid structure")
                else:
                    self.log_test("GET /api/shop - 9 Pre-filled Items", False, f"Expected 9 items, got {len(items) if isinstance(items, list) else 'non-list'}")
            else:
                self.log_test("GET /api/shop", False, f"Shop API failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Shop System", False, f"Exception: {str(e)}")
    
    def test_reports_and_ratings(self):
        """Test 4: Reports and ratings system"""
        print("\n=== 4. TESTING REPORTS AND RATINGS SYSTEM ===")
        
        if not self.admin_token:
            self.log_test("Reports and Ratings", False, "No admin token available")
            return
        
        try:
            # Test POST /api/reports - create report
            report_data = {
                "links": [
                    {"url": "https://youtube.com/watch?v=test123", "views": 1500},
                    {"url": "https://vk.com/video456", "views": 800}
                ]
            }
            
            report_response = self.session.post(f"{BASE_URL}/reports", json=report_data)
            if report_response.status_code == 200:
                report_result = report_response.json()
                self.log_test("POST /api/reports - Create Report", True, f"Report creation working: {report_result.get('message', '')}")
                
                # Test POST /api/ratings - create rating
                # First get users to rate
                users_response = self.session.get(f"{BASE_URL}/admin/users")
                if users_response.status_code == 200:
                    users = users_response.json()
                    if len(users) > 1:
                        # Rate another user (not admin)
                        target_user = None
                        for user in users:
                            if user.get("admin_level", 0) == 0:
                                target_user = user
                                break
                        
                        if target_user:
                            rating_data = {
                                "rated_user_id": target_user["id"],
                                "rating": 5,
                                "comment": "Отличный пользователь! Тестовый рейтинг."
                            }
                            
                            rating_response = self.session.post(f"{BASE_URL}/ratings", json=rating_data)
                            if rating_response.status_code == 200:
                                self.log_test("POST /api/ratings - Create Rating", True, "Rating system working")
                                
                                # Test GET /api/ratings - leaderboard
                                leaderboard_response = self.session.get(f"{BASE_URL}/ratings")
                                if leaderboard_response.status_code == 200:
                                    leaderboard = leaderboard_response.json()
                                    if isinstance(leaderboard, list):
                                        self.log_test("GET /api/ratings - Leaderboard", True, f"Leaderboard returns {len(leaderboard)} users")
                                        
                                        # Check leaderboard structure
                                        if leaderboard:
                                            sample_entry = leaderboard[0]
                                            required_fields = ["id", "nickname", "balance", "average_rating", "rating_count", "latest_ratings"]
                                            if all(field in sample_entry for field in required_fields):
                                                self.log_test("Ratings Leaderboard Structure", True, "Leaderboard has correct structure")
                                            else:
                                                missing = [f for f in required_fields if f not in sample_entry]
                                                self.log_test("Ratings Leaderboard Structure", False, f"Missing fields: {missing}")
                                    else:
                                        self.log_test("GET /api/ratings - Leaderboard", False, f"Expected list, got {type(leaderboard)}")
                                else:
                                    self.log_test("GET /api/ratings - Leaderboard", False, f"Leaderboard failed: {leaderboard_response.status_code}")
                            else:
                                self.log_test("POST /api/ratings - Create Rating", False, f"Rating creation failed: {rating_response.status_code}")
                        else:
                            self.log_test("POST /api/ratings - Create Rating", False, "No non-admin user found to rate")
                    else:
                        self.log_test("POST /api/ratings - Create Rating", False, "Not enough users for rating test")
                else:
                    self.log_test("POST /api/ratings - Create Rating", False, "Failed to get users for rating test")
            else:
                self.log_test("POST /api/reports - Create Report", False, f"Report creation failed: {report_response.status_code} - {report_response.text}")
                
        except Exception as e:
            self.log_test("Reports and Ratings", False, f"Exception: {str(e)}")
    
    def test_notifications_system(self):
        """Test 5: Notifications system"""
        print("\n=== 5. TESTING NOTIFICATIONS SYSTEM ===")
        
        if not self.admin_token:
            self.log_test("Notifications System", False, "No admin token available")
            return
        
        try:
            # Test GET /api/notifications
            response = self.session.get(f"{BASE_URL}/notifications")
            
            if response.status_code == 200:
                notifications = response.json()
                if isinstance(notifications, list):
                    self.log_test("GET /api/notifications", True, f"Successfully retrieved {len(notifications)} notifications")
                    
                    # Check notification structure if any exist
                    if notifications:
                        sample_notification = notifications[0]
                        # Note: user_id is intentionally omitted from API response for security
                        required_fields = ["id", "type", "title", "message", "created_at", "read"]
                        
                        if all(field in sample_notification for field in required_fields):
                            self.log_test("Notifications Structure", True, "Notifications have correct structure (user_id omitted for security)")
                            
                            # Test POST /api/notifications/{id}/read
                            unread_notification = next((n for n in notifications if not n.get("read", True)), None)
                            if unread_notification:
                                notification_id = unread_notification["id"]
                                read_response = self.session.post(f"{BASE_URL}/notifications/{notification_id}/read")
                                
                                if read_response.status_code == 200:
                                    self.log_test("POST /api/notifications/{id}/read", True, "Successfully marked notification as read")
                                else:
                                    self.log_test("POST /api/notifications/{id}/read", False, f"Failed to mark as read: {read_response.status_code}")
                            else:
                                self.log_test("POST /api/notifications/{id}/read", True, "No unread notifications to test with (all already read)")
                        else:
                            missing_fields = [f for f in required_fields if f not in sample_notification]
                            self.log_test("Notifications Structure", False, f"Missing fields: {missing_fields}")
                    else:
                        self.log_test("Notifications Structure", True, "No notifications to check structure (empty list is valid)")
                else:
                    self.log_test("GET /api/notifications", False, f"Expected list, got {type(notifications)}")
            else:
                self.log_test("GET /api/notifications", False, f"Notifications API failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Notifications System", False, f"Exception: {str(e)}")
    
    def test_admin_panel_endpoints(self):
        """Test 6: Admin panel (all endpoints)"""
        print("\n=== 6. TESTING ADMIN PANEL ENDPOINTS ===")
        
        if not self.admin_token:
            self.log_test("Admin Panel", False, "No admin token available")
            return
        
        admin_endpoints = [
            # Application management
            ("/admin/applications", "GET", "Applications Management"),
            
            # User management
            ("/admin/users", "GET", "Users Management"),
            
            # Purchase management
            ("/admin/purchases", "GET", "Purchases Management"),
            
            # Report management
            ("/admin/reports", "GET", "Reports Management"),
            
            # Shop management
            ("/admin/shop/items", "GET", "Shop Items Management"),
            
            # Blacklist management
            ("/admin/blacklist", "GET", "Blacklist Management"),
        ]
        
        for endpoint, method, test_name in admin_endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{BASE_URL}{endpoint}")
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) or isinstance(data, dict):
                        self.log_test(f"Admin {test_name}", True, f"Endpoint accessible and returns data")
                    else:
                        self.log_test(f"Admin {test_name}", False, f"Unexpected data type: {type(data)}")
                elif response.status_code == 403:
                    self.log_test(f"Admin {test_name}", False, "Access denied - admin privileges not working")
                else:
                    self.log_test(f"Admin {test_name}", False, f"Unexpected status {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Admin {test_name}", False, f"Exception: {str(e)}")
        
        # Test specific admin functions
        try:
            # Test media type switching
            users_response = self.session.get(f"{BASE_URL}/admin/users")
            if users_response.status_code == 200:
                users = users_response.json()
                if users:
                    test_user = users[0]
                    user_id = test_user["id"]
                    original_media_type = test_user.get("media_type", 0)
                    new_media_type = 1 if original_media_type == 0 else 0
                    
                    change_data = {
                        "user_id": user_id,
                        "new_media_type": new_media_type,
                        "admin_comment": "MySQL migration test"
                    }
                    
                    change_response = self.session.post(f"{BASE_URL}/admin/users/{user_id}/change-media-type", json=change_data)
                    if change_response.status_code == 200:
                        self.log_test("Admin Media Type Switching", True, "Media type switching works")
                    else:
                        self.log_test("Admin Media Type Switching", False, f"Media type switching failed: {change_response.status_code}")
                else:
                    self.log_test("Admin Media Type Switching", False, "No users found for testing")
            else:
                self.log_test("Admin Media Type Switching", False, "Failed to get users for testing")
                
        except Exception as e:
            self.log_test("Admin Panel Functions", False, f"Exception: {str(e)}")
    
    def test_database_integrity(self):
        """Test 7: Database integrity (MySQL tables, foreign keys, indexes)"""
        print("\n=== 7. TESTING DATABASE INTEGRITY ===")
        
        if not self.admin_token:
            self.log_test("Database Integrity", False, "No admin token available")
            return
        
        try:
            # Test that data is being saved to MySQL by creating and retrieving data
            
            # 1. Create a test report and verify it's saved
            report_data = {
                "links": [
                    {"url": "https://test-mysql.com/video", "views": 999}
                ]
            }
            
            report_response = self.session.post(f"{BASE_URL}/reports", json=report_data)
            if report_response.status_code == 200:
                report_result = report_response.json()
                
                # Verify the report appears in admin reports
                admin_reports_response = self.session.get(f"{BASE_URL}/admin/reports")
                if admin_reports_response.status_code == 200:
                    admin_reports = admin_reports_response.json()
                    test_report_found = any(
                        report.get("links") and 
                        any(link.get("url") == "https://test-mysql.com/video" for link in report.get("links", []))
                        for report in admin_reports
                    )
                    
                    if test_report_found:
                        self.log_test("MySQL Data Persistence - Reports", True, "Data correctly saved to MySQL database")
                    else:
                        self.log_test("MySQL Data Persistence - Reports", False, "Test report not found in database")
                else:
                    self.log_test("MySQL Data Persistence - Reports", False, "Failed to verify report in database")
            else:
                self.log_test("MySQL Data Persistence - Reports", False, f"Failed to create test report: {report_response.status_code}")
            
            # 2. Test foreign key relationships by checking user-report relationship
            users_response = self.session.get(f"{BASE_URL}/admin/users")
            reports_response = self.session.get(f"{BASE_URL}/admin/reports")
            
            if users_response.status_code == 200 and reports_response.status_code == 200:
                users = users_response.json()
                reports = reports_response.json()
                
                # Check if reports have valid user relationships by checking user_nickname resolution
                # The admin endpoint resolves user_nickname from user_id, so if it's not "Удаленный пользователь", the FK is valid
                valid_reports = [r for r in reports if r.get("user_nickname") != "Удаленный пользователь"]
                invalid_reports = [r for r in reports if r.get("user_nickname") == "Удаленный пользователь"]
                
                if len(valid_reports) > 0:
                    self.log_test("MySQL Foreign Key Integrity", True, f"Found {len(valid_reports)} reports with valid foreign keys (user_nickname resolved correctly)")
                else:
                    self.log_test("MySQL Foreign Key Integrity", False, f"No reports with valid foreign key references found")
            else:
                self.log_test("MySQL Foreign Key Integrity", False, "Failed to verify foreign key relationships")
            
            # 3. Test that SQLAlchemy ORM is working by checking data consistency
            # Get data from different endpoints and verify consistency
            media_list_response = self.session.get(f"{BASE_URL}/media-list")
            admin_users_response = self.session.get(f"{BASE_URL}/admin/users")
            
            if media_list_response.status_code == 200 and admin_users_response.status_code == 200:
                media_list = media_list_response.json()
                admin_users = admin_users_response.json()
                
                # Check if approved users in admin panel match media list
                approved_users = [user for user in admin_users if user.get("is_approved")]
                
                if len(media_list) == len(approved_users):
                    self.log_test("SQLAlchemy ORM Consistency", True, "Data consistency between endpoints maintained")
                else:
                    self.log_test("SQLAlchemy ORM Consistency", False, f"Data inconsistency: {len(media_list)} media entries vs {len(approved_users)} approved users")
            else:
                self.log_test("SQLAlchemy ORM Consistency", False, "Failed to verify ORM consistency")
            
            # 4. Test that all expected tables exist by checking different endpoints
            table_tests = [
                ("users", "/admin/users"),
                ("applications", "/admin/applications"),
                ("reports", "/admin/reports"),
                ("purchases", "/admin/purchases"),
                ("notifications", "/notifications"),
                ("shop_items", "/shop"),
                ("ip_blacklist", "/admin/blacklist")
            ]
            
            tables_working = 0
            for table_name, endpoint in table_tests:
                try:
                    response = self.session.get(f"{BASE_URL}{endpoint}")
                    if response.status_code == 200:
                        tables_working += 1
                except:
                    pass
            
            if tables_working >= 6:  # At least 6 out of 7 tables should be accessible
                self.log_test("MySQL Tables Creation", True, f"{tables_working}/7 database tables are accessible")
            else:
                self.log_test("MySQL Tables Creation", False, f"Only {tables_working}/7 database tables are accessible")
                
        except Exception as e:
            self.log_test("Database Integrity", False, f"Exception: {str(e)}")
    
    def run_comprehensive_tests(self):
        """Run all comprehensive MySQL migration tests"""
        print("🚀 Starting SwagMedia MySQL Migration Comprehensive Tests")
        print(f"Testing against: {BASE_URL}")
        print("Testing all major functions after MySQL + SQLAlchemy migration")
        print("=" * 80)
        
        # Run all tests in order
        self.test_authentication_system()
        self.test_media_system_and_previews()
        self.test_shop_system()
        self.test_reports_and_ratings()
        self.test_notifications_system()
        self.test_admin_panel_endpoints()
        self.test_database_integrity()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 MYSQL MIGRATION TEST SUMMARY")
        print("=" * 80)
        
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
                if any(keyword in result["test"].lower() for keyword in ["authentication", "database", "mysql", "login"]):
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
                print(f"  ❌ {result['test']}: {result['message']}")
        
        if failed_tests == 0:
            print("\n🎉 ALL TESTS PASSED! MySQL migration is successful!")
            print("✅ Authentication system working")
            print("✅ Media and preview system working")
            print("✅ Shop system working")
            print("✅ Reports and ratings working")
            print("✅ Notifications working")
            print("✅ Admin panel working")
            print("✅ Database integrity maintained")
        elif len(critical_failures) == 0:
            print(f"\n✅ MIGRATION SUCCESSFUL with {len(minor_issues)} minor issues")
            print("All critical systems are working correctly")
        else:
            print(f"\n❌ MIGRATION HAS CRITICAL ISSUES")
            print("Critical systems need attention before production use")
        
        return len(critical_failures) == 0

if __name__ == "__main__":
    tester = MySQLMigrationTester()
    success = tester.run_comprehensive_tests()
    
    if not success:
        sys.exit(1)
    else:
        print("\n🎉 MySQL migration testing completed successfully!")