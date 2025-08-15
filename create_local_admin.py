#!/usr/bin/env python3
"""
Скрипт для создания администратора SwagMedia (локальная версия)
"""

import sys
import os
from pathlib import Path

# Добавляем backend в путь
sys.path.append(str(Path(__file__).parent / "backend"))

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import uuid
from datetime import datetime
from getpass import getpass

# Загружаем переменные окружения
load_dotenv(Path(__file__).parent / "backend" / ".env")

def get_database_url():
    """Получить URL базы данных из окружения или ввода пользователя"""
    db_url = os.getenv("MYSQL_URL")
    
    if not db_url:
        print("❌ MYSQL_URL не найден в .env файле!")
        print("\nВведите данные для подключения к БД:")
        
        host = input("Хост БД (localhost): ").strip() or "localhost"
        port = input("Порт БД (3306): ").strip() or "3306"
        username = input("Пользователь БД: ").strip()
        
        if not username:
            print("❌ Пользователь БД обязателен!")
            return None
            
        password = getpass("Пароль БД: ").strip()
        database = input("Имя БД: ").strip()
        
        if not database:
            print("❌ Имя БД обязательно!")
            return None
            
        db_url = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database}"
    
    return db_url

def test_connection(db_url):
    """Проверить подключение к БД"""
    try:
        engine = create_engine(db_url, echo=False)
        connection = engine.connect()
        connection.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к БД: {e}")
        return False

def create_admin():
    """Создать администратора"""
    print("🚀 Создание администратора SwagMedia")
    print("=" * 40)
    
    # Получаем URL БД
    db_url = get_database_url()
    if not db_url:
        return False
        
    # Проверяем подключение
    print("\n🔍 Проверяем подключение к БД...")
    if not test_connection(db_url):
        return False
    print("✅ Подключение к БД успешно!")
    
    # Подключаемся к БД
    try:
        engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        # Импортируем модели после установки подключения
        from server import User, Application
        
        print("\n👤 Введите данные администратора:")
        
        # Получаем данные от пользователя
        nickname = input("Никнейм админа (admin): ").strip() or "admin"
        login = input("Логин админа (admin): ").strip() or "admin"
        
        # Проверяем уникальность
        existing_user = db.query(User).filter(
            (User.login == login) | (User.nickname == nickname)
        ).first()
        
        if existing_user:
            print(f"❌ Пользователь с логином '{login}' или никнеймом '{nickname}' уже существует!")
            return False
        
        password = getpass("Пароль админа: ").strip()
        if not password:
            print("❌ Пароль не может быть пустым!")
            return False
            
        vk_link = input("VK ссылка (https://vk.com/admin): ").strip() or "https://vk.com/admin"
        channel_link = input("Ссылка на канал (https://t.me/admin): ").strip() or "https://t.me/admin"
        
        # Создаем пользователя
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed_password = pwd_context.hash(password)
        
        admin_user = User(
            id=str(uuid.uuid4()),
            login=login,
            password=hashed_password,
            nickname=nickname,
            vk_link=vk_link,
            channel_link=channel_link,
            balance=10000,  # Начальный баланс
            admin_level=1,  # Админ уровень
            is_approved=True,  # Автоматически одобрен
            media_type=1,  # Платный тип медиа
            warnings=0,
            previews_used=0,
            previews_limit=3,
            blacklist_until=None,
            registration_ip="127.0.0.1",
            created_at=datetime.utcnow()
        )
        
        db.add(admin_user)
        db.commit()
        
        print(f"\n✅ Администратор создан успешно!")
        print(f"👤 Никнейм: {nickname}")
        print(f"🔑 Логин: {login}")
        print(f"💰 Баланс: 10,000 MC")
        print(f"🏆 Админ уровень: 1")
        print(f"💎 Тип медиа: Платный")
        
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта моделей: {e}")
        print("Убедитесь что вы запускаете скрипт из корневой директории проекта")
        return False
    except Exception as e:
        print(f"❌ Ошибка создания администратора: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

def check_admin_exists():
    """Проверить существование администраторов"""
    db_url = get_database_url()
    if not db_url or not test_connection(db_url):
        return False
        
    try:
        engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        from server import User
        
        # Ищем админов
        admins = db.query(User).filter(User.admin_level > 0).all()
        
        if admins:
            print(f"\n👑 Найдено администраторов: {len(admins)}")
            for admin in admins:
                print(f"   - {admin.nickname} ({admin.login}) - Уровень: {admin.admin_level}")
        else:
            print("\n⚠️  Администраторы не найдены")
            
        return len(admins) > 0
        
    except Exception as e:
        print(f"❌ Ошибка проверки администраторов: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    print("🎯 SwagMedia Admin Creator")
    print("=" * 30)
    
    # Проверяем существующих админов
    has_admins = check_admin_exists()
    
    if has_admins:
        response = input("\nАдминистраторы уже существуют. Создать еще одного? (y/N): ").strip().lower()
        if response not in ['y', 'yes', 'да', 'д']:
            print("👋 Отменено пользователем")
            sys.exit(0)
    
    # Создаем админа
    success = create_admin()
    
    if success:
        print("\n🎉 Готово! Теперь вы можете войти в систему с правами администратора")
        print("\n📋 Следующие шаги:")
        print("1. 🚀 Запустите приложение: ./start-all.sh")
        print("2. 🌐 Откройте http://localhost:3000")
        print("3. 🔑 Войдите с созданными учетными данными")
    else:
        print("\n❌ Создание администратора не удалось")
        sys.exit(1)