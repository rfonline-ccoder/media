#!/bin/bash

# Скрипт обновления .env файлов для продакшена

echo "🔧 Обновление конфигурации для продакшена..."

# Обновляем backend .env
cat > /root/media/backend/.env <<EOF
MYSQL_URL="mysql+pymysql://hesus:ba7a7m1ZX3.,@localhost:3306/swagmedia1"
CORS_ORIGINS="https://swagmedia.site,http://swagmedia.site,http://89.169.1.168"
EOF

# Обновляем frontend .env
cat > /root/media/frontend/.env <<EOF
REACT_APP_BACKEND_URL=https://swagmedia.site
WDS_SOCKET_PORT=443
EOF

echo "✅ Конфигурация обновлена"

# Пересобираем frontend если нужно
if [ "$1" = "rebuild" ]; then
    echo "🔄 Пересборка frontend..."
    cd /root/media/frontend
    yarn build
    echo "✅ Frontend пересобран"
fi

# Перезапускаем сервисы
echo "🔄 Перезапуск сервисов..."
pm2 restart swagmedia-backend
systemctl reload nginx

echo "✅ Все готово!"