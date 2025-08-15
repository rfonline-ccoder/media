#!/usr/bin/env python3
"""
Скрипт для создания админ пользователя admin с точно указанными данными
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

def main():
    """Основная функция"""
    print("🚀 Создание админ пользователя admin...")
    
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
        
        # Сначала проверим есть ли уже пользователь admin
        existing_admin = db.query(User).filter(User.login == "admin").first()
        
        if existing_admin:
            print(f"❗ Пользователь admin уже существует:")
            print(f"   ID: {existing_admin.id}")
            print(f"   Login: {existing_admin.login}")
            print(f"   Nickname: {existing_admin.nickname}")
            print(f"   Admin Level: {existing_admin.admin_level}")
            print(f"   Is Approved: {existing_admin.is_approved}")
            print("\n🔄 Обновляем пароль существующего админа на ba7a7am1ZX3...")
            
            # Обновляем пароль
            existing_admin.password = hash_password("ba7a7am1ZX3")
            db.commit()
            
            print("✅ Пароль админа обновлен на ba7a7am1ZX3")
            
        else:
            print("📋 Создаем нового админ пользователя admin...")
            
            # Создаем нового админа с точными данными из запроса
            admin_user = User(
                id=str(uuid.uuid4()),
                login="admin",
                password=hash_password("ba7a7am1ZX3"),
                nickname="admin",  # или можно использовать другой nickname если admin занят
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
            
            db.add(admin_user)
            db.commit()
            print(f"✅ Админ пользователь создан: login=admin, password=ba7a7am1ZX3")
        
        # Показываем итоговую информацию
        updated_admin = db.query(User).filter(User.login == "admin").first()
        print(f"\n📊 Итоговая информация об админе:")
        print(f"   Login: {updated_admin.login}")
        print(f"   Nickname: {updated_admin.nickname}")
        print(f"   Admin Level: {updated_admin.admin_level}")
        print(f"   Balance: {updated_admin.balance}")
        print(f"   Is Approved: {updated_admin.is_approved}")
        
        # Показываем всех админов в системе
        all_admins = db.query(User).filter(User.admin_level >= 1).all()
        print(f"\n👑 Все админы в системе ({len(all_admins)}):")
        for admin in all_admins:
            print(f"   - {admin.login} ({admin.nickname}) - Level {admin.admin_level}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()