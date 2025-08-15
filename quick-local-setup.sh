#!/bin/bash

# SwagMedia - Быстрая локальная установка
# Этот скрипт поможет быстро запустить SwagMedia локально

set -e

echo "🚀 Быстрая установка SwagMedia для локальной разработки"
echo "=================================================="

# Цвета для логов
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

# Проверка системных требований
log_step "1. Проверка системных требований..."

# Проверяем Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d" " -f2)
    log_info "Python найден: $PYTHON_VERSION"
else
    log_error "Python 3 не найден! Установите Python 3.8+"
    exit 1
fi

# Проверяем Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    log_info "Node.js найден: $NODE_VERSION"
else
    log_error "Node.js не найден! Установите Node.js 16+"
    exit 1
fi

# Проверяем Yarn
if command -v yarn &> /dev/null; then
    YARN_VERSION=$(yarn --version)
    log_info "Yarn найден: $YARN_VERSION"
else
    log_warn "Yarn не найден, пытаемся установить..."
    npm install -g yarn
fi

# Проверяем MySQL
if command -v mysql &> /dev/null; then
    log_info "MySQL найден"
else
    log_warn "MySQL не найден. Убедитесь что у вас есть доступ к БД"
fi

log_step "2. Настройка Backend..."

# Переходим в директорию backend
cd backend

# Создаем виртуальное окружение если его нет
if [ ! -d "venv" ]; then
    log_info "Создаем виртуальное окружение..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
log_info "Активируем виртуальное окружение..."
source venv/bin/activate

# Обновляем pip
log_info "Обновляем pip..."
pip install --upgrade pip

# Устанавливаем зависимости
log_info "Устанавливаем Python зависимости..."
pip install -r requirements.txt

# Создаем .env файл если его нет
if [ ! -f ".env" ]; then
    log_info "Создаем .env файл из примера..."
    cp .env.example .env
    log_warn "Отредактируйте backend/.env с вашими настройками БД!"
fi

log_step "3. Настройка Frontend..."

# Переходим в директорию frontend
cd ../frontend

# Устанавливаем зависимости
log_info "Устанавливаем Node.js зависимости..."
yarn install

# Создаем .env файл если его нет
if [ ! -f ".env" ]; then
    log_info "Создаем .env файл из примера..."
    cp .env.example .env
fi

log_step "4. Проверка конфигурации..."

# Проверяем что .env файлы созданы
if [ -f "backend/.env" ] && [ -f "frontend/.env" ]; then
    log_info "Конфигурационные файлы созданы"
else
    log_error "Не удалось создать .env файлы"
    exit 1
fi

cd ..

log_step "5. Создание скриптов запуска..."

# Создаем скрипт запуска backend
cat > start-backend.sh << 'EOF'
#!/bin/bash
echo "🚀 Запуск SwagMedia Backend..."
cd backend
source venv/bin/activate
python server.py
EOF

# Создаем скрипт запуска frontend  
cat > start-frontend.sh << 'EOF'
#!/bin/bash
echo "🚀 Запуск SwagMedia Frontend..."
cd frontend
yarn start
EOF

# Создаем комбинированный скрипт
cat > start-all.sh << 'EOF'
#!/bin/bash
echo "🚀 Запуск SwagMedia (Backend + Frontend)..."

# Запуск backend в фоне
echo "Запуск Backend на порту 8001..."
cd backend && source venv/bin/activate && python server.py &
BACKEND_PID=$!

# Ожидание запуска backend
sleep 3

# Запуск frontend
echo "Запуск Frontend на порту 3000..."
cd ../frontend && yarn start &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "Для остановки нажмите Ctrl+C или выполните:"
echo "kill $BACKEND_PID $FRONTEND_PID"

# Ожидание завершения
wait
EOF

# Делаем скрипты исполняемыми
chmod +x start-backend.sh start-frontend.sh start-all.sh

log_info "✅ Установка завершена успешно!"
echo ""
echo "📋 Следующие шаги:"
echo ""
echo "1. 🗄️ Настройте базу данных:"
echo "   - Создайте БД: CREATE DATABASE swagmedia_local;"
echo "   - Создайте пользователя с правами доступа"
echo "   - Обновите backend/.env с настройками БД"
echo ""
echo "2. 🚀 Запустите приложение:"
echo "   ./start-all.sh          # Backend + Frontend"
echo "   ./start-backend.sh      # Только Backend"  
echo "   ./start-frontend.sh     # Только Frontend"
echo ""
echo "3. 🌐 Откройте в браузере:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8001"
echo "   API Docs: http://localhost:8001/docs"
echo ""
echo "4. 👤 Создайте админа (после первого запуска):"
echo "   cd backend && python create_admin.py"
echo ""
echo "📖 Подробная документация: LOCAL_SETUP.md"

log_warn "Не забудьте настроить базу данных перед запуском!"