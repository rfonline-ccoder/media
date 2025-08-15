from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
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
from datetime import datetime
import jwt
from passlib.context import CryptContext
import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client["swagmedia"]  # Using swagmedia database name

# Create the main app without a prefix
app = FastAPI()

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

# Helper functions
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
async def register(registration: RegistrationRequest):
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
async def login(login_data: LoginRequest):
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
async def approve_report(report_id: str, comment: str = "", current_user: dict = Depends(get_current_user)):
    if current_user["admin_level"] < 1:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get the report
    report = await db.reports.find_one({"id": report_id})
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    # Calculate MC reward based on total views
    total_views = sum(link.get("views", 0) for link in report.get("links", []))
    mc_reward = max(10, total_views // 100)  # At least 10 MC, 1 MC per 100 views
    
    # Update report status
    await db.reports.update_one(
        {"id": report_id},
        {"$set": {"status": "approved", "admin_comment": comment, "reviewed_at": datetime.utcnow()}}
    )
    
    # Add MC to user balance
    await db.users.update_one(
        {"id": report["user_id"]},
        {"$inc": {"balance": mc_reward}}
    )
    
    return {"message": f"Report approved and {mc_reward} MC added to user balance"}

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

# Statistics endpoint
@api_router.get("/stats")
async def get_stats():
    total_media = await db.users.count_documents({"is_approved": True})
    total_mc_spent = await db.purchases.aggregate([
        {"$match": {"status": "approved"}},
        {"$group": {"_id": None, "total": {"$sum": "$total_price"}}}
    ]).to_list(1)
    
    all_users = await db.users.find({"is_approved": True}).to_list(1000)
    total_mc_current = sum(user.get("balance", 0) for user in all_users)
    
    total_spent = total_mc_spent[0]["total"] if total_mc_spent else 0
    
    return {
        "total_media": total_media,
        "total_mc_spent": total_spent,
        "total_mc_current": total_mc_current
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

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()