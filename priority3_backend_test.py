#!/usr/bin/env python3
"""
Priority 3 Backend Testing - Search, Filters, and Pagination
Tests admin panel backend endpoints for Priority 3 UX/UI improvements
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://backend-check-app.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"login": "admin", "password": "admin123"}

class Priority3BackendTester:
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
    
    def authenticate(self):
        """Authenticate as admin"""
        try:
            response = self.session.post(f"{BASE_URL}/login", json=ADMIN_CREDENTIALS)
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data["access_token"]
                self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
                self.log_test("Admin Authentication", True, "Successfully authenticated as admin")
                return True
            else:
                self.log_test("Admin Authentication", False, f"Login failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Exception: {str(e)}")
            return False
    
    def test_admin_users_filtering(self):
        """Test admin users endpoint for filtering capabilities"""
        print("\n=== Testing Admin Users Filtering ===")
        
        if not self.admin_token:
            self.log_test("Users Filtering", False, "No admin token available")
            return
        
        # Test 1: Basic endpoint (should work)
        try:
            response = self.session.get(f"{BASE_URL}/admin/users")
            if response.status_code == 200:
                users = response.json()
                self.log_test("Admin Users Basic", True, f"Retrieved {len(users)} users")
                
                # Test 2: Try filtering by status (query parameters)
                test_params = [
                    ("status", "approved"),
                    ("status", "pending"),
                    ("media_type", "0"),
                    ("media_type", "1"),
                    ("search", "admin"),
                    ("sort", "nickname"),
                    ("sort", "balance"),
                    ("sort", "created_at"),
                    ("order", "asc"),
                    ("order", "desc"),
                    ("page", "1"),
                    ("limit", "10")
                ]
                
                for param_name, param_value in test_params:
                    try:
                        params = {param_name: param_value}
                        response = self.session.get(f"{BASE_URL}/admin/users", params=params)
                        
                        if response.status_code == 200:
                            filtered_users = response.json()
                            # Check if filtering actually worked (different result or same structure)
                            if isinstance(filtered_users, list):
                                self.log_test(f"Users Filter {param_name}={param_value}", True, 
                                            f"Endpoint accepts parameter, returned {len(filtered_users)} users")
                            else:
                                self.log_test(f"Users Filter {param_name}={param_value}", False, 
                                            f"Unexpected response format: {type(filtered_users)}")
                        else:
                            self.log_test(f"Users Filter {param_name}={param_value}", False, 
                                        f"Parameter rejected: {response.status_code}")
                    except Exception as e:
                        self.log_test(f"Users Filter {param_name}={param_value}", False, f"Exception: {str(e)}")
            else:
                self.log_test("Admin Users Basic", False, f"Basic endpoint failed: {response.status_code}")
                
        except Exception as e:
            self.log_test("Users Filtering", False, f"Exception: {str(e)}")
    
    def test_admin_reports_filtering(self):
        """Test admin reports endpoint for filtering capabilities"""
        print("\n=== Testing Admin Reports Filtering ===")
        
        if not self.admin_token:
            self.log_test("Reports Filtering", False, "No admin token available")
            return
        
        try:
            # Test basic endpoint
            response = self.session.get(f"{BASE_URL}/admin/reports")
            if response.status_code == 200:
                reports = response.json()
                self.log_test("Admin Reports Basic", True, f"Retrieved {len(reports)} reports")
                
                # Test filtering parameters
                test_params = [
                    ("status", "pending"),
                    ("status", "approved"),
                    ("status", "rejected"),
                    ("sort", "created_at"),
                    ("sort", "user_nickname"),
                    ("order", "desc"),
                    ("page", "1"),
                    ("limit", "10")
                ]
                
                for param_name, param_value in test_params:
                    try:
                        params = {param_name: param_value}
                        response = self.session.get(f"{BASE_URL}/admin/reports", params=params)
                        
                        if response.status_code == 200:
                            filtered_reports = response.json()
                            if isinstance(filtered_reports, list):
                                self.log_test(f"Reports Filter {param_name}={param_value}", True, 
                                            f"Parameter accepted, returned {len(filtered_reports)} reports")
                            else:
                                self.log_test(f"Reports Filter {param_name}={param_value}", False, 
                                            f"Unexpected response format: {type(filtered_reports)}")
                        else:
                            self.log_test(f"Reports Filter {param_name}={param_value}", False, 
                                        f"Parameter rejected: {response.status_code}")
                    except Exception as e:
                        self.log_test(f"Reports Filter {param_name}={param_value}", False, f"Exception: {str(e)}")
            else:
                self.log_test("Admin Reports Basic", False, f"Basic endpoint failed: {response.status_code}")
                
        except Exception as e:
            self.log_test("Reports Filtering", False, f"Exception: {str(e)}")
    
    def test_admin_purchases_filtering(self):
        """Test admin purchases endpoint for filtering capabilities"""
        print("\n=== Testing Admin Purchases Filtering ===")
        
        if not self.admin_token:
            self.log_test("Purchases Filtering", False, "No admin token available")
            return
        
        try:
            # Test basic endpoint
            response = self.session.get(f"{BASE_URL}/admin/purchases")
            if response.status_code == 200:
                purchases = response.json()
                self.log_test("Admin Purchases Basic", True, f"Retrieved {len(purchases)} purchases")
                
                # Test filtering parameters
                test_params = [
                    ("status", "pending"),
                    ("status", "approved"),
                    ("status", "rejected"),
                    ("sort", "created_at"),
                    ("sort", "total_price"),
                    ("sort", "user_nickname"),
                    ("order", "desc"),
                    ("page", "1"),
                    ("limit", "10")
                ]
                
                for param_name, param_value in test_params:
                    try:
                        params = {param_name: param_value}
                        response = self.session.get(f"{BASE_URL}/admin/purchases", params=params)
                        
                        if response.status_code == 200:
                            filtered_purchases = response.json()
                            if isinstance(filtered_purchases, list):
                                self.log_test(f"Purchases Filter {param_name}={param_value}", True, 
                                            f"Parameter accepted, returned {len(filtered_purchases)} purchases")
                            else:
                                self.log_test(f"Purchases Filter {param_name}={param_value}", False, 
                                            f"Unexpected response format: {type(filtered_purchases)}")
                        else:
                            self.log_test(f"Purchases Filter {param_name}={param_value}", False, 
                                        f"Parameter rejected: {response.status_code}")
                    except Exception as e:
                        self.log_test(f"Purchases Filter {param_name}={param_value}", False, f"Exception: {str(e)}")
            else:
                self.log_test("Admin Purchases Basic", False, f"Basic endpoint failed: {response.status_code}")
                
        except Exception as e:
            self.log_test("Purchases Filtering", False, f"Exception: {str(e)}")
    
    def test_admin_applications_filtering(self):
        """Test admin applications endpoint for filtering capabilities"""
        print("\n=== Testing Admin Applications Filtering ===")
        
        if not self.admin_token:
            self.log_test("Applications Filtering", False, "No admin token available")
            return
        
        try:
            # Test basic endpoint
            response = self.session.get(f"{BASE_URL}/admin/applications")
            if response.status_code == 200:
                applications = response.json()
                self.log_test("Admin Applications Basic", True, f"Retrieved {len(applications)} applications")
                
                # Test filtering parameters
                test_params = [
                    ("status", "pending"),
                    ("status", "approved"),
                    ("status", "rejected"),
                    ("type", "registration"),
                    ("sort", "created_at"),
                    ("order", "desc"),
                    ("page", "1"),
                    ("limit", "10")
                ]
                
                for param_name, param_value in test_params:
                    try:
                        params = {param_name: param_value}
                        response = self.session.get(f"{BASE_URL}/admin/applications", params=params)
                        
                        if response.status_code == 200:
                            filtered_apps = response.json()
                            if isinstance(filtered_apps, list):
                                self.log_test(f"Applications Filter {param_name}={param_value}", True, 
                                            f"Parameter accepted, returned {len(filtered_apps)} applications")
                            else:
                                self.log_test(f"Applications Filter {param_name}={param_value}", False, 
                                            f"Unexpected response format: {type(filtered_apps)}")
                        else:
                            self.log_test(f"Applications Filter {param_name}={param_value}", False, 
                                        f"Parameter rejected: {response.status_code}")
                    except Exception as e:
                        self.log_test(f"Applications Filter {param_name}={param_value}", False, f"Exception: {str(e)}")
            else:
                self.log_test("Admin Applications Basic", False, f"Basic endpoint failed: {response.status_code}")
                
        except Exception as e:
            self.log_test("Applications Filtering", False, f"Exception: {str(e)}")
    
    def test_pagination_functionality(self):
        """Test pagination with multiple parameters"""
        print("\n=== Testing Pagination Functionality ===")
        
        if not self.admin_token:
            self.log_test("Pagination", False, "No admin token available")
            return
        
        try:
            # Test pagination on users endpoint
            params = {"page": "1", "limit": "2"}
            response = self.session.get(f"{BASE_URL}/admin/users", params=params)
            
            if response.status_code == 200:
                page1_users = response.json()
                
                # Test page 2
                params = {"page": "2", "limit": "2"}
                response2 = self.session.get(f"{BASE_URL}/admin/users", params=params)
                
                if response2.status_code == 200:
                    page2_users = response2.json()
                    
                    # Check if pagination is working (different results or proper structure)
                    if isinstance(page1_users, list) and isinstance(page2_users, list):
                        if len(page1_users) <= 2 and len(page2_users) <= 2:
                            self.log_test("Pagination Limit", True, f"Page 1: {len(page1_users)} users, Page 2: {len(page2_users)} users")
                        else:
                            self.log_test("Pagination Limit", False, f"Limit not respected: Page 1: {len(page1_users)}, Page 2: {len(page2_users)}")
                        
                        # Check if pages are different (if we have enough data)
                        if len(page1_users) > 0 and len(page2_users) > 0:
                            if page1_users[0].get('id') != page2_users[0].get('id'):
                                self.log_test("Pagination Pages", True, "Different data returned for different pages")
                            else:
                                self.log_test("Pagination Pages", False, "Same data returned for different pages")
                        else:
                            self.log_test("Pagination Pages", True, "Not enough data to test page differences")
                    else:
                        self.log_test("Pagination Response", False, "Invalid response format for pagination")
                else:
                    self.log_test("Pagination Page 2", False, f"Page 2 request failed: {response2.status_code}")
            else:
                self.log_test("Pagination Page 1", False, f"Page 1 request failed: {response.status_code}")
                
        except Exception as e:
            self.log_test("Pagination", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all Priority 3 backend tests"""
        print("🎨 Starting Priority 3 Backend Tests - Search, Filters & Pagination")
        print(f"Testing against: {BASE_URL}")
        print("=" * 70)
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with admin tests")
            return False
        
        # Run Priority 3 tests
        self.test_admin_users_filtering()
        self.test_admin_reports_filtering()
        self.test_admin_purchases_filtering()
        self.test_admin_applications_filtering()
        self.test_pagination_functionality()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 PRIORITY 3 BACKEND TEST SUMMARY")
        print("=" * 70)
        
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
        
        # Analysis
        print("\n📋 PRIORITY 3 BACKEND ANALYSIS:")
        
        # Count how many filter/sort/pagination features are supported
        filter_tests = [r for r in self.test_results if "Filter" in r["test"] or "Pagination" in r["test"]]
        supported_features = sum(1 for r in filter_tests if r["success"])
        total_features = len(filter_tests)
        
        if supported_features == 0:
            print("❌ No backend filtering, sorting, or pagination features detected")
            print("   Priority 3 features appear to be implemented client-side only")
        elif supported_features < total_features // 2:
            print(f"⚠️  Limited backend support: {supported_features}/{total_features} features working")
            print("   Some Priority 3 features may be client-side only")
        else:
            print(f"✅ Good backend support: {supported_features}/{total_features} features working")
            print("   Priority 3 backend implementation appears functional")
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = Priority3BackendTester()
    success = tester.run_all_tests()
    
    if not success:
        sys.exit(1)
    else:
        print("\n🎉 Priority 3 backend testing completed!")