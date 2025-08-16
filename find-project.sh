#!/bin/bash

# Скрипт поиска файлов проекта SwagMedia
# Помогает найти где лежат папки backend/ и frontend/

echo "🔍 Поиск файлов проекта SwagMedia"
echo "================================="
echo ""

# Текущая информация
echo "📍 Текущая директория: $(pwd)"
echo "📍 Скрипт находится в: $(dirname "$(readlink -f "$0")" 2>/dev/null || dirname "$0")"
echo ""

# Проверяем различные места
echo "📋 Проверяем наличие файлов проекта:"
echo ""

check_location() {
    local path="$1"
    local name="$2"
    
    echo "📂 $name: $path"
    
    if [ -d "$path/backend" ]; then
        echo "   ✅ backend/ найдена"
    else
        echo "   ❌ backend/ отсутствует"
    fi
    
    if [ -d "$path/frontend" ]; then
        echo "   ✅ frontend/ найдена"  
    else
        echo "   ❌ frontend/ отсутствует"
    fi
    
    if [ -f "$path/quick-deploy.sh" ]; then
        echo "   ✅ quick-deploy.sh найден"
    else
        echo "   ❌ quick-deploy.sh отсутствует"
    fi
    
    # Проверяем готовность
    if [ -d "$path/backend" ] && [ -d "$path/frontend" ]; then
        echo "   🎯 ГОТОВО К ДЕПЛОЮ!"
        return 0
    else
        echo "   ⚠️  не готово"
        return 1
    fi
}

# Список мест для проверки
READY_COUNT=0

echo "1. Текущая директория:"
if check_location "$(pwd)" "Текущая папка"; then
    ((READY_COUNT++))
fi
echo ""

echo "2. Директория скрипта:"
SCRIPT_DIR="$(dirname "$(readlink -f "$0")" 2>/dev/null || dirname "$0")"
if check_location "$SCRIPT_DIR" "Папка скрипта"; then
    ((READY_COUNT++))
fi
echo ""

echo "3. /root/media:"
if check_location "/root/media" "Целевая папка"; then
    ((READY_COUNT++))
fi
echo ""

echo "4. /root:"
if check_location "/root" "Корень root"; then
    ((READY_COUNT++))
fi
echo ""

echo "5. Родительская директория:"
if check_location "$(dirname "$(pwd)")" "Родительская папка"; then
    ((READY_COUNT++))
fi
echo ""

# Поиск во всей системе (только в /root и /home)
echo "🔍 Поиск по всей системе (это может занять время)..."
FOUND_DIRS=$(find /root /home -name "backend" -type d 2>/dev/null | head -10)

if [ -n "$FOUND_DIRS" ]; then
    echo "📍 Найдены папки backend в:"
    echo "$FOUND_DIRS" | while read dir; do
        parent_dir="$(dirname "$dir")"
        if [ -d "$parent_dir/frontend" ]; then
            echo "   🎯 $parent_dir (полный проект!)"
        else
            echo "   📂 $parent_dir (только backend)"
        fi
    done
else
    echo "   ❌ Папки backend не найдены"
fi
echo ""

# Итоговый результат
echo "🎯 РЕЗУЛЬТАТ:"
echo "============="

if [ $READY_COUNT -gt 0 ]; then
    echo "✅ Найдено $READY_COUNT готовых к деплою локаций"
    echo ""
    echo "🚀 Для запуска установки:"
    echo "   1. Перейдите в папку с проектом"
    echo "   2. Запустите: ./quick-deploy.sh"
    echo ""
    echo "📋 Или укажите путь в интерактивном режиме при установке"
else
    echo "❌ Готовых к деплою проектов не найдено"
    echo ""
    echo "💡 Что нужно сделать:"
    echo "   1. Убедитесь что папки backend/ и frontend/ находятся в одном месте"
    echo "   2. Скопируйте все файлы проекта на сервер"
    echo "   3. Перейдите в папку с проектом перед запуском скрипта"
    echo ""
    echo "📁 Структура должна быть:"
    echo "   project-folder/"
    echo "   ├── backend/"
    echo "   ├── frontend/" 
    echo "   ├── quick-deploy.sh"
    echo "   └── ..."
fi

echo ""
echo "📖 Подробная документация: PRODUCTION-DEPLOY.md"