#!/usr/bin/env python3
"""
SwagMedia Backend API Testing Suite
Tests all backend endpoints for functionality and data integrity
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://swagmedia.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"login": "admin", "password": "admin123"}

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        
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
    
    def test_authentication(self):
        """Test authentication system"""
        print("\n=== Testing Authentication System ===")
        
        # Test admin login
        try:
            response = self.session.post(f"{BASE_URL}/login", json=ADMIN_CREDENTIALS)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user" in data:
                    self.admin_token = data["access_token"]
                    user = data["user"]
                    
                    # Verify admin user properties
                    if user.get("login") == "admin" and user.get("admin_level", 0) >= 1:
                        self.log_test("Admin Login", True, f"Successfully logged in as admin with token")
                        
                        # Set authorization header for future requests
                        self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
                        
                        # Test profile endpoint with token
                        profile_response = self.session.get(f"{BASE_URL}/profile")
                        if profile_response.status_code == 200:
                            profile_data = profile_response.json()
                            if profile_data.get("login") == "admin":
                                self.log_test("JWT Token Validation", True, "Token works correctly for protected routes")
                            else:
                                self.log_test("JWT Token Validation", False, "Token validation failed", profile_data)
                        else:
                            self.log_test("JWT Token Validation", False, f"Profile endpoint failed: {profile_response.status_code}")
                    else:
                        self.log_test("Admin Login", False, "User is not admin or missing admin_level", user)
                else:
                    self.log_test("Admin Login", False, "Missing access_token or user in response", data)
            else:
                self.log_test("Admin Login", False, f"Login failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Admin Login", False, f"Exception during login: {str(e)}")
    
    def test_shop_api(self):
        """Test shop API endpoints"""
        print("\n=== Testing Shop API ===")
        
        try:
            # First initialize shop if needed
            init_response = self.session.post(f"{BASE_URL}/admin/init-shop")
            print(f"Shop initialization: {init_response.status_code} - {init_response.text}")
            
            # Test shop items endpoint
            response = self.session.get(f"{BASE_URL}/shop/items")
            
            if response.status_code == 200:
                items = response.json()
                
                if isinstance(items, list):
                    item_count = len(items)
                    
                    # Check if we have 9 items as expected
                    if item_count == 9:
                        self.log_test("Shop Items Count", True, f"Returns {item_count} items as expected")
                        
                        # Check categories
                        categories = set()
                        valid_items = 0
                        
                        for item in items:
                            if all(key in item for key in ["id", "name", "description", "price", "category"]):
                                valid_items += 1
                                categories.add(item["category"])
                        
                        expected_categories = {"Премиум", "Буст", "Дизайн"}
                        if categories == expected_categories:
                            self.log_test("Shop Categories", True, f"All 3 expected categories present: {categories}")
                        else:
                            self.log_test("Shop Categories", False, f"Categories mismatch. Expected: {expected_categories}, Got: {categories}")
                        
                        if valid_items == item_count:
                            self.log_test("Shop Item Structure", True, "All items have required fields (id, name, description, price, category)")
                        else:
                            self.log_test("Shop Item Structure", False, f"Only {valid_items}/{item_count} items have valid structure")
                        
                        # Log sample item for debugging
                        if items:
                            sample_item = items[0]
                            self.log_test("Shop API Response Format", True, "Sample item structure looks correct", sample_item)
                            
                    else:
                        self.log_test("Shop Items Count", False, f"Expected 9 items, got {item_count}", {"item_count": item_count, "items": items[:3]})
                else:
                    self.log_test("Shop Items Response", False, "Response is not a list", {"response_type": type(items), "response": items})
            else:
                self.log_test("Shop Items API", False, f"API call failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Shop API", False, f"Exception during shop API test: {str(e)}")
    
    def test_statistics_api(self):
        """Test statistics API"""
        print("\n=== Testing Statistics API ===")
        
        try:
            response = self.session.get(f"{BASE_URL}/stats")
            
            if response.status_code == 200:
                stats = response.json()
                
                required_fields = ["total_media", "total_mc_spent", "total_mc_current"]
                if all(field in stats for field in required_fields):
                    self.log_test("Statistics API Structure", True, "All required fields present", stats)
                    
                    # Check if values are reasonable
                    total_media = stats.get("total_media", 0)
                    total_mc_current = stats.get("total_mc_current", 0)
                    
                    if total_media >= 3:  # Expected at least 3 media
                        self.log_test("Statistics Media Count", True, f"Total media: {total_media} (≥3 as expected)")
                    else:
                        self.log_test("Statistics Media Count", False, f"Total media: {total_media} (expected ≥3)")
                    
                    if total_mc_current >= 1000000:  # Expected 1M+ MC
                        self.log_test("Statistics MC Balance", True, f"Total MC: {total_mc_current:,} (≥1M as expected)")
                    else:
                        self.log_test("Statistics MC Balance", False, f"Total MC: {total_mc_current:,} (expected ≥1M)")
                        
                else:
                    missing_fields = [field for field in required_fields if field not in stats]
                    self.log_test("Statistics API Structure", False, f"Missing fields: {missing_fields}", stats)
            else:
                self.log_test("Statistics API", False, f"API call failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Statistics API", False, f"Exception during stats API test: {str(e)}")
    
    def test_admin_endpoints(self):
        """Test admin panel endpoints"""
        print("\n=== Testing Admin Endpoints ===")
        
        if not self.admin_token:
            self.log_test("Admin Endpoints", False, "No admin token available - skipping admin tests")
            return
        
        admin_endpoints = [
            ("/admin/applications", "GET", "Applications List"),
            ("/admin/purchases", "GET", "Purchases List"),
            ("/admin/reports", "GET", "Reports List"),
            ("/admin/users", "GET", "Users List")
        ]
        
        for endpoint, method, test_name in admin_endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{BASE_URL}{endpoint}")
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        self.log_test(f"Admin {test_name}", True, f"Endpoint accessible, returned {len(data)} items")
                    else:
                        self.log_test(f"Admin {test_name}", False, f"Expected list, got {type(data)}", data)
                elif response.status_code == 403:
                    self.log_test(f"Admin {test_name}", False, "Access denied - admin privileges not working")
                else:
                    self.log_test(f"Admin {test_name}", False, f"Unexpected status {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Admin {test_name}", False, f"Exception: {str(e)}")
    
    def test_user_endpoints(self):
        """Test general user endpoints"""
        print("\n=== Testing User Endpoints ===")
        
        try:
            # Test media list endpoint (public)
            response = self.session.get(f"{BASE_URL}/media-list")
            
            if response.status_code == 200:
                media_list = response.json()
                if isinstance(media_list, list):
                    self.log_test("Media List API", True, f"Returns {len(media_list)} media entries")
                    
                    # Check structure of media entries
                    if media_list:
                        sample_media = media_list[0]
                        required_fields = ["nickname", "channel_link", "vk_link", "media_type"]
                        if all(field in sample_media for field in required_fields):
                            self.log_test("Media List Structure", True, "Media entries have correct structure")
                        else:
                            missing = [f for f in required_fields if f not in sample_media]
                            self.log_test("Media List Structure", False, f"Missing fields: {missing}", sample_media)
                else:
                    self.log_test("Media List API", False, f"Expected list, got {type(media_list)}", media_list)
            else:
                self.log_test("Media List API", False, f"API call failed with status {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("User Endpoints", False, f"Exception during user endpoints test: {str(e)}")
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting SwagMedia Backend API Tests")
        print(f"Testing against: {BASE_URL}")
        print("=" * 60)
        
        # Run tests in order
        self.test_authentication()
        self.test_shop_api()
        self.test_statistics_api()
        self.test_admin_endpoints()
        self.test_user_endpoints()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
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
    tester = BackendTester()
    success = tester.run_all_tests()
    
    if not success:
        sys.exit(1)
    else:
        print("\n🎉 All tests passed!")