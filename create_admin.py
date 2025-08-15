#!/usr/bin/env python3
"""
Create admin user in MongoDB for testing
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment
ROOT_DIR = Path(__file__).parent / "backend"
load_dotenv(ROOT_DIR / '.env')

async def create_admin_user():
    # MongoDB connection
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client["swagmedia"]
    
    # Check if admin user already exists
    existing_admin = await db.users.find_one({"login": "admin"})
    if existing_admin:
        print("Admin user already exists!")
        return
    
    # Create admin user
    admin_user = {
        "id": str(uuid.uuid4()),
        "login": "admin",
        "password": "admin123",  # Plain text as per requirement
        "nickname": "Administrator",
        "vk_link": "https://vk.com/admin",
        "channel_link": "https://t.me/admin",
        "balance": 10000,
        "admin_level": 1,
        "is_approved": True,
        "media_type": 1,  # Paid media
        "warnings": 0,
        "previews_used": 0,
        "previews_limit": 3,
        "blacklist_until": None,
        "registration_ip": "127.0.0.1",
        "created_at": datetime.utcnow()
    }
    
    # Insert admin user
    result = await db.users.insert_one(admin_user)
    print(f"Admin user created with ID: {admin_user['id']}")
    
    # Create a few test users for testing admin functions
    test_users = []
    for i in range(3):
        test_user = {
            "id": str(uuid.uuid4()),
            "login": f"testuser{i+1}",
            "password": "testpass123",
            "nickname": f"TestUser{i+1}",
            "vk_link": f"https://vk.com/testuser{i+1}",
            "channel_link": f"https://t.me/testuser{i+1}",
            "balance": 100 * (i+1),
            "admin_level": 0,
            "is_approved": True,
            "media_type": 0,  # Free media
            "warnings": 0,
            "previews_used": 0,
            "previews_limit": 3,
            "blacklist_until": None,
            "registration_ip": f"192.168.1.{i+10}",
            "created_at": datetime.utcnow()
        }
        test_users.append(test_user)
    
    # Insert test users
    if test_users:
        await db.users.insert_many(test_users)
        print(f"Created {len(test_users)} test users")
    
    # Close connection
    client.close()
    print("Database setup complete!")

if __name__ == "__main__":
    asyncio.run(create_admin_user())