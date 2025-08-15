#!/bin/bash

# SwagMedia Deployment Script
# Скрипт для деплоя приложения на продакшн сервер

set -e

echo "🚀 Деплоим SwagMedia на продакшн..."

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
    log_error "Пожалуйста, запустите скрипт от root (sudo)"
    exit 1
fi

# Переменные
APP_DIR="/var/www/swagmedia"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"
DEPLOY_DIR="/tmp/swagmedia-deploy"

log_step "1. Подготовка к деплою..."

# Создаем временную директорию
mkdir -p $DEPLOY_DIR
cd $DEPLOY_DIR

# Клонируем или копируем код (в зависимости от того, откуда запускается)
if [ -d "/app" ]; then
    log_info "Копируем код из /app..."
    cp -r /app/* $DEPLOY_DIR/
else
    log_info "Скачиваем код из репозитория..."
    # git clone <your-repo-url> .
fi

log_step "2. Настройка backend..."

# Создаем backend директорию
mkdir -p $BACKEND_DIR
cp -r backend/* $BACKEND_DIR/ 2>/dev/null || true
cp -r *.py $BACKEND_DIR/ 2>/dev/null || true

# Копируем production конфигурацию
cp deploy/production.env $BACKEND_DIR/.env

# Устанавливаем Python зависимости
cd $BACKEND_DIR
log_info "Устанавливаем Python зависимости..."

# Создаем виртуальное окружение
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Устанавливаем зависимости
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    log_warn "requirements.txt не найден, устанавливаем базовые зависимости..."
    pip install fastapi uvicorn sqlalchemy pymysql python-dotenv pydantic passlib python-jose bcrypt slowapi
fi

# Создаем таблицы в базе данных
log_info "Создаем таблицы в базе данных..."
python3 -c "from models import create_tables; create_tables()" 2>/dev/null || log_warn "Не удалось создать таблицы автоматически"

log_step "3. Настройка frontend..."

# Создаем frontend директорию
mkdir -p $FRONTEND_DIR
cd $DEPLOY_DIR
cp -r frontend/* $FRONTEND_DIR/ 2>/dev/null || true

cd $FRONTEND_DIR

# Копируем production конфигурацию
cp $DEPLOY_DIR/deploy/frontend-production.env .env

# Устанавливаем Node.js зависимости
log_info "Устанавливаем Node.js зависимости..."
if [ -f "package.json" ]; then
    yarn install --production=false
    
    # Сборка production версии
    log_info "Собираем production версию frontend..."
    yarn build
else
    log_error "package.json не найден в frontend директории"
    exit 1
fi

log_step "4. Настройка Nginx..."

# Копируем конфигурацию Nginx
cp $DEPLOY_DIR/deploy/nginx.conf /etc/nginx/sites-available/swagmedia.site

# Включаем сайт
ln -sf /etc/nginx/sites-available/swagmedia.site /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Проверяем конфигурацию Nginx
nginx -t

log_step "5. Настройка PM2..."

# Копируем конфигурацию PM2
cp $DEPLOY_DIR/deploy/ecosystem.config.js $APP_DIR/

# Меняем владельца файлов
chown -R swagmedia:swagmedia $APP_DIR

# Запускаем PM2 как пользователь swagmedia
su - swagmedia -c "cd $APP_DIR && pm2 start ecosystem.config.js"
su - swagmedia -c "pm2 save"
su - swagmedia -c "pm2 startup"

# Включаем PM2 startup для автозапуска
env PATH=$PATH:/usr/bin pm2 startup systemd -u swagmedia --hp /var/www/swagmedia

log_step "6. Получение SSL сертификата..."

# Перезапускаем Nginx
systemctl restart nginx

# Получаем SSL сертификат
log_info "Получаем SSL сертификат для swagmedia.site..."
certbot --nginx -d swagmedia.site -d www.swagmedia.site --non-interactive --agree-tos --email admin@swagmedia.site

log_step "7. Финальная настройка..."

# Перезапускаем все службы
systemctl restart nginx
su - swagmedia -c "pm2 restart all"

# Настраиваем автоматическое обновление SSL
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -

# Очищаем временную директорию
rm -rf $DEPLOY_DIR

log_info "✅ Деплой завершен успешно!"
echo ""
echo "🌐 Сайт доступен по адресу: https://swagmedia.site"
echo "🔧 Управление PM2: su - swagmedia -c 'pm2 [command]'"
echo "📊 Статус служб:"
echo "   - Nginx: systemctl status nginx"
echo "   - PM2: su - swagmedia -c 'pm2 status'"
echo "   - MySQL: systemctl status mysql"
echo ""
echo "📝 Логи:"
echo "   - Nginx: /var/log/nginx/swagmedia.*.log"
echo "   - Backend: /var/log/pm2/swagmedia-backend-*.log"
echo "   - SSL: /var/log/letsencrypt/letsencrypt.log"