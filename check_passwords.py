#!/usr/bin/env python3
"""
Проверка паролей в базе данных
"""

import sys
from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = "mysql+pymysql://hesus:ba7a7m1ZX3.,@89.169.1.168:3306/swagmedia1?charset=utf8mb4"

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True)
    login = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    nickname = Column(String(100), unique=True, nullable=False)
    admin_level = Column(Integer, default=0)
    is_approved = Column(Boolean, default=False)

def main():
    """Проверяем пароли пользователей"""
    print("🔍 Проверка паролей в базе данных...")
    
    try:
        engine = create_engine(DATABASE_URL, echo=False)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Получаем всех пользователей
        users = db.query(User).all()
        
        print(f"📊 Найдено пользователей: {len(users)}\n")
        
        for user in users:
            password_type = "хешированный" if user.password.startswith('$') else "открытый"
            admin_mark = " 👑" if user.admin_level >= 1 else ""
            
            print(f"👤 {user.login} ({user.nickname}){admin_mark}")
            print(f"   Пароль ({password_type}): {user.password[:50]}{'...' if len(user.password) > 50 else ''}")
            print(f"   Одобрен: {user.is_approved}")
            print()
        
        # Проверяем конкретно админа
        admin_user = db.query(User).filter(User.login == "admin").first()
        if admin_user:
            print(f"🎯 АДМИН НАЙДЕН:")
            print(f"   Login: {admin_user.login}")
            print(f"   Password: {admin_user.password}")
            print(f"   Хешированный: {'Да' if admin_user.password.startswith('$') else 'Нет'}")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()