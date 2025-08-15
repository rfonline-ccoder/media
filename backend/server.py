from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
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

# Simple in-memory cache
cache = {}
cache_ttl = {}

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Rate Limiter setup
limiter = Limiter(key_func=get_remote_address)

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client["swagmedia"]  # Using swagmedia database name

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

# Models
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
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        user = await db.users.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Remove MongoDB _id field to avoid serialization issues
        if "_id" in user:
            del user["_id"]
            
        return user
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Authentication endpoints
@api_router.post("/register")
@limiter.limit("5/minute")  # 5 registrations per minute
async def register(request: Request, registration: RegistrationRequest):
    # Check if login already exists
    existing_login = await db.users.find_one({"login": registration.login})
    if existing_login:
        raise HTTPException(status_code=400, detail="Логин уже занят")
    
    # Check if nickname already exists
    existing_nickname = await db.users.find_one({"nickname": registration.nickname})
    if existing_nickname:
        raise HTTPException(status_code=400, detail="Никнейм уже занят")
    
    # Create registration application
    application = {
        "id": str(uuid.uuid4()),
        "type": "registration",
        "data": registration.dict(),
        "status": "pending",
        "created_at": datetime.utcnow()
    }
    
    await db.applications.insert_one(application)
    return {"message": "Заявка на регистрацию отправлена! Ожидайте одобрения администратора."}

@api_router.post("/login")
@limiter.limit("10/minute")  # 10 login attempts per minute
async def login(request: Request, login_data: LoginRequest):
    user = await db.users.find_one({"login": login_data.login})
    if not user or user["password"] != login_data.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user["is_approved"]:
        raise HTTPException(status_code=401, detail="Account not approved yet")
    
    # Remove MongoDB _id field to avoid serialization issues
    if "_id" in user:
        del user["_id"]
    
    token = jwt.encode({"user_id": user["id"]}, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return {"access_token": token, "token_type": "bearer", "user": user}

# User endpoints
@api_router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    return current_user

@api_router.get("/media-list")
async def get_media_list():
    users = await db.users.find({"is_approved": True}).to_list(1000)
    media_list = []
    for user in users:
        media_list.append({
            "nickname": user["nickname"],
            "channel_link": user["channel_link"],
            "vk_link": user["vk_link"],
            "media_type": "Платное" if user["media_type"] == 1 else "Бесплатное"
        })
    return media_list

# Shop endpoints
@api_router.get("/shop/items")
async def get_shop_items():
    items = await db.shop_items.find().to_list(1000)
    # Remove MongoDB _id fields
    for item in items:
        if "_id" in item:
            del item["_id"]
    return items

@api_router.post("/shop/purchase")
async def purchase_item(purchase: PurchaseRequest, current_user: dict = Depends(get_current_user)):
    item = await db.shop_items.find_one({"id": purchase.item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    total_price = item["price"] * purchase.quantity
    
    # Create purchase request
    purchase_obj = Purchase(
        user_id=current_user["id"],
        item_id=purchase.item_id,
        quantity=purchase.quantity,
        total_price=total_price
    )
    
    await db.purchases.insert_one(purchase_obj.dict())
    return {"message": "Purchase request submitted for admin approval"}

# Reports endpoints
@api_router.post("/reports")
async def submit_report(report_data: ReportCreate, current_user: dict = Depends(get_current_user)):
    report = Report(
        user_id=current_user["id"],
        links=report_data.links
    )
    
    await db.reports.insert_one(report.dict())
    return {"message": "Report submitted successfully"}

@api_router.get("/reports/my")
async def get_my_reports(current_user: dict = Depends(get_current_user)):
    reports = await db.reports.find({"user_id": current_user["id"]}).to_list(1000)
    # Remove MongoDB _id fields
    for report in reports:
        if "_id" in report:
            del report["_id"]
    return reports

# Admin endpoints
@api_router.get("/admin/applications")
async def get_applications(current_user: dict = Depends(get_current_user)):
    if current_user["admin_level"] < 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    applications = await db.applications.find().to_list(1000)
    # Remove MongoDB _id fields
    for app in applications:
        if "_id" in app:
            del app["_id"]
    return applications

@api_router.post("/admin/applications/{app_id}/approve")
async def approve_application(app_id: str, media_type: int = 0, current_user: dict = Depends(get_current_user)):
    if current_user["admin_level"] < 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    application = await db.applications.find_one({"id": app_id})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    if application["type"] == "registration":
        # Create user
        user_data = application["data"]
        user = User(
            login=user_data["login"],
            password=user_data["password"],
            nickname=user_data["nickname"],
            vk_link=user_data["vk_link"],
            channel_link=user_data["channel_link"],
            is_approved=True,
            media_type=media_type
        )
        
        await db.users.insert_one(user.dict())
    
    # Update application status
    await db.applications.update_one(
        {"id": app_id},
        {"$set": {"status": "approved", "reviewed_at": datetime.utcnow()}}
    )
    
    return {"message": "Application approved"}

@api_router.post("/admin/applications/{app_id}/reject")
async def reject_application(app_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["admin_level"] < 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.applications.update_one(
        {"id": app_id},
        {"$set": {"status": "rejected", "reviewed_at": datetime.utcnow()}}
    )
    
    return {"message": "Application rejected"}

@api_router.get("/admin/purchases")
async def get_purchases(current_user: dict = Depends(get_current_user)):
    if current_user["admin_level"] < 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    purchases = await db.purchases.find().to_list(1000)
    # Remove MongoDB _id fields and enrich with user info
    for purchase in purchases:
        if "_id" in purchase:
            del purchase["_id"]
        user = await db.users.find_one({"id": purchase["user_id"]})
        purchase["user_nickname"] = user["nickname"] if user else "Unknown"
        item = await db.shop_items.find_one({"id": purchase["item_id"]})
        purchase["item_name"] = item["name"] if item else "Unknown"
    
    return purchases

@api_router.post("/admin/purchases/{purchase_id}/approve")
async def approve_purchase(purchase_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["admin_level"] < 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.purchases.update_one(
        {"id": purchase_id},
        {"$set": {"status": "approved", "reviewed_at": datetime.utcnow()}}
    )
    
    return {"message": "Purchase approved"}

@api_router.post("/admin/purchases/{purchase_id}/reject")
async def reject_purchase(purchase_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["admin_level"] < 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.purchases.update_one(
        {"id": purchase_id},
        {"$set": {"status": "rejected", "reviewed_at": datetime.utcnow()}}
    )
    
    return {"message": "Purchase rejected"}

@api_router.get("/admin/reports")
async def get_all_reports(current_user: dict = Depends(get_current_user)):
    if current_user["admin_level"] < 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    reports = await db.reports.find().to_list(1000)
    # Remove MongoDB _id fields and enrich with user info
    for report in reports:
        if "_id" in report:
            del report["_id"]
        user = await db.users.find_one({"id": report["user_id"]})
        report["user_nickname"] = user["nickname"] if user else "Unknown"
    
    return reports

@api_router.post("/admin/reports/{report_id}/approve")
async def approve_report(report_id: str, report_data: ApproveReportRequest, current_user: dict = Depends(get_current_user)):
    if current_user["admin_level"] < 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get the report
    report = await db.reports.find_one({"id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Calculate MC reward
    if report_data.mc_reward is not None:
        mc_reward = report_data.mc_reward
    else:
        # Default calculation based on total views
        total_views = sum(link.get("views", 0) for link in report.get("links", []))
        mc_reward = max(10, total_views // 100)  # At least 10 MC, 1 MC per 100 views
    
    # Update report status
    await db.reports.update_one(
        {"id": report_id},
        {"$set": {"status": "approved", "admin_comment": report_data.comment, "reviewed_at": datetime.utcnow()}}
    )
    
    # Add MC to user balance
    await db.users.update_one(
        {"id": report["user_id"]},
        {"$inc": {"balance": mc_reward}}
    )
    
    return {"message": f"Отчет одобрен и {mc_reward} MC добавлено на баланс пользователя"}

@api_router.get("/admin/users")
async def get_all_users(current_user: dict = Depends(get_current_user)):
    if current_user["admin_level"] < 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users = await db.users.find().to_list(1000)
    # Remove MongoDB _id fields
    for user in users:
        if "_id" in user:
            del user["_id"]
    return users

@api_router.post("/admin/users/{user_id}/balance")
async def update_user_balance(user_id: str, amount: int, current_user: dict = Depends(get_current_user)):
    if current_user["admin_level"] < 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    await db.users.update_one(
        {"id": user_id},
        {"$inc": {"balance": amount}}
    )
    
    return {"message": f"Balance updated by {amount} MC"}

@api_router.post("/admin/users/{user_id}/change-media-type")
async def change_user_media_type(user_id: str, media_type_data: MediaTypeChange, current_user: dict = Depends(get_current_user)):
    if current_user["admin_level"] < 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    old_type = user.get("media_type", 0)
    new_type = media_type_data.new_media_type
    
    # Update user media type
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"media_type": new_type}}
    )
    
    # Create notification record
    notification = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": "media_type_change",
        "title": "Изменен тип медиа",
        "message": f"Ваш статус медиа изменен с {'Платное' if old_type == 1 else 'Бесплатное'} на {'Платное' if new_type == 1 else 'Бесплатное'}",
        "admin_comment": media_type_data.admin_comment or "",
        "created_at": datetime.utcnow(),
        "read": False
    }
    
    await db.notifications.insert_one(notification)
    
    type_names = {0: "Бесплатное", 1: "Платное"}
    return {"message": f"Тип медиа пользователя {user['nickname']} изменен с '{type_names[old_type]}' на '{type_names[new_type]}'. Пользователь уведомлен."}

@api_router.get("/notifications")
async def get_notifications(current_user: dict = Depends(get_current_user)):
    notifications = await db.notifications.find({"user_id": current_user["id"]}).sort("created_at", -1).to_list(50)
    # Remove MongoDB _id fields
    for notification in notifications:
        if "_id" in notification:
            del notification["_id"]
    return notifications

@api_router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    # Update notification as read
    result = await db.notifications.update_one(
        {"id": notification_id, "user_id": current_user["id"]},
        {"$set": {"read": True}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification marked as read"}

@api_router.post("/admin/users/{user_id}/warning")
async def add_user_warning(user_id: str, current_user: dict = Depends(get_current_user)):
    if current_user["admin_level"] < 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_warnings = user.get("warnings", 0) + 1
    if new_warnings >= 3:
        # Block user
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"warnings": new_warnings, "is_approved": False}}
        )
        return {"message": "User blocked (3 warnings reached)"}
    else:
        await db.users.update_one(
            {"id": user_id},
            {"$set": {"warnings": new_warnings}}
        )
        return {"message": f"Warning added. Total warnings: {new_warnings}"}

@api_router.post("/admin/shop/item/{item_id}/image")
async def update_shop_item_image(item_id: str, image_data: dict, current_user: dict = Depends(get_current_user)):
    if current_user["admin_level"] < 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    image_url = image_data.get("image_url", "")
    
    # Validate URL if provided
    if image_url and not image_url.startswith(('http://', 'https://')):
        raise HTTPException(status_code=400, detail="Изображение должно быть валидной HTTP/HTTPS ссылкой")
    
    # Update shop item
    result = await db.shop_items.update_one(
        {"id": item_id},
        {"$set": {"image_url": image_url}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    return {"message": "Изображение товара обновлено"}

@api_router.get("/admin/shop/items")
async def get_admin_shop_items(current_user: dict = Depends(get_current_user)):
    if current_user["admin_level"] < 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    items = await db.shop_items.find().to_list(1000)
    # Remove MongoDB _id fields
    for item in items:
        if "_id" in item:
            del item["_id"]
    return items

# Statistics endpoint
@api_router.get("/stats")
async def get_stats():
    # Check cache first
    cached_stats = get_cache("basic_stats")
    if cached_stats:
        return cached_stats
    
    total_media = await db.users.count_documents({"is_approved": True})
    total_mc_spent = await db.purchases.aggregate([
        {"$match": {"status": "approved"}},
        {"$group": {"_id": None, "total": {"$sum": "$total_price"}}}
    ]).to_list(1)
    
    all_users = await db.users.find({"is_approved": True}).to_list(1000)
    total_mc_current = sum(user.get("balance", 0) for user in all_users)
    
    total_spent = total_mc_spent[0]["total"] if total_mc_spent else 0
    
    stats = {
        "total_media": total_media,
        "total_mc_spent": total_spent,
        "total_mc_current": total_mc_current
    }
    
    # Cache for 5 minutes
    set_cache("basic_stats", stats, 300)
    return stats

# Advanced Statistics endpoint
@api_router.get("/stats/advanced")
async def get_advanced_stats():
    # Check cache first
    cached_advanced_stats = get_cache("advanced_stats")
    if cached_advanced_stats:
        return cached_advanced_stats
    # User stats by media type
    paid_users = await db.users.count_documents({"is_approved": True, "media_type": 1})
    free_users = await db.users.count_documents({"is_approved": True, "media_type": 0})
    
    # Reports stats
    total_reports = await db.reports.count_documents({})
    pending_reports = await db.reports.count_documents({"status": "pending"})
    approved_reports = await db.reports.count_documents({"status": "approved"})
    
    # Purchases stats
    total_purchases = await db.purchases.count_documents({})
    pending_purchases = await db.purchases.count_documents({"status": "pending"})
    approved_purchases = await db.purchases.count_documents({"status": "approved"})
    
    # Shop items by category
    shop_categories = await db.shop_items.aggregate([
        {"$group": {"_id": "$category", "count": {"$sum": 1}, "total_price": {"$sum": "$price"}}}
    ]).to_list(10)
    
    # User warnings distribution
    warning_stats = await db.users.aggregate([
        {"$group": {"_id": "$warnings", "count": {"$sum": 1}}}
    ]).to_list(10)
    
    # Monthly reports trend (last 6 months)
    from datetime import datetime, timedelta
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    monthly_reports = await db.reports.aggregate([
        {"$match": {"created_at": {"$gte": six_months_ago}}},
        {"$group": {
            "_id": {
                "year": {"$year": "$created_at"},
                "month": {"$month": "$created_at"}
            },
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id.year": 1, "_id.month": 1}}
    ]).to_list(12)
    
    # Balance distribution
    balance_ranges = await db.users.aggregate([
        {"$bucket": {
            "groupBy": "$balance",
            "boundaries": [0, 100, 500, 1000, 5000, 10000, float('inf')],
            "default": "Other",
            "output": {"count": {"$sum": 1}}
        }}
    ]).to_list(10)
    
    return {
        "user_stats": {
            "paid_users": paid_users,
            "free_users": free_users,
            "total_users": paid_users + free_users
        },
        "report_stats": {
            "total": total_reports,
            "pending": pending_reports,
            "approved": approved_reports,
            "rejected": total_reports - pending_reports - approved_reports
        },
        "purchase_stats": {
            "total": total_purchases,
            "pending": pending_purchases,
            "approved": approved_purchases,
            "rejected": total_purchases - pending_purchases - approved_purchases
        },
        "shop_categories": [{"category": item["_id"], "count": item["count"], "total_price": item["total_price"]} for item in shop_categories],
        "warning_distribution": [{"warnings": item["_id"], "count": item["count"]} for item in warning_stats],
        "monthly_reports": [{"month": f"{item['_id']['year']}-{item['_id']['month']:02d}", "count": item["count"]} for item in monthly_reports],
        "balance_ranges": balance_ranges
    }

# Initialize shop items
@api_router.post("/admin/init-shop")
async def init_shop():
    # Check if items already exist
    existing_count = await db.shop_items.count_documents({})
    if existing_count > 0:
        return {"message": "Shop already initialized"}
    
    shop_items = [
        {"name": "VIP статус", "description": "Получите VIP статус на месяц с дополнительными привилегиями", "price": 500, "category": "Премиум"},
        {"name": "Премиум аккаунт", "description": "Расширенные возможности и приоритетная поддержка", "price": 1000, "category": "Премиум"},
        {"name": "Золотой значок", "description": "Эксклюзивный золотой значок для вашего профиля", "price": 300, "category": "Премиум"},
        {"name": "Ускорение отчетов", "description": "Быстрое одобрение ваших отчетов в течение 24 часов", "price": 200, "category": "Буст"},
        {"name": "Двойные медиа-коины", "description": "Получайте в 2 раза больше медиа-коинов за отчеты на неделю", "price": 400, "category": "Буст"},
        {"name": "Приоритет в очереди", "description": "Ваши заявки обрабатываются в первую очередь", "price": 150, "category": "Буст"},
        {"name": "Кастомная тема", "description": "Персональная цветовая схема для вашего профиля", "price": 250, "category": "Дизайн"},
        {"name": "Анимированный аватар", "description": "Возможность использовать GIF в качестве аватара", "price": 350, "category": "Дизайн"},
        {"name": "Уникальная рамка", "description": "Красивая рамка вокруг вашего профиля", "price": 180, "category": "Дизайн"},
    ]
    
    for item_data in shop_items:
        item = ShopItem(**item_data)
        await db.shop_items.insert_one(item.dict())
    
    return {"message": "Shop initialized with items"}

# Rating System Endpoints
@api_router.post("/ratings")
async def rate_user(rating_data: UserRating, current_user: dict = Depends(get_current_user)):
    # Check if user already rated this user
    existing_rating = await db.ratings.find_one({
        "user_id": current_user["id"],
        "rated_user_id": rating_data.rated_user_id
    })
    
    if existing_rating:
        # Update existing rating
        await db.ratings.update_one(
            {"id": existing_rating["id"]},
            {"$set": {
                "rating": rating_data.rating,
                "comment": rating_data.comment,
                "created_at": datetime.utcnow()
            }}
        )
        return {"message": "Rating updated successfully"}
    else:
        # Create new rating
        rating = UserRating(
            user_id=current_user["id"],
            rated_user_id=rating_data.rated_user_id,
            rating=rating_data.rating,
            comment=rating_data.comment
        )
        await db.ratings.insert_one(rating.dict())
        return {"message": "Rating submitted successfully"}

@api_router.get("/ratings/{user_id}")
async def get_user_ratings(user_id: str):
    ratings = await db.ratings.find({"rated_user_id": user_id}).to_list(1000)
    
    # Remove MongoDB _id fields
    for rating in ratings:
        if "_id" in rating:
            del rating["_id"]
    
    # Calculate average rating
    if ratings:
        avg_rating = sum(r["rating"] for r in ratings) / len(ratings)
        return {
            "ratings": ratings,
            "average_rating": round(avg_rating, 2),
            "total_ratings": len(ratings)
        }
    else:
        return {
            "ratings": [],
            "average_rating": 0,
            "total_ratings": 0
        }

@api_router.get("/leaderboard")
async def get_leaderboard():
    # Get all users with their ratings
    pipeline = [
        {
            "$group": {
                "_id": "$rated_user_id",
                "avg_rating": {"$avg": "$rating"},
                "total_ratings": {"$sum": 1}
            }
        },
        {
            "$match": {
                "total_ratings": {"$gte": 1}  # At least 1 rating
            }
        },
        {
            "$sort": {"avg_rating": -1}
        },
        {
            "$limit": 50
        }
    ]
    
    leaderboard_data = await db.ratings.aggregate(pipeline).to_list(50)
    
    # Enrich with user data
    leaderboard = []
    for item in leaderboard_data:
        user = await db.users.find_one({"id": item["_id"]})
        if user and user.get("is_approved"):
            leaderboard.append({
                "user_id": item["_id"],
                "nickname": user["nickname"],
                "media_type": user["media_type"],
                "avg_rating": round(item["avg_rating"], 2),
                "total_ratings": item["total_ratings"],
                "channel_link": user["channel_link"]
            })
    
# Data Export Endpoints
@api_router.get("/admin/export/{data_type}")
async def export_data(data_type: str, current_user: dict = Depends(get_current_user)):
    if current_user["admin_level"] < 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    import csv
    from io import StringIO
    from fastapi.responses import Response
    
    if data_type == "users":
        users = await db.users.find().to_list(10000)
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Login", "Nickname", "VK Link", "Channel Link", "Balance", "Media Type", "Admin Level", "Is Approved", "Warnings", "Created At"])
        
        for user in users:
            writer.writerow([
                user.get("id", ""),
                user.get("login", ""),
                user.get("nickname", ""),
                user.get("vk_link", ""),
                user.get("channel_link", ""),
                user.get("balance", 0),
                "Платное" if user.get("media_type") == 1 else "Бесплатное",
                user.get("admin_level", 0),
                "Да" if user.get("is_approved") else "Нет",
                user.get("warnings", 0),
                user.get("created_at", "").isoformat() if user.get("created_at") else ""
            ])
        
        content = output.getvalue()
        output.close()
        
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=users.csv"}
        )
    
    elif data_type == "reports":
        reports = await db.reports.find().to_list(10000)
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "User ID", "Status", "Links", "Admin Comment", "Created At"])
        
        for report in reports:
            user = await db.users.find_one({"id": report.get("user_id")})
            links_str = "; ".join([f"{link.get('url', '')} ({link.get('views', 0)} views)" for link in report.get("links", [])])
            
            writer.writerow([
                report.get("id", ""),
                user.get("nickname", "") if user else report.get("user_id", ""),
                report.get("status", ""),
                links_str,
                report.get("admin_comment", ""),
                report.get("created_at", "").isoformat() if report.get("created_at") else ""
            ])
        
        content = output.getvalue()
        output.close()
        
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=reports.csv"}
        )
    
    elif data_type == "purchases":
        purchases = await db.purchases.find().to_list(10000)
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "User", "Item", "Quantity", "Total Price", "Status", "Admin Comment", "Created At"])
        
        for purchase in purchases:
            user = await db.users.find_one({"id": purchase.get("user_id")})
            item = await db.shop_items.find_one({"id": purchase.get("item_id")})
            
            writer.writerow([
                purchase.get("id", ""),
                user.get("nickname", "") if user else purchase.get("user_id", ""),
                item.get("name", "") if item else purchase.get("item_id", ""),
                purchase.get("quantity", 0),
                purchase.get("total_price", 0),
                purchase.get("status", ""),
                purchase.get("admin_comment", ""),
                purchase.get("created_at", "").isoformat() if purchase.get("created_at") else ""
            ])
        
        content = output.getvalue()
        output.close()
        
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=purchases.csv"}
        )
    
    elif data_type == "ratings":
        ratings = await db.ratings.find().to_list(10000)
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Rater", "Rated User", "Rating", "Comment", "Created At"])
        
        for rating in ratings:
            rater = await db.users.find_one({"id": rating.get("user_id")})
            rated_user = await db.users.find_one({"id": rating.get("rated_user_id")})
            
            writer.writerow([
                rating.get("id", ""),
                rater.get("nickname", "") if rater else rating.get("user_id", ""),
                rated_user.get("nickname", "") if rated_user else rating.get("rated_user_id", ""),
                rating.get("rating", 0),
                rating.get("comment", ""),
                rating.get("created_at", "").isoformat() if rating.get("created_at") else ""
            ])
        
        content = output.getvalue()
        output.close()
        
        return Response(
            content=content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=ratings.csv"}
        )
    
    else:
        raise HTTPException(status_code=400, detail="Invalid export type. Options: users, reports, purchases, ratings")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
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
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()