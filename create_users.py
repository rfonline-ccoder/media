#!/usr/bin/env python3
"""
Скрипт для создания пользователей в SwagMedia
Создает админ пользователя admin с паролем ba7a7am1ZX3 и несколько тестовых пользователей
"""

import sys
import os
import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Database connection
DATABASE_URL = "mysql+pymysql://hesus:ba7a7m1ZX3.,@89.169.1.168:3306/swagmedia1?charset=utf8mb4"

Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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

def hash_password(password: str) -> str:
    """Хешировать пароль"""
    return pwd_context.hash(password)

def create_admin_user(db_session):
    """Создать админ пользователя admin с паролем ba7a7am1ZX3"""
    
    # Проверяем существует ли уже такой пользователь
    existing = db_session.query(User).filter(
        (User.login == "admin_new") | (User.nickname == "admin_new")
    ).first()
    
    if existing:
        print("❗ Пользователь admin_new уже существует")
        return existing
    
    # Создаем нового админа
    admin_user = User(
        id=str(uuid.uuid4()),
        login="admin_new",
        password=hash_password("ba7a7am1ZX3"),
        nickname="admin_new",
        vk_link="https://vk.com/swagmedia_admin",
        channel_link="https://t.me/swagmedia_official",
        balance=100000,  # Большой баланс для админа
        admin_level=1,   # Админские права
        is_approved=True,
        media_type=1,    # Платный доступ
        warnings=0,
        previews_used=0,
        previews_limit=999,  # Неограниченные предпросмотры
        registration_ip="127.0.0.1",
        created_at=datetime.utcnow()
    )
    
    try:
        db_session.add(admin_user)
        db_session.commit()
        print(f"✅ Админ пользователь создан: login=admin_new, password=ba7a7am1ZX3, nickname=admin_new")
        return admin_user
    except Exception as e:
        db_session.rollback()
        print(f"❌ Ошибка создания админа: {e}")
        return None

def create_test_users(db_session):
    """Создать тестовых пользователей"""
    
    test_users_data = [
        {
            "login": "testuser_demo1",
            "password": "testpass123",
            "nickname": "DemoUser1",
            "vk_link": "https://vk.com/testuser1",
            "channel_link": "https://t.me/testchannel1",
            "balance": 1000,
            "media_type": 0,  # Бесплатный
        },
        {
            "login": "testuser_demo2", 
            "password": "testpass456",
            "nickname": "DemoUser2",
            "vk_link": "https://vk.com/testuser2",
            "channel_link": "https://youtube.com/testchannel2",
            "balance": 5000,
            "media_type": 1,  # Платный
        },
        {
            "login": "testuser_demo3",
            "password": "testpass789",
            "nickname": "DemoUser3", 
            "vk_link": "https://vk.com/testuser3",
            "channel_link": "https://instagram.com/testchannel3",
            "balance": 2500,
            "media_type": 0,  # Бесплатный
        }
    ]
    
    created_users = []
    
    for user_data in test_users_data:
        # Проверяем существование
        existing = db_session.query(User).filter(
            (User.login == user_data["login"]) | (User.nickname == user_data["nickname"])
        ).first()
        
        if existing:
            print(f"❗ Пользователь {user_data['nickname']} уже существует")
            created_users.append(existing)
            continue
        
        # Создаем нового пользователя
        user = User(
            id=str(uuid.uuid4()),
            login=user_data["login"],
            password=hash_password(user_data["password"]),
            nickname=user_data["nickname"],
            vk_link=user_data["vk_link"],
            channel_link=user_data["channel_link"],
            balance=user_data["balance"],
            admin_level=0,   # Обычный пользователь
            is_approved=True,
            media_type=user_data["media_type"],
            warnings=0,
            previews_used=0,
            previews_limit=3,
            registration_ip="192.168.1.100",
            created_at=datetime.utcnow()
        )
        
        try:
            db_session.add(user)
            db_session.commit()
            print(f"✅ Тестовый пользователь создан: {user.nickname} (login={user.login}, type={'Платный' if user.media_type else 'Бесплатный'})")
            created_users.append(user)
        except Exception as e:
            db_session.rollback()
            print(f"❌ Ошибка создания пользователя {user_data['nickname']}: {e}")
    
    return created_users

def main():
    """Основная функция"""
    print("🚀 Создание пользователей SwagMedia...")
    
    try:
        # Подключение к базе данных
        engine = create_engine(
            DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={"charset": "utf8mb4"}
        )
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        print("✅ Подключение к базе данных установлено")
        
        # Создаем админа
        print("\n📋 Создание админ пользователя...")
        admin_user = create_admin_user(db)
        
        # Создаем тестовых пользователей
        print("\n📋 Создание тестовых пользователей...")
        test_users = create_test_users(db)
        
        print(f"\n🎉 ГОТОВО! Создано пользователей:")
        print(f"   👑 Админ: {1 if admin_user else 0}")
        print(f"   👥 Тестовые: {len([u for u in test_users if u])}")
        
        # Показываем итоговую статистику
        total_users = db.query(User).count()
        admin_users = db.query(User).filter(User.admin_level >= 1).count()
        print(f"\n📊 Общая статистика БД:")
        print(f"   Всего пользователей: {total_users}")
        print(f"   Админов: {admin_users}")
        print(f"   Обычных пользователей: {total_users - admin_users}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()