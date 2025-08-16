#!/bin/bash

# SwagMedia Quick Deploy - Быстрая установка
# Использование: sudo ./quick-deploy.sh

set -e

echo "🚀 SwagMedia Quick Deploy для Ubuntu 22"
echo "======================================"

# Проверка root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Запустите с sudo: sudo ./quick-deploy.sh"
   exit 1
fi

# Конфигурация
DOMAIN="swagmedia.site"
PROJECT_DIR="/root/media"

echo "📋 Устанавливаем в: $PROJECT_DIR"
echo "🌐 Домен: $DOMAIN"
echo ""
read -p "Продолжить? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Установка отменена"
    exit 1
fi

# Обновление системы
echo "📦 Обновляем систему..."
apt update > /dev/null 2>&1

# Базовые пакеты
echo "🔧 Устанавливаем базовые пакеты..."
apt install -y curl git build-essential > /dev/null 2>&1

# Node.js
echo "📱 Устанавливаем Node.js..."
curl -fsSL https://deb.nodesource.com/setup_20.x | bash - > /dev/null 2>&1
apt install -y nodejs > /dev/null 2>&1
npm install -g yarn pm2 serve > /dev/null 2>&1

# Python
echo "🐍 Настраиваем Python..."
apt install -y python3.11 python3.11-venv python3-pip > /dev/null 2>&1

# Nginx
echo "🌐 Устанавливаем Nginx..."
apt install -y nginx > /dev/null 2>&1

# MySQL
echo "🗄️ Устанавливаем MySQL..."
apt install -y mariadb-server > /dev/null 2>&1

# SSL
echo "🔐 Устанавливаем Certbot..."
apt install -y certbot python3-certbot-nginx > /dev/null 2>&1

# Firewall
echo "🛡️ Настраиваем firewall..."
ufw --force enable > /dev/null 2>&1
ufw allow ssh > /dev/null 2>&1
ufw allow 80/tcp > /dev/null 2>&1
ufw allow 443/tcp > /dev/null 2>&1

# Создание проекта
echo "📁 Создаем директорию проекта..."
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Поиск и копирование файлов
echo "📋 Ищем файлы проекта..."

# Функция поиска папок проекта
find_project() {
    local dirs=(
        "$(pwd)"
        "$(dirname "$(readlink -f "$0")" 2>/dev/null || dirname "$0")"
        "/root/media" 
        "/root"
        "$(dirname "$(pwd)")"
    )
    
    for dir in "${dirs[@]}"; do
        if [ -d "$dir/backend" ] && [ -d "$dir/frontend" ]; then
            echo "$dir"
            return 0
        fi
    done
    return 1
}

SOURCE=$(find_project)

if [ -n "$SOURCE" ]; then
    echo "✅ Найдены файлы в: $SOURCE"
    if [ "$SOURCE" != "$PROJECT_DIR" ]; then
        echo "📂 Копируем файлы..."
        cp -r "$SOURCE/backend" "$SOURCE/frontend" "$PROJECT_DIR/"
        echo "✅ Файлы скопированы"
    else
        echo "✅ Файлы уже в нужном месте"
    fi
else
    echo "❌ Не найдены папки backend/ и frontend/"
    echo ""
    echo "Проверьте структуру файлов:"
    echo "$(pwd)/backend/  - $([ -d "$(pwd)/backend" ] && echo "✅ есть" || echo "❌ нет")"
    echo "$(pwd)/frontend/ - $([ -d "$(pwd)/frontend" ] && echo "✅ есть" || echo "❌ нет")"
    echo ""
    
    read -p "Введите путь к папке с проектом (или Enter для отмены): " custom_path
    
    if [ -n "$custom_path" ] && [ -d "$custom_path/backend" ] && [ -d "$custom_path/frontend" ]; then
        echo "✅ Найдены файлы в: $custom_path"
        cp -r "$custom_path/backend" "$custom_path/frontend" "$PROJECT_DIR/"
        echo "✅ Файлы скопированы"
    else
        echo "❌ Установка отменена"
        exit 1
    fi
fi

# База данных
echo "🗄️ Настраиваем базу данных..."
mysql -e "CREATE DATABASE IF NOT EXISTS swagmedia_prod;"
mysql -e "CREATE USER IF NOT EXISTS 'swagmedia'@'localhost' IDENTIFIED BY 'SwagMedia2024!';"
mysql -e "GRANT ALL PRIVILEGES ON swagmedia_prod.* TO 'swagmedia'@'localhost';"
mysql -e "FLUSH PRIVILEGES;" > /dev/null 2>&1

# Backend .env
echo "⚙️ Настраиваем backend..."
cat > $PROJECT_DIR/backend/.env << EOF
MYSQL_URL="mysql+pymysql://swagmedia:SwagMedia2024!@localhost:3306/swagmedia_prod"
CORS_ORIGINS="https://$DOMAIN,http://localhost:3000"
EOF

# Frontend .env
echo "⚙️ Настраиваем frontend..."
cat > $PROJECT_DIR/frontend/.env << EOF
REACT_APP_BACKEND_URL=https://$DOMAIN
GENERATE_SOURCEMAP=false
EOF

# Backend зависимости
echo "🐍 Устанавливаем backend зависимости..."
cd $PROJECT_DIR/backend
python3 -m venv venv > /dev/null 2>&1
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1

# Инициализация БД и админ
python3 << EOF
import sys
import os
sys.path.append('.')
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User, Base
from passlib.context import CryptContext
from datetime import datetime

engine = create_engine("mysql+pymysql://swagmedia:SwagMedia2024!@localhost:3306/swagmedia_prod")
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

admin = db.query(User).filter(User.login == "admin").first()
if not admin:
    admin_user = User(
        user_id="admin-12345",
        login="admin",
        nickname="Admin",
        password=pwd_context.hash("admin123"),
        vk_link="https://vk.com/admin",
        channel_links=["https://t.me/swagmedia"],
        is_admin=True,
        is_approved=True,
        media_type=1,
        balance=10000,
        previews_used=0,
        previews_limit=3,
        warnings=0,
        registration_ip="127.0.0.1",
        created_at=datetime.utcnow()
    )
    db.add(admin_user)
    db.commit()
print("✅ Admin создан: admin/admin123")
db.close()
EOF

# Frontend сборка
echo "📱 Собираем frontend..."
cd $PROJECT_DIR/frontend
yarn install > /dev/null 2>&1
yarn build > /dev/null 2>&1

# PM2 конфигурация
echo "⚡ Настраиваем PM2..."
cat > $PROJECT_DIR/ecosystem.config.js << EOF
module.exports = {
  apps: [
    {
      name: 'swagmedia-backend',
      script: 'venv/bin/python',
      args: '-m uvicorn server:app --host 0.0.0.0 --port 8001',
      cwd: '$PROJECT_DIR/backend',
      instances: 1,
      autorestart: true,
      max_memory_restart: '1G'
    },
    {
      name: 'swagmedia-frontend',
      script: 'npx',
      args: 'serve -s build -l 3000',
      cwd: '$PROJECT_DIR/frontend',
      instances: 1,
      autorestart: true,
      max_memory_restart: '512M'
    }
  ]
};
EOF

# Nginx конфигурация
echo "🌐 Настраиваем Nginx..."
cat > /etc/nginx/sites-available/$DOMAIN << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /api/ {
        proxy_pass http://localhost:8001/api/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# Запуск PM2
echo "🚀 Запускаем сервисы..."
cd $PROJECT_DIR
pm2 delete all 2>/dev/null || true
pm2 start ecosystem.config.js > /dev/null 2>&1
pm2 startup systemd -u root --hp /root > /dev/null 2>&1
pm2 save > /dev/null 2>&1

# Проверка
sleep 5
echo ""
echo "🔍 Проверяем статус..."
if pm2 list | grep -q "online.*swagmedia"; then
    echo "✅ PM2 процессы запущены"
else
    echo "⚠️ Проблемы с PM2, проверьте: pm2 status"
fi

if systemctl is-active --quiet nginx; then
    echo "✅ Nginx работает"
else
    echo "⚠️ Проблемы с Nginx"
fi

# SSL сертификат
echo ""
echo "🔐 Получаем SSL сертификат..."
echo "ВАЖНО: Убедитесь что $DOMAIN указывает на IP этого сервера!"
read -p "Домен настроен? Получить SSL? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN || echo "⚠️ SSL не получен, проверьте DNS"
fi

# Финал
echo ""
echo "🎉 УСТАНОВКА ЗАВЕРШЕНА!"
echo "======================="
echo ""
echo "🌐 Сайт: https://$DOMAIN (или http://$DOMAIN если SSL не настроен)"
echo "👤 Админ: admin / admin123"
echo ""
echo "📊 Команды управления:"
echo "  pm2 status     - статус сервисов"
echo "  pm2 logs       - логи приложений"
echo "  pm2 restart all - перезапуск"
echo ""
echo "🔧 Nginx:"
echo "  systemctl status nginx"
echo "  systemctl restart nginx"
echo ""
echo "✅ SwagMedia готов к работе!"