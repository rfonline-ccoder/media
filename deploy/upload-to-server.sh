#!/bin/bash

# Скрипт для загрузки SwagMedia на продакшн сервер
# Server: 89.169.1.168

set -e

SERVER="89.169.1.168"
USER="root"
PROJECT_DIR="/app"
TEMP_DIR="/tmp/swagmedia"

echo "🚀 Загрузка SwagMedia на сервер $SERVER"

# Цвета
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Проверяем что мы в правильной директории
if [ ! -f "$PROJECT_DIR/backend/server.py" ]; then
    echo "❌ Ошибка: Не найден файл backend/server.py в $PROJECT_DIR"
    echo "Убедитесь что вы запускаете скрипт из корня проекта SwagMedia"
    exit 1
fi

log_info "Подготовка файлов для загрузки..."

# Создаем временный архив
cd $PROJECT_DIR
tar -czf /tmp/swagmedia.tar.gz \
    backend/ \
    frontend/ \
    deploy/ \
    *.py \
    *.md \
    --exclude=node_modules \
    --exclude=.git \
    --exclude=__pycache__ \
    --exclude=.env \
    --exclude=venv \
    --exclude=build

log_info "Загрузка на сервер $SERVER..."

# Загружаем архив
scp /tmp/swagmedia.tar.gz $USER@$SERVER:/tmp/

log_info "Распаковка на сервере..."

# Подключаемся и распаковываем
ssh $USER@$SERVER << 'EOF'
cd /tmp
rm -rf swagmedia
mkdir -p swagmedia
cd swagmedia
tar -xzf ../swagmedia.tar.gz
chmod +x deploy/*.sh
echo "✅ Файлы распакованы в /tmp/swagmedia"
ls -la deploy/
EOF

# Очищаем временный архив
rm -f /tmp/swagmedia.tar.gz

echo ""
echo "✅ Файлы успешно загружены на сервер!"
echo ""
echo "📋 Следующие шаги на сервере $SERVER:"
echo ""
echo "1. Подключитесь к серверу:"
echo "   ssh $USER@$SERVER"
echo ""
echo "2. Запустите установку:"
echo "   cd /tmp/swagmedia"
echo "   ./deploy/quick-setup.sh"
echo ""
echo "3. После установки сайт будет доступен по адресу:"
echo "   https://swagmedia.site"
echo ""
echo "🔑 Логин в админ панель:"
echo "   Логин: admin"
echo "   Пароль: admin123"