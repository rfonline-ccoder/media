#!/usr/bin/env python3
"""
Initialize admin user for SwagMedia testing
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import uuid
from datetime import datetime

load_dotenv('backend/.env')
mongo_url = os.environ['MONGO_URL']

async def init_admin():
    client = AsyncIOMotorClient(mongo_url)
    db = client['swagmedia']
    
    # Check if admin already exists
    existing_admin = await db.users.find_one({"login": "admin"})
    if existing_admin:
        print("Admin user already exists")
        client.close()
        return
    
    # Create admin user
    admin_user = {
        "id": str(uuid.uuid4()),
        "login": "admin",
        "password": "admin123",
        "nickname": "Administrator",
        "vk_link": "https://vk.com/admin",
        "channel_link": "https://t.me/admin",
        "balance": 1000000,  # 1M MC for testing
        "admin_level": 1,
        "is_approved": True,
        "media_type": 0,
        "warnings": 0,
        "created_at": datetime.utcnow()
    }
    
    await db.users.insert_one(admin_user)
    print("Admin user created successfully")
    
    # Create some test users for testing
    test_users = [
        {
            "id": str(uuid.uuid4()),
            "login": "testuser1",
            "password": "testpass123",
            "nickname": "TestUser1",
            "vk_link": "https://vk.com/testuser1",
            "channel_link": "https://t.me/testuser1",
            "balance": 500,
            "admin_level": 0,
            "is_approved": True,
            "media_type": 0,
            "warnings": 0,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "login": "testuser2",
            "password": "testpass123",
            "nickname": "TestUser2",
            "vk_link": "https://vk.com/testuser2",
            "channel_link": "https://youtube.com/testuser2",
            "balance": 750,
            "admin_level": 0,
            "is_approved": True,
            "media_type": 1,
            "warnings": 0,
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "login": "testuser3",
            "password": "testpass123",
            "nickname": "TestUser3",
            "vk_link": "https://vk.com/testuser3",
            "channel_link": "https://instagram.com/testuser3",
            "balance": 300,
            "admin_level": 0,
            "is_approved": True,
            "media_type": 0,
            "warnings": 0,
            "created_at": datetime.utcnow()
        }
    ]
    
    for user in test_users:
        await db.users.insert_one(user)
    
    print(f"Created {len(test_users)} test users")
    
    # Create some test reports for testing
    test_reports = [
        {
            "id": str(uuid.uuid4()),
            "user_id": test_users[0]["id"],
            "links": [
                {"url": "https://youtube.com/watch?v=test1", "views": 1500},
                {"url": "https://vk.com/video123", "views": 800}
            ],
            "status": "pending",
            "created_at": datetime.utcnow(),
            "admin_comment": None
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": test_users[1]["id"],
            "links": [
                {"url": "https://t.me/channel/post123", "views": 2000}
            ],
            "status": "pending",
            "created_at": datetime.utcnow(),
            "admin_comment": None
        }
    ]
    
    for report in test_reports:
        await db.reports.insert_one(report)
    
    print(f"Created {len(test_reports)} test reports")
    
    client.close()
    print("Database initialization complete!")

if __name__ == "__main__":
    asyncio.run(init_admin())