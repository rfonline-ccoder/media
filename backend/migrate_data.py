#!/usr/bin/env python3
"""
Скрипт миграции данных из MongoDB в MySQL
"""

import asyncio
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Application, ShopItem, Purchase, Report, UserRating, IPBlacklist, MediaAccess, Notification

# MongoDB connection
MONGO_URL = "mongodb://localhost:27017"
MONGO_DB = "swagmedia"

# MySQL connection
MYSQL_URL = "mysql+pymysql://root:@localhost:3306/swagmedia_sql"

class DataMigrator:
    def __init__(self):
        # MongoDB setup
        self.mongo_client = AsyncIOMotorClient(MONGO_URL)
        self.mongo_db = self.mongo_client[MONGO_DB]
        
        # MySQL setup
        self.mysql_engine = create_engine(MYSQL_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.mysql_engine)
    
    async def migrate_users(self):
        """Migrate users from MongoDB to MySQL"""
        print("Migrating users...")
        users = await self.mongo_db.users.find().to_list(None)
        
        session = self.SessionLocal()
        try:
            migrated_count = 0
            for user_doc in users:
                # Convert MongoDB document to SQLAlchemy model
                user = User(
                    id=user_doc.get("id"),
                    login=user_doc.get("login"),
                    password=user_doc.get("password"),
                    nickname=user_doc.get("nickname"),
                    vk_link=user_doc.get("vk_link"),
                    channel_link=user_doc.get("channel_link"),
                    balance=user_doc.get("balance", 0),
                    admin_level=user_doc.get("admin_level", 0),
                    is_approved=user_doc.get("is_approved", False),
                    media_type=user_doc.get("media_type", 0),
                    warnings=user_doc.get("warnings", 0),
                    previews_used=user_doc.get("previews_used", 0),
                    previews_limit=user_doc.get("previews_limit", 3),
                    blacklist_until=user_doc.get("blacklist_until"),
                    registration_ip=user_doc.get("registration_ip"),
                    created_at=user_doc.get("created_at", datetime.utcnow())
                )
                
                session.merge(user)  # Use merge to handle duplicates
                migrated_count += 1
            
            session.commit()
            print(f"Successfully migrated {migrated_count} users")
            
        except Exception as e:
            session.rollback()
            print(f"Error migrating users: {e}")
        finally:
            session.close()
    
    async def migrate_applications(self):
        """Migrate applications from MongoDB to MySQL"""
        print("Migrating applications...")
        applications = await self.mongo_db.applications.find().to_list(None)
        
        session = self.SessionLocal()
        try:
            migrated_count = 0
            for app_doc in applications:
                application = Application(
                    id=app_doc.get("id"),
                    nickname=app_doc.get("nickname"),
                    login=app_doc.get("login"),
                    password=app_doc.get("password"),
                    vk_link=app_doc.get("vk_link"),
                    channel_link=app_doc.get("channel_link"),
                    status=app_doc.get("status", "pending"),
                    created_at=app_doc.get("created_at", datetime.utcnow())
                )
                
                session.merge(application)
                migrated_count += 1
            
            session.commit()
            print(f"Successfully migrated {migrated_count} applications")
            
        except Exception as e:
            session.rollback()
            print(f"Error migrating applications: {e}")
        finally:
            session.close()
    
    async def migrate_shop_items(self):
        """Migrate shop items from MongoDB to MySQL"""
        print("Migrating shop items...")
        shop_items = await self.mongo_db.shop_items.find().to_list(None)
        
        session = self.SessionLocal()
        try:
            migrated_count = 0
            for item_doc in shop_items:
                shop_item = ShopItem(
                    id=item_doc.get("id"),
                    name=item_doc.get("name"),
                    description=item_doc.get("description"),
                    price=item_doc.get("price"),
                    category=item_doc.get("category"),
                    image_url=item_doc.get("image_url"),
                    created_at=item_doc.get("created_at", datetime.utcnow())
                )
                
                session.merge(shop_item)
                migrated_count += 1
            
            session.commit()
            print(f"Successfully migrated {migrated_count} shop items")
            
        except Exception as e:
            session.rollback()
            print(f"Error migrating shop items: {e}")
        finally:
            session.close()
    
    async def migrate_purchases(self):
        """Migrate purchases from MongoDB to MySQL"""
        print("Migrating purchases...")
        purchases = await self.mongo_db.purchases.find().to_list(None)
        
        session = self.SessionLocal()
        try:
            migrated_count = 0
            for purchase_doc in purchases:
                purchase = Purchase(
                    id=purchase_doc.get("id"),
                    user_id=purchase_doc.get("user_id"),
                    item_id=purchase_doc.get("item_id"),
                    quantity=purchase_doc.get("quantity"),
                    total_price=purchase_doc.get("total_price"),
                    status=purchase_doc.get("status", "pending"),
                    created_at=purchase_doc.get("created_at", datetime.utcnow()),
                    reviewed_at=purchase_doc.get("reviewed_at"),
                    admin_comment=purchase_doc.get("admin_comment")
                )
                
                session.merge(purchase)
                migrated_count += 1
            
            session.commit()
            print(f"Successfully migrated {migrated_count} purchases")
            
        except Exception as e:
            session.rollback()
            print(f"Error migrating purchases: {e}")
        finally:
            session.close()
    
    async def migrate_reports(self):
        """Migrate reports from MongoDB to MySQL"""
        print("Migrating reports...")
        reports = await self.mongo_db.reports.find().to_list(None)
        
        session = self.SessionLocal()
        try:
            migrated_count = 0
            for report_doc in reports:
                report = Report(
                    id=report_doc.get("id"),
                    user_id=report_doc.get("user_id"),
                    links=report_doc.get("links"),
                    status=report_doc.get("status", "pending"),
                    created_at=report_doc.get("created_at", datetime.utcnow()),
                    admin_comment=report_doc.get("admin_comment")
                )
                
                session.merge(report)
                migrated_count += 1
            
            session.commit()
            print(f"Successfully migrated {migrated_count} reports")
            
        except Exception as e:
            session.rollback()
            print(f"Error migrating reports: {e}")
        finally:
            session.close()
    
    async def migrate_user_ratings(self):
        """Migrate user ratings from MongoDB to MySQL"""
        print("Migrating user ratings...")
        ratings = await self.mongo_db.user_ratings.find().to_list(None)
        
        session = self.SessionLocal()
        try:
            migrated_count = 0
            for rating_doc in ratings:
                rating = UserRating(
                    id=rating_doc.get("id"),
                    user_id=rating_doc.get("user_id"),
                    rated_user_id=rating_doc.get("rated_user_id"),
                    rating=rating_doc.get("rating"),
                    comment=rating_doc.get("comment"),
                    created_at=rating_doc.get("created_at", datetime.utcnow())
                )
                
                session.merge(rating)
                migrated_count += 1
            
            session.commit()
            print(f"Successfully migrated {migrated_count} user ratings")
            
        except Exception as e:
            session.rollback()
            print(f"Error migrating user ratings: {e}")
        finally:
            session.close()
    
    async def migrate_ip_blacklist(self):
        """Migrate IP blacklist from MongoDB to MySQL"""
        print("Migrating IP blacklist...")
        blacklist = await self.mongo_db.ip_blacklist.find().to_list(None)
        
        session = self.SessionLocal()
        try:
            migrated_count = 0
            for bl_doc in blacklist:
                ip_blacklist = IPBlacklist(
                    id=bl_doc.get("id"),
                    ip_address=bl_doc.get("ip_address"),
                    vk_link=bl_doc.get("vk_link"),
                    blacklist_until=bl_doc.get("blacklist_until"),
                    reason=bl_doc.get("reason", "User exceeded preview limit"),
                    created_at=bl_doc.get("created_at", datetime.utcnow())
                )
                
                session.merge(ip_blacklist)
                migrated_count += 1
            
            session.commit()
            print(f"Successfully migrated {migrated_count} IP blacklist entries")
            
        except Exception as e:
            session.rollback()
            print(f"Error migrating IP blacklist: {e}")
        finally:
            session.close()
    
    async def migrate_media_access(self):
        """Migrate media access from MongoDB to MySQL"""
        print("Migrating media access...")
        media_access = await self.mongo_db.media_access.find().to_list(None)
        
        session = self.SessionLocal()
        try:
            migrated_count = 0
            for ma_doc in media_access:
                media_acc = MediaAccess(
                    id=ma_doc.get("id"),
                    user_id=ma_doc.get("user_id"),
                    media_user_id=ma_doc.get("media_user_id"),
                    access_type=ma_doc.get("access_type"),
                    accessed_at=ma_doc.get("accessed_at", datetime.utcnow())
                )
                
                session.merge(media_acc)
                migrated_count += 1
            
            session.commit()
            print(f"Successfully migrated {migrated_count} media access entries")
            
        except Exception as e:
            session.rollback()
            print(f"Error migrating media access: {e}")
        finally:
            session.close()
    
    async def migrate_notifications(self):
        """Migrate notifications from MongoDB to MySQL"""
        print("Migrating notifications...")
        notifications = await self.mongo_db.notifications.find().to_list(None)
        
        session = self.SessionLocal()
        try:
            migrated_count = 0
            for notif_doc in notifications:
                notification = Notification(
                    id=notif_doc.get("id"),
                    user_id=notif_doc.get("user_id"),
                    title=notif_doc.get("title"),
                    message=notif_doc.get("message"),
                    type=notif_doc.get("type", "info"),
                    read=notif_doc.get("read", False),
                    created_at=notif_doc.get("created_at", datetime.utcnow())
                )
                
                session.merge(notification)
                migrated_count += 1
            
            session.commit()
            print(f"Successfully migrated {migrated_count} notifications")
            
        except Exception as e:
            session.rollback()
            print(f"Error migrating notifications: {e}")
        finally:
            session.close()
    
    async def run_migration(self):
        """Run the complete migration process"""
        print("Starting data migration from MongoDB to MySQL...")
        print(f"MongoDB: {MONGO_URL}/{MONGO_DB}")
        print(f"MySQL: {MYSQL_URL}")
        print("="*50)
        
        try:
            # Check MongoDB collections
            collections = await self.mongo_db.list_collection_names()
            print(f"Available MongoDB collections: {collections}")
            
            # Migrate each collection
            await self.migrate_users()
            await self.migrate_applications()
            await self.migrate_shop_items()
            await self.migrate_purchases()
            await self.migrate_reports()
            await self.migrate_user_ratings()
            await self.migrate_ip_blacklist()
            await self.migrate_media_access()
            await self.migrate_notifications()
            
            print("="*50)
            print("Migration completed successfully!")
            
        except Exception as e:
            print(f"Migration failed: {e}")
        finally:
            self.mongo_client.close()
            self.mysql_engine.dispose()

async def main():
    migrator = DataMigrator()
    await migrator.run_migration()

if __name__ == "__main__":
    asyncio.run(main())