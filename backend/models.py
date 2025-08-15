from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
import uuid
import os

Base = declarative_base()

# Database URL for MySQL
DATABASE_URL = f"mysql+pymysql://root:@localhost:3306/swagmedia_sql"

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    login = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)  # Plain text as per original requirement
    nickname = Column(String(100), unique=True, nullable=False, index=True)
    vk_link = Column(String(255), nullable=False)
    channel_link = Column(String(255), nullable=False)
    balance = Column(Integer, default=0)
    admin_level = Column(Integer, default=0)
    is_approved = Column(Boolean, default=False)
    media_type = Column(Integer, default=0)  # 0 = free, 1 = paid
    warnings = Column(Integer, default=0)
    previews_used = Column(Integer, default=0)  # Number of previews used
    previews_limit = Column(Integer, default=3)  # Maximum previews allowed
    blacklist_until = Column(DateTime, nullable=True)  # Blacklist expiration date
    registration_ip = Column(String(45), nullable=True)  # IP address used for registration
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    purchases = relationship("Purchase", back_populates="user")
    reports = relationship("Report", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    media_accesses = relationship("MediaAccess", back_populates="user")
    ratings_given = relationship("UserRating", foreign_keys="[UserRating.user_id]", back_populates="user")
    ratings_received = relationship("UserRating", foreign_keys="[UserRating.rated_user_id]", back_populates="rated_user")

class Application(Base):
    __tablename__ = "applications"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nickname = Column(String(100), nullable=False)
    login = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)
    vk_link = Column(String(255), nullable=False)
    channel_link = Column(String(255), nullable=False)
    status = Column(String(20), default="pending")  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)

class ShopItem(Base):
    __tablename__ = "shop_items"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    price = Column(Integer, nullable=False)
    category = Column(String(100), nullable=False)
    image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    purchases = relationship("Purchase", back_populates="item")

class Purchase(Base):
    __tablename__ = "purchases"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    item_id = Column(String(36), ForeignKey("shop_items.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    total_price = Column(Integer, nullable=False)
    status = Column(String(20), default="pending")  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    admin_comment = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="purchases")
    item = relationship("ShopItem", back_populates="purchases")

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    links = Column(JSON, nullable=False)  # JSON field for links array
    status = Column(String(20), default="pending")  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    admin_comment = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="reports")

class UserRating(Base):
    __tablename__ = "user_ratings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    rated_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="ratings_given")
    rated_user = relationship("User", foreign_keys=[rated_user_id], back_populates="ratings_received")

class IPBlacklist(Base):
    __tablename__ = "ip_blacklist"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    ip_address = Column(String(45), nullable=False, index=True)
    vk_link = Column(String(255), nullable=False)
    blacklist_until = Column(DateTime, nullable=False)
    reason = Column(String(255), default="User exceeded preview limit")
    created_at = Column(DateTime, default=datetime.utcnow)

class MediaAccess(Base):
    __tablename__ = "media_access"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    media_user_id = Column(String(36), nullable=False)  # User whose media is being accessed
    access_type = Column(String(20), nullable=False)  # "preview" or "full"
    accessed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="media_accesses")

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(20), default="info")  # info, warning, error, success
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="notifications")

# Database initialization
def create_engine_instance():
    """Create SQLAlchemy engine with proper configuration"""
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # Set to True for SQL debugging
        pool_pre_ping=True,
        pool_recycle=3600
    )
    return engine

def get_session_maker():
    """Get session maker for database operations"""
    engine = create_engine_instance()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all database tables"""
    engine = create_engine_instance()
    Base.metadata.create_all(bind=engine)
    print("All database tables created successfully!")

if __name__ == "__main__":
    # Create tables when running this file directly
    create_tables()