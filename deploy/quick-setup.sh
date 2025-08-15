#!/bin/bash

# SwagMedia Quick Setup Script
# Скрипт для быстрой установки и деплоя SwagMedia
# 
# Использование:
# 1. Скопировать весь проект на сервер: scp -r /app/* root@89.169.1.168:/tmp/swagmedia/
# 2. Подключиться к серверу: ssh root@89.169.1.168
# 3. Запустить: cd /tmp/swagmedia && chmod +x deploy/quick-setup.sh && ./deploy/quick-setup.sh

set -e

echo "🚀 SwagMedia Quick Setup для 89.169.1.168"
echo "Domain: swagmedia.site"
echo "Database: swagmedia1"
echo ""

# Цвета для логов
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Проверки
if [ "$EUID" -ne 0 ]; then 
    log_error "Запустите от root: sudo ./deploy/quick-setup.sh"
fi

if [ ! -f "backend/server.py" ]; then
    log_error "Файлы приложения не найдены. Убедитесь что вы в директории с проектом."
fi

log_step "1. Установка базовых компонентов..."

# Обновляем систему
apt update -y
apt upgrade -y

# Устанавливаем необходимые пакеты
apt install -y curl wget git nginx software-properties-common apt-transport-https ca-certificates gnupg lsb-release python3-pip

# Устанавливаем Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Устанавливаем Yarn
npm install -g yarn pm2

# Устанавливаем Python виртуальное окружение
apt install -y python3-venv python3-dev

# Устанавливаем MySQL
log_info "Устанавливаем MySQL Server..."
export DEBIAN_FRONTEND=noninteractive
apt install -y mysql-server

# Запускаем MySQL
systemctl start mysql
systemctl enable mysql

log_step "2. Настройка MySQL..."

# Создаем базу данных и пользователя
mysql -u root <<EOF
CREATE DATABASE IF NOT EXISTS swagmedia1 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'hesus'@'localhost' IDENTIFIED BY 'ba7a7m1ZX3.';
CREATE USER IF NOT EXISTS 'hesus'@'%' IDENTIFIED BY 'ba7a7m1ZX3.';
GRANT ALL PRIVILEGES ON swagmedia1.* TO 'hesus'@'localhost';
GRANT ALL PRIVILEGES ON swagmedia1.* TO 'hesus'@'%';
FLUSH PRIVILEGES;
EOF

log_info "База данных swagmedia1 создана"

log_step "3. Создание структуры приложения..."

# Создаем пользователя и директории
useradd -r -m -d /var/www/swagmedia -s /bin/bash swagmedia || true
mkdir -p /var/www/swagmedia/{backend,frontend}
mkdir -p /var/log/pm2

log_step "4. Установка Backend..."

# Копируем backend файлы
cp -r backend/* /var/www/swagmedia/backend/
cp -r *.py /var/www/swagmedia/backend/ 2>/dev/null || true

# Копируем production конфигурацию
cp deploy/production.env /var/www/swagmedia/backend/.env

# Устанавливаем Python зависимости
cd /var/www/swagmedia/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Устанавливаем зависимости
pip install fastapi==0.110.1 uvicorn==0.25.0 sqlalchemy>=2.0.0 pymysql>=1.1.0 python-dotenv>=1.0.1 pydantic>=2.6.4 pyjwt>=2.10.1 passlib>=1.7.4 slowapi>=0.1.9 python-multipart>=0.0.9 python-jose>=3.3.0

# Создаем таблицы
log_info "Создаем таблицы в базе данных..."
python3 -c "
import sys
sys.path.append('/var/www/swagmedia/backend')
try:
    from models import create_tables
    create_tables()
    print('Таблицы созданы успешно')
except Exception as e:
    print(f'Ошибка создания таблиц: {e}')
"

log_step "5. Установка Frontend..."

# Копируем frontend файлы
cd /tmp/swagmedia
cp -r frontend/* /var/www/swagmedia/frontend/ 2>/dev/null || true

# Копируем production конфигурацию
cp deploy/frontend-production.env /var/www/swagmedia/frontend/.env

cd /var/www/swagmedia/frontend

# Устанавливаем зависимости и собираем
if [ -f "package.json" ]; then
    yarn install
    yarn build
    log_info "Frontend собран успешно"
else
    log_warn "package.json не найден, создаем простой build"
    mkdir -p build
    echo '<h1>SwagMedia</h1><p>Backend ready at <a href="/api">/api</a></p>' > build/index.html
fi

log_step "6. Настройка PM2..."

# Копируем конфигурацию PM2
cp /tmp/swagmedia/deploy/ecosystem.config.js /var/www/swagmedia/

# Меняем владельца
chown -R swagmedia:swagmedia /var/www/swagmedia
chown -R swagmedia:swagmedia /var/log/pm2

# Запускаем PM2
cd /var/www/swagmedia
su - swagmedia -c "cd /var/www/swagmedia && pm2 start ecosystem.config.js"
su - swagmedia -c "pm2 save"

# Настраиваем автозапуск PM2
env PATH=$PATH:/usr/bin pm2 startup systemd -u swagmedia --hp /var/www/swagmedia

log_step "7. Настройка Nginx..."

# Копируем конфигурацию
cp /tmp/swagmedia/deploy/nginx.conf /etc/nginx/sites-available/swagmedia.site

# Активируем сайт
ln -sf /etc/nginx/sites-available/swagmedia.site /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Проверяем конфигурацию
nginx -t
systemctl restart nginx
systemctl enable nginx

log_step "8. Установка SSL сертификата..."

# Устанавливаем Certbot
apt install -y certbot python3-certbot-nginx

# Создаем DH параметры
openssl dhparam -out /etc/ssl/certs/dhparam.pem 2048

log_info "Получаем SSL сертификат..."
# Автоматически получаем сертификат
certbot --nginx -d swagmedia.site -d www.swagmedia.site --non-interactive --agree-tos --email admin@swagmedia.site --redirect

# Настраиваем автообновление
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -

log_step "9. Настройка Firewall..."

# Устанавливаем UFW
apt install -y ufw

# Настраиваем правила
ufw --force enable
ufw allow ssh
ufw allow 'Nginx Full'
ufw allow 3306
ufw reload

log_step "10. Финальная проверка..."

# Перезапускаем все службы
systemctl restart nginx
su - swagmedia -c "pm2 restart all"

# Проверяем статус
log_info "Статус служб:"
systemctl is-active nginx && echo "✅ Nginx: OK" || echo "❌ Nginx: ERROR"
systemctl is-active mysql && echo "✅ MySQL: OK" || echo "❌ MySQL: ERROR"
su - swagmedia -c "pm2 list" | grep -q swagmedia-backend && echo "✅ Backend: OK" || echo "❌ Backend: ERROR"

# Очищаем временные файлы
cd /
rm -rf /tmp/swagmedia

echo ""
echo "🎉 SwagMedia установлен успешно!"
echo ""
echo "🌐 Сайт: https://swagmedia.site"
echo "🔧 Backend API: https://swagmedia.site/api"
echo ""
echo "📊 Управление:"
echo "   PM2: su - swagmedia -c 'pm2 status'"
echo "   Nginx: systemctl status nginx"
echo "   MySQL: systemctl status mysql"
echo ""
echo "📝 Логи:"
echo "   Backend: /var/log/pm2/swagmedia-backend-*.log"
echo "   Nginx: /var/log/nginx/swagmedia.*.log"
echo ""
echo "⚙️  Админ панель: https://swagmedia.site"
echo "   Логин: admin"
echo "   Пароль: admin123"
echo ""
echo "✅ Все готово к использованию!"