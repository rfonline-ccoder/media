# 🚀 SwagMedia Production Deploy

## 📦 Готовые скрипты для деплоя

В проекте есть 3 скрипта для различных сценариев деплоя:

### 1. 🏃‍♂️ Быстрый деплой - `quick-deploy.sh`
**Для быстрой установки на чистый Ubuntu 22 сервер**

```bash
# Скопируйте проект на сервер
scp -r /path/to/project root@your-server:/root/

# Запустите быструю установку
cd /root
chmod +x quick-deploy.sh
sudo ./quick-deploy.sh
```

**Что установит:**
- ✅ Node.js, Python, MySQL, Nginx
- ✅ PM2 для управления процессами
- ✅ Базовую конфигурацию Nginx
- ✅ Админ аккаунт (admin/admin123)
- ✅ SSL сертификат (опционально)

---

### 2. 🔧 Полный деплой - `deploy-production.sh`
**Для продакшн сервера с максимальными настройками**

```bash
cd /root
chmod +x deploy-production.sh
sudo ./deploy-production.sh
```

**Дополнительно включает:**
- ✅ Расширенные настройки безопасности
- ✅ Автоматический мониторинг
- ✅ Скрипты обновления
- ✅ Продвинутую конфигурацию Nginx
- ✅ Автообновление SSL сертификатов
- ✅ Системные оптимизации

---

### 3. 📋 Инструкция - `PRODUCTION-DEPLOY.md`
**Подробная документация по деплою и управлению**

Содержит:
- Пошаговые инструкции
- Команды управления PM2
- Настройки мониторинга
- Решение проблем
- Обновление проекта

---

## ⚡ Быстрый старт

### Минимальные требования:
- Ubuntu 22.04 LTS
- 2GB RAM
- 20GB диска
- Root доступ

### За 5 минут:

1. **Подготовьте сервер:**
```bash
# Обновите систему
apt update && apt upgrade -y
```

2. **Скопируйте проект:**
```bash
# Загрузите весь проект в /root/media
mkdir -p /root/media
# Скопируйте файлы: backend/, frontend/, *.sh, *.md
```

3. **Запустите установку:**
```bash
cd /root
chmod +x quick-deploy.sh
./quick-deploy.sh
```

4. **Настройте DNS:**
   - Направьте домен `swagmedia.site` на IP сервера
   - Получите SSL сертификат (будет предложено в процессе)

5. **Готово!** 
   - Сайт: https://swagmedia.site
   - Админ: admin/admin123

---

## 🔧 Управление после установки

### PM2 команды:
```bash
pm2 status          # Статус процессов
pm2 logs            # Просмотр логов
pm2 restart all     # Перезапуск всех сервисов
pm2 monit          # Мониторинг в реальном времени
```

### Nginx:
```bash
systemctl status nginx    # Статус
systemctl restart nginx   # Перезапуск  
nginx -t                 # Проверка конфигурации
```

### MySQL:
```bash
systemctl status mariadb  # Статус базы данных
mysql -u swagmedia -p    # Подключение к БД
```

### SSL:
```bash
certbot certificates     # Статус сертификатов
certbot renew           # Обновление сертификатов
```

---

## 📊 Мониторинг

После установки доступны скрипты:

```bash
# Полный отчет о состоянии системы
/root/swagmedia-monitor.sh

# Обновление проекта
/root/swagmedia-update.sh
```

---

## 🆘 Решение проблем

### Сервисы не запускаются:
```bash
pm2 delete all
pm2 start ecosystem.config.js
pm2 save
```

### Проблемы с SSL:
```bash
# Проверьте DNS
nslookup swagmedia.site

# Принудительное получение сертификата
certbot --nginx -d swagmedia.site --force-renewal
```

### Ошибки базы данных:
```bash
systemctl restart mariadb
mysql -u root -p -e "SHOW DATABASES;"
```

---

## 🌟 Особенности продакшн версии

✅ **Высокая доступность** - PM2 автоматически перезапускает упавшие процессы  
✅ **SSL/HTTPS** - Автоматическое получение и обновление сертификатов  
✅ **Безопасность** - Настроенный firewall и security headers  
✅ **Производительность** - Gzip сжатие и кэширование статики  
✅ **Мониторинг** - Логи и система мониторинга состояния  
✅ **Обновления** - Автоматизированная система обновления  

---

## 📞 Поддержка

После установки в системе будут созданы:
- Логи: `/var/log/pm2/`  
- Конфигурация: `/root/media/`
- Скрипты управления: `/root/swagmedia-*.sh`

**Документация:** Полные инструкции в `PRODUCTION-DEPLOY.md`

---

*SwagMedia - готов к продакшену за 5 минут! 🚀*