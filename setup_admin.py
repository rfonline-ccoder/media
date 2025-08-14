#!/usr/bin/env python3
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

async def setup_admin():
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client["swagmedia"]
    
    # Create admin user
    admin_user = {
        "id": str(uuid.uuid4()),
        "login": "admin",
        "password": "admin123",
        "nickname": "Administrator",
        "vk_link": "https://vk.com/admin",
        "channel_link": "https://t.me/admin_channel",
        "balance": 999999,
        "admin_level": 1,
        "is_approved": True,
        "media_type": 1,
        "warnings": 0,
        "created_at": datetime.utcnow()
    }
    
    # Check if admin already exists
    existing_admin = await db.users.find_one({"login": "admin"})
    if existing_admin:
        print("Admin already exists")
    else:
        await db.users.insert_one(admin_user)
        print("Admin user created successfully")
    
    # Create a few test users
    test_users = [
        {
            "id": str(uuid.uuid4()),
            "login": "testuser1",
            "password": "test123",
            "nickname": "TestUser1",
            "vk_link": "https://vk.com/testuser1",
            "channel_link": "https://t.me/testchannel1",
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
            "password": "test123",
            "nickname": "TestUser2",
            "vk_link": "https://vk.com/testuser2",
            "channel_link": "https://t.me/testchannel2",
            "balance": 300,
            "admin_level": 0,
            "is_approved": True,
            "media_type": 1,
            "warnings": 1,
            "created_at": datetime.utcnow()
        }
    ]
    
    for user in test_users:
        existing = await db.users.find_one({"login": user["login"]})
        if not existing:
            await db.users.insert_one(user)
            print(f"Created test user: {user['nickname']}")
    
    # Add some test registration applications
    test_applications = [
        {
            "id": str(uuid.uuid4()),
            "type": "registration",
            "data": {
                "nickname": "PendingUser1",
                "login": "pending1",
                "password": "pending123",
                "vk_link": "https://vk.com/pending1",
                "channel_link": "https://t.me/pending1"
            },
            "status": "pending",
            "created_at": datetime.utcnow()
        },
        {
            "id": str(uuid.uuid4()),
            "type": "registration", 
            "data": {
                "nickname": "PendingUser2",
                "login": "pending2",
                "password": "pending123",
                "vk_link": "https://vk.com/pending2",
                "channel_link": "https://youtube.com/pending2"
            },
            "status": "pending",
            "created_at": datetime.utcnow()
        }
    ]
    
    for app in test_applications:
        existing = await db.applications.find_one({"data.login": app["data"]["login"]})
        if not existing:
            await db.applications.insert_one(app)
            print(f"Created test application: {app['data']['nickname']}")
    
    print("Setup completed!")
    client.close()

if __name__ == "__main__":
    asyncio.run(setup_admin())