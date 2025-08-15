#!/bin/bash

# SwagMedia Health Check Script
# Скрипт для проверки состояния всех компонентов системы

echo "🏥 SwagMedia Health Check"
echo "========================="

# Цвета
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_ok() {
    echo -e "${GREEN}✅ OK${NC}: $1"
}

check_error() {
    echo -e "${RED}❌ ERROR${NC}: $1"
}

check_warning() {
    echo -e "${YELLOW}⚠️  WARNING${NC}: $1"
}

echo "1. Системные службы:"

# Проверяем Nginx
if systemctl is-active --quiet nginx; then
    check_ok "Nginx is running"
else
    check_error "Nginx is not running"
fi

# Проверяем MySQL
if systemctl is-active --quiet mysql; then
    check_ok "MySQL is running"
else
    check_error "MySQL is not running"
fi

# Проверяем PM2
if su - swagmedia -c "pm2 list" | grep -q "swagmedia-backend" 2>/dev/null; then
    if su - swagmedia -c "pm2 list" | grep "swagmedia-backend" | grep -q "online"; then
        check_ok "PM2 Backend is running"
    else
        check_error "PM2 Backend is stopped"
    fi
else
    check_error "PM2 Backend not found"
fi

echo ""
echo "2. Сетевые проверки:"

# Проверяем порты
if netstat -tlpn | grep -q ":80 "; then
    check_ok "Port 80 (HTTP) is listening"
else
    check_error "Port 80 (HTTP) is not listening"
fi

if netstat -tlpn | grep -q ":443 "; then
    check_ok "Port 443 (HTTPS) is listening"
else
    check_warning "Port 443 (HTTPS) is not listening"
fi

if netstat -tlpn | grep -q ":8001 "; then
    check_ok "Port 8001 (Backend) is listening"
else
    check_error "Port 8001 (Backend) is not listening"
fi

if netstat -tlpn | grep -q ":3306 "; then
    check_ok "Port 3306 (MySQL) is listening"
else
    check_error "Port 3306 (MySQL) is not listening"
fi

echo ""
echo "3. HTTP доступность:"

# Проверяем основной сайт
if curl -s -o /dev/null -w "%{http_code}" http://localhost | grep -q "200\|301\|302"; then
    check_ok "HTTP site is accessible"
else
    check_error "HTTP site is not accessible"
fi

# Проверяем API
if curl -s http://localhost:8001 | grep -q "SwagMedia\|FastAPI\|API"; then
    check_ok "Backend API is responding"
else
    check_error "Backend API is not responding"
fi

echo ""
echo "4. База данных:"

# Проверяем подключение к MySQL
if mysql -u hesus -pba7a7m1ZX3. -e "USE swagmedia1; SHOW TABLES;" > /dev/null 2>&1; then
    check_ok "MySQL database connection works"
    
    # Проверяем таблицы
    TABLE_COUNT=$(mysql -u hesus -pba7a7m1ZX3. -s -e "USE swagmedia1; SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'swagmedia1';" 2>/dev/null)
    if [ "$TABLE_COUNT" -gt 0 ]; then
        check_ok "Database has $TABLE_COUNT tables"
    else
        check_warning "Database has no tables"
    fi
else
    check_error "Cannot connect to MySQL database"
fi

echo ""
echo "5. SSL сертификаты:"

if [ -f "/etc/letsencrypt/live/swagmedia.site/fullchain.pem" ]; then
    check_ok "SSL certificate exists"
    
    # Проверяем срок действия
    CERT_DAYS=$(openssl x509 -enddate -noout -in /etc/letsencrypt/live/swagmedia.site/cert.pem | cut -d= -f2 | xargs -I {} date -d {} +%s)
    NOW=$(date +%s)
    DAYS_LEFT=$(( (CERT_DAYS - NOW) / 86400 ))
    
    if [ "$DAYS_LEFT" -gt 30 ]; then
        check_ok "SSL certificate valid for $DAYS_LEFT days"
    elif [ "$DAYS_LEFT" -gt 7 ]; then
        check_warning "SSL certificate expires in $DAYS_LEFT days"
    else
        check_error "SSL certificate expires in $DAYS_LEFT days"
    fi
else
    check_error "SSL certificate not found"
fi

echo ""
echo "6. Дисковое пространство:"

DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    check_ok "Disk usage: ${DISK_USAGE}%"
elif [ "$DISK_USAGE" -lt 90 ]; then
    check_warning "Disk usage: ${DISK_USAGE}%"
else
    check_error "Disk usage: ${DISK_USAGE}% (critically high)"
fi

echo ""
echo "7. Память:"

MEM_USAGE=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
if [ "$MEM_USAGE" -lt 80 ]; then
    check_ok "Memory usage: ${MEM_USAGE}%"
elif [ "$MEM_USAGE" -lt 90 ]; then
    check_warning "Memory usage: ${MEM_USAGE}%"
else
    check_error "Memory usage: ${MEM_USAGE}% (high)"
fi

echo ""
echo "8. Логи (последние ошибки):"

# Проверяем ошибки в логах
ERROR_COUNT=$(tail -n 100 /var/log/nginx/swagmedia.error.log 2>/dev/null | wc -l)
if [ "$ERROR_COUNT" -eq 0 ]; then
    check_ok "No recent Nginx errors"
else
    check_warning "$ERROR_COUNT recent Nginx log entries"
fi

# Проверяем PM2 ошибки
if [ -f "/var/log/pm2/swagmedia-backend-error.log" ]; then
    PM2_ERRORS=$(tail -n 50 /var/log/pm2/swagmedia-backend-error.log 2>/dev/null | grep -i error | wc -l)
    if [ "$PM2_ERRORS" -eq 0 ]; then
        check_ok "No recent PM2 errors"
    else
        check_warning "$PM2_ERRORS recent PM2 errors"
    fi
fi

echo ""
echo "========================="
echo "Health check completed!"
echo ""
echo "📊 Quick commands:"
echo "   Status: systemctl status nginx mysql"
echo "   PM2: su - swagmedia -c 'pm2 status'"
echo "   Logs: tail -f /var/log/nginx/swagmedia.access.log"
echo "   API: curl http://localhost:8001"
echo ""
echo "🌐 Site: https://swagmedia.site"