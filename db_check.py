#!/usr/bin/env python3
"""
Direct database connection test to check the current state
"""

import pymysql
import json
from datetime import datetime

# Database connection
DATABASE_CONFIG = {
    'host': '89.169.1.168',
    'port': 3306,
    'user': 'hesus',
    'password': 'ba7a7m1ZX3.,',
    'database': 'swagmedia1',
    'charset': 'utf8mb4'
}

def check_database():
    try:
        # Connect to database
        connection = pymysql.connect(**DATABASE_CONFIG)
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        print("✅ Connected to MySQL database successfully")
        
        # Check tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"📊 Found {len(tables)} tables:")
        for table in tables:
            table_name = list(table.values())[0]
            cursor.execute(f"SELECT COUNT(*) as count FROM {table_name}")
            count = cursor.fetchone()['count']
            print(f"  - {table_name}: {count} records")
        
        # Check users table specifically
        print("\n👥 Users table content:")
        cursor.execute("SELECT id, login, nickname, admin_level, is_approved, created_at FROM users LIMIT 10")
        users = cursor.fetchall()
        
        if users:
            for user in users:
                print(f"  - {user['login']} ({user['nickname']}) - Admin: {user['admin_level']} - Approved: {user['is_approved']}")
        else:
            print("  No users found")
        
        # Check applications table
        print("\n📝 Applications table content:")
        cursor.execute("SELECT id, login, nickname, status, created_at FROM applications ORDER BY created_at DESC LIMIT 10")
        applications = cursor.fetchall()
        
        if applications:
            for app in applications:
                print(f"  - {app['login']} ({app['nickname']}) - Status: {app['status']} - Created: {app['created_at']}")
        else:
            print("  No applications found")
        
        # Try to create admin user if not exists
        cursor.execute("SELECT * FROM users WHERE login = 'admin'")
        admin_user = cursor.fetchone()
        
        if not admin_user:
            print("\n🔧 Creating admin user...")
            try:
                cursor.execute("""
                    INSERT INTO users (id, login, password, nickname, vk_link, channel_link, 
                                     balance, admin_level, is_approved, media_type, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    'admin-id-123',
                    'admin',
                    'admin123',
                    'Administrator',
                    'https://vk.com/admin',
                    'https://t.me/admin',
                    10000,
                    1,
                    True,
                    1,
                    datetime.now()
                ))
                connection.commit()
                print("✅ Admin user created successfully")
            except Exception as e:
                print(f"❌ Failed to create admin user: {e}")
        else:
            print(f"\n👤 Admin user exists: {admin_user['login']} - Password: {admin_user['password']}")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

if __name__ == "__main__":
    check_database()