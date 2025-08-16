# 🚀 SwagMedia Production Deploy

## Автоматическая установка на Ubuntu 22 Server

### 📋 Требования
- Ubuntu 22.04 LTS сервер
- Root доступ
- Домен `swagmedia.site` направленный на IP сервера
- Минимум 2GB RAM и 20GB диска

### 🎯 Быстрая установка

1. **Загрузите проект на сервер:**
```bash
# Скопируйте весь проект в /root/media
scp -r /path/to/project root@your-server-ip:/root/
```

2. **Запустите автоматическую установку:**
```bash
cd /root
chmod +x deploy-production.sh
./deploy-production.sh
```

### 🔧 Что делает скрипт автоматически:

#### Системные компоненты:
- ✅ Обновляет Ubuntu 22
- ✅ Устанавливает Node.js 20 LTS
- ✅ Устанавливает Python 3.11
- ✅ Устанавливает MySQL/MariaDB
- ✅ Устанавливает Nginx
- ✅ Настраивает UFW Firewall

#### PM2 Management:
- ✅ Устанавливает PM2 глобально
- ✅ Настраивает автозапуск PM2
- ✅ Создает конфигурацию для backend и frontend
- ✅ Запускает процессы с автоперезапуском

#### База данных:
- ✅ Создает базу данных `swagmedia_prod`
- ✅ Создает пользователя `swagmedia_user`
- ✅ Инициализирует таблицы
- ✅ Создает админ аккаунт (admin/admin123)

#### Nginx + SSL:
- ✅ Настраивает виртуальный хост для `swagmedia.site`
- ✅ Настраивает проксирование на PM2 процессы
- ✅ Получает SSL сертификат от Let's Encrypt
- ✅ Настраивает автообновление SSL

#### Безопасность:
- ✅ Настраивает CORS
- ✅ Добавляет security headers
- ✅ Настраивает gzip сжатие
- ✅ Конфигурирует SSL с современными протоколами

### 📁 Структура после установки:

```
/root/media/
├── backend/
│   ├── venv/              # Python virtual environment
│   ├── server.py          # FastAPI приложение
│   ├── models.py          # SQLAlchemy модели
│   ├── requirements.txt   # Python зависимости
│   └── .env              # Backend конфигурация
├── frontend/
│   ├── build/            # Собранное React приложение
│   ├── src/              # React исходники
│   ├── package.json      # Node.js зависимости
│   └── .env              # Frontend конфигурация
└── ecosystem.config.js   # PM2 конфигурация
```

### 🎛️ Управление сервисами:

#### PM2 команды:
```bash
# Статус всех процессов
pm2 status

# Перезапуск всех сервисов
pm2 restart all

# Просмотр логов
pm2 logs

# Перезапуск конкретного сервиса
pm2 restart swagmedia-backend
pm2 restart swagmedia-frontend

# Мониторинг в реальном времени
pm2 monit
```

#### Системные сервисы:
```bash
# Nginx
systemctl status nginx
systemctl restart nginx
systemctl reload nginx

# MySQL
systemctl status mariadb
systemctl restart mariadb

# Проверка портов
netstat -tlnp | grep :80
netstat -tlnp | grep :443
netstat -tlnp | grep :3000
netstat -tlnp | grep :8001
```

### 📊 Мониторинг:

#### Автоматический скрипт мониторинга:
```bash
# Запуск отчета о состоянии системы
/root/swagmedia-monitor.sh
```

#### Логи приложения:
```bash
# Backend логи
tail -f /var/log/pm2/swagmedia-backend.log

# Frontend логи  
tail -f /var/log/pm2/swagmedia-frontend.log

# Nginx логи
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### 🔄 Обновление проекта:

```bash
# Автоматическое обновление (если есть git репозиторий)
/root/swagmedia-update.sh

# Ручное обновление backend
cd /root/media/backend
source venv/bin/activate
pip install -r requirements.txt
pm2 restart swagmedia-backend

# Ручное обновление frontend
cd /root/media/frontend
yarn install
yarn build
pm2 restart swagmedia-frontend
```

### 🔐 SSL сертификат:

#### Статус сертификата:
```bash
certbot certificates
```

#### Ручное обновление:
```bash
certbot renew
systemctl reload nginx
```

### 🗄️ База данных:

#### Подключение к MySQL:
```bash
mysql -u swagmedia_user -p swagmedia_prod
# Пароль: SwagMedia2024!Production
```

#### Бэкап базы данных:
```bash
mysqldump -u swagmedia_user -p swagmedia_prod > backup_$(date +%Y%m%d).sql
```

#### Восстановление из бэкапа:
```bash
mysql -u swagmedia_user -p swagmedia_prod < backup_20240815.sql
```

### 🌐 Доступ к сайту:

- **Основной сайт:** https://swagmedia.site
- **API документация:** https://swagmedia.site/api/docs
- **Админ панель:** https://swagmedia.site (логин: admin, пароль: admin123)

### 🆘 Troubleshooting:

#### Проблемы с SSL:
```bash
# Проверка DNS
nslookup swagmedia.site

# Принудительное получение сертификата
certbot --nginx -d swagmedia.site --force-renewal
```

#### Проблемы с PM2:
```bash
# Полный перезапуск PM2
pm2 kill
pm2 resurrect

# Обновление PM2 конфигурации
pm2 delete all
pm2 start ecosystem.config.js
pm2 save
```

#### Проблемы с базой данных:
```bash
# Проверка статуса MySQL
systemctl status mariadb

# Перезапуск MySQL
systemctl restart mariadb

# Проверка подключения
mysql -u swagmedia_user -p -e "SELECT 1"
```

### 📱 Мобильная оптимизация:

Сайт автоматически оптимизирован для:
- ✅ Мобильные устройства
- ✅ Планшеты
- ✅ Десктоп
- ✅ PWA поддержка

### 🔧 Дополнительные настройки:

#### Изменение домена:
1. Измените переменную `DOMAIN` в скрипте
2. Обновите DNS записи
3. Перезапустите скрипт

#### Изменение портов:
1. Измените `BACKEND_PORT` и `FRONTEND_PORT`
2. Обновите UFW правила
3. Обновите Nginx конфигурацию

#### Масштабирование:
```bash
# Увеличение количества PM2 процессов
pm2 scale swagmedia-backend 4  # 4 процесса backend
pm2 scale swagmedia-frontend 2 # 2 процесса frontend
```

---

## 🎉 Готово!

После успешного запуска скрипта ваш SwagMedia сайт будет полностью готов к работе на продакшене с автоматическим SSL, мониторингом и высокой доступностью через PM2.

**Поддержка:** admin@swagmedia.site