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
BASE_URL = "https://dev-deploy-config.preview.emergentagent.com/api"
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
    
    def test_priority2_media_type_switching(self):
        """Test Priority 2: Media Type Switching in Admin"""
        print("\n=== Testing Priority 2: Media Type Switching ===")
        
        if not self.admin_token:
            self.log_test("Media Type Switching", False, "No admin token available")
            return
        
        try:
            # First get list of users to find a test user
            users_response = self.session.get(f"{BASE_URL}/admin/users")
            if users_response.status_code != 200:
                self.log_test("Media Type Switching - Get Users", False, f"Failed to get users: {users_response.status_code}")
                return
            
            users = users_response.json()
            if not users:
                self.log_test("Media Type Switching", False, "No users found to test with")
                return
            
            # Find a non-admin user to test with
            test_user = None
            for user in users:
                if user.get("admin_level", 0) == 0:  # Non-admin user
                    test_user = user
                    break
            
            if not test_user:
                self.log_test("Media Type Switching", False, "No non-admin user found for testing")
                return
            
            user_id = test_user["id"]
            original_media_type = test_user.get("media_type", 0)
            new_media_type = 1 if original_media_type == 0 else 0
            
            # Test media type change
            change_data = {
                "user_id": user_id,
                "new_media_type": new_media_type,
                "admin_comment": "Тестовое изменение типа медиа"
            }
            
            response = self.session.post(f"{BASE_URL}/admin/users/{user_id}/change-media-type", json=change_data)
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Media Type Change API", True, f"Successfully changed media type: {result.get('message', '')}")
                
                # Verify user's media type was updated
                updated_user_response = self.session.get(f"{BASE_URL}/admin/users")
                if updated_user_response.status_code == 200:
                    updated_users = updated_user_response.json()
                    updated_user = next((u for u in updated_users if u["id"] == user_id), None)
                    
                    if updated_user and updated_user.get("media_type") == new_media_type:
                        self.log_test("Media Type Update Verification", True, f"User media type successfully updated to {new_media_type}")
                        
                        # Check if notification was created
                        # We need to get notifications for this user (but we can't authenticate as them)
                        # So we'll check if the notification collection has the entry by checking the response message
                        if "уведомлен" in result.get("message", "").lower():
                            self.log_test("Media Type Notification Creation", True, "Notification creation confirmed in response message")
                        else:
                            self.log_test("Media Type Notification Creation", False, "No notification confirmation in response")
                    else:
                        self.log_test("Media Type Update Verification", False, f"User media type not updated correctly. Expected: {new_media_type}, Got: {updated_user.get('media_type') if updated_user else 'User not found'}")
                else:
                    self.log_test("Media Type Update Verification", False, "Failed to verify user update")
                    
            else:
                self.log_test("Media Type Change API", False, f"API call failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Media Type Switching", False, f"Exception: {str(e)}")
    
    def test_priority2_form_validation(self):
        """Test Priority 2: Form Validation Backend"""
        print("\n=== Testing Priority 2: Form Validation ===")
        
        try:
            # Test 1: Password validation (< 8 characters should fail)
            short_password_data = {
                "nickname": "testuser_short_pwd",
                "login": "testlogin_short",
                "password": "123",  # Too short
                "vk_link": "https://vk.com/testuser",
                "channel_link": "https://t.me/testchannel"
            }
            
            response = self.session.post(f"{BASE_URL}/register", json=short_password_data)
            if response.status_code == 422:  # Validation error expected
                error_data = response.json()
                if "8 символов" in str(error_data).lower():
                    self.log_test("Password Validation (< 8 chars)", True, "Short password correctly rejected")
                else:
                    self.log_test("Password Validation (< 8 chars)", False, f"Wrong error message: {error_data}")
            else:
                self.log_test("Password Validation (< 8 chars)", False, f"Expected 422, got {response.status_code}")
            
            # Test 2: VK link validation (must contain vk.com)
            invalid_vk_data = {
                "nickname": "testuser_invalid_vk",
                "login": "testlogin_invalid_vk",
                "password": "validpassword123",
                "vk_link": "https://facebook.com/testuser",  # Not VK
                "channel_link": "https://t.me/testchannel"
            }
            
            response = self.session.post(f"{BASE_URL}/register", json=invalid_vk_data)
            if response.status_code == 422:
                error_data = response.json()
                if "vk" in str(error_data).lower():
                    self.log_test("VK Link Validation", True, "Invalid VK link correctly rejected")
                else:
                    self.log_test("VK Link Validation", False, f"Wrong error message: {error_data}")
            else:
                self.log_test("VK Link Validation", False, f"Expected 422, got {response.status_code}")
            
            # Test 3: Channel link validation (must be t.me, youtube.com, etc.)
            invalid_channel_data = {
                "nickname": "testuser_invalid_channel",
                "login": "testlogin_invalid_channel",
                "password": "validpassword123",
                "vk_link": "https://vk.com/testuser",
                "channel_link": "https://badsite.com/channel"  # Invalid domain
            }
            
            response = self.session.post(f"{BASE_URL}/register", json=invalid_channel_data)
            if response.status_code == 422:
                error_data = response.json()
                if any(domain in str(error_data).lower() for domain in ["telegram", "youtube", "instagram"]):
                    self.log_test("Channel Link Validation", True, "Invalid channel link correctly rejected")
                else:
                    self.log_test("Channel Link Validation", False, f"Wrong error message: {error_data}")
            else:
                self.log_test("Channel Link Validation", False, f"Expected 422, got {response.status_code}")
            
            # Test 4: Valid registration (should succeed)
            valid_data = {
                "nickname": f"validuser_{datetime.now().strftime('%H%M%S')}",
                "login": f"validlogin_{datetime.now().strftime('%H%M%S')}",
                "password": "validpassword123",
                "vk_link": "https://vk.com/validuser",
                "channel_link": "https://t.me/validchannel"
            }
            
            response = self.session.post(f"{BASE_URL}/register", json=valid_data)
            if response.status_code == 200:
                result = response.json()
                if "заявка" in result.get("message", "").lower():
                    self.log_test("Valid Registration", True, "Valid registration data accepted")
                else:
                    self.log_test("Valid Registration", False, f"Unexpected response: {result}")
            else:
                self.log_test("Valid Registration", False, f"Valid registration failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Form Validation", False, f"Exception: {str(e)}")
    
    def test_priority2_custom_mc_rewards(self):
        """Test Priority 2: Custom MC Rewards for Reports"""
        print("\n=== Testing Priority 2: Custom MC Rewards ===")
        
        if not self.admin_token:
            self.log_test("Custom MC Rewards", False, "No admin token available")
            return
        
        try:
            # Get reports to test with
            reports_response = self.session.get(f"{BASE_URL}/admin/reports")
            if reports_response.status_code != 200:
                self.log_test("Custom MC Rewards - Get Reports", False, f"Failed to get reports: {reports_response.status_code}")
                return
            
            reports = reports_response.json()
            pending_report = None
            
            # Find a pending report
            for report in reports:
                if report.get("status") == "pending":
                    pending_report = report
                    break
            
            if not pending_report:
                self.log_test("Custom MC Rewards", False, "No pending reports found for testing")
                return
            
            report_id = pending_report["id"]
            user_id = pending_report["user_id"]
            
            # Get user's current balance
            users_response = self.session.get(f"{BASE_URL}/admin/users")
            if users_response.status_code != 200:
                self.log_test("Custom MC Rewards - Get User Balance", False, "Failed to get users")
                return
            
            users = users_response.json()
            test_user = next((u for u in users if u["id"] == user_id), None)
            if not test_user:
                self.log_test("Custom MC Rewards", False, "Report user not found")
                return
            
            original_balance = test_user.get("balance", 0)
            
            # Test 1: Approve with custom MC reward
            custom_mc = 500
            approve_data = {
                "comment": "Тестовое одобрение с кастомной суммой MC",
                "mc_reward": custom_mc
            }
            
            response = self.session.post(f"{BASE_URL}/admin/reports/{report_id}/approve", json=approve_data)
            
            if response.status_code == 200:
                result = response.json()
                if str(custom_mc) in result.get("message", ""):
                    self.log_test("Custom MC Reward API", True, f"Report approved with custom MC: {result.get('message', '')}")
                    
                    # Verify balance was updated
                    updated_users_response = self.session.get(f"{BASE_URL}/admin/users")
                    if updated_users_response.status_code == 200:
                        updated_users = updated_users_response.json()
                        updated_user = next((u for u in updated_users if u["id"] == user_id), None)
                        
                        if updated_user:
                            new_balance = updated_user.get("balance", 0)
                            expected_balance = original_balance + custom_mc
                            
                            if new_balance == expected_balance:
                                self.log_test("Custom MC Balance Update", True, f"Balance correctly updated: {original_balance} + {custom_mc} = {new_balance}")
                            else:
                                self.log_test("Custom MC Balance Update", False, f"Balance mismatch. Expected: {expected_balance}, Got: {new_balance}")
                        else:
                            self.log_test("Custom MC Balance Update", False, "User not found after update")
                    else:
                        self.log_test("Custom MC Balance Update", False, "Failed to verify balance update")
                else:
                    self.log_test("Custom MC Reward API", False, f"Custom MC amount not found in response: {result}")
            else:
                self.log_test("Custom MC Reward API", False, f"API call failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Custom MC Rewards", False, f"Exception: {str(e)}")
    
    def test_priority2_shop_images(self):
        """Test Priority 2: Shop Item Images Management"""
        print("\n=== Testing Priority 2: Shop Images Management ===")
        
        if not self.admin_token:
            self.log_test("Shop Images Management", False, "No admin token available")
            return
        
        try:
            # Test 1: Get admin shop items
            response = self.session.get(f"{BASE_URL}/admin/shop/items")
            
            if response.status_code == 200:
                items = response.json()
                if isinstance(items, list) and len(items) > 0:
                    self.log_test("Admin Shop Items API", True, f"Successfully retrieved {len(items)} shop items")
                    
                    # Test 2: Update item image
                    test_item = items[0]
                    item_id = test_item["id"]
                    test_image_url = "https://example.com/test-image.jpg"
                    
                    image_data = {"image_url": test_image_url}
                    update_response = self.session.post(f"{BASE_URL}/admin/shop/item/{item_id}/image", json=image_data)
                    
                    if update_response.status_code == 200:
                        result = update_response.json()
                        self.log_test("Shop Item Image Update", True, f"Image updated: {result.get('message', '')}")
                        
                        # Verify the image was updated
                        verify_response = self.session.get(f"{BASE_URL}/admin/shop/items")
                        if verify_response.status_code == 200:
                            updated_items = verify_response.json()
                            updated_item = next((item for item in updated_items if item["id"] == item_id), None)
                            
                            if updated_item and updated_item.get("image_url") == test_image_url:
                                self.log_test("Shop Item Image Verification", True, "Image URL correctly updated in database")
                            else:
                                self.log_test("Shop Item Image Verification", False, f"Image URL not updated. Expected: {test_image_url}, Got: {updated_item.get('image_url') if updated_item else 'Item not found'}")
                        else:
                            self.log_test("Shop Item Image Verification", False, "Failed to verify image update")
                    else:
                        self.log_test("Shop Item Image Update", False, f"Image update failed: {update_response.status_code} - {update_response.text}")
                        # Skip verification test if update failed
                        self.log_test("Shop Item Image Verification", False, "Skipped due to update failure")
                    
                    # Test 3: Invalid image URL validation (use a different item to avoid conflicts)
                    test_item_2 = items[1] if len(items) > 1 else items[0]
                    item_id_2 = test_item_2["id"]
                    invalid_image_data = {"image_url": "not-a-valid-url"}
                    invalid_response = self.session.post(f"{BASE_URL}/admin/shop/item/{item_id_2}/image", json=invalid_image_data)
                    
                    if invalid_response.status_code == 400:
                        self.log_test("Shop Image URL Validation", True, "Invalid image URL correctly rejected")
                    else:
                        self.log_test("Shop Image URL Validation", False, f"Expected 400 for invalid URL, got {invalid_response.status_code}")
                        
                else:
                    self.log_test("Admin Shop Items API", False, f"Expected non-empty list, got: {items}")
            else:
                self.log_test("Admin Shop Items API", False, f"API call failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Shop Images Management", False, f"Exception: {str(e)}")
    
    def test_priority2_notifications(self):
        """Test Priority 2: Notifications System"""
        print("\n=== Testing Priority 2: Notifications System ===")
        
        if not self.admin_token:
            self.log_test("Notifications System", False, "No admin token available")
            return
        
        try:
            # Test notifications endpoint (as admin user)
            response = self.session.get(f"{BASE_URL}/notifications")
            
            if response.status_code == 200:
                notifications = response.json()
                if isinstance(notifications, list):
                    self.log_test("Notifications API", True, f"Successfully retrieved {len(notifications)} notifications")
                    
                    # Check notification structure if any exist
                    if notifications:
                        sample_notification = notifications[0]
                        required_fields = ["id", "user_id", "type", "title", "message", "created_at", "read"]
                        
                        if all(field in sample_notification for field in required_fields):
                            self.log_test("Notification Structure", True, "Notifications have correct structure")
                            
                            # Test marking notification as read (if we have unread ones)
                            unread_notification = next((n for n in notifications if not n.get("read", True)), None)
                            if unread_notification:
                                notification_id = unread_notification["id"]
                                read_response = self.session.post(f"{BASE_URL}/notifications/{notification_id}/read")
                                
                                if read_response.status_code == 200:
                                    self.log_test("Mark Notification Read", True, "Successfully marked notification as read")
                                else:
                                    self.log_test("Mark Notification Read", False, f"Failed to mark as read: {read_response.status_code} - {read_response.text}")
                            else:
                                self.log_test("Mark Notification Read", True, "No unread notifications to test with (all already read)")
                        else:
                            missing_fields = [f for f in required_fields if f not in sample_notification]
                            self.log_test("Notification Structure", False, f"Missing fields: {missing_fields}", sample_notification)
                    else:
                        self.log_test("Notification Structure", True, "No notifications to check structure (empty list is valid)")
                else:
                    self.log_test("Notifications API", False, f"Expected list, got {type(notifications)}: {notifications}")
            else:
                self.log_test("Notifications API", False, f"API call failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Notifications System", False, f"Exception: {str(e)}")
    
    def test_priority2_report_validation(self):
        """Test Priority 2: Report URL Validation"""
        print("\n=== Testing Priority 2: Report URL Validation ===")
        
        if not self.admin_token:
            self.log_test("Report URL Validation", False, "No admin token available")
            return
        
        try:
            # Test 1: Invalid URL (no http/https)
            invalid_url_data = {
                "links": [
                    {"url": "badurl.com/video", "views": 1000}
                ]
            }
            
            response = self.session.post(f"{BASE_URL}/reports", json=invalid_url_data)
            if response.status_code == 422:  # Validation error expected
                error_data = response.json()
                if "http" in str(error_data).lower():
                    self.log_test("Report URL Validation (No Protocol)", True, "Invalid URL without protocol correctly rejected")
                else:
                    self.log_test("Report URL Validation (No Protocol)", False, f"Wrong error message: {error_data}")
            else:
                self.log_test("Report URL Validation (No Protocol)", False, f"Expected 422, got {response.status_code}")
            
            # Test 2: Invalid URL format
            invalid_format_data = {
                "links": [
                    {"url": "https://", "views": 1000}  # Incomplete URL
                ]
            }
            
            response = self.session.post(f"{BASE_URL}/reports", json=invalid_format_data)
            if response.status_code == 422:
                error_data = response.json()
                if "корректный" in str(error_data).lower() or "url" in str(error_data).lower():
                    self.log_test("Report URL Validation (Invalid Format)", True, "Invalid URL format correctly rejected")
                else:
                    self.log_test("Report URL Validation (Invalid Format)", False, f"Wrong error message: {error_data}")
            else:
                self.log_test("Report URL Validation (Invalid Format)", False, f"Expected 422, got {response.status_code}")
            
            # Test 3: Valid URL (should succeed)
            valid_data = {
                "links": [
                    {"url": "https://youtube.com/watch?v=test123", "views": 1500},
                    {"url": "https://vk.com/video123", "views": 800}
                ]
            }
            
            response = self.session.post(f"{BASE_URL}/reports", json=valid_data)
            if response.status_code == 200:
                result = response.json()
                if "successfully" in result.get("message", "").lower() or "успешно" in result.get("message", "").lower():
                    self.log_test("Report URL Validation (Valid URLs)", True, "Valid URLs accepted successfully")
                else:
                    self.log_test("Report URL Validation (Valid URLs)", False, f"Unexpected response: {result}")
            else:
                self.log_test("Report URL Validation (Valid URLs)", False, f"Valid URLs rejected: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Report URL Validation", False, f"Exception: {str(e)}")
    
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
        
        # Priority 2 Feature Tests
        self.test_priority2_media_type_switching()
        self.test_priority2_form_validation()
        self.test_priority2_custom_mc_rewards()
        self.test_priority2_shop_images()
        self.test_priority2_notifications()
        self.test_priority2_report_validation()
        
        # Original tests
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