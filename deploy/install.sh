#!/bin/bash

# SwagMedia Production Installation Script
# Для Ubuntu 20.04/22.04
# Server: 89.169.1.168
# Domain: swagmedia.site

set -e

echo "🚀 Начинаем установку SwagMedia на продакшн сервер..."

# Цвета для логов
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Проверяем что запущено от root
if [ "$EUID" -ne 0 ]; then 
    log_error "Пожалуйста, запустите скрипт от root (sudo)"
    exit 1
fi

# Обновляем систему
log_info "Обновляем систему..."
apt update && apt upgrade -y

# Устанавливаем необходимые пакеты
log_info "Устанавливаем базовые пакеты..."
apt install -y curl wget git nginx software-properties-common apt-transport-https ca-certificates gnupg lsb-release

# Устанавливаем Node.js 18
log_info "Устанавливаем Node.js 18..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
apt install -y nodejs

# Устанавливаем Yarn
log_info "Устанавливаем Yarn..."
npm install -g yarn

# Устанавливаем Python 3.11 и pip
log_info "Устанавливаем Python 3.11..."
add-apt-repository ppa:deadsnakes/ppa -y
apt update
apt install -y python3.11 python3.11-pip python3.11-venv python3.11-dev

# Создаем симлинк для python3
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Устанавливаем PM2
log_info "Устанавливаем PM2..."
npm install -g pm2

# Устанавливаем MySQL Server
log_info "Устанавливаем MySQL Server..."
apt install -y mysql-server

# Настраиваем MySQL
log_info "Настраиваем MySQL..."
mysql -u root <<EOF
CREATE DATABASE IF NOT EXISTS swagmedia1 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'hesus'@'localhost' IDENTIFIED BY 'ba7a7m1ZX3.';
CREATE USER IF NOT EXISTS 'hesus'@'%' IDENTIFIED BY 'ba7a7m1ZX3.';
GRANT ALL PRIVILEGES ON swagmedia1.* TO 'hesus'@'localhost';
GRANT ALL PRIVILEGES ON swagmedia1.* TO 'hesus'@'%';
FLUSH PRIVILEGES;
EOF

# Создаем директорию для приложения
log_info "Создаем директорию приложения..."
mkdir -p /var/www/swagmedia
chown -R www-data:www-data /var/www/swagmedia

# Создаем пользователя для приложения
log_info "Создаем пользователя swagmedia..."
useradd -r -s /bin/bash -d /var/www/swagmedia swagmedia || true
usermod -a -G www-data swagmedia

# Создаем директории для логов
log_info "Создаем директории для логов..."
mkdir -p /var/log/pm2
mkdir -p /var/log/nginx
chown -R swagmedia:swagmedia /var/log/pm2

# Устанавливаем UFW Firewall
log_info "Настраиваем файрвол..."
ufw allow ssh
ufw allow 'Nginx Full'
ufw allow 3306  # MySQL
ufw --force enable

# Генерируем DH параметры для SSL
log_info "Генерируем DH параметры для SSL..."
openssl dhparam -out /etc/ssl/certs/dhparam.pem 2048

# Устанавливаем Certbot для SSL
log_info "Устанавливаем Certbot..."
apt install -y certbot python3-certbot-nginx

log_info "✅ Базовая установка завершена!"
log_warn "Следующие шаги:"
echo "1. Скопируйте файлы приложения в /var/www/swagmedia/"
echo "2. Запустите deploy.sh для завершения настройки"
echo "3. Получите SSL сертификат: certbot --nginx -d swagmedia.site"