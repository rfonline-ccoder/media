#!/bin/bash

# SwagMedia Update Script
# Скрипт для обновления приложения без полного переустанавливания

set -e

echo "🔄 Обновляем SwagMedia..."

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
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Проверяем что запущено от root
if [ "$EUID" -ne 0 ]; then 
    log_error "Пожалуйста, запустите скрипт от root (sudo)"
    exit 1
fi

APP_DIR="/var/www/swagmedia"
BACKUP_DIR="/var/backups/swagmedia-$(date +%Y%m%d-%H%M%S)"

log_step "1. Создаем бэкап..."
mkdir -p $BACKUP_DIR
cp -r $APP_DIR $BACKUP_DIR/
log_info "Бэкап создан: $BACKUP_DIR"

log_step "2. Останавливаем приложение..."
su - swagmedia -c "pm2 stop all"

log_step "3. Обновляем код..."
# Здесь должен быть код для обновления из Git репозитория
# git pull origin main

log_step "4. Обновляем зависимости..."
cd $APP_DIR/backend
source venv/bin/activate
pip install -r requirements.txt

cd $APP_DIR/frontend
yarn install
yarn build

log_step "5. Применяем миграции БД..."
cd $APP_DIR/backend
source venv/bin/activate
python3 -c "from models import create_tables; create_tables()" 2>/dev/null || log_warn "Миграции не применены"

log_step "6. Запускаем приложение..."
chown -R swagmedia:swagmedia $APP_DIR
su - swagmedia -c "pm2 restart all"
systemctl reload nginx

log_info "✅ Обновление завершено успешно!"
echo "🌐 Сайт: https://swagmedia.site"
echo "📊 Статус: su - swagmedia -c 'pm2 status'"