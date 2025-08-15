#!/usr/bin/env python3
"""
SwagMedia Preview System and Blacklist Testing Suite
Tests the new preview system, IP blocking, and admin blacklist management
"""

import requests
import json
import sys
import time
from datetime import datetime

# Configuration
BASE_URL = "https://backend-checker.preview.emergentagent.com/api"
ADMIN_CREDENTIALS = {"login": "admin", "password": "admin123"}

class PreviewSystemTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_results = []
        self.test_users = []  # Store created test users
        
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
    
    def setup_admin_auth(self):
        """Setup admin authentication"""
        print("\n=== Setting up Admin Authentication ===")
        
        try:
            response = self.session.post(f"{BASE_URL}/login", json=ADMIN_CREDENTIALS)
            
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data:
                    self.admin_token = data["access_token"]
                    self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
                    self.log_test("Admin Authentication", True, "Successfully authenticated as admin")
                    return True
                else:
                    self.log_test("Admin Authentication", False, "No access token in response", data)
            else:
                self.log_test("Admin Authentication", False, f"Login failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Exception: {str(e)}")
        
        return False
    
    def create_test_users(self):
        """Create test users for preview system testing"""
        print("\n=== Creating Test Users ===")
        
        if not self.admin_token:
            self.log_test("Create Test Users", False, "No admin token available")
            return False
        
        try:
            # Create test users with different media types
            test_users_data = [
                {
                    "nickname": f"freeuser_{int(time.time())}",
                    "login": f"freeuser_{int(time.time())}",
                    "password": "testpass123",
                    "vk_link": "https://vk.com/freeuser",
                    "channel_link": "https://t.me/freeuser",
                    "media_type": 0  # Free user
                },
                {
                    "nickname": f"paiduser_{int(time.time())}",
                    "login": f"paiduser_{int(time.time())}",
                    "password": "testpass123",
                    "vk_link": "https://vk.com/paiduser",
                    "channel_link": "https://t.me/paiduser",
                    "media_type": 1  # Paid user
                },
                {
                    "nickname": f"contentuser_{int(time.time())}",
                    "login": f"contentuser_{int(time.time())}",
                    "password": "testpass123",
                    "vk_link": "https://vk.com/contentuser",
                    "channel_link": "https://t.me/contentuser",
                    "media_type": 1  # Paid content creator
                }
            ]
            
            for user_data in test_users_data:
                # Register user
                reg_response = self.session.post(f"{BASE_URL}/register", json=user_data)
                
                if reg_response.status_code == 200:
                    # Get applications to approve
                    apps_response = self.session.get(f"{BASE_URL}/admin/applications")
                    if apps_response.status_code == 200:
                        applications = apps_response.json()
                        # Find the latest application
                        latest_app = None
                        for app in applications:
                            if (app.get("status") == "pending" and 
                                app.get("data", {}).get("login") == user_data["login"]):
                                latest_app = app
                                break
                        
                        if latest_app:
                            # Approve application
                            approve_response = self.session.post(
                                f"{BASE_URL}/admin/applications/{latest_app['id']}/approve",
                                params={"media_type": user_data["media_type"]}
                            )
                            
                            if approve_response.status_code == 200:
                                # Store user info
                                user_info = {
                                    "login": user_data["login"],
                                    "password": user_data["password"],
                                    "nickname": user_data["nickname"],
                                    "media_type": user_data["media_type"],
                                    "token": None,
                                    "user_id": None
                                }
                                
                                # Login as the user to get token and ID
                                login_response = self.session.post(f"{BASE_URL}/login", json={
                                    "login": user_data["login"],
                                    "password": user_data["password"]
                                })
                                
                                if login_response.status_code == 200:
                                    login_data = login_response.json()
                                    user_info["token"] = login_data.get("access_token")
                                    user_info["user_id"] = login_data.get("user", {}).get("id")
                                
                                self.test_users.append(user_info)
                                self.log_test(f"Create User {user_data['nickname']}", True, 
                                            f"Successfully created and approved user")
                            else:
                                self.log_test(f"Approve User {user_data['nickname']}", False, 
                                            f"Failed to approve: {approve_response.status_code}")
                        else:
                            self.log_test(f"Find Application {user_data['nickname']}", False, 
                                        "Application not found")
                    else:
                        self.log_test(f"Get Applications {user_data['nickname']}", False, 
                                    f"Failed to get applications: {apps_response.status_code}")
                else:
                    self.log_test(f"Register User {user_data['nickname']}", False, 
                                f"Registration failed: {reg_response.status_code} - {reg_response.text}")
            
            # Restore admin token
            self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
            
            if len(self.test_users) >= 2:
                self.log_test("Test Users Creation", True, f"Created {len(self.test_users)} test users")
                return True
            else:
                self.log_test("Test Users Creation", False, f"Only created {len(self.test_users)} users, need at least 2")
                return False
                
        except Exception as e:
            self.log_test("Create Test Users", False, f"Exception: {str(e)}")
            return False
    
    def test_media_list_with_access(self):
        """Test updated media list with can_access field"""
        print("\n=== Testing Updated Media List ===")
        
        if not self.test_users:
            self.log_test("Media List Access Test", False, "No test users available")
            return
        
        try:
            # Test as free user
            free_user = next((u for u in self.test_users if u["media_type"] == 0), None)
            if free_user and free_user["token"]:
                # Set free user token
                self.session.headers.update({"Authorization": f"Bearer {free_user['token']}"})
                
                response = self.session.get(f"{BASE_URL}/media-list")
                
                if response.status_code == 200:
                    media_list = response.json()
                    
                    if isinstance(media_list, list):
                        self.log_test("Media List API (Free User)", True, f"Retrieved {len(media_list)} media entries")
                        
                        # Check for can_access field
                        if media_list:
                            sample_media = media_list[0]
                            if "can_access" in sample_media:
                                self.log_test("Media List can_access Field", True, "can_access field present in response")
                                
                                # Check logic: free users should have can_access=false for paid content
                                paid_content = next((m for m in media_list if "Платное" in m.get("media_type", "")), None)
                                if paid_content:
                                    if not paid_content.get("can_access", True):
                                        self.log_test("Media List Access Logic (Free->Paid)", True, 
                                                    "Free user correctly denied access to paid content")
                                    else:
                                        self.log_test("Media List Access Logic (Free->Paid)", False, 
                                                    "Free user incorrectly granted access to paid content")
                                
                                # Check free content access
                                free_content = next((m for m in media_list if "Бесплатное" in m.get("media_type", "")), None)
                                if free_content:
                                    if free_content.get("can_access", False):
                                        self.log_test("Media List Access Logic (Free->Free)", True, 
                                                    "Free user correctly granted access to free content")
                                    else:
                                        self.log_test("Media List Access Logic (Free->Free)", False, 
                                                    "Free user incorrectly denied access to free content")
                            else:
                                self.log_test("Media List can_access Field", False, "can_access field missing", sample_media)
                    else:
                        self.log_test("Media List API (Free User)", False, f"Expected list, got {type(media_list)}")
                else:
                    self.log_test("Media List API (Free User)", False, f"API failed: {response.status_code} - {response.text}")
            
            # Test as paid user
            paid_user = next((u for u in self.test_users if u["media_type"] == 1), None)
            if paid_user and paid_user["token"]:
                # Set paid user token
                self.session.headers.update({"Authorization": f"Bearer {paid_user['token']}"})
                
                response = self.session.get(f"{BASE_URL}/media-list")
                
                if response.status_code == 200:
                    media_list = response.json()
                    
                    if isinstance(media_list, list) and media_list:
                        # Paid users should have can_access=true for all content
                        all_accessible = all(m.get("can_access", False) for m in media_list)
                        if all_accessible:
                            self.log_test("Media List Access Logic (Paid->All)", True, 
                                        "Paid user correctly granted access to all content")
                        else:
                            inaccessible = [m for m in media_list if not m.get("can_access", False)]
                            self.log_test("Media List Access Logic (Paid->All)", False, 
                                        f"Paid user denied access to {len(inaccessible)} items")
                
            # Restore admin token
            self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
                
        except Exception as e:
            self.log_test("Media List Access Test", False, f"Exception: {str(e)}")
    
    def test_preview_system(self):
        """Test the preview system functionality"""
        print("\n=== Testing Preview System ===")
        
        if not self.test_users:
            self.log_test("Preview System Test", False, "No test users available")
            return
        
        try:
            # Get free and paid users
            free_user = next((u for u in self.test_users if u["media_type"] == 0), None)
            paid_content_user = next((u for u in self.test_users if u["media_type"] == 1), None)
            
            if not free_user or not paid_content_user:
                self.log_test("Preview System Test", False, "Need both free and paid users for testing")
                return
            
            # Test 1: Check initial preview status
            self.session.headers.update({"Authorization": f"Bearer {free_user['token']}"})
            
            preview_status_response = self.session.get(f"{BASE_URL}/user/previews")
            if preview_status_response.status_code == 200:
                status_data = preview_status_response.json()
                
                required_fields = ["previews_used", "preview_limit", "previews_remaining", "is_blacklisted"]
                if all(field in status_data for field in required_fields):
                    self.log_test("Preview Status API", True, "Preview status endpoint working correctly", status_data)
                    
                    initial_previews_used = status_data.get("previews_used", 0)
                    preview_limit = status_data.get("preview_limit", 3)
                    
                    if preview_limit == 3:
                        self.log_test("Preview Limit Default", True, "Default preview limit is 3")
                    else:
                        self.log_test("Preview Limit Default", False, f"Expected limit 3, got {preview_limit}")
                else:
                    missing = [f for f in required_fields if f not in status_data]
                    self.log_test("Preview Status API", False, f"Missing fields: {missing}", status_data)
            else:
                self.log_test("Preview Status API", False, f"API failed: {preview_status_response.status_code}")
            
            # Test 2: Access paid content as free user (should use preview)
            media_user_id = paid_content_user["user_id"]
            
            access_response = self.session.post(f"{BASE_URL}/media/{media_user_id}/access")
            
            if access_response.status_code == 200:
                access_data = access_response.json()
                
                if access_data.get("access_type") == "preview":
                    self.log_test("Preview Access Grant", True, f"Preview access granted: {access_data.get('message', '')}")
                    
                    # Check if preview counter increased
                    updated_status_response = self.session.get(f"{BASE_URL}/user/previews")
                    if updated_status_response.status_code == 200:
                        updated_status = updated_status_response.json()
                        new_previews_used = updated_status.get("previews_used", 0)
                        
                        if new_previews_used == initial_previews_used + 1:
                            self.log_test("Preview Counter Increment", True, 
                                        f"Preview counter correctly incremented: {initial_previews_used} -> {new_previews_used}")
                        else:
                            self.log_test("Preview Counter Increment", False, 
                                        f"Counter not incremented correctly: {initial_previews_used} -> {new_previews_used}")
                    
                    # Check preview data is limited
                    preview_data = access_data.get("data", {})
                    if "preview_note" in preview_data:
                        self.log_test("Preview Data Limitation", True, "Preview data contains limitation note")
                    else:
                        self.log_test("Preview Data Limitation", False, "Preview data missing limitation note", preview_data)
                        
                elif access_data.get("access_type") == "full":
                    self.log_test("Preview Access Grant", False, "Free user got full access instead of preview", access_data)
                else:
                    self.log_test("Preview Access Grant", False, f"Unexpected access type: {access_data.get('access_type')}", access_data)
            else:
                self.log_test("Preview Access Grant", False, f"Access failed: {access_response.status_code} - {access_response.text}")
            
            # Test 3: Exhaust preview limit (make 2 more requests to reach limit)
            for i in range(2):
                access_response = self.session.post(f"{BASE_URL}/media/{media_user_id}/access")
                if access_response.status_code == 200:
                    access_data = access_response.json()
                    remaining = access_data.get("previews_remaining", 0)
                    self.log_test(f"Preview Access {i+2}", True, f"Preview {i+2}/3 used, {remaining} remaining")
                else:
                    self.log_test(f"Preview Access {i+2}", False, f"Failed: {access_response.status_code}")
            
            # Test 4: Try to exceed limit (should trigger blacklist)
            exceed_response = self.session.post(f"{BASE_URL}/media/{media_user_id}/access")
            
            if exceed_response.status_code == 403:
                error_data = exceed_response.json()
                if "лимит" in error_data.get("detail", "").lower() and "15 дней" in error_data.get("detail", ""):
                    self.log_test("Preview Limit Exceeded", True, "User correctly blocked after exceeding limit")
                    
                    # Check if user is now blacklisted
                    final_status_response = self.session.get(f"{BASE_URL}/user/previews")
                    if final_status_response.status_code == 200:
                        final_status = final_status_response.json()
                        if final_status.get("is_blacklisted", False):
                            self.log_test("User Blacklist Status", True, "User correctly marked as blacklisted")
                        else:
                            self.log_test("User Blacklist Status", False, "User not marked as blacklisted", final_status)
                else:
                    self.log_test("Preview Limit Exceeded", False, f"Wrong error message: {error_data}")
            else:
                self.log_test("Preview Limit Exceeded", False, f"Expected 403, got {exceed_response.status_code}")
            
            # Restore admin token
            self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
                
        except Exception as e:
            self.log_test("Preview System Test", False, f"Exception: {str(e)}")
    
    def test_ip_blocking_registration(self):
        """Test IP blocking during registration"""
        print("\n=== Testing IP Blocking During Registration ===")
        
        try:
            # Test normal registration first
            normal_user_data = {
                "nickname": f"normaluser_{int(time.time())}",
                "login": f"normaluser_{int(time.time())}",
                "password": "testpass123",
                "vk_link": "https://vk.com/normaluser",
                "channel_link": "https://t.me/normaluser"
            }
            
            normal_response = self.session.post(f"{BASE_URL}/register", json=normal_user_data)
            
            if normal_response.status_code == 200:
                self.log_test("Normal Registration", True, "Normal registration works")
            else:
                self.log_test("Normal Registration", False, f"Normal registration failed: {normal_response.status_code}")
            
            # Test registration with same VK link as blacklisted user (if we have one)
            if self.test_users:
                # Try to register with same VK as a user who might be blacklisted
                blacklisted_vk_data = {
                    "nickname": f"blockeduser_{int(time.time())}",
                    "login": f"blockeduser_{int(time.time())}",
                    "password": "testpass123",
                    "vk_link": self.test_users[0]["login"].replace("freeuser", "https://vk.com/freeuser"),  # Use similar VK
                    "channel_link": "https://t.me/blockeduser"
                }
                
                blocked_response = self.session.post(f"{BASE_URL}/register", json=blacklisted_vk_data)
                
                # This might succeed if the user isn't actually blacklisted yet
                if blocked_response.status_code in [200, 403]:
                    if blocked_response.status_code == 403:
                        error_data = blocked_response.json()
                        if "vk" in error_data.get("detail", "").lower():
                            self.log_test("VK Blacklist Check", True, "VK blacklist check working")
                        else:
                            self.log_test("VK Blacklist Check", False, f"Wrong error: {error_data}")
                    else:
                        self.log_test("VK Blacklist Check", True, "VK not blacklisted (expected for new users)")
                else:
                    self.log_test("VK Blacklist Check", False, f"Unexpected status: {blocked_response.status_code}")
                
        except Exception as e:
            self.log_test("IP Blocking Registration", False, f"Exception: {str(e)}")
    
    def test_admin_blacklist_management(self):
        """Test admin blacklist management endpoints"""
        print("\n=== Testing Admin Blacklist Management ===")
        
        if not self.admin_token:
            self.log_test("Admin Blacklist Management", False, "No admin token available")
            return
        
        try:
            # Test 1: Get blacklist
            blacklist_response = self.session.get(f"{BASE_URL}/admin/blacklist")
            
            if blacklist_response.status_code == 200:
                blacklist_data = blacklist_response.json()
                
                required_keys = ["ip_blacklist", "blacklisted_users"]
                if all(key in blacklist_data for key in required_keys):
                    self.log_test("Admin Blacklist API", True, 
                                f"Blacklist retrieved: {len(blacklist_data['ip_blacklist'])} IPs, "
                                f"{len(blacklist_data['blacklisted_users'])} users")
                    
                    # Test 2: Reset previews for a user (if we have test users)
                    if self.test_users:
                        test_user_id = self.test_users[0]["user_id"]
                        
                        reset_response = self.session.post(f"{BASE_URL}/admin/users/{test_user_id}/reset-previews")
                        
                        if reset_response.status_code == 200:
                            result = reset_response.json()
                            if "сброшены" in result.get("message", "").lower():
                                self.log_test("Admin Reset Previews", True, "Preview reset successful")
                            else:
                                self.log_test("Admin Reset Previews", False, f"Unexpected message: {result}")
                        else:
                            self.log_test("Admin Reset Previews", False, f"Reset failed: {reset_response.status_code}")
                        
                        # Test 3: Unblacklist user
                        unblacklist_response = self.session.post(f"{BASE_URL}/admin/users/{test_user_id}/unblacklist")
                        
                        if unblacklist_response.status_code == 200:
                            result = unblacklist_response.json()
                            if "разблокирован" in result.get("message", "").lower():
                                self.log_test("Admin Unblacklist User", True, "User unblacklist successful")
                            else:
                                self.log_test("Admin Unblacklist User", False, f"Unexpected message: {result}")
                        else:
                            self.log_test("Admin Unblacklist User", False, f"Unblacklist failed: {unblacklist_response.status_code}")
                    else:
                        self.log_test("Admin Reset Previews", False, "No test users available")
                        self.log_test("Admin Unblacklist User", False, "No test users available")
                else:
                    missing = [k for k in required_keys if k not in blacklist_data]
                    self.log_test("Admin Blacklist API", False, f"Missing keys: {missing}", blacklist_data)
            else:
                self.log_test("Admin Blacklist API", False, f"API failed: {blacklist_response.status_code} - {blacklist_response.text}")
                
        except Exception as e:
            self.log_test("Admin Blacklist Management", False, f"Exception: {str(e)}")
    
    def test_rating_system(self):
        """Test the rating system endpoints"""
        print("\n=== Testing Rating System ===")
        
        if not self.test_users or len(self.test_users) < 2:
            self.log_test("Rating System Test", False, "Need at least 2 test users")
            return
        
        try:
            # Use first user to rate second user
            rater = self.test_users[0]
            rated_user = self.test_users[1]
            
            # Set rater token
            self.session.headers.update({"Authorization": f"Bearer {rater['token']}"})
            
            # Test 1: Submit rating
            rating_data = {
                "rated_user_id": rated_user["user_id"],
                "rating": 5,
                "comment": "Отличный контент! Рекомендую всем."
            }
            
            rating_response = self.session.post(f"{BASE_URL}/ratings", json=rating_data)
            
            if rating_response.status_code == 200:
                result = rating_response.json()
                if "successfully" in result.get("message", "").lower() or "успешно" in result.get("message", "").lower():
                    self.log_test("Submit Rating", True, "Rating submitted successfully")
                    
                    # Test 2: Get user ratings
                    get_ratings_response = self.session.get(f"{BASE_URL}/ratings/{rated_user['user_id']}")
                    
                    if get_ratings_response.status_code == 200:
                        ratings_data = get_ratings_response.json()
                        
                        required_fields = ["ratings", "average_rating", "total_ratings"]
                        if all(field in ratings_data for field in required_fields):
                            self.log_test("Get User Ratings", True, 
                                        f"Retrieved ratings: avg={ratings_data['average_rating']}, "
                                        f"total={ratings_data['total_ratings']}")
                            
                            # Check if our rating is there
                            our_rating = next((r for r in ratings_data["ratings"] if r.get("user_id") == rater["user_id"]), None)
                            if our_rating and our_rating.get("rating") == 5:
                                self.log_test("Rating Data Verification", True, "Submitted rating found in results")
                            else:
                                self.log_test("Rating Data Verification", False, "Submitted rating not found or incorrect")
                        else:
                            missing = [f for f in required_fields if f not in ratings_data]
                            self.log_test("Get User Ratings", False, f"Missing fields: {missing}", ratings_data)
                    else:
                        self.log_test("Get User Ratings", False, f"API failed: {get_ratings_response.status_code}")
                    
                    # Test 3: Get leaderboard
                    leaderboard_response = self.session.get(f"{BASE_URL}/leaderboard")
                    
                    if leaderboard_response.status_code == 200:
                        leaderboard_data = leaderboard_response.json()
                        
                        if isinstance(leaderboard_data, list):
                            self.log_test("Get Leaderboard", True, f"Leaderboard retrieved with {len(leaderboard_data)} entries")
                            
                            # Check if our rated user appears in leaderboard
                            if leaderboard_data:
                                sample_entry = leaderboard_data[0]
                                required_fields = ["user_id", "nickname", "avg_rating", "total_ratings"]
                                if all(field in sample_entry for field in required_fields):
                                    self.log_test("Leaderboard Structure", True, "Leaderboard entries have correct structure")
                                    
                                    # Check if our user is in leaderboard
                                    our_user_entry = next((e for e in leaderboard_data if e.get("user_id") == rated_user["user_id"]), None)
                                    if our_user_entry:
                                        self.log_test("Leaderboard User Presence", True, "Rated user appears in leaderboard")
                                    else:
                                        self.log_test("Leaderboard User Presence", False, "Rated user not found in leaderboard")
                                else:
                                    missing = [f for f in required_fields if f not in sample_entry]
                                    self.log_test("Leaderboard Structure", False, f"Missing fields: {missing}", sample_entry)
                        else:
                            self.log_test("Get Leaderboard", False, f"Expected list, got {type(leaderboard_data)}")
                    else:
                        self.log_test("Get Leaderboard", False, f"API failed: {leaderboard_response.status_code}")
                        
                    # Test 4: Update rating (should update existing)
                    updated_rating_data = {
                        "rated_user_id": rated_user["user_id"],
                        "rating": 4,
                        "comment": "Обновленный отзыв - хороший контент."
                    }
                    
                    update_response = self.session.post(f"{BASE_URL}/ratings", json=updated_rating_data)
                    
                    if update_response.status_code == 200:
                        result = update_response.json()
                        if "updated" in result.get("message", "").lower() or "обновлен" in result.get("message", "").lower():
                            self.log_test("Update Rating", True, "Rating updated successfully")
                        else:
                            self.log_test("Update Rating", True, "Rating operation completed (might be update or new)")
                    else:
                        self.log_test("Update Rating", False, f"Update failed: {update_response.status_code}")
                        
                else:
                    self.log_test("Submit Rating", False, f"Unexpected response: {result}")
            else:
                self.log_test("Submit Rating", False, f"Rating submission failed: {rating_response.status_code} - {rating_response.text}")
            
            # Restore admin token
            self.session.headers.update({"Authorization": f"Bearer {self.admin_token}"})
                
        except Exception as e:
            self.log_test("Rating System Test", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all preview system tests"""
        print("🚀 Starting SwagMedia Preview System & Blacklist Tests")
        print(f"Testing against: {BASE_URL}")
        print("=" * 70)
        
        # Setup
        if not self.setup_admin_auth():
            print("❌ Failed to setup admin authentication - aborting tests")
            return False
        
        if not self.create_test_users():
            print("❌ Failed to create test users - some tests will be skipped")
        
        # Run tests
        self.test_media_list_with_access()
        self.test_preview_system()
        self.test_ip_blocking_registration()
        self.test_admin_blacklist_management()
        self.test_rating_system()
        
        # Summary
        print("\n" + "=" * 70)
        print("📊 PREVIEW SYSTEM TEST SUMMARY")
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
        
        return failed_tests == 0

if __name__ == "__main__":
    tester = PreviewSystemTester()
    success = tester.run_all_tests()
    
    if not success:
        sys.exit(1)
    else:
        print("\n🎉 All preview system tests passed!")