#!/bin/bash

# SwagMedia Auto-Install Script
# Сервер: 89.169.1.168
# Пользователь: hesus 
# База данных: swagmedia1
# Домен: swagmedia.site

set -e

echo "🚀 SwagMedia Auto-Installation Script"
echo "======================================"

# Цвета для логов
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Проверяем что запущено от root
if [ "$EUID" -ne 0 ]; then 
    log_error "Пожалуйста, запустите скрипт от root: sudo bash install.sh"
    exit 1
fi

# Создаем основные директории
log_step "Создание директорий..."
mkdir -p /root/media/backend
mkdir -p /root/media/frontend
mkdir -p /var/log/swagmedia
mkdir -p /etc/nginx/sites-available
mkdir -p /etc/nginx/sites-enabled

# Обновляем систему
log_step "Обновление системы..."
apt update && apt upgrade -y

# Устанавливаем базовые пакеты
log_step "Установка базовых пакеты..."
apt install -y curl wget git nginx software-properties-common apt-transport-https ca-certificates gnupg lsb-release unzip

# Устанавливаем Node.js 18 LTS
log_step "Установка Node.js 18 LTS..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
apt install -y nodejs

# Проверяем версии Node.js и npm
node_version=$(node --version)
npm_version=$(npm --version)
log_info "Node.js версия: $node_version"
log_info "npm версия: $npm_version"

# Устанавливаем Yarn
log_step "Установка Yarn..."
npm install -g yarn
yarn_version=$(yarn --version)
log_info "Yarn версия: $yarn_version"

# Устанавливаем Python 3.11
log_step "Установка Python 3.11..."
add-apt-repository ppa:deadsnakes/ppa -y
apt update
apt install -y python3.11 python3.11-pip python3.11-venv python3.11-dev python3.11-distutils

# Создаем симлинк для python3
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Проверяем версию Python
python3_version=$(python3 --version)
log_info "Python версия: $python3_version"

# Устанавливаем pip для Python 3.11
log_step "Настройка pip..."
curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# Устанавливаем PM2
log_step "Установка PM2..."
npm install -g pm2

# Устанавливаем MariaDB Server
log_step "Установка MariaDB Server..."
apt install -y mariadb-server mariadb-client

# Запускаем и включаем MariaDB
systemctl start mariadb
systemctl enable mariadb

# Настройка MariaDB
log_step "Настройка базы данных..."
mysql -u root <<EOF
CREATE DATABASE IF NOT EXISTS swagmedia1 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'hesus'@'localhost' IDENTIFIED BY 'ba7a7m1ZX3.,';
CREATE USER IF NOT EXISTS 'hesus'@'%' IDENTIFIED BY 'ba7a7m1ZX3.,';
GRANT ALL PRIVILEGES ON swagmedia1.* TO 'hesus'@'localhost';
GRANT ALL PRIVILEGES ON swagmedia1.* TO 'hesus'@'%';
FLUSH PRIVILEGES;
EOF

log_info "✅ База данных swagmedia1 создана и настроена"

# Копируем файлы приложения в /root/media
log_step "Копирование файлов приложения..."

# Копируем backend файлы
cp -r /app/backend/* /root/media/backend/
chown -R root:root /root/media/backend

# Копируем frontend файлы
cp -r /app/frontend/* /root/media/frontend/
chown -R root:root /root/media/frontend

# Настройка backend
log_step "Настройка backend (Python зависимости)..."
cd /root/media/backend

# Создаем виртуальное окружение
python3.11 -m venv venv
source venv/bin/activate

# Обновляем pip в виртуальном окружении
pip install --upgrade pip

# Устанавливаем Python зависимости
pip install fastapi==0.110.1
pip install uvicorn==0.25.0
pip install sqlalchemy>=2.0.0
pip install pymysql>=1.1.0
pip install alembic>=1.13.0
pip install python-dotenv>=1.0.1
pip install pydantic>=2.6.4
pip install pyjwt>=2.10.1
pip install passlib>=1.7.4
pip install python-multipart>=0.0.9
pip install slowapi>=0.1.9
pip install python-jose>=3.3.0
pip install requests>=2.31.0

log_info "✅ Backend зависимости установлены"

# Настройка frontend
log_step "Настройка frontend (Node.js зависимости)..."
cd /root/media/frontend

# Обновляем .env файл для продакшена
cat > .env <<EOF
REACT_APP_BACKEND_URL=https://swagmedia.site
WDS_SOCKET_PORT=443
EOF

# Устанавливаем зависимости
yarn install

# Собираем production build
yarn build

log_info "✅ Frontend построен и готов"

# Создаем конфигурацию PM2
log_step "Настройка PM2..."
cat > /root/media/ecosystem.config.js <<EOF
module.exports = {
  apps: [
    {
      name: 'swagmedia-backend',
      cwd: '/root/media/backend',
      script: 'venv/bin/python',
      args: '-m uvicorn server:app --host 0.0.0.0 --port 8001 --workers 1',
      env: {
        NODE_ENV: 'production',
        PYTHONPATH: '/root/media/backend'
      },
      instances: 1,
      exec_mode: 'fork',
      autorestart: true,
      watch: false,
      max_memory_restart: '512M',
      error_file: '/var/log/swagmedia/backend-error.log',
      out_file: '/var/log/swagmedia/backend-out.log',
      log_file: '/var/log/swagmedia/backend-combined.log',
      time: true,
      min_uptime: '10s',
      max_restarts: 10
    }
  ]
};
EOF

# Настройка Nginx
log_step "Настройка Nginx..."
cat > /etc/nginx/sites-available/swagmedia.site <<EOF
# Nginx configuration for SwagMedia
server {
    listen 80;
    server_name swagmedia.site www.swagmedia.site;
    
    # Redirect HTTP to HTTPS (after SSL setup)
    # return 301 https://\$server_name\$request_uri;
    
    # Временно работаем по HTTP до получения SSL
    root /root/media/frontend/build;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Client max body size
    client_max_body_size 50M;

    # API routes - proxy to backend
    location /api {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout       60s;
        proxy_send_timeout          60s;
        proxy_read_timeout          60s;
        
        # CORS headers
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
        
        # Handle preflight requests
        if (\$request_method = 'OPTIONS') {
            add_header 'Access-Control-Max-Age' 1728000;
            add_header 'Content-Type' 'text/plain; charset=utf-8';
            add_header 'Content-Length' 0;
            return 204;
        }
    }

    # Frontend routes - serve React app
    location / {
        try_files \$uri \$uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Security - deny access to hidden files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }

    # Logs
    access_log /var/log/nginx/swagmedia.access.log;
    error_log /var/log/nginx/swagmedia.error.log;
}
EOF

# Включаем сайт
ln -sf /etc/nginx/sites-available/swagmedia.site /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Тестируем конфигурацию Nginx
nginx -t
if [ $? -eq 0 ]; then
    log_info "✅ Конфигурация Nginx валидна"
else
    log_error "❌ Ошибка в конфигурации Nginx"
    exit 1
fi

# Перезапускаем Nginx
systemctl restart nginx
systemctl enable nginx

# Настраиваем UFW Firewall
log_step "Настройка firewall..."
ufw allow ssh
ufw allow 'Nginx Full'
ufw allow 3306  # MySQL
ufw --force enable

# Запускаем backend через PM2
log_step "Запуск backend сервиса..."
cd /root/media
pm2 start ecosystem.config.js

# Настраиваем автозапуск PM2
pm2 startup
pm2 save

log_info "✅ PM2 настроен для автозапуска"

# Устанавливаем Certbot для SSL (опционально)
log_step "Установка Certbot для SSL..."
apt install -y certbot python3-certbot-nginx

# Создаем скрипт для получения SSL сертификата
cat > /root/get-ssl.sh <<'EOF'
#!/bin/bash
echo "Получение SSL сертификата для swagmedia.site..."
certbot --nginx -d swagmedia.site -d www.swagmedia.site --non-interactive --agree-tos --email admin@swagmedia.site

# После получения сертификата, обновляем конфигурацию nginx для редиректа на HTTPS
if [ $? -eq 0 ]; then
    echo "✅ SSL сертификат получен успешно"
    echo "Перезапускаем nginx..."
    systemctl reload nginx
else
    echo "❌ Ошибка получения SSL сертификата"
fi
EOF

chmod +x /root/get-ssl.sh

# Создаем скрипт проверки статуса
cat > /root/check-status.sh <<'EOF'
#!/bin/bash
echo "🔍 Проверка статуса SwagMedia..."
echo "================================"

echo "1. Статус PM2 процессов:"
pm2 status

echo -e "\n2. Статус Nginx:"
systemctl status nginx --no-pager -l

echo -e "\n3. Статус MariaDB:"
systemctl status mariadb --no-pager -l

echo -e "\n4. Проверка подключения к базе данных:"
mysql -u hesus -pba7a7m1ZX3., -e "SHOW DATABASES;" | grep swagmedia1

echo -e "\n5. Проверка backend API:"
curl -s http://localhost:8001/api/health | head -c 200

echo -e "\n\n6. Логи backend (последние 10 строк):"
tail -n 10 /var/log/swagmedia/backend-combined.log

echo -e "\n7. Логи Nginx (последние 5 строк):"
tail -n 5 /var/log/nginx/swagmedia.error.log
EOF

chmod +x /root/check-status.sh

# Создаем скрипт перезапуска сервисов
cat > /root/restart-services.sh <<'EOF'
#!/bin/bash
echo "🔄 Перезапуск всех сервисов SwagMedia..."

echo "Перезапуск PM2 процессов..."
pm2 restart all

echo "Перезапуск Nginx..."
systemctl restart nginx

echo "Перезапуск MariaDB..."
systemctl restart mariadb

echo "✅ Все сервисы перезапущены"
pm2 status
EOF

chmod +x /root/restart-services.sh

# Создаем cron задачу для автоматического обновления SSL
log_step "Настройка автообновления SSL..."
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -

# Финальная проверка
log_step "Финальная проверка установки..."

# Проверяем что все сервисы запущены
sleep 5

# Проверяем PM2
pm2_status=$(pm2 list | grep swagmedia-backend | grep online)
if [ -n "$pm2_status" ]; then
    log_info "✅ Backend запущен через PM2"
else
    log_error "❌ Backend не запущен"
fi

# Проверяем Nginx
if systemctl is-active --quiet nginx; then
    log_info "✅ Nginx активен"
else
    log_error "❌ Nginx не активен"
fi

# Проверяем MariaDB
if systemctl is-active --quiet mariadb; then
    log_info "✅ MariaDB активен"
else
    log_error "❌ MariaDB не активен"
fi

# Проверяем API endpoint
api_check=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/health)
if [ "$api_check" = "200" ]; then
    log_info "✅ Backend API отвечает"
else
    log_warn "⚠️ Backend API не отвечает (код: $api_check)"
fi

echo ""
echo "🎉 УСТАНОВКА ЗАВЕРШЕНА!"
echo "======================"
echo ""
echo "📋 Информация о системе:"
echo "   Домен: http://swagmedia.site (или http://89.169.1.168)"
echo "   Backend API: http://89.169.1.168:8001/api/health"
echo "   База данных: swagmedia1"
echo "   Пользователь БД: hesus"
echo ""
echo "🔧 Полезные команды:"
echo "   Проверить статус:     ./check-status.sh"
echo "   Перезапустить все:    ./restart-services.sh"
echo "   Получить SSL:         ./get-ssl.sh"
echo "   PM2 процессы:         pm2 status"
echo "   Логи backend:         pm2 logs swagmedia-backend"
echo ""
echo "🔑 Админ доступ:"
echo "   Логин: admin"
echo "   Пароль: admin123"
echo ""
echo "⚠️ СЛЕДУЮЩИЕ ШАГИ:"
echo "1. Направьте домен swagmedia.site на IP 89.169.1.168"
echo "2. Запустите ./get-ssl.sh для получения SSL сертификата"
echo "3. Проверьте работу сайта: http://swagmedia.site"
echo ""

# Проводим первоначальную инициализацию базы данных
log_step "Инициализация базы данных..."
cd /root/media/backend
source venv/bin/activate
python3 -c "
from server import init_database
init_database()
print('База данных инициализирована!')
"

log_info "✅ Установка SwagMedia завершена успешно!"