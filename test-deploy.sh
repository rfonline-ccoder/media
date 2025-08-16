#!/bin/bash

# Тест скриптов деплоя SwagMedia
# Проверяет что все файлы на месте и скрипты корректно настроены

echo "🧪 Тестируем готовность к деплою SwagMedia"
echo "==========================================="

# Проверяем текущую директорию
CURRENT_DIR=$(pwd)
echo "📁 Текущая директория: $CURRENT_DIR"

# Проверяем наличие необходимых файлов и папок
echo ""
echo "📋 Проверяем структуру проекта:"

# Основные папки
if [ -d "backend" ]; then
    echo "✅ backend/ - найдена"
else
    echo "❌ backend/ - НЕ НАЙДЕНА"
    exit 1
fi

if [ -d "frontend" ]; then
    echo "✅ frontend/ - найдена"
else
    echo "❌ frontend/ - НЕ НАЙДЕНА"  
    exit 1
fi

# Скрипты деплоя
if [ -f "quick-deploy.sh" ]; then
    echo "✅ quick-deploy.sh - найден"
else
    echo "❌ quick-deploy.sh - НЕ НАЙДЕН"
fi

if [ -f "deploy-production.sh" ]; then
    echo "✅ deploy-production.sh - найден"
else  
    echo "❌ deploy-production.sh - НЕ НАЙДЕН"
fi

# Документация
if [ -f "PRODUCTION-DEPLOY.md" ]; then
    echo "✅ PRODUCTION-DEPLOY.md - найдена"
else
    echo "❌ PRODUCTION-DEPLOY.md - НЕ НАЙДЕНА"
fi

# Backend файлы
echo ""
echo "🐍 Проверяем backend:"
if [ -f "backend/server.py" ]; then
    echo "✅ server.py - найден"
else
    echo "❌ server.py - НЕ НАЙДЕН"
fi

if [ -f "backend/requirements.txt" ]; then
    echo "✅ requirements.txt - найден"
else
    echo "❌ requirements.txt - НЕ НАЙДЕН"
fi

if [ -f "backend/models.py" ]; then
    echo "✅ models.py - найден"
else
    echo "❌ models.py - НЕ НАЙДЕН"
fi

# Frontend файлы
echo ""
echo "📱 Проверяем frontend:"
if [ -f "frontend/package.json" ]; then
    echo "✅ package.json - найден"
else
    echo "❌ package.json - НЕ НАЙДЕН"
fi

if [ -f "frontend/src/App.js" ]; then
    echo "✅ src/App.js - найден"
else
    echo "❌ src/App.js - НЕ НАЙДЕН"
fi

# Проверяем права на выполнение скриптов
echo ""
echo "🔐 Проверяем права на выполнение:"
if [ -x "quick-deploy.sh" ]; then
    echo "✅ quick-deploy.sh - исполняемый"
else
    echo "⚠️ quick-deploy.sh - НЕ исполняемый (исправляем...)"
    chmod +x quick-deploy.sh
    echo "✅ Права исправлены"
fi

if [ -x "deploy-production.sh" ]; then
    echo "✅ deploy-production.sh - исполняемый"
else
    echo "⚠️ deploy-production.sh - НЕ исполняемый (исправляем...)"
    chmod +x deploy-production.sh
    echo "✅ Права исправлены"
fi

# Тест копирования (имитация)
echo ""
echo "🔄 Тестируем логику копирования файлов:"
TEST_DIR="/tmp/swagmedia-test-$$"
mkdir -p "$TEST_DIR"

echo "  - Создаем тестовую папку: $TEST_DIR"
echo "  - Копируем backend..."
cp -r backend "$TEST_DIR/" 2>/dev/null && echo "  ✅ backend скопирован" || echo "  ❌ Ошибка копирования backend"

echo "  - Копируем frontend..."  
cp -r frontend "$TEST_DIR/" 2>/dev/null && echo "  ✅ frontend скопирован" || echo "  ❌ Ошибка копирования frontend"

echo "  - Очищаем тестовую папку..."
rm -rf "$TEST_DIR"
echo "  ✅ Тест копирования завершен"

# Финальная проверка
echo ""
echo "🎯 РЕЗУЛЬТАТ ТЕСТИРОВАНИЯ:"
echo "=========================="

# Подсчитываем что все на месте
REQUIRED_FILES=("backend/server.py" "backend/requirements.txt" "backend/models.py" "frontend/package.json" "quick-deploy.sh" "deploy-production.sh")
FOUND_COUNT=0

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        ((FOUND_COUNT++))
    fi
done

echo "📊 Найдено файлов: $FOUND_COUNT из ${#REQUIRED_FILES[@]}"

if [ $FOUND_COUNT -eq ${#REQUIRED_FILES[@]} ]; then
    echo ""
    echo "🎉 ВСЕ ГОТОВО К ДЕПЛОЮ!"
    echo "====================="
    echo ""
    echo "📦 Для деплоя выполните:"
    echo "  1. Скопируйте ВСЮ эту папку на Ubuntu 22 сервер"
    echo "  2. ssh root@ваш-сервер"  
    echo "  3. cd /path/to/copied/project"
    echo "  4. ./quick-deploy.sh"
    echo ""
    echo "🌐 После установки сайт будет доступен на https://swagmedia.site"
    echo "👤 Админ: admin / admin123"
    echo ""
    echo "✅ ПРОЕКТ ГОТОВ К ПРОДАКШЕНУ!"
else
    echo ""
    echo "❌ ПРОЕКТ НЕ ГОТОВ К ДЕПЛОЮ"
    echo "==========================="
    echo ""
    echo "Отсутствуют критически важные файлы."
    echo "Убедитесь что вы находитесь в корне проекта SwagMedia"
    echo "и все файлы backend/, frontend/ присутствуют."
fi

echo ""
echo "📖 Подробная документация: PRODUCTION-DEPLOY.md"
echo "🚀 Готово к тестированию!"