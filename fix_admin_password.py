#!/usr/bin/env python3
"""
Исправление пароля админа для совместимости с системой аутентификации
"""

import sys
from sqlalchemy import create_engine, Column, String, Integer, Boolean, DateTime
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
    """Исправляем пароль админа"""
    print("🔧 Исправление пароля администратора...")
    
    try:
        engine = create_engine(DATABASE_URL, echo=False)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Находим админа
        admin_user = db.query(User).filter(User.login == "admin").first()
        
        if not admin_user:
            print("❌ Админ пользователь не найден!")
            return
        
        print(f"👤 Найден админ: {admin_user.login} ({admin_user.nickname})")
        print(f"📋 Текущий пароль: {admin_user.password[:50]}...")
        
        # Устанавливаем пароль в открытом виде (как ожидает система)
        admin_user.password = "ba7a7am1ZX3"
        db.commit()
        
        print(f"✅ Пароль админа обновлен на: ba7a7am1ZX3")
        print(f"📋 Новый пароль в БД: {admin_user.password}")
        
        db.close()
        
        print("\n🎯 ДАННЫЕ ДЛЯ ВХОДА:")
        print(f"   Login: admin")
        print(f"   Password: ba7a7am1ZX3")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()