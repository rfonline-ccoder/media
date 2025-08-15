# SwagMedia Production Deployment

Инструкции по деплою SwagMedia на продакшн сервер.

## Сервер
- **IP**: 89.169.1.168
- **Домен**: swagmedia.site
- **База данных**: MySQL (swagmedia1)
- **Пользователь БД**: hesus / ba7a7m1ZX3.

## Быстрый старт

### 1. Подготовка сервера (Ubuntu 20.04/22.04)

```bash
# Подключаемся к серверу
ssh root@89.169.1.168

# Скачиваем и запускаем установку
wget https://raw.githubusercontent.com/yourusername/swagmedia/main/deploy/install.sh
chmod +x install.sh
./install.sh
```

### 2. Деплой приложения

```bash
# Копируем файлы приложения на сервер
scp -r /app/* root@89.169.1.168:/tmp/swagmedia-deploy/

# На сервере запускаем деплой
ssh root@89.169.1.168
cd /tmp/swagmedia-deploy/deploy
chmod +x deploy.sh
./deploy.sh
```

### 3. Настройка DNS

Добавьте A-записи для домена swagmedia.site:

```
swagmedia.site.     A    89.169.1.168
www.swagmedia.site. A    89.169.1.168
```

## Структура файлов

```
/var/www/swagmedia/
├── backend/              # FastAPI приложение
│   ├── server.py
│   ├── models.py
│   ├── requirements.txt
│   ├── .env             # production.env
│   └── venv/            # Python virtual environment
├── frontend/            # React приложение
│   ├── src/
│   ├── build/           # Собранная версия для production
│   ├── package.json
│   └── .env             # frontend-production.env
└── ecosystem.config.js  # PM2 конфигурация
```

## Управление

### PM2 (Backend)
```bash
su - swagmedia
pm2 status                # Статус
pm2 restart swagmedia-backend
pm2 logs swagmedia-backend
pm2 monit                 # Мониторинг
```

### Nginx
```bash
systemctl status nginx
systemctl restart nginx
nginx -t                  # Проверка конфигурации
tail -f /var/log/nginx/swagmedia.access.log
```

### MySQL
```bash
systemctl status mysql
mysql -u hesus -p swagmedia1
```

### SSL Сертификаты
```bash
certbot certificates      # Статус сертификатов
certbot renew --dry-run   # Тест обновления
```

## Обновление приложения

```bash
cd /var/www/swagmedia
chmod +x update.sh
./update.sh
```

## Мониторинг и логи

### Логи приложений
- Backend: `/var/log/pm2/swagmedia-backend-*.log`
- Nginx: `/var/log/nginx/swagmedia.*.log`
- SSL: `/var/log/letsencrypt/letsencrypt.log`

### Мониторинг ресурсов
```bash
htop                      # CPU/Memory
df -h                     # Disk space
netstat -tulpn           # Network connections
```

## Резервное копирование

### Автоматический бэкап БД
```bash
# Добавить в crontab
0 2 * * * mysqldump -u hesus -pba7a7m1ZX3. swagmedia1 > /var/backups/swagmedia-$(date +\%Y\%m\%d).sql
```

### Бэкап файлов приложения
```bash
tar -czf /var/backups/swagmedia-files-$(date +%Y%m%d).tar.gz /var/www/swagmedia
```

## Безопасность

### Firewall (UFW)
```bash
ufw status                # Статус
ufw allow 22              # SSH
ufw allow 'Nginx Full'    # HTTP/HTTPS
ufw enable
```

### Fail2Ban (опционально)
```bash
apt install fail2ban
systemctl enable fail2ban
```

## Troubleshooting

### Backend не запускается
```bash
# Проверить логи
su - swagmedia -c "pm2 logs swagmedia-backend"

# Проверить зависимости
cd /var/www/swagmedia/backend
source venv/bin/activate
python3 server.py
```

### Frontend не собирается
```bash
cd /var/www/swagmedia/frontend
yarn install
yarn build
```

### База данных недоступна
```bash
# Проверить подключение
mysql -u hesus -p -h 89.169.1.168 swagmedia1

# Проверить статус MySQL
systemctl status mysql
```

### SSL проблемы
```bash
# Обновить сертификат
certbot renew

# Проверить конфигурацию
nginx -t
```

## Контакты

При возникновении проблем с деплоем проверьте:
1. Логи в `/var/log/`
2. Статус служб через `systemctl status`
3. PM2 статус через `pm2 status`