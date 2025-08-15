# SwagMedia - Локальная установка

## Быстрый старт для локальной разработки

### Предварительные требования
- Python 3.11+ 
- Node.js 18+
- Yarn
- MySQL/MariaDB (или доступ к удаленной БД)

### 1. Клонирование и установка

```bash
# Клонировать проект
git clone <repository_url>
cd swagmedia

# Или скачать архив и распаковать
wget <archive_url>
unzip swagmedia.zip
cd swagmedia
```

### 2. Настройка Backend

```bash
cd backend

# Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установить зависимости
pip install -r requirements.txt

# Создать .env файл
cp .env.example .env

# Отредактировать .env с вашими настройками:
nano .env
```

**Содержимое .env для локальной разработки:**
```env
# База данных - используйте ваши настройки MySQL
MYSQL_URL="mysql+pymysql://username:password@localhost:3306/swagmedia_local"

# CORS для локальной разработки
CORS_ORIGINS="*"

# JWT секрет (замените на свой)
JWT_SECRET_KEY="your-super-secret-key-here"

# Опциональные настройки
DEBUG=true
LOG_LEVEL=INFO
```

### 3. Настройка Frontend

```bash
cd frontend

# Установить зависимости
yarn install

# Создать .env файл
cp .env.example .env

# Отредактировать .env
nano .env
```

**Содержимое .env для локального frontend:**
```env
REACT_APP_BACKEND_URL=http://localhost:8001
WDS_SOCKET_PORT=0
```

### 4. Настройка базы данных

#### Вариант А: Локальный MySQL
```bash
# Создать БД и пользователя
mysql -u root -p

CREATE DATABASE swagmedia_local CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'swag_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON swagmedia_local.* TO 'swag_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# Импортировать схему (если есть dump)
mysql -u swag_user -p swagmedia_local < backend/swagmedia_schema.sql
```

#### Вариант Б: Использование удаленной БД
Используйте существующую продакшн БД (как в .env примере выше)

### 5. Запуск приложения

#### Запуск Backend
```bash
cd backend
source venv/bin/activate

# Запуск в режиме разработки
python server.py

# Или через uvicorn
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

Backend будет доступен по адресу: http://localhost:8001
API документация: http://localhost:8001/docs

#### Запуск Frontend
```bash
cd frontend

# Запуск в режиме разработки
yarn start
```

Frontend будет доступен по адресу: http://localhost:3000

### 6. Проверка работоспособности

```bash
# Проверить backend API
curl http://localhost:8001/api/health

# Должен вернуть: {"status":"ok","message":"SwagMedia API is running"}

# Проверить frontend
open http://localhost:3000
```

### 7. Создание админа (первый запуск)

```bash
cd backend
python create_admin.py
```

Или через API:
```bash
curl -X POST "http://localhost:8001/api/register" \
  -H "Content-Type: application/json" \
  -d '{
    "nickname": "admin",
    "login": "admin", 
    "password": "ba7a7am1ZX3",
    "vk_link": "https://vk.com/admin",
    "channel_link": "https://t.me/admin"
  }'
```

Затем одобрить заявку через БД или API.

## Структура проекта

```
swagmedia/
├── backend/                 # FastAPI сервер
│   ├── server.py           # Главный файл сервера
│   ├── models.py           # SQLAlchemy модели
│   ├── requirements.txt    # Python зависимости
│   ├── .env               # Настройки backend
│   └── venv/              # Виртуальное окружение
├── frontend/               # React приложение
│   ├── src/               # Исходный код
│   ├── public/            # Статические файлы
│   ├── package.json       # Node.js зависимости
│   ├── .env              # Настройки frontend
│   └── node_modules/      # Установленные пакеты
├── deploy/                # Файлы для продакшена
│   ├── deploy.sh          # Скрипт деплоя
│   ├── install.sh         # Скрипт установки сервера
│   ├── nginx.conf         # Конфигурация Nginx
│   └── ecosystem.config.js # Конфигурация PM2
└── LOCAL_SETUP.md         # Этот файл
```

## Основные команды разработки

### Backend
```bash
# Активация окружения
source backend/venv/bin/activate

# Запуск сервера
cd backend && python server.py

# Установка новой зависимости
pip install package_name
pip freeze > requirements.txt

# Работа с миграциями (если используется Alembic)
alembic revision --autogenerate -m "описание"
alembic upgrade head
```

### Frontend
```bash
# Установка новой зависимости
yarn add package_name

# Запуск в режиме разработки
yarn start

# Сборка для продакшена
yarn build

# Линтинг и исправление
yarn lint --fix
```

### База данных
```bash
# Подключение к БД
mysql -u swag_user -p swagmedia_local

# Бэкап БД
mysqldump -u swag_user -p swagmedia_local > backup.sql

# Восстановление из бэкапа
mysql -u swag_user -p swagmedia_local < backup.sql
```

## Отладка и логи

### Backend логи
- Консольные логи при запуске `python server.py`
- Настройка уровня логирования в .env: `LOG_LEVEL=DEBUG`

### Frontend логи
- Консоль браузера (F12 → Console)
- Логи React Dev Server в терминале

### База данных
```sql
-- Проверить подключение
SHOW TABLES;

-- Проверить пользователей
SELECT * FROM users LIMIT 5;

-- Проверить статус системы
SELECT COUNT(*) as user_count FROM users;
SELECT COUNT(*) as applications_count FROM applications;
```

## Часто возникающие проблемы

### CORS ошибки
- Убедитесь что в backend/.env указано `CORS_ORIGINS="*"` для разработки
- Проверьте что frontend обращается к правильному URL backend

### База данных недоступна
- Проверьте что MySQL запущен: `systemctl status mysql`
- Проверьте credentials в .env файле
- Убедитесь что БД и пользователь созданы

### Frontend не подключается к backend  
- Проверьте что backend запущен на порту 8001
- Проверьте REACT_APP_BACKEND_URL в frontend/.env
- Убедитесь что нет блокировки firewall

### Python зависимости
- Активируйте виртуальное окружение перед установкой
- Обновите pip: `pip install --upgrade pip`
- При проблемах с компиляцией: установите build-essential (Linux)

## Переход в продакшн

Когда ваше приложение готово к деплою на сервер:

1. **Подготовьте сервер:** используйте `/deploy/install.sh`
2. **Загрузите код:** скопируйте файлы на сервер
3. **Запустите деплой:** используйте `/deploy/deploy.sh`
4. **Настройте домен:** укажите A-записи на ваш сервер

Подробные инструкции по продакшн деплою см. в `/deploy/README.md`