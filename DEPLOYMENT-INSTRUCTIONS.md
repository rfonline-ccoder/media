# 🚀 Инструкция по деплою SwagMedia на 89.169.1.168

## Быстрый деплой (рекомендуется)

### Шаг 1: Загрузка на сервер

Из текущей директории запустите:

```bash
./deploy/upload-to-server.sh
```

### Шаг 2: Установка на сервере

Подключитесь к серверу и запустите установку:

```bash
ssh root@89.169.1.168
cd /tmp/swagmedia
./deploy/quick-setup.sh
```

### Шаг 3: Проверка

Сайт будет доступен по адресу: https://swagmedia.site

**Админ панель:**
- Логин: `admin`  
- Пароль: `admin123`

---

## Ручная установка (альтернатива)

### 1. Подготовка сервера

```bash
ssh root@89.169.1.168
wget https://raw.githubusercontent.com/yourusername/swagmedia/main/deploy/install.sh
chmod +x install.sh
./install.sh
```

### 2. Копирование файлов

```bash
# Локально
scp -r /app/* root@89.169.1.168:/var/www/swagmedia/

# На сервере
cd /var/www/swagmedia
chmod +x deploy/*.sh
./deploy/deploy.sh
```

---

## Конфигурация

### База данных
- **Хост**: 89.169.1.168 (localhost на сервере)
- **База**: swagmedia1
- **Пользователь**: hesus
- **Пароль**: ba7a7m1ZX3.

### Домен
- **Основной**: swagmedia.site
- **Алиас**: www.swagmedia.site
- **SSL**: Автоматически через Let's Encrypt

### Порты
- **Frontend**: 80/443 (через Nginx)
- **Backend**: 8001 (внутренний, через PM2)
- **MySQL**: 3306

---

## Управление после установки

### PM2 (Backend)
```bash
su - swagmedia
pm2 status                    # Статус приложения
pm2 restart swagmedia-backend # Перезапуск
pm2 logs swagmedia-backend    # Просмотр логов
pm2 monit                     # Мониторинг
```

### Nginx
```bash
systemctl status nginx        # Статус веб-сервера
systemctl restart nginx       # Перезапуск
nginx -t                      # Проверка конфигурации
tail -f /var/log/nginx/swagmedia.access.log
```

### MySQL
```bash
systemctl status mysql        # Статус БД
mysql -u hesus -p swagmedia1  # Подключение к БД
```

### SSL сертификаты
```bash
certbot certificates          # Список сертификатов
certbot renew --dry-run      # Тест обновления
```

---

## Функции администрирования

После деплоя проверьте что работают:

### 1. ✅ ЧС (Черный список)
- **Endpoint**: `POST /api/admin/users/{user_id}/emergency-state`
- **Функция**: Блокировка аккаунта и IP на 1-365 дней
- **Тестирование**: Войдите в админ панель → Пользователи → Кнопка "ЧС"

### 2. ✅ Система предупреждений  
- **Endpoint**: `POST /api/admin/users/{user_id}/warning`
- **Функция**: Выдача предупреждений с автоматической блокировкой при 3/3
- **Тестирование**: Админ панель → Пользователи → Кнопка "Предупреждение"

### 3. ✅ Снять медиа
- **Endpoint**: `POST /api/admin/users/{user_id}/remove-from-media`  
- **Функция**: Полное удаление аккаунта из БД
- **Тестирование**: Админ панель → Пользователи → Кнопка "Снять медиа"

---

## Мониторинг и логи

### Основные логи
```bash
# Backend
tail -f /var/log/pm2/swagmedia-backend-*.log

# Nginx
tail -f /var/log/nginx/swagmedia.access.log
tail -f /var/log/nginx/swagmedia.error.log

# MySQL
tail -f /var/log/mysql/error.log

# SSL
tail -f /var/log/letsencrypt/letsencrypt.log
```

### Системные ресурсы
```bash
htop                          # CPU/Memory
df -h                         # Дисковое пространство  
netstat -tulpn               # Сетевые соединения
ufw status                   # Статус файрвола
```

---

## Обновление приложения

```bash
ssh root@89.169.1.168
cd /var/www/swagmedia
./update.sh
```

---

## Резервное копирование

### Автоматический бэкап БД
```bash
# Добавить в crontab
crontab -e

# Добавить строку:
0 2 * * * mysqldump -u hesus -pba7a7m1ZX3. swagmedia1 > /var/backups/swagmedia-$(date +\%Y\%m\%d).sql
```

### Бэкап файлов
```bash
tar -czf /var/backups/swagmedia-files-$(date +%Y%m%d).tar.gz /var/www/swagmedia
```

---

## Troubleshooting

### Проблемы с доменом
1. Проверьте DNS записи для swagmedia.site:
   ```
   swagmedia.site.     A    89.169.1.168
   www.swagmedia.site. A    89.169.1.168
   ```

2. Проверьте статус Nginx:
   ```bash
   systemctl status nginx
   nginx -t
   ```

### Проблемы с SSL
```bash
certbot certificates
certbot renew --force-renewal -d swagmedia.site
systemctl restart nginx
```

### Backend не запускается
```bash
su - swagmedia -c "pm2 logs swagmedia-backend"
cd /var/www/swagmedia/backend
source venv/bin/activate
python3 server.py  # Ручной запуск для диагностики
```

### База данных недоступна
```bash
systemctl status mysql
mysql -u hesus -p swagmedia1  # Проверка подключения
```

---

## Контакты и поддержка

При возникновении проблем:

1. Проверьте логи в `/var/log/`
2. Убедитесь что все службы запущены: `systemctl status nginx mysql`
3. Проверьте PM2: `su - swagmedia -c "pm2 status"`

**Основные команды диагностики:**
```bash
# Полная проверка системы
./deploy/health-check.sh  # (создается автоматически)

# Быстрая диагностика
curl -I https://swagmedia.site
curl -I https://swagmedia.site/api/health
```

---

**✨ После успешного деплоя SwagMedia будет полностью готов к использованию с автоматическим запуском, SSL сертификатами и всеми административными функциями!**