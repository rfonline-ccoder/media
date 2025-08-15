-- SwagMedia Database Initialization Script
-- Полная схема базы данных с начальными данными

USE swagmedia1;

-- Создание таблиц
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    login VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    nickname VARCHAR(100) NOT NULL UNIQUE,
    vk_link VARCHAR(255) NOT NULL,
    channel_link VARCHAR(255) NOT NULL,
    balance INT DEFAULT 0,
    admin_level INT DEFAULT 0,
    is_approved BOOLEAN DEFAULT FALSE,
    media_type INT DEFAULT 0,
    warnings INT DEFAULT 0,
    previews_used INT DEFAULT 0,
    previews_limit INT DEFAULT 3,
    blacklist_until DATETIME NULL,
    registration_ip VARCHAR(45) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_login (login),
    INDEX idx_nickname (nickname),
    INDEX idx_is_approved (is_approved),
    INDEX idx_media_type (media_type),
    INDEX idx_blacklist_until (blacklist_until)
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS applications (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    nickname VARCHAR(100) NOT NULL,
    login VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    vk_link VARCHAR(255) NOT NULL,
    channel_link VARCHAR(255) NOT NULL,
    registration_ip VARCHAR(45) NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS shop_items (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    price INT NOT NULL,
    category VARCHAR(100) NOT NULL,
    image_url VARCHAR(500) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_category (category),
    INDEX idx_price (price)
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS purchases (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    item_id VARCHAR(36) NOT NULL,
    quantity INT NOT NULL,
    total_price INT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    reviewed_at DATETIME NULL,
    admin_comment TEXT NULL,
    
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS reports (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    links JSON NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    admin_comment TEXT NULL,
    
    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS user_ratings (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    rated_user_id VARCHAR(36) NOT NULL,
    rating INT NOT NULL,
    comment TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user_id (user_id),
    INDEX idx_rated_user_id (rated_user_id),
    INDEX idx_rating (rating),
    INDEX idx_created_at (created_at),
    UNIQUE KEY unique_rating (user_id, rated_user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (rated_user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ip_blacklist (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    ip_address VARCHAR(45) NOT NULL,
    vk_link VARCHAR(255) NOT NULL,
    blacklist_until DATETIME NOT NULL,
    reason VARCHAR(255) DEFAULT 'User exceeded preview limit',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_ip_address (ip_address),
    INDEX idx_blacklist_until (blacklist_until),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS media_access (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    media_user_id VARCHAR(36) NOT NULL,
    access_type VARCHAR(20) NOT NULL,
    accessed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user_id (user_id),
    INDEX idx_media_user_id (media_user_id),
    INDEX idx_access_type (access_type),
    INDEX idx_accessed_at (accessed_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS notifications (
    id VARCHAR(36) NOT NULL PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(20) DEFAULT 'info',
    `read` BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_user_id (user_id),
    INDEX idx_read (`read`),
    INDEX idx_created_at (created_at),
    INDEX idx_type (type),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Вставка начальных данных

-- Админ пользователь
INSERT IGNORE INTO users (id, login, password, nickname, vk_link, channel_link, balance, admin_level, is_approved, media_type, created_at) 
VALUES ('admin-id-123', 'admin', 'admin123', 'Administrator', 'https://vk.com/admin', 'https://t.me/admin', 10000, 1, 1, 1, NOW());

-- Тестовые пользователи
INSERT IGNORE INTO users (id, login, password, nickname, vk_link, channel_link, balance, admin_level, is_approved, media_type, created_at) 
VALUES 
('test-user-1', 'testuser1', 'password123', 'TestUser1', 'https://vk.com/testuser1', 'https://t.me/testuser1', 500, 0, 1, 0, NOW()),
('test-user-2', 'testuser2', 'password123', 'TestUser2', 'https://vk.com/testuser2', 'https://t.me/testuser2', 1500, 0, 1, 1, NOW()),
('test-user-3', 'freeuser', 'password123', 'FreeUser', 'https://vk.com/freeuser', 'https://t.me/freeuser', 100, 0, 1, 0, NOW());

-- Магазин товаров
INSERT IGNORE INTO shop_items (id, name, description, price, category, created_at) VALUES 
('1', 'VIP статус', 'Получите VIP статус на месяц с дополнительными привилегиями', 500, 'Премиум', NOW()),
('2', 'Премиум аккаунт', 'Расширенные возможности и приоритетная поддержка', 1000, 'Премиум', NOW()),
('3', 'Золотой значок', 'Эксклюзивный золотой значок для вашего профиля', 300, 'Премиум', NOW()),
('4', 'Ускорение отчетов', 'Быстрое одобрение ваших отчетов в течение 24 часов', 200, 'Буст', NOW()),
('5', 'Двойные медиа-коины', 'Получайте в 2 раза больше медиа-коинов за отчеты на неделю', 400, 'Буст', NOW()),
('6', 'Приоритет в очереди', 'Ваши заявки обрабатываются в первую очередь', 150, 'Буст', NOW()),
('7', 'Кастомная тема', 'Персональная цветовая схема для вашего профиля', 250, 'Дизайн', NOW()),
('8', 'Анимированный аватар', 'Возможность использовать GIF в качестве аватара', 350, 'Дизайн', NOW()),
('9', 'Уникальная рамка', 'Красивая рамка вокруг вашего профиля', 180, 'Дизайн', NOW());

-- Тестовые отчеты
INSERT IGNORE INTO reports (id, user_id, links, status, created_at, admin_comment) VALUES
('report-1', 'test-user-1', '[{"url": "https://example.com/video1", "views": 1500}]', 'approved', NOW(), 'Отличный контент!'),
('report-2', 'test-user-2', '[{"url": "https://example.com/video2", "views": 2300}]', 'pending', NOW(), NULL),
('report-3', 'test-user-3', '[{"url": "https://example.com/video3", "views": 800}]', 'approved', NOW(), 'Хороший материал');

-- Тестовые рейтинги
INSERT IGNORE INTO user_ratings (id, user_id, rated_user_id, rating, comment, created_at) VALUES
('rating-1', 'test-user-1', 'test-user-2', 5, 'Отличный контент, рекомендую!', NOW()),
('rating-2', 'test-user-2', 'test-user-1', 4, 'Хороший материал, есть что улучшить', NOW()),
('rating-3', 'admin-id-123', 'test-user-2', 5, 'Превосходное качество!', NOW());

-- Уведомления для тестовых пользователей
INSERT IGNORE INTO notifications (id, user_id, title, message, type, created_at) VALUES
('notif-1', 'test-user-1', 'Добро пожаловать!', 'Добро пожаловать в SwagMedia! Ваш аккаунт успешно активирован.', 'success', NOW()),
('notif-2', 'test-user-2', 'Отчет одобрен', 'Ваш отчет был одобрен администратором. На ваш баланс начислено 23 MC.', 'success', NOW()),
('notif-3', 'test-user-3', 'Информация', 'Не забудьте ознакомиться с правилами платформы.', 'info', NOW());

-- Тестовые записи доступа к медиа
INSERT IGNORE INTO media_access (id, user_id, media_user_id, access_type, accessed_at) VALUES
('access-1', 'test-user-1', 'test-user-2', 'preview', NOW()),
('access-2', 'test-user-2', 'test-user-1', 'full', NOW()),
('access-3', 'admin-id-123', 'test-user-2', 'full', NOW());

-- Обновляем статистику
ANALYZE TABLE users, shop_items, reports, user_ratings, notifications, media_access, purchases, applications, ip_blacklist;

SELECT 'Database initialized successfully!' as status;
SELECT COUNT(*) as user_count FROM users;
SELECT COUNT(*) as shop_items_count FROM shop_items;
SELECT COUNT(*) as reports_count FROM reports;