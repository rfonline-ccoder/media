#!/bin/bash

# SwagMedia Production Deploy Script for Ubuntu 22
# Полная автоматизация деплоя с PM2, Nginx и SSL
# Автор: SwagMedia Team

set -e  # Exit on any error

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Логирование
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Проверка что скрипт запущен с root правами
if [[ $EUID -ne 0 ]]; then
   error "Этот скрипт должен быть запущен с правами root (sudo)"
fi

log "🚀 Начинаем установку SwagMedia на продакшн сервер"

# Конфигурация
DOMAIN="swagmedia.site"
PROJECT_DIR="/root/media"
BACKEND_PORT="8001"
FRONTEND_PORT="3000"
DB_NAME="swagmedia_prod"
DB_USER="swagmedia_user"
DB_PASSWORD="SwagMedia2024!Production"

log "📋 Конфигурация:"
echo "  - Домен: $DOMAIN"
echo "  - Проект: $PROJECT_DIR"
echo "  - Backend порт: $BACKEND_PORT"
echo "  - Frontend порт: $FRONTEND_PORT"
echo "  - База данных: $DB_NAME"

# Обновление системы
log "📦 Обновляем систему Ubuntu 22..."
apt update && apt upgrade -y

# Установка базовых пакетов
log "🔧 Устанавливаем базовые пакеты..."
apt install -y curl wget git build-essential software-properties-common ufw

# Установка Node.js 20 LTS
log "📱 Устанавливаем Node.js 20 LTS..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
apt install -y nodejs

# Установка Yarn
log "🧶 Устанавливаем Yarn..."
npm install -g yarn

# Установка Python 3.11 и pip
log "🐍 Устанавливаем Python 3.11..."
apt install -y python3.11 python3.11-venv python3-pip python3.11-dev

# Создание символических ссылок для python
ln -sf /usr/bin/python3.11 /usr/bin/python
ln -sf /usr/bin/python3.11 /usr/bin/python3

# Установка PM2
log "⚡ Устанавливаем PM2..."
npm install -g pm2
pm2 startup systemd -u root --hp /root

# Установка Nginx
log "🌐 Устанавливаем Nginx..."
apt install -y nginx

# Установка MySQL/MariaDB
log "🗄️ Устанавливаем MariaDB..."
apt install -y mariadb-server mariadb-client

# Установка Certbot для SSL
log "🔐 Устанавливаем Certbot для SSL..."
apt install -y certbot python3-certbot-nginx

# Настройка firewall
log "🛡️ Настраиваем UFW firewall..."
ufw --force enable
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow $BACKEND_PORT/tcp
ufw allow $FRONTEND_PORT/tcp

# Создание директории проекта
log "📁 Создаем директорию проекта..."
rm -rf $PROJECT_DIR
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Копирование файлов проекта
log "📋 Копируем файлы проекта..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "$SCRIPT_DIR/backend" ] && [ -d "$SCRIPT_DIR/frontend" ]; then
    cp -r "$SCRIPT_DIR/backend" $PROJECT_DIR/
    cp -r "$SCRIPT_DIR/frontend" $PROJECT_DIR/
    cp -r "$SCRIPT_DIR/tests" $PROJECT_DIR/ 2>/dev/null || true
    cp "$SCRIPT_DIR"/*.md $PROJECT_DIR/ 2>/dev/null || true
    log "✅ Файлы проекта скопированы из $SCRIPT_DIR"
else
    error "Не найдены директории backend и frontend в $SCRIPT_DIR. Убедитесь что скрипт лежит в корне проекта рядом с папками backend/ и frontend/"
fi

# Настройка базы данных MySQL
log "🗄️ Настраиваем MySQL базу данных..."
mysql -e "CREATE DATABASE IF NOT EXISTS $DB_NAME;"
mysql -e "CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';"
mysql -e "GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"

# Создание .env файла для backend
log "⚙️ Создаем конфигурацию backend..."
cat > $PROJECT_DIR/backend/.env << EOF
MYSQL_URL="mysql+pymysql://$DB_USER:$DB_PASSWORD@localhost:3306/$DB_NAME"
CORS_ORIGINS="https://$DOMAIN,http://localhost:$FRONTEND_PORT"
JWT_SECRET="SwagMedia2024ProductionJWTSecretKey!VerySecure"
REDIS_URL="redis://localhost:6379"
EOF

# Создание .env файла для frontend
log "⚙️ Создаем конфигурацию frontend..."
cat > $PROJECT_DIR/frontend/.env << EOF
REACT_APP_BACKEND_URL=https://$DOMAIN
GENERATE_SOURCEMAP=false
EOF

# Установка зависимостей backend
log "🐍 Устанавливаем зависимости backend..."
cd $PROJECT_DIR/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Установка зависимостей frontend
log "📱 Устанавливаем зависимости frontend..."
cd $PROJECT_DIR/frontend
yarn install

# Сборка frontend для продакшна
log "🔨 Собираем frontend для продакшна..."
yarn build

# Создание PM2 конфигурации
log "⚡ Создаем PM2 конфигурацию..."
cat > $PROJECT_DIR/ecosystem.config.js << EOF
module.exports = {
  apps: [
    {
      name: 'swagmedia-backend',
      script: 'venv/bin/python',
      args: '-m uvicorn server:app --host 0.0.0.0 --port $BACKEND_PORT',
      cwd: '$PROJECT_DIR/backend',
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: '$PROJECT_DIR/backend'
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      error_file: '/var/log/pm2/swagmedia-backend-error.log',
      out_file: '/var/log/pm2/swagmedia-backend-out.log',
      log_file: '/var/log/pm2/swagmedia-backend.log'
    },
    {
      name: 'swagmedia-frontend',
      script: 'npx',
      args: 'serve -s build -l $FRONTEND_PORT',
      cwd: '$PROJECT_DIR/frontend',
      env: {
        NODE_ENV: 'production'
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '512M',
      error_file: '/var/log/pm2/swagmedia-frontend-error.log',
      out_file: '/var/log/pm2/swagmedia-frontend-out.log',
      log_file: '/var/log/pm2/swagmedia-frontend.log'
    }
  ]
};
EOF

# Установка serve для статических файлов
log "📦 Устанавливаем serve для frontend..."
npm install -g serve

# Создание директории для логов PM2
mkdir -p /var/log/pm2

# Инициализация базы данных
log "🗄️ Инициализируем базу данных..."
cd $PROJECT_DIR/backend
source venv/bin/activate

# Создание базовых таблиц (если есть скрипт инициализации)
if [ -f "init_db.py" ]; then
    python init_db.py
fi

# Создание админ пользователя
cat > create_admin.py << EOF
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User, Base
from passlib.context import CryptContext
from datetime import datetime

# Database connection
MYSQL_URL = "mysql+pymysql://$DB_USER:$DB_PASSWORD@localhost:3306/$DB_NAME"
engine = create_engine(MYSQL_URL)
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

try:
    # Check if admin exists
    admin = db.query(User).filter(User.login == "admin").first()
    
    if not admin:
        # Create admin user
        admin_user = User(
            user_id="admin-user-id-12345",
            login="admin",
            nickname="Administrator",
            password=pwd_context.hash("admin123"),
            vk_link="https://vk.com/admin",
            channel_links=["https://t.me/swagmedia"],
            is_admin=True,
            is_approved=True,
            media_type=1,  # Premium
            balance=10000,
            previews_used=0,
            previews_limit=3,
            warnings=0,
            registration_ip="127.0.0.1",
            created_at=datetime.utcnow()
        )
        db.add(admin_user)
        db.commit()
        print("✅ Admin user created successfully")
        print("Login: admin")
        print("Password: admin123")
    else:
        print("✅ Admin user already exists")
        
except Exception as e:
    print(f"❌ Error creating admin: {e}")
    db.rollback()
finally:
    db.close()
EOF

python create_admin.py

# Настройка Nginx
log "🌐 Настраиваем Nginx..."
cat > /etc/nginx/sites-available/$DOMAIN << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;

    # SSL certificates (will be added by certbot)
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384:ECDHE-RSA-AES128-SHA:ECDHE-RSA-AES256-SHA:DHE-RSA-AES128-SHA256:DHE-RSA-AES256-SHA256:AES128-GCM-SHA256:AES256-GCM-SHA384:AES128-SHA256:AES256-SHA256:AES128-SHA:AES256-SHA:DES-CBC3-SHA;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # Frontend (React app)
    location / {
        proxy_pass http://localhost:$FRONTEND_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_redirect off;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:$BACKEND_PORT/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        
        # CORS headers
        add_header Access-Control-Allow-Origin *;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
        add_header Access-Control-Allow-Headers "Origin, X-Requested-With, Content-Type, Accept, Authorization";
        
        # Handle preflight requests
        if (\$request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin *;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "Origin, X-Requested-With, Content-Type, Accept, Authorization";
            add_header Content-Length 0;
            add_header Content-Type text/plain;
            return 200;
        }
    }

    # Static files with caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        proxy_pass http://localhost:$FRONTEND_PORT;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;
}
EOF

# Активация сайта в Nginx
ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Тестирование конфигурации Nginx
log "🧪 Тестируем конфигурацию Nginx..."
nginx -t

# Перезапуск Nginx
systemctl restart nginx
systemctl enable nginx

# Запуск приложений через PM2
log "🚀 Запускаем приложения через PM2..."
cd $PROJECT_DIR
pm2 delete all 2>/dev/null || true  # Удаляем старые процессы
pm2 start ecosystem.config.js
pm2 save
pm2 startup

# Ожидание запуска сервисов
log "⏳ Ожидаем запуска сервисов..."
sleep 10

# Проверка статуса PM2
log "📊 Статус PM2 процессов:"
pm2 status

# Получение SSL сертификата
log "🔐 Получаем SSL сертификат от Let's Encrypt..."
warning "ВАЖНО: Убедитесь что домен $DOMAIN указывает на IP этого сервера!"
read -p "Нажмите Enter когда домен будет настроен, или Ctrl+C для отмены..."

# Получение сертификата без перезаписи Nginx конфига (мы его уже настроили)
certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN || warning "SSL сертификат не получен. Проверьте DNS настройки домена."

# Настройка автообновления SSL
log "🔄 Настраиваем автообновление SSL сертификата..."
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet && systemctl reload nginx") | crontab -

# Создание скрипта для мониторинга
log "📊 Создаем скрипт мониторинга..."
cat > /root/swagmedia-monitor.sh << EOF
#!/bin/bash
echo "=== SwagMedia Status Report ==="
echo "Date: \$(date)"
echo ""
echo "=== PM2 Status ==="
pm2 status
echo ""
echo "=== Nginx Status ==="
systemctl status nginx --no-pager -l
echo ""
echo "=== MySQL Status ==="
systemctl status mariadb --no-pager -l
echo ""
echo "=== Disk Usage ==="
df -h
echo ""
echo "=== Memory Usage ==="
free -h
echo ""
echo "=== SSL Certificate Status ==="
certbot certificates
EOF

chmod +x /root/swagmedia-monitor.sh

# Создание скрипта для обновления
log "🔄 Создаем скрипт обновления..."
cat > /root/swagmedia-update.sh << EOF
#!/bin/bash
set -e

log() {
    echo "[UPDATE] \$(date): \$1"
}

log "Начинаем обновление SwagMedia..."

cd $PROJECT_DIR

# Обновление backend
log "Обновляем backend..."
cd backend
source venv/bin/activate
git pull origin main || log "Git pull не выполнен (возможно, нет удаленного репозитория)"
pip install -r requirements.txt

# Обновление frontend
log "Обновляем frontend..."
cd ../frontend
yarn install
yarn build

# Перезапуск сервисов
log "Перезапускаем сервисы..."
pm2 reload all

log "Обновление завершено!"
EOF

chmod +x /root/swagmedia-update.sh

# Финальная проверка
log "🔍 Выполняем финальную проверку..."

# Проверка портов
if netstat -tlnp | grep -q ":$BACKEND_PORT "; then
    log "✅ Backend запущен на порту $BACKEND_PORT"
else
    warning "⚠️ Backend не отвечает на порту $BACKEND_PORT"
fi

if netstat -tlnp | grep -q ":$FRONTEND_PORT "; then
    log "✅ Frontend запущен на порту $FRONTEND_PORT"
else
    warning "⚠️ Frontend не отвечает на порту $FRONTEND_PORT"
fi

# Проверка MySQL
if systemctl is-active --quiet mariadb; then
    log "✅ MySQL/MariaDB запущен"
else
    warning "⚠️ MySQL/MariaDB не запущен"
fi

# Проверка Nginx
if systemctl is-active --quiet nginx; then
    log "✅ Nginx запущен"
else
    warning "⚠️ Nginx не запущен"
fi

# Итоговая информация
echo ""
echo "========================================"
echo "🎉 ДЕПЛОЙ ЗАВЕРШЕН УСПЕШНО!"
echo "========================================"
echo ""
echo "📍 URL сайта: https://$DOMAIN"
echo "🔧 Админ панель: https://$DOMAIN"
echo "👤 Админ логин: admin"
echo "🔑 Админ пароль: admin123"
echo ""
echo "📊 Мониторинг: /root/swagmedia-monitor.sh"
echo "🔄 Обновление: /root/swagmedia-update.sh"
echo ""
echo "📝 Логи PM2:"
echo "  - Backend: /var/log/pm2/swagmedia-backend.log"
echo "  - Frontend: /var/log/pm2/swagmedia-frontend.log"
echo ""
echo "🔧 Полезные команды:"
echo "  - pm2 status           # Статус процессов"
echo "  - pm2 logs             # Просмотр логов"
echo "  - pm2 restart all      # Перезапуск всех процессов"
echo "  - systemctl status nginx  # Статус Nginx"
echo "  - certbot certificates    # Статус SSL"
echo ""
echo "🚀 SwagMedia готов к работе!"
echo "========================================"

log "🏁 Установка завершена! Проект доступен по адресу: https://$DOMAIN"