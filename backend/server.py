from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
import re
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Database setup
DATABASE_URL = f"mysql+pymysql://hesus:ba7a7m1ZX3.,@89.169.1.168:3306/swagmedia1?charset=utf8mb4"

# SQLAlchemy setup
Base = declarative_base()
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={"charset": "utf8mb4"}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    login = Column(String(100), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    nickname = Column(String(100), unique=True, nullable=False, index=True)
    vk_link = Column(String(255), nullable=False)
    channel_link = Column(String(255), nullable=False)
    balance = Column(Integer, default=0)
    admin_level = Column(Integer, default=0)
    is_approved = Column(Boolean, default=False)
    media_type = Column(Integer, default=0)
    warnings = Column(Integer, default=0)
    previews_used = Column(Integer, default=0)
    previews_limit = Column(Integer, default=3)
    blacklist_until = Column(DateTime, nullable=True)
    registration_ip = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Application(Base):
    __tablename__ = "applications"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    nickname = Column(String(100), nullable=False)
    login = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)
    vk_link = Column(String(255), nullable=False)
    channel_link = Column(String(255), nullable=False)
    registration_ip = Column(String(45), nullable=True)
    status = Column(String(20), default="pending")
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

class Purchase(Base):
    __tablename__ = "purchases"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    item_id = Column(String(36), nullable=False)
    quantity = Column(Integer, nullable=False)
    total_price = Column(Integer, nullable=False)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    admin_comment = Column(Text, nullable=True)

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    links = Column(JSON, nullable=False)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    admin_comment = Column(Text, nullable=True)

class UserRating(Base):
    __tablename__ = "user_ratings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    rated_user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

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
    media_user_id = Column(String(36), nullable=False)
    access_type = Column(String(20), nullable=False)
    accessed_at = Column(DateTime, default=datetime.utcnow)

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(20), default="info")
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Database initialization function
def init_database():
    """Initialize database tables and default data"""
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        
        # Create session to add default data
        db = SessionLocal()
        
        try:
            # Check if admin user exists
            admin_user = db.query(User).filter(User.login == "admin").first()
            if not admin_user:
                # Create default admin user
                admin_user = User(
                    id="admin-id-123",
                    login="admin",
                    password="admin123",
                    nickname="Administrator",
                    vk_link="https://vk.com/admin",
                    channel_link="https://t.me/admin",
                    balance=10000,
                    admin_level=1,
                    is_approved=True,
                    media_type=1
                )
                db.add(admin_user)
                print("✅ Admin user created (admin/admin123)")
            
            # Check if shop items exist
            shop_count = db.query(ShopItem).count()
            if shop_count == 0:
                # Create default shop items
                shop_items = [
                    ShopItem(id="1", name="VIP статус", description="Получите VIP статус на месяц", price=500, category="Премиум"),
                    ShopItem(id="2", name="Премиум аккаунт", description="Доступ к премиум функциям", price=1000, category="Премиум"),
                    ShopItem(id="3", name="Золотой значок", description="Эксклюзивный золотой значок", price=750, category="Премиум"),
                    ShopItem(id="4", name="Ускорение отчетов", description="Быстрая обработка ваших отчетов", price=300, category="Буст"),
                    ShopItem(id="5", name="Двойные медиа-коины", description="Удвоение получаемых MC на неделю", price=400, category="Буст"),
                    ShopItem(id="6", name="Приоритет в очереди", description="Приоритетная обработка заявок", price=350, category="Буст"),
                    ShopItem(id="7", name="Кастомная тема", description="Персональная тема интерфейса", price=600, category="Дизайн"),
                    ShopItem(id="8", name="Анимированный аватар", description="Возможность загрузки GIF аватара", price=450, category="Дизайн"),
                    ShopItem(id="9", name="Уникальная рамка", description="Эксклюзивная рамка профиля", price=550, category="Дизайн")
                ]
                
                for item in shop_items:
                    db.add(item)
                print("✅ Shop items created")
            
            db.commit()
            print("✅ Database initialized successfully")
            
        except Exception as e:
            print(f"❌ Error initializing data: {e}")
            db.rollback()
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# FastAPI setup
app = FastAPI(title="SwagMedia API", version="1.0.0")
api_router = APIRouter(prefix="/api")

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security
security = HTTPBearer()
JWT_SECRET = "swagmedia-secret-key-production-2025"
JWT_ALGORITHM = "HS256"

# Pydantic models
class RegistrationRequest(BaseModel):
    nickname: str
    login: str
    password: str
    vk_link: str
    channel_link: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Пароль должен содержать минимум 8 символов')
        return v
    
    @validator('vk_link')
    def validate_vk_link(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('VK ссылка должна начинаться с http:// или https://')
        if 'vk.com' not in v.lower():
            raise ValueError('Это должна быть ссылка на VK')
        return v
    
    @validator('channel_link')
    def validate_channel_link(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Ссылка на канал должна начинаться с http:// или https://')
        valid_domains = ['t.me', 'youtube.com', 'youtu.be', 'instagram.com']
        if not any(domain in v.lower() for domain in valid_domains):
            raise ValueError('Ссылка должна вести на Telegram, YouTube или Instagram')
        return v

class LoginRequest(BaseModel):
    login: str
    password: str

class ReportCreate(BaseModel):
    links: List[dict]
    
    @validator('links')
    def validate_links(cls, v):
        for link in v:
            url = link.get('url', '')
            if not url.startswith(('http://', 'https://')):
                raise ValueError('Все ссылки должны начинаться с http:// или https://')
        return v

class ApproveReportRequest(BaseModel):
    comment: str = ""
    mc_reward: Optional[int] = None

class MediaTypeChangeRequest(BaseModel):
    new_media_type: int
    admin_comment: Optional[str] = None

class WarningRequest(BaseModel):
    reason: str

class EmergencyStateRequest(BaseModel):
    days: int = Field(ge=1, le=365)
    reason: str

class RatingRequest(BaseModel):
    rated_user_id: str
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None

# Helper functions
def check_ip_blacklist(ip_address: str, db: Session):
    """Check if IP is blacklisted"""
    blacklist_entry = db.query(IPBlacklist).filter(
        IPBlacklist.ip_address == ip_address,
        IPBlacklist.blacklist_until > datetime.utcnow()
    ).first()
    return blacklist_entry is not None

def check_vk_blacklist(vk_link: str, db: Session):
    """Check if VK link is associated with blacklisted user"""
    user_with_vk = db.query(User).filter(
        User.vk_link == vk_link,
        User.blacklist_until.isnot(None),
        User.blacklist_until > datetime.utcnow()
    ).first()
    return user_with_vk is not None

def add_ip_to_blacklist(ip_address: str, vk_link: str, db: Session, days: int = 15, reason: str = "User exceeded preview limit"):
    """Add IP to blacklist for specified days"""
    # Check if IP is already blacklisted
    existing = db.query(IPBlacklist).filter(IPBlacklist.ip_address == ip_address).first()
    if existing:
        # Update existing record
        existing.blacklist_until = datetime.utcnow() + timedelta(days=days)
        existing.reason = reason
    else:
        # Create new record
        blacklist_entry = IPBlacklist(
            id=str(uuid.uuid4()),
            ip_address=ip_address,
            vk_link=vk_link,
            blacklist_until=datetime.utcnow() + timedelta(days=days),
            reason=reason
        )
        db.add(blacklist_entry)
    db.commit()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return {
            "id": user.id,
            "login": user.login,
            "nickname": user.nickname,
            "vk_link": user.vk_link,
            "channel_link": user.channel_link,
            "balance": user.balance,
            "admin_level": user.admin_level,
            "is_approved": user.is_approved,
            "media_type": user.media_type,
            "warnings": user.warnings,
            "previews_used": user.previews_used,
            "previews_limit": user.previews_limit,
            "blacklist_until": user.blacklist_until,
            "registration_ip": user.registration_ip,
            "created_at": user.created_at
        }
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user["admin_level"] < 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# API Routes
@api_router.post("/register")
@limiter.limit("10/hour")
async def register_user(request: Request, registration: RegistrationRequest, db: Session = Depends(get_db)):
    # Get client IP address
    client_ip = get_remote_address(request)
    
    # Check if IP is blacklisted
    if check_ip_blacklist(client_ip, db):
        raise HTTPException(
            status_code=403, 
            detail="Регистрация временно недоступна с вашего IP адреса"
        )
    
    # Check if VK link is associated with blacklisted account
    if check_vk_blacklist(registration.vk_link, db):
        raise HTTPException(
            status_code=403, 
            detail="Регистрация с данными VK временно недоступна"
        )
    
    # Check if login already exists
    existing_login = db.query(User).filter(User.login == registration.login).first()
    if existing_login:
        raise HTTPException(status_code=400, detail="Логин уже занят")
    
    # Check if nickname already exists
    existing_nickname = db.query(User).filter(User.nickname == registration.nickname).first()
    if existing_nickname:
        raise HTTPException(status_code=400, detail="Никнейм уже занят")
    
    # Create registration application
    application = Application(
        id=str(uuid.uuid4()),
        nickname=registration.nickname,
        login=registration.login,
        password=registration.password,
        vk_link=registration.vk_link,
        channel_link=registration.channel_link,
        registration_ip=client_ip
    )
    
    db.add(application)
    db.commit()
    
    return {"message": "Заявка на регистрацию отправлена! Ожидайте одобрения администратора."}

@api_router.post("/login")
@limiter.limit("30/hour")
async def login_user(request: Request, login_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.login == login_data.login).first()
    if not user or user.password != login_data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.is_approved:
        raise HTTPException(status_code=401, detail="Account not approved yet")
    
    # Check if user is blacklisted
    if user.blacklist_until and user.blacklist_until > datetime.utcnow():
        raise HTTPException(
            status_code=403,
            detail=f"Доступ заблокирован до {user.blacklist_until.strftime('%d.%m.%Y %H:%M')}"
        )
    
    token = jwt.encode({"user_id": user.id}, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return {
        "access_token": token, 
        "token_type": "bearer", 
        "user": {
            "id": user.id,
            "nickname": user.nickname,
            "admin_level": user.admin_level,
            "balance": user.balance,
            "media_type": user.media_type
        }
    }

@api_router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    return current_user

@api_router.get("/media-list")
async def get_media_list(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check if user is blacklisted
    if current_user.get("blacklist_until") and current_user["blacklist_until"] > datetime.utcnow():
        raise HTTPException(
            status_code=403,
            detail=f"Доступ заблокирован до {current_user['blacklist_until'].strftime('%d.%m.%Y %H:%M')}"
        )
    
    users = db.query(User).filter(User.is_approved == True).all()
    media_list = []
    
    for user in users:
        # Don't show blacklisted users
        if user.blacklist_until and user.blacklist_until > datetime.utcnow():
            continue
            
        media_list.append({
            "id": user.id,
            "nickname": user.nickname,
            "channel_link": user.channel_link,
            "vk_link": user.vk_link,
            "media_type": "Платное" if user.media_type == 1 else "Бесплатное",
            "can_access": user.media_type == 0 or current_user["media_type"] == 1
        })
    
    return media_list

@api_router.post("/media/{media_user_id}/access")
async def access_media(media_user_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check if user is blacklisted
    if current_user.get("blacklist_until") and current_user["blacklist_until"] > datetime.utcnow():
        raise HTTPException(
            status_code=403,
            detail=f"Доступ заблокирован до {current_user['blacklist_until'].strftime('%d.%m.%Y %H:%M')}"
        )
    
    # Get media user
    media_user = db.query(User).filter(User.id == media_user_id).first()
    if not media_user or not media_user.is_approved:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # If media is free, allow full access
    if media_user.media_type == 0:
        access_record = MediaAccess(
            id=str(uuid.uuid4()),
            user_id=current_user["id"],
            media_user_id=media_user_id,
            access_type="full"
        )
        db.add(access_record)
        db.commit()
        
        return {
            "access_type": "full",
            "message": "Полный доступ к бесплатному медиа",
            "data": {
                "nickname": media_user.nickname,
                "channel_link": media_user.channel_link,
                "vk_link": media_user.vk_link
            }
        }
    
    # If user has paid access, allow full access
    if current_user["media_type"] == 1:
        access_record = MediaAccess(
            id=str(uuid.uuid4()),
            user_id=current_user["id"],
            media_user_id=media_user_id,
            access_type="full"
        )
        db.add(access_record)
        db.commit()
        
        return {
            "access_type": "full",
            "message": "Полный доступ для платного пользователя",
            "data": {
                "nickname": media_user.nickname,
                "channel_link": media_user.channel_link,
                "vk_link": media_user.vk_link
            }
        }
    
    # For free users accessing paid media - use preview system
    user_obj = db.query(User).filter(User.id == current_user["id"]).first()
    
    if user_obj.previews_used >= user_obj.previews_limit:
        # User has exceeded preview limit - trigger blacklist
        user_obj.blacklist_until = datetime.utcnow() + timedelta(days=15)
        user_obj.is_approved = False
        
        # Add IP to blacklist if available
        if user_obj.registration_ip:
            add_ip_to_blacklist(
                user_obj.registration_ip,
                user_obj.vk_link,
                db,
                days=15,
                reason="Превышен лимит предварительных просмотров"
            )
        
        db.commit()
        
        raise HTTPException(
            status_code=403,
            detail="Лимит предварительных просмотров исчерпан. Доступ заблокирован на 15 дней."
        )
    
    # Increment preview counter
    user_obj.previews_used += 1
    
    # Log preview access
    access_record = MediaAccess(
        id=str(uuid.uuid4()),
        user_id=current_user["id"],
        media_user_id=media_user_id,
        access_type="preview"
    )
    db.add(access_record)
    db.commit()
    
    previews_remaining = user_obj.previews_limit - user_obj.previews_used
    
    return {
        "access_type": "preview",
        "message": f"Предварительный просмотр. Осталось: {previews_remaining}/3",
        "previews_remaining": previews_remaining,
        "data": {
            "nickname": media_user.nickname,
            "channel_link": media_user.channel_link[:20] + "..." if len(media_user.channel_link) > 20 else media_user.channel_link,
            "vk_link": media_user.vk_link[:20] + "..." if len(media_user.vk_link) > 20 else media_user.vk_link,
            "preview_note": "Это предварительный просмотр. Для полного доступа приобретите платный аккаунт."
        }
    }

@api_router.get("/user/previews")
async def get_user_previews(current_user: dict = Depends(get_current_user)):
    return {
        "previews_used": current_user.get("previews_used", 0),
        "preview_limit": current_user.get("previews_limit", 3),
        "previews_remaining": max(0, current_user.get("previews_limit", 3) - current_user.get("previews_used", 0)),
        "is_blacklisted": current_user.get("blacklist_until") and current_user["blacklist_until"] > datetime.utcnow(),
        "blacklist_until": current_user["blacklist_until"].isoformat() if current_user.get("blacklist_until") else None
    }

# Shop endpoints
@api_router.get("/shop/items")
async def get_shop_items(db: Session = Depends(get_db)):
    items = db.query(ShopItem).all()
    return [{
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "category": item.category,
        "image_url": item.image_url
    } for item in items]

# Reports endpoints
@api_router.post("/reports")
@limiter.limit("50/day")
async def submit_report(request: Request, report_data: ReportCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    report = Report(
        id=str(uuid.uuid4()),
        user_id=current_user["id"],
        links=report_data.links
    )
    
    db.add(report)
    db.commit()
    
    return {"message": "Report submitted successfully"}

@api_router.get("/reports/my")
async def get_my_reports(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    reports = db.query(Report).filter(Report.user_id == current_user["id"]).all()
    return [{
        "id": report.id,
        "links": report.links,
        "status": report.status,
        "created_at": report.created_at,
        "admin_comment": report.admin_comment
    } for report in reports]

@api_router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """Получить профиль текущего пользователя"""
    return {
        "id": current_user["id"],
        "login": current_user["login"],
        "nickname": current_user["nickname"],
        "vk_link": current_user["vk_link"],
        "channel_link": current_user["channel_link"],
        "balance": current_user["balance"],
        "admin_level": current_user["admin_level"],
        "is_approved": current_user["is_approved"],
        "media_type": current_user["media_type"],
        "warnings": current_user["warnings"],
        "previews_used": current_user["previews_used"],
        "previews_limit": current_user["previews_limit"],
        "blacklist_until": current_user["blacklist_until"],
        "registration_ip": current_user["registration_ip"]
    }

@api_router.get("/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Получить общую статистику платформы"""
    try:
        total_users = db.query(User).count()
        approved_users = db.query(User).filter(User.is_approved == True).count()
        total_reports = db.query(Report).count()
        approved_reports = db.query(Report).filter(Report.status == "approved").count()
        
        return {
            "total_users": total_users,
            "approved_users": approved_users,
            "pending_users": total_users - approved_users,
            "total_reports": total_reports,
            "approved_reports": approved_reports,
            "pending_reports": total_reports - approved_reports
        }
    except Exception as e:
        # В случае ошибки возвращаем дефолтные значения
        return {
            "total_users": 0,
            "approved_users": 0,
            "pending_users": 0,
            "total_reports": 0,
            "approved_reports": 0,
            "pending_reports": 0
        }

# Admin endpoints
@api_router.get("/admin/applications")
async def get_applications(admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    applications = db.query(Application).all()
    return [{
        "id": app.id,
        "nickname": app.nickname,
        "login": app.login,
        "vk_link": app.vk_link,
        "channel_link": app.channel_link,
        "status": app.status,
        "created_at": app.created_at
    } for app in applications]

@api_router.post("/admin/applications/{app_id}/approve")
async def approve_application(app_id: str, media_type: int = 0, admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if application.status != "pending":
        raise HTTPException(status_code=400, detail="Application already processed")
    
    # Create user
    user = User(
        id=str(uuid.uuid4()),
        login=application.login,
        password=application.password,
        nickname=application.nickname,
        vk_link=application.vk_link,
        channel_link=application.channel_link,
        is_approved=True,
        media_type=media_type,
        registration_ip=application.registration_ip
    )
    
    db.add(user)
    
    # Update application status
    application.status = "approved"
    
    db.commit()
    
    return {"message": "Application approved"}

@api_router.post("/admin/applications/{app_id}/reject")
async def reject_application(app_id: str, admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    application.status = "rejected"
    db.commit()
    
    return {"message": "Application rejected"}

@api_router.get("/admin/users")
async def get_all_users(admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{
        "id": user.id,
        "login": user.login,
        "nickname": user.nickname,
        "vk_link": user.vk_link,
        "channel_link": user.channel_link,
        "balance": user.balance,
        "admin_level": user.admin_level,
        "is_approved": user.is_approved,
        "media_type": user.media_type,
        "warnings": user.warnings,
        "previews_used": user.previews_used,
        "blacklist_until": user.blacklist_until,
        "created_at": user.created_at
    } for user in users]

@api_router.get("/admin/reports")
async def get_all_reports(admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    reports = db.query(Report).all()
    result = []
    
    for report in reports:
        user = db.query(User).filter(User.id == report.user_id).first()
        result.append({
            "id": report.id,
            "user_id": report.user_id,
            "user_nickname": user.nickname if user else "Unknown",
            "links": report.links,
            "status": report.status,
            "created_at": report.created_at,
            "admin_comment": report.admin_comment
        })
    
    return result

@api_router.post("/admin/reports/{report_id}/approve")
async def approve_report(report_id: str, report_data: ApproveReportRequest, admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    # Get the report
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Calculate MC reward
    if report_data.mc_reward is not None:
        mc_reward = report_data.mc_reward
    else:
        # Default calculation based on total views
        total_views = sum(link.get("views", 0) for link in report.links)
        mc_reward = max(10, total_views // 100)  # At least 10 MC, 1 MC per 100 views
    
    # Update report status
    report.status = "approved"
    report.admin_comment = report_data.comment
    
    # Add MC to user balance
    user = db.query(User).filter(User.id == report.user_id).first()
    if user:
        user.balance += mc_reward
    
    db.commit()
    
    return {"message": f"Отчет одобрен и {mc_reward} MC добавлено на баланс пользователя"}

@api_router.post("/admin/users/{user_id}/balance")
async def update_user_balance(user_id: str, amount: int, admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.balance += amount
    db.commit()
    
    return {"message": f"Balance updated by {amount} MC"}

@api_router.post("/admin/users/{user_id}/change-media-type")
async def change_user_media_type(user_id: str, media_type_data: MediaTypeChangeRequest, admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    old_type = user.media_type
    new_type = media_type_data.new_media_type
    
    # Update user media type
    user.media_type = new_type
    
    # Create notification
    notification = Notification(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title="Изменен тип медиа",
        message=f"Ваш статус медиа изменен с {'Платное' if old_type == 1 else 'Бесплатное'} на {'Платное' if new_type == 1 else 'Бесплатное'}",
        type="info"
    )
    
    db.add(notification)
    db.commit()
    
    type_names = {0: "Бесплатное", 1: "Платное"}
    return {
        "message": f"Тип медиа пользователя {user.nickname} изменен с '{type_names[old_type]}' на '{type_names[new_type]}'. Пользователь уведомлен."
    }

@api_router.get("/notifications")
async def get_notifications(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    notifications = db.query(Notification).filter(Notification.user_id == current_user["id"]).order_by(Notification.created_at.desc()).limit(50).all()
    return [{
        "id": notification.id,
        "title": notification.title,
        "message": notification.message,
        "type": notification.type,
        "read": notification.read,
        "created_at": notification.created_at
    } for notification in notifications]

@api_router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user["id"]
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.read = True
    db.commit()
    
    return {"message": "Notification marked as read"}

@api_router.post("/admin/users/{user_id}/warning")
async def give_user_warning(user_id: str, warning_data: WarningRequest, admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    """Выдать предупреждение пользователю"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Увеличиваем счетчик предупреждений
    user.warnings += 1
    current_warnings = user.warnings
    
    # Проверяем, нужно ли автоматически заблокировать при 3-х предупреждениях
    auto_blocked = False
    if current_warnings >= 3:
        # Автоматическая блокировка на 30 дней при 3-х предупреждениях
        user.blacklist_until = datetime.utcnow() + timedelta(days=30)
        user.is_approved = False
        auto_blocked = True
        
        # Добавляем IP в черный список, если есть
        if user.registration_ip:
            add_ip_to_blacklist(user.registration_ip, user.vk_link, db, days=30, reason="3 warnings")
    
    # Create notification for user
    if auto_blocked:
        notification_message = f"Warning issued. Reason: {warning_data.reason}. Total warnings: {current_warnings}. ATTENTION: Account automatically blocked for 30 days due to exceeding warning limit (3/3)."
        notification_title = "BLOCKED FOR WARNINGS"
        notification_type = "error"
    else:
        notification_message = f"Warning issued. Reason: {warning_data.reason}. Total warnings: {current_warnings}/3. Account will be automatically blocked upon receiving 3rd warning."
        notification_title = "Warning"
        notification_type = "warning"
    
    notification = Notification(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title=notification_title,
        message=notification_message,
        type=notification_type
    )
    db.add(notification)
    
    db.commit()
    
    return {
        "message": f"Предупреждение выдано пользователю {user.nickname}",
        "warnings_count": current_warnings,
        "reason": warning_data.reason,
        "auto_blocked": auto_blocked,
        "blocked_until": user.blacklist_until.isoformat() if auto_blocked else None
    }

@api_router.get("/admin/blacklist")
async def get_blacklist(admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    # Get IP blacklist
    ip_blacklist = db.query(IPBlacklist).all()
    
    # Get blacklisted users
    blacklisted_users = db.query(User).filter(
        User.blacklist_until.isnot(None),
        User.blacklist_until > datetime.utcnow()
    ).all()
    
    return {
        "ip_blacklist": [{
            "id": entry.id,
            "ip_address": entry.ip_address,
            "vk_link": entry.vk_link,
            "blacklist_until": entry.blacklist_until,
            "reason": entry.reason,
            "created_at": entry.created_at
        } for entry in ip_blacklist],
        "blacklisted_users": [{
            "id": user.id,
            "nickname": user.nickname,
            "vk_link": user.vk_link,
            "blacklist_until": user.blacklist_until,
            "warnings": user.warnings,
            "previews_used": user.previews_used,
            "registration_ip": user.registration_ip
        } for user in blacklisted_users]
    }

@api_router.post("/admin/users/{user_id}/reset-previews")
async def reset_user_previews(user_id: str, admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.previews_used = 0
    db.commit()
    
    return {"message": "Предварительные просмотры сброшены"}

@api_router.post("/admin/users/{user_id}/unblacklist")
async def unblacklist_user(user_id: str, admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Разблокировать пользователя
    user.blacklist_until = None
    user.is_approved = True
    
    # Удалить IP из черного списка если есть
    if user.registration_ip:
        db.query(IPBlacklist).filter(IPBlacklist.ip_address == user.registration_ip).delete()
    
    db.commit()
    
    return {"message": "Пользователь разблокирован"}

@api_router.post("/admin/users/{user_id}/emergency-state")
async def set_emergency_state(user_id: str, emergency_data: EmergencyStateRequest, admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    """Выдать ЧС (чрезвычайное состояние) - блокировка IP на регистрацию и вход"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Устанавливаем срок блокировки
    blacklist_until = datetime.utcnow() + timedelta(days=emergency_data.days)
    
    # Блокируем пользователя
    user.blacklist_until = blacklist_until
    user.is_approved = False
    
    # Добавляем IP в черный список, если есть
    if user.registration_ip:
        add_ip_to_blacklist(
            user.registration_ip,
            user.vk_link,
            db,
            days=emergency_data.days,
            reason=f"ES: {emergency_data.reason}"
        )
    
    # Create notification for user
    notification = Notification(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title="EMERGENCY STATE",
        message=f"Emergency state imposed on your account for {emergency_data.days} days. Reason: {emergency_data.reason}. Login and registration from your IP blocked until {blacklist_until.strftime('%d.%m.%Y %H:%M')}",
        type="error"
    )
    db.add(notification)
    
    db.commit()
    
    return {
        "message": f"ЧС выдано пользователю '{user.nickname}' на {emergency_data.days} дней",
        "user_id": user_id,
        "blocked_until": blacklist_until.isoformat(),
        "reason": emergency_data.reason,
        "ip_blocked": user.registration_ip is not None,
        "blocked_ip": user.registration_ip
    }

@api_router.post("/admin/users/{user_id}/remove-from-media")
async def remove_user_from_media(user_id: str, admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    """Снять с медиа - полное удаление пользователя из БД"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_nickname = user.nickname
    
    # Удаляем все связанные данные пользователя
    # Удаляем рейтинги пользователя (как выставленные, так и полученные)
    db.query(UserRating).filter(
        (UserRating.user_id == user_id) | (UserRating.rated_user_id == user_id)
    ).delete()
    
    # Удаляем записи доступа к медиа
    db.query(MediaAccess).filter(
        (MediaAccess.user_id == user_id) | (MediaAccess.media_user_id == user_id)
    ).delete()
    
    # Удаляем уведомления
    db.query(Notification).filter(Notification.user_id == user_id).delete()
    
    # Удаляем отчеты
    db.query(Report).filter(Report.user_id == user_id).delete()
    
    # Удаляем покупки
    db.query(Purchase).filter(Purchase.user_id == user_id).delete()
    
    # Удаляем заявки (если есть)
    db.query(Application).filter(Application.login == user.login).delete()
    
    # Наконец удаляем самого пользователя
    db.delete(user)
    
    db.commit()
    
    return {
        "message": f"Пользователь '{user_nickname}' полностью удален из системы",
        "removed_user_id": user_id
    }

# Rating System Endpoints
@api_router.post("/ratings")
@limiter.limit("100/day")
async def rate_user(request: Request, rating_data: RatingRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check if user already rated this user
    existing_rating = db.query(UserRating).filter(
        UserRating.user_id == current_user["id"],
        UserRating.rated_user_id == rating_data.rated_user_id
    ).first()
    
    if existing_rating:
        # Update existing rating
        existing_rating.rating = rating_data.rating
        existing_rating.comment = rating_data.comment
        existing_rating.created_at = datetime.utcnow()
        db.commit()
        return {"message": "Rating updated successfully"}
    else:
        # Create new rating
        rating = UserRating(
            id=str(uuid.uuid4()),
            user_id=current_user["id"],
            rated_user_id=rating_data.rated_user_id,
            rating=rating_data.rating,
            comment=rating_data.comment
        )
        db.add(rating)
        db.commit()
        return {"message": "Rating submitted successfully"}

@api_router.get("/ratings/{user_id}")
async def get_user_ratings(user_id: str, db: Session = Depends(get_db)):
    ratings = db.query(UserRating).filter(UserRating.rated_user_id == user_id).all()
    
    rating_list = []
    for rating in ratings:
        # Get user who gave the rating
        rater = db.query(User).filter(User.id == rating.user_id).first()
        rating_list.append({
            "id": rating.id,
            "user_id": rating.user_id,
            "user_nickname": rater.nickname if rater else "Unknown",
            "rating": rating.rating,
            "comment": rating.comment,
            "created_at": rating.created_at
        })
    
    # Calculate average rating
    if rating_list:
        avg_rating = sum(r["rating"] for r in rating_list) / len(rating_list)
        return {
            "ratings": rating_list,
            "average_rating": round(avg_rating, 2),
            "total_ratings": len(rating_list)
        }
    else:
        return {
            "ratings": [],
            "average_rating": 0,
            "total_ratings": 0
        }

@api_router.get("/leaderboard")
async def get_leaderboard(db: Session = Depends(get_db)):
    # Get ratings with user data using raw SQL for better performance
    from sqlalchemy import text
    
    query = text("""
        SELECT ur.rated_user_id, u.nickname, u.media_type, u.channel_link, 
               AVG(ur.rating) as avg_rating, COUNT(ur.rating) as total_ratings
        FROM user_ratings ur 
        JOIN users u ON ur.rated_user_id = u.id 
        WHERE u.is_approved = 1 
        GROUP BY ur.rated_user_id 
        HAVING COUNT(ur.rating) >= 1 
        ORDER BY avg_rating DESC 
        LIMIT 50
    """)
    
    result = db.execute(query)
    leaderboard = []
    
    for row in result:
        leaderboard.append({
            "user_id": row[0],
            "nickname": row[1],
            "media_type": row[2],
            "channel_link": row[5] if len(row) > 5 else "",
            "avg_rating": round(float(row[4]), 2),
            "total_ratings": row[5] if len(row) > 5 else row[4]
        })
    
    return leaderboard

# Initialize shop items endpoint (for admin use)
@api_router.post("/admin/init-shop")
async def init_shop(admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    # Check if items already exist
    existing_count = db.query(ShopItem).count()
    if existing_count > 0:
        return {"message": "Shop already initialized"}
    
    shop_items = [
        {"id": "1", "name": "VIP статус", "description": "Получите VIP статус на месяц с дополнительными привилегиями", "price": 500, "category": "Премиум"},
        {"id": "2", "name": "Премиум аккаунт", "description": "Расширенные возможности и приоритетная поддержка", "price": 1000, "category": "Премиум"},
        {"id": "3", "name": "Золотой значок", "description": "Эксклюзивный золотой значок для вашего профиля", "price": 300, "category": "Премиум"},
        {"id": "4", "name": "Ускорение отчетов", "description": "Быстрое одобрение ваших отчетов в течение 24 часов", "price": 200, "category": "Буст"},
        {"id": "5", "name": "Двойные медиа-коины", "description": "Получайте в 2 раза больше медиа-коинов за отчеты на неделю", "price": 400, "category": "Буст"},
        {"id": "6", "name": "Приоритет в очереди", "description": "Ваши заявки обрабатываются в первую очередь", "price": 150, "category": "Буст"},
        {"id": "7", "name": "Кастомная тема", "description": "Персональная цветовая схема для вашего профиля", "price": 250, "category": "Дизайн"},
        {"id": "8", "name": "Анимированный аватар", "description": "Возможность использовать GIF в качестве аватара", "price": 350, "category": "Дизайн"},
        {"id": "9", "name": "Уникальная рамка", "description": "Красивая рамка вокруг вашего профиля", "price": 180, "category": "Дизайн"},
    ]
    
    for item_data in shop_items:
        item = ShopItem(**item_data)
        db.add(item)
    
    db.commit()
    
    return {"message": "Shop initialized with items"}

@api_router.get("/admin/shop/items")
async def get_admin_shop_items(admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    items = db.query(ShopItem).all()
    return [{
        "id": item.id,
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "category": item.category,
        "image_url": item.image_url,
        "created_at": item.created_at
    } for item in items]

@api_router.post("/admin/shop/item/{item_id}/image")
async def update_shop_item_image(item_id: str, image_data: dict, admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    image_url = image_data.get("image_url", "")
    
    # Validate URL if provided
    if image_url and not image_url.startswith(('http://', 'https://')):
        raise HTTPException(status_code=400, detail="Изображение должно быть валидной HTTP/HTTPS ссылкой")
    
    # Update shop item
    item = db.query(ShopItem).filter(ShopItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    item.image_url = image_url
    db.commit()
    
    return {"message": "Изображение товара обновлено"}

# Health check endpoint
@api_router.get("/health")
async def health_check():
    return {"status": "ok", "message": "SwagMedia API is running"}

# Include the router in the main app
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    print("🚀 Initializing SwagMedia database...")
    init_database()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)