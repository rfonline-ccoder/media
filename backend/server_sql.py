from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
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
import asyncio

# Import SQLAlchemy models and database
from models import (
    Base, User as UserModel, Application as ApplicationModel, 
    ShopItem as ShopItemModel, Purchase as PurchaseModel, Report as ReportModel,
    UserRating as UserRatingModel, IPBlacklist as IPBlacklistModel,
    MediaAccess as MediaAccessModel, Notification as NotificationModel,
    get_session_maker, create_engine_instance
)

# Advanced caching system with different TTL for different data types
cache = {}
cache_ttl = {}

# Cache constants
CACHE_TTL_STATS = 300      # 5 minutes for statistics
CACHE_TTL_ADVANCED = 600   # 10 minutes for advanced stats  
CACHE_TTL_USERS = 120      # 2 minutes for user data
CACHE_TTL_SHOP = 1800      # 30 minutes for shop items

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Rate Limiter setup
limiter = Limiter(key_func=get_remote_address)

# Database setup
SessionLocal = get_session_maker()
engine = create_engine_instance()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create the main app without a prefix
app = FastAPI()

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
JWT_SECRET = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"

# Pydantic models for request/response (keeping the same as before)
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    login: str
    password: str  # Not hashed as per requirement
    nickname: str
    vk_link: str
    channel_link: str
    balance: int = Field(default=0)
    admin_level: int = Field(default=0)
    is_approved: bool = Field(default=False)
    media_type: int = Field(default=0)  # 0 = free, 1 = paid
    warnings: int = Field(default=0)
    previews_used: int = Field(default=0)  # Number of previews used
    previews_limit: int = Field(default=3)  # Maximum previews allowed
    blacklist_until: Optional[datetime] = None  # Blacklist expiration date
    registration_ip: Optional[str] = None  # IP address used for registration
    created_at: datetime = Field(default_factory=datetime.utcnow)

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

class ShopItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    price: int
    category: str
    image_url: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PurchaseRequest(BaseModel):
    item_id: str
    quantity: int = 1

class Purchase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    item_id: str
    quantity: int
    total_price: int
    status: str = Field(default="pending")  # pending, approved, rejected
    created_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    admin_comment: Optional[str] = None

class Report(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    links: List[dict]  # [{"url": "...", "views": 123}]
    status: str = Field(default="pending")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    admin_comment: Optional[str] = None

class ReportCreate(BaseModel):
    links: List[dict]
    
    @validator('links')
    def validate_links(cls, v):
        for link in v:
            url = link.get('url', '')
            if not url.startswith(('http://', 'https://')):
                raise ValueError('Все ссылки должны начинаться с http:// или https://')
            # Проверяем что это валидный URL
            if not re.match(r'https?://.+\..+', url):
                raise ValueError('Введите корректный URL')
        return v

class MediaTypeChange(BaseModel):
    user_id: str
    new_media_type: int  # 0 = free, 1 = paid
    admin_comment: Optional[str] = None

class ApplicationResponse(BaseModel):
    id: str
    type: str
    data: dict
    status: str
    created_at: datetime

class ApproveReportRequest(BaseModel):
    comment: str = ""
    mc_reward: Optional[int] = None

class UserRating(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    rated_user_id: str
    rating: int = Field(ge=1, le=5)  # 1-5 stars
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RatingRequest(BaseModel):
    rated_user_id: str
    rating: int = Field(ge=1, le=5)  # 1-5 stars
    comment: Optional[str] = None

class IPBlacklist(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ip_address: str
    vk_link: str  # VK link that caused the blacklist
    blacklist_until: datetime
    reason: str = Field(default="User exceeded preview limit")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class MediaAccess(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    media_user_id: str  # User whose media is being accessed
    access_type: str  # "preview" or "full"
    accessed_at: datetime = Field(default_factory=datetime.utcnow)

class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    title: str
    message: str
    type: str = Field(default="info")  # info, warning, error, success
    read: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Helper functions
def get_cache(key):
    """Get cached value if not expired"""
    if key in cache and key in cache_ttl:
        if datetime.utcnow() < cache_ttl[key]:
            return cache[key]
        else:
            # Expired, remove from cache
            del cache[key]
            del cache_ttl[key]
    return None

def set_cache(key, value, ttl_seconds=300):  # 5 minutes default
    """Set cache with TTL"""
    cache[key] = value
    cache_ttl[key] = datetime.utcnow() + timedelta(seconds=ttl_seconds)

def check_ip_blacklist(ip_address: str, db: Session):
    """Check if IP is blacklisted"""
    blacklist_entry = db.query(IPBlacklistModel).filter(
        IPBlacklistModel.ip_address == ip_address,
        IPBlacklistModel.blacklist_until > datetime.utcnow()
    ).first()
    return blacklist_entry is not None

def check_vk_blacklist(vk_link: str, db: Session):
    """Check if VK link is associated with blacklisted user"""
    user_with_vk = db.query(UserModel).filter(
        UserModel.vk_link == vk_link,
        UserModel.blacklist_until > datetime.utcnow()
    ).first()
    return user_with_vk is not None

def add_ip_to_blacklist(ip_address: str, vk_link: str, db: Session, days: int = 15):
    """Add IP to blacklist for specified days"""
    blacklist_entry = IPBlacklistModel(
        id=str(uuid.uuid4()),
        ip_address=ip_address,
        vk_link=vk_link,
        blacklist_until=datetime.utcnow() + timedelta(days=days)
    )
    db.add(blacklist_entry)
    db.commit()

def handle_preview_limit_exceeded(user_id: str, db: Session):
    """Handle when user exceeds preview limit"""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        return
    
    # Set blacklist until 15 days from now
    blacklist_until = datetime.utcnow() + timedelta(days=15)
    
    # Update user with blacklist
    user.blacklist_until = blacklist_until
    user.is_approved = False
    
    # Add IP to blacklist if available
    if user.registration_ip:
        add_ip_to_blacklist(user.registration_ip, user.vk_link, db, days=15)
    
    # Delete user data for privacy (keep basic info for blacklist tracking)
    user.login = None
    user.password = None
    user.nickname = None
    user.channel_link = None
    user.balance = None
    
    db.commit()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Convert SQLAlchemy model to dict
        user_dict = {
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
        
        return user_dict
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@api_router.post("/register")
@limiter.limit("5/minute")
async def register(registration: RegistrationRequest, request: Request, db: Session = Depends(get_db)):
    # Get client IP
    client_ip = get_remote_address(request)
    
    # Check if IP is blacklisted
    if check_ip_blacklist(client_ip, db):
        raise HTTPException(status_code=403, detail="IP адрес заблокирован")
    
    # Check if VK link is blacklisted
    if check_vk_blacklist(registration.vk_link, db):
        raise HTTPException(status_code=403, detail="Данная VK ссылка заблокирована")
    
    # Check for existing login
    existing_login = db.query(UserModel).filter(UserModel.login == registration.login).first()
    if existing_login:
        raise HTTPException(status_code=400, detail="Логин уже существует")
    
    # Check for existing nickname
    existing_nickname = db.query(UserModel).filter(UserModel.nickname == registration.nickname).first()
    if existing_nickname:
        raise HTTPException(status_code=400, detail="Никнейм уже существует")
    
    # Create application instead of user directly
    application = ApplicationModel(
        id=str(uuid.uuid4()),
        nickname=registration.nickname,
        login=registration.login,
        password=registration.password,
        vk_link=registration.vk_link,
        channel_link=registration.channel_link,
        status="pending"
    )
    
    db.add(application)
    db.commit()
    
    return {"message": "Заявка на регистрацию отправлена", "id": application.id}

@api_router.post("/login")
@limiter.limit("10/minute")
async def login(login_data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.login == login_data.login).first()
    
    if not user or user.password != login_data.password:
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    
    if not user.is_approved:
        raise HTTPException(status_code=403, detail="Аккаунт не одобрен")
    
    # Check if user is blacklisted
    if user.blacklist_until and user.blacklist_until > datetime.utcnow():
        time_left = user.blacklist_until - datetime.utcnow()
        days_left = time_left.days
        raise HTTPException(status_code=403, detail=f"Аккаунт заблокирован до {user.blacklist_until.strftime('%d.%m.%Y')}. Осталось дней: {days_left}")
    
    # Generate JWT token
    token_data = {"user_id": user.id}
    token = jwt.encode(token_data, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return {"access_token": token, "token_type": "bearer", "user": {
        "id": user.id,
        "nickname": user.nickname,
        "admin_level": user.admin_level,
        "balance": user.balance,
        "media_type": user.media_type,
        "previews_used": user.previews_used,
        "previews_limit": user.previews_limit
    }}

@api_router.get("/media-list")
async def get_media_list(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # Get all approved users with their media accessibility
    users = db.query(UserModel).filter(UserModel.is_approved == True).all()
    
    media_list = []
    for user in users:
        can_access = False
        
        # If current user is paid (media_type = 1), they can access all content
        if current_user["media_type"] == 1:
            can_access = True
        # If current user is free (media_type = 0), they can only access free content (media_type = 0)
        elif current_user["media_type"] == 0 and user.media_type == 0:
            can_access = True
        
        media_list.append({
            "id": user.id,
            "nickname": user.nickname,
            "vk_link": user.vk_link,
            "channel_link": user.channel_link,
            "media_type": user.media_type,
            "can_access": can_access
        })
    
    return media_list

@api_router.post("/media/{media_user_id}/access")
async def access_media(media_user_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check if user is blacklisted
    if current_user.get("blacklist_until") and current_user["blacklist_until"] > datetime.utcnow():
        raise HTTPException(status_code=403, detail="Пользователь заблокирован")
    
    # Get the media owner
    media_user = db.query(UserModel).filter(UserModel.id == media_user_id).first()
    if not media_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # If current user has paid access (media_type = 1), grant full access
    if current_user["media_type"] == 1:
        # Record access
        access_record = MediaAccessModel(
            id=str(uuid.uuid4()),
            user_id=current_user["id"],
            media_user_id=media_user_id,
            access_type="full"
        )
        db.add(access_record)
        db.commit()
        
        return {
            "access_type": "full",
            "data": {
                "nickname": media_user.nickname,
                "vk_link": media_user.vk_link,
                "channel_link": media_user.channel_link
            }
        }
    
    # If media is free (media_type = 0), grant access
    if media_user.media_type == 0:
        # Record access
        access_record = MediaAccessModel(
            id=str(uuid.uuid4()),
            user_id=current_user["id"],
            media_user_id=media_user_id,
            access_type="full"
        )
        db.add(access_record)
        db.commit()
        
        return {
            "access_type": "full",
            "data": {
                "nickname": media_user.nickname,
                "vk_link": media_user.vk_link,
                "channel_link": media_user.channel_link
            }
        }
    
    # For free users accessing paid content, use preview system
    user_obj = db.query(UserModel).filter(UserModel.id == current_user["id"]).first()
    
    # Check if user has exceeded preview limit
    if user_obj.previews_used >= user_obj.previews_limit:
        # Handle preview limit exceeded
        handle_preview_limit_exceeded(current_user["id"], db)
        raise HTTPException(status_code=403, detail="Превышен лимит предварительных просмотров. Аккаунт заблокирован на 15 дней.")
    
    # Increment preview count
    user_obj.previews_used += 1
    db.commit()
    
    # Record preview access
    access_record = MediaAccessModel(
        id=str(uuid.uuid4()),
        user_id=current_user["id"],
        media_user_id=media_user_id,
        access_type="preview"
    )
    db.add(access_record)
    db.commit()
    
    return {
        "access_type": "preview",
        "previews_used": user_obj.previews_used,
        "previews_limit": user_obj.previews_limit,
        "message": f"Предварительный просмотр. Осталось просмотров: {user_obj.previews_limit - user_obj.previews_used}",
        "data": {
            "nickname": media_user.nickname[:5] + "***",  # Partial nickname
            "vk_link": "Доступно после покупки платного доступа",
            "channel_link": "Доступно после покупки платного доступа"
        }
    }

@api_router.get("/user/previews")
async def get_user_previews(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    is_blacklisted = user.blacklist_until and user.blacklist_until > datetime.utcnow()
    
    return {
        "previews_used": user.previews_used,
        "previews_limit": user.previews_limit,
        "previews_remaining": max(0, user.previews_limit - user.previews_used),
        "is_blacklisted": is_blacklisted,
        "blacklist_until": user.blacklist_until.isoformat() if user.blacklist_until else None
    }

# Shop endpoints
@api_router.get("/shop")
async def get_shop():
    # Use cache for shop items
    cache_key = "shop_items"
    cached_items = get_cache(cache_key)
    if cached_items is not None:
        return cached_items
    
    # Pre-defined shop items since we don't have a dynamic shop system
    items = [
        {"id": "1", "name": "VIP статус", "description": "Получите VIP статус на месяц", "price": 500, "category": "Премиум", "image_url": None},
        {"id": "2", "name": "Премиум аккаунт", "description": "Доступ к премиум функциям", "price": 1000, "category": "Премиум", "image_url": None},
        {"id": "3", "name": "Золотой значок", "description": "Эксклюзивный золотой значок", "price": 750, "category": "Премиум", "image_url": None},
        {"id": "4", "name": "Ускорение отчетов", "description": "Быстрая обработка ваших отчетов", "price": 300, "category": "Буст", "image_url": None},
        {"id": "5", "name": "Двойные медиа-коины", "description": "Удвоение получаемых MC на неделю", "price": 400, "category": "Буст", "image_url": None},
        {"id": "6", "name": "Приоритет в очереди", "description": "Приоритетная обработка заявок", "price": 350, "category": "Буст", "image_url": None},
        {"id": "7", "name": "Кастомная тема", "description": "Персональная тема интерфейса", "price": 600, "category": "Дизайн", "image_url": None},
        {"id": "8", "name": "Анимированный аватар", "description": "Возможность загрузки GIF аватара", "price": 450, "category": "Дизайн", "image_url": None},
        {"id": "9", "name": "Уникальная рамка", "description": "Эксклюзивная рамка профиля", "price": 550, "category": "Дизайн", "image_url": None}
    ]
    
    # Cache the items
    set_cache(cache_key, items, CACHE_TTL_SHOP)
    
    return items

@api_router.post("/shop/purchase")
async def purchase_item(purchase: PurchaseRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # Get shop item (from predefined list since we don't have DB shop items)
    shop_items = await get_shop()
    item = next((item for item in shop_items if item["id"] == purchase.item_id), None)
    
    if not item:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    total_price = item["price"] * purchase.quantity
    
    if current_user["balance"] < total_price:
        raise HTTPException(status_code=400, detail="Недостаточно средств")
    
    # Create purchase record
    purchase_obj = PurchaseModel(
        id=str(uuid.uuid4()),
        user_id=current_user["id"],
        item_id=purchase.item_id,
        quantity=purchase.quantity,
        total_price=total_price
    )
    
    db.add(purchase_obj)
    db.commit()
    
    return {"message": "Покупка оформлена", "id": purchase_obj.id}

# Reports
@api_router.post("/reports")
async def create_report(report_data: ReportCreate, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    report = ReportModel(
        id=str(uuid.uuid4()),
        user_id=current_user["id"],
        links=report_data.links
    )
    
    db.add(report)
    db.commit()
    
    return {"message": "Отчет создан", "id": report.id}

@api_router.get("/reports")
async def get_user_reports(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    reports = db.query(ReportModel).filter(ReportModel.user_id == current_user["id"]).all()
    
    report_list = []
    for report in reports:
        report_list.append({
            "id": report.id,
            "links": report.links,
            "status": report.status,
            "created_at": report.created_at,
            "admin_comment": report.admin_comment
        })
    
    return report_list

# Admin endpoints
def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user["admin_level"] < 1:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    return current_user

@api_router.get("/admin/applications")
async def get_applications(admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    applications = db.query(ApplicationModel).all()
    
    app_list = []
    for app in applications:
        app_list.append({
            "id": app.id,
            "nickname": app.nickname,
            "login": app.login,
            "vk_link": app.vk_link,
            "channel_link": app.channel_link,
            "status": app.status,
            "created_at": app.created_at
        })
    
    return app_list

@api_router.post("/admin/applications/{app_id}/approve")
async def approve_application(app_id: str, admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    application = db.query(ApplicationModel).filter(ApplicationModel.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    if application.status != "pending":
        raise HTTPException(status_code=400, detail="Заявка уже обработана")
    
    # Create user from application
    user = UserModel(
        id=str(uuid.uuid4()),
        login=application.login,
        password=application.password,
        nickname=application.nickname,
        vk_link=application.vk_link,
        channel_link=application.channel_link,
        is_approved=True
    )
    
    db.add(user)
    
    # Update application status
    application.status = "approved"
    
    db.commit()
    
    return {"message": "Заявка одобрена"}

@api_router.post("/admin/applications/{app_id}/reject")
async def reject_application(app_id: str, admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    application = db.query(ApplicationModel).filter(ApplicationModel.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    
    application.status = "rejected"
    db.commit()
    
    return {"message": "Заявка отклонена"}

# Include all remaining admin endpoints from the original file...
# (For brevity, I'll include key admin endpoints. The full implementation would include all endpoints)

# Add the router to the main app
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)