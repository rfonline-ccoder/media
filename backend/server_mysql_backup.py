from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
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

# Pydantic models for request/response
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

class ItemImageUpdate(BaseModel):
    image_url: str
    
    @validator('image_url')
    def validate_image_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL изображения должен начинаться с http:// или https://')
        return v

class WarningRequest(BaseModel):
    reason: str

class EmergencyStateRequest(BaseModel):
    days: int = Field(ge=1, le=365)  # От 1 до 365 дней
    reason: str

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

def require_admin(current_user: dict = Depends(get_current_user)):
    if current_user["admin_level"] < 1:
        raise HTTPException(status_code=403, detail="Доступ запрещен")
    return current_user

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth Routes
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

# Media Routes
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

# Ratings
@api_router.post("/ratings")
async def create_rating(rating_data: RatingRequest, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check if user exists
    rated_user = db.query(UserModel).filter(UserModel.id == rating_data.rated_user_id).first()
    if not rated_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Check if user already rated this user
    existing_rating = db.query(UserRatingModel).filter(
        UserRatingModel.user_id == current_user["id"],
        UserRatingModel.rated_user_id == rating_data.rated_user_id
    ).first()
    
    if existing_rating:
        # Update existing rating
        existing_rating.rating = rating_data.rating
        existing_rating.comment = rating_data.comment
    else:
        # Create new rating
        rating = UserRatingModel(
            id=str(uuid.uuid4()),
            user_id=current_user["id"],
            rated_user_id=rating_data.rated_user_id,
            rating=rating_data.rating,
            comment=rating_data.comment
        )
        db.add(rating)
    
    db.commit()
    return {"message": "Рейтинг сохранен"}

@api_router.get("/ratings")
async def get_ratings(db: Session = Depends(get_db)):
    # Get all users with their average ratings
    users = db.query(UserModel).filter(UserModel.is_approved == True).all()
    
    ratings_data = []
    for user in users:
        # Get average rating for this user
        avg_rating = db.query(func.avg(UserRatingModel.rating)).filter(
            UserRatingModel.rated_user_id == user.id
        ).scalar()
        
        # Get rating count
        rating_count = db.query(func.count(UserRatingModel.id)).filter(
            UserRatingModel.rated_user_id == user.id
        ).scalar()
        
        # Get latest ratings with comments
        latest_ratings = db.query(UserRatingModel).filter(
            UserRatingModel.rated_user_id == user.id,
            UserRatingModel.comment.isnot(None)
        ).order_by(UserRatingModel.created_at.desc()).limit(3).all()
        
        ratings_list = []
        for rating in latest_ratings:
            rater = db.query(UserModel).filter(UserModel.id == rating.user_id).first()
            ratings_list.append({
                "rating": rating.rating,
                "comment": rating.comment,
                "rater_nickname": rater.nickname if rater else "Удаленный пользователь",
                "created_at": rating.created_at
            })
        
        ratings_data.append({
            "id": user.id,
            "nickname": user.nickname,
            "balance": user.balance,
            "average_rating": float(avg_rating) if avg_rating else 0,
            "rating_count": rating_count or 0,
            "latest_ratings": ratings_list
        })
    
    # Sort by average rating descending
    ratings_data.sort(key=lambda x: x["average_rating"], reverse=True)
    
    return ratings_data

# Notifications
@api_router.get("/notifications")
async def get_notifications(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    notifications = db.query(NotificationModel).filter(
        NotificationModel.user_id == current_user["id"]
    ).order_by(NotificationModel.created_at.desc()).all()
    
    notif_list = []
    for notif in notifications:
        notif_list.append({
            "id": notif.id,
            "title": notif.title,
            "message": notif.message,
            "type": notif.type,
            "read": notif.read,
            "created_at": notif.created_at
        })
    
    return notif_list

@api_router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    notification = db.query(NotificationModel).filter(
        NotificationModel.id == notification_id,
        NotificationModel.user_id == current_user["id"]
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Уведомление не найдено")
    
    notification.read = True
    db.commit()
    
    return {"message": "Уведомление отмечено как прочитанное"}

# Admin endpoints
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

@api_router.get("/admin/purchases")
async def get_purchases(admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    purchases = db.query(PurchaseModel).all()
    
    purchase_list = []
    for purchase in purchases:
        user = db.query(UserModel).filter(UserModel.id == purchase.user_id).first()
        # Get item from predefined list
        shop_items = await get_shop()
        item = next((item for item in shop_items if item["id"] == purchase.item_id), None)
        
        purchase_list.append({
            "id": purchase.id,
            "user_nickname": user.nickname if user else "Удаленный пользователь",
            "item_name": item["name"] if item else "Удаленный товар",
            "quantity": purchase.quantity,
            "total_price": purchase.total_price,
            "status": purchase.status,
            "created_at": purchase.created_at
        })
    
    return purchase_list

@api_router.get("/admin/reports")
async def get_all_reports(admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    reports = db.query(ReportModel).all()
    
    report_list = []
    for report in reports:
        user = db.query(UserModel).filter(UserModel.id == report.user_id).first()
        report_list.append({
            "id": report.id,
            "user_nickname": user.nickname if user else "Удаленный пользователь",
            "links": report.links,
            "status": report.status,
            "created_at": report.created_at,
            "admin_comment": report.admin_comment
        })
    
    return report_list

@api_router.post("/admin/reports/{report_id}/approve")
async def approve_report(report_id: str, approve_data: ApproveReportRequest, admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    report = db.query(ReportModel).filter(ReportModel.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Отчет не найден")
    
    # Calculate MC reward
    if approve_data.mc_reward is not None:
        mc_reward = approve_data.mc_reward
    else:
        # Automatic calculation based on views
        total_views = sum(link.get("views", 0) for link in report.links)
        mc_reward = min(total_views // 100 * 10, 500)  # 10 MC per 100 views, max 500
    
    # Update user balance
    user = db.query(UserModel).filter(UserModel.id == report.user_id).first()
    if user:
        user.balance += mc_reward
    
    # Update report
    report.status = "approved"
    report.admin_comment = approve_data.comment
    
    # Create notification
    notification = NotificationModel(
        id=str(uuid.uuid4()),
        user_id=report.user_id,
        title="Отчет одобрен",
        message=f"Ваш отчет одобрен. Начислено {mc_reward} MC.",
        type="success"
    )
    db.add(notification)
    
    db.commit()
    
    return {"message": "Отчет одобрен", "mc_reward": mc_reward}

@api_router.post("/admin/reports/{report_id}/reject")
async def reject_report(report_id: str, comment: str, admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    report = db.query(ReportModel).filter(ReportModel.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Отчет не найден")
    
    report.status = "rejected"
    report.admin_comment = comment
    
    # Create notification
    notification = NotificationModel(
        id=str(uuid.uuid4()),
        user_id=report.user_id,
        title="Отчет отклонен",
        message=f"Ваш отчет отклонен. Причина: {comment}",
        type="error"
    )
    db.add(notification)
    
    db.commit()
    
    return {"message": "Отчет отклонен"}

@api_router.get("/admin/users")
async def get_users(admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    users = db.query(UserModel).all()
    
    user_list = []
    for user in users:
        user_list.append({
            "id": user.id,
            "nickname": user.nickname,
            "login": user.login,
            "balance": user.balance,
            "admin_level": user.admin_level,
            "is_approved": user.is_approved,
            "media_type": user.media_type,
            "warnings": user.warnings,
            "previews_used": user.previews_used,
            "previews_limit": user.previews_limit,
            "blacklist_until": user.blacklist_until,
            "created_at": user.created_at
        })
    
    return user_list

@api_router.post("/admin/users/{user_id}/change-media-type")
async def change_user_media_type(user_id: str, change_data: MediaTypeChange, admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    old_type = "Бесплатное" if user.media_type == 0 else "Платное"
    new_type = "Бесплатное" if change_data.new_media_type == 0 else "Платное"
    
    user.media_type = change_data.new_media_type
    
    # Create notification
    notification = NotificationModel(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title="Изменен тип медиа",
        message=f"Ваш тип медиа изменен с '{old_type}' на '{new_type}'. {change_data.admin_comment or ''}",
        type="info"
    )
    db.add(notification)
    
    db.commit()
    
    return {"message": f"Тип медиа изменен с '{old_type}' на '{new_type}'"}

@api_router.get("/admin/blacklist")
async def get_blacklist(admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    # Get blacklisted users
    blacklisted_users = db.query(UserModel).filter(
        UserModel.blacklist_until > datetime.utcnow()
    ).all()
    
    # Get blacklisted IPs
    blacklisted_ips = db.query(IPBlacklistModel).filter(
        IPBlacklistModel.blacklist_until > datetime.utcnow()
    ).all()
    
    users_data = []
    for user in blacklisted_users:
        users_data.append({
            "id": user.id,
            "nickname": user.nickname or "Удален",
            "vk_link": user.vk_link or "Удален",
            "blacklist_until": user.blacklist_until,
            "previews_used": user.previews_used,
            "previews_limit": user.previews_limit,
            "type": "user"
        })
    
    ips_data = []
    for ip in blacklisted_ips:
        ips_data.append({
            "id": ip.id,
            "ip_address": ip.ip_address,
            "vk_link": ip.vk_link,
            "blacklist_until": ip.blacklist_until,
            "reason": ip.reason,
            "created_at": ip.created_at,
            "type": "ip"
        })
    
    return {
        "blacklisted_users": users_data,
        "blacklisted_ips": ips_data
    }

@api_router.post("/admin/users/{user_id}/reset-previews")
async def reset_user_previews(user_id: str, admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    user.previews_used = 0
    db.commit()
    
    return {"message": "Счетчик предварительных просмотров сброшен"}

@api_router.post("/admin/users/{user_id}/unblacklist")
async def unblacklist_user(user_id: str, admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    user.blacklist_until = None
    user.is_approved = True
    db.commit()
    
    return {"message": "Пользователь разблокирован"}

@api_router.get("/admin/shop/items")
async def get_admin_shop_items(admin_user: dict = Depends(require_admin)):
    # Return the predefined shop items for admin management
    return await get_shop()

@api_router.post("/admin/shop/item/{item_id}/image")
async def update_shop_item_image(item_id: str, image_data: ItemImageUpdate, admin_user: dict = Depends(require_admin)):
    # For now, we'll just validate the request since shop items are predefined
    # In a real implementation, you would update the database
    return {"message": f"Изображение для товара {item_id} обновлено", "image_url": image_data.image_url}

# Новые функции для администрирования

@api_router.post("/admin/users/{user_id}/warning")
async def give_user_warning(user_id: str, warning_data: WarningRequest, admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    """Выдать предупреждение пользователю"""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Увеличиваем счетчик предупреждений
    user.warnings += 1
    
    # Создаем уведомление пользователю
    notification = NotificationModel(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title="⚠️ Предупреждение",
        message=f"Вам выдано предупреждение. Причина: {warning_data.reason}. Всего предупреждений: {user.warnings}",
        type="warning"
    )
    db.add(notification)
    
    db.commit()
    
    return {
        "message": f"Предупреждение выдано пользователю {user.nickname}", 
        "warnings_count": user.warnings,
        "reason": warning_data.reason
    }

@api_router.post("/admin/users/{user_id}/remove-from-media")
async def remove_user_from_media(user_id: str, admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    """Снять с медиа - полное удаление пользователя из БД"""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    user_nickname = user.nickname
    
    # Удаляем все связанные данные пользователя
    # Удаляем рейтинги пользователя (как выставленные, так и полученные)
    db.query(UserRatingModel).filter(
        (UserRatingModel.user_id == user_id) | (UserRatingModel.rated_user_id == user_id)
    ).delete()
    
    # Удаляем записи доступа к медиа
    db.query(MediaAccessModel).filter(
        (MediaAccessModel.user_id == user_id) | (MediaAccessModel.media_user_id == user_id)
    ).delete()
    
    # Удаляем уведомления
    db.query(NotificationModel).filter(NotificationModel.user_id == user_id).delete()
    
    # Удаляем отчеты
    db.query(ReportModel).filter(ReportModel.user_id == user_id).delete()
    
    # Удаляем покупки
    db.query(PurchaseModel).filter(PurchaseModel.user_id == user_id).delete()
    
    # Удаляем заявки (если есть)
    db.query(ApplicationModel).filter(ApplicationModel.login == user.login).delete()
    
    # Наконец удаляем самого пользователя
    db.delete(user)
    
    db.commit()
    
    return {
        "message": f"Пользователь '{user_nickname}' полностью удален из системы",
        "removed_user_id": user_id
    }

@api_router.post("/admin/users/{user_id}/emergency-state")
async def set_emergency_state(user_id: str, emergency_data: EmergencyStateRequest, admin_user: dict = Depends(require_admin), db: Session = Depends(get_db)):
    """Выдать ЧС (чрезвычайное состояние) - блокировка IP на регистрацию и вход"""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    user_nickname = user.nickname
    user_ip = user.registration_ip
    user_vk = user.vk_link
    
    # Устанавливаем срок блокировки
    blacklist_until = datetime.utcnow() + timedelta(days=emergency_data.days)
    
    # Блокируем пользователя
    user.blacklist_until = blacklist_until
    user.is_approved = False
    
    # Добавляем IP в черный список, если есть
    if user_ip:
        # Проверяем, нет ли уже такой записи
        existing_ip_blacklist = db.query(IPBlacklistModel).filter(
            IPBlacklistModel.ip_address == user_ip
        ).first()
        
        if existing_ip_blacklist:
            # Обновляем существующую запись
            existing_ip_blacklist.blacklist_until = blacklist_until
            existing_ip_blacklist.reason = f"ЧС: {emergency_data.reason}"
        else:
            # Создаем новую запись
            ip_blacklist = IPBlacklistModel(
                id=str(uuid.uuid4()),
                ip_address=user_ip,
                vk_link=user_vk,
                blacklist_until=blacklist_until,
                reason=f"ЧС: {emergency_data.reason}"
            )
            db.add(ip_blacklist)
    
    # Создаем уведомление пользователю
    notification = NotificationModel(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title="🚨 ЧРЕЗВЫЧАЙНОЕ СОСТОЯНИЕ",
        message=f"На ваш аккаунт наложено ЧС на {emergency_data.days} дней. Причина: {emergency_data.reason}. Вход и регистрация с вашего IP заблокированы до {blacklist_until.strftime('%d.%m.%Y %H:%M')}",
        type="error"
    )
    db.add(notification)
    
    db.commit()
    
    return {
        "message": f"ЧС выдано пользователю '{user_nickname}' на {emergency_data.days} дней",
        "user_id": user_id,
        "blocked_until": blacklist_until.isoformat(),
        "reason": emergency_data.reason,
        "ip_blocked": user_ip is not None,
        "blocked_ip": user_ip
    }

# Include the router
app.include_router(api_router)

# Initialize database tables on startup
@app.on_event("startup")
async def startup_event():
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)