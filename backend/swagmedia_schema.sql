-- SwagMedia Database Schema (MySQL)
-- Generated automatically from SQLAlchemy models

CREATE DATABASE IF NOT EXISTS swagmedia_sql CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE swagmedia_sql;


CREATE TABLE users (
	id VARCHAR(36) NOT NULL, 
	login VARCHAR(100) NOT NULL, 
	password VARCHAR(255) NOT NULL, 
	nickname VARCHAR(100) NOT NULL, 
	vk_link VARCHAR(255) NOT NULL, 
	channel_link VARCHAR(255) NOT NULL, 
	balance INTEGER, 
	admin_level INTEGER, 
	is_approved BOOL, 
	media_type INTEGER, 
	warnings INTEGER, 
	previews_used INTEGER, 
	previews_limit INTEGER, 
	blacklist_until DATETIME, 
	registration_ip VARCHAR(45), 
	created_at DATETIME, 
	PRIMARY KEY (id)
);

-- Indexes for users table
CREATE UNIQUE INDEX ix_users_login ON users (login);
CREATE UNIQUE INDEX ix_users_nickname ON users (nickname);
CREATE INDEX ix_users_is_approved ON users (is_approved);
CREATE INDEX ix_users_media_type ON users (media_type);
CREATE INDEX ix_users_blacklist_until ON users (blacklist_until);


CREATE TABLE applications (
	id VARCHAR(36) NOT NULL, 
	nickname VARCHAR(100) NOT NULL, 
	login VARCHAR(100) NOT NULL, 
	password VARCHAR(255) NOT NULL, 
	vk_link VARCHAR(255) NOT NULL, 
	channel_link VARCHAR(255) NOT NULL, 
	status VARCHAR(20), 
	created_at DATETIME, 
	PRIMARY KEY (id)
);

-- Indexes for applications table
CREATE INDEX ix_applications_status ON applications (status);
CREATE INDEX ix_applications_created_at ON applications (created_at);


CREATE TABLE shop_items (
	id VARCHAR(36) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	description TEXT NOT NULL, 
	price INTEGER NOT NULL, 
	category VARCHAR(100) NOT NULL, 
	image_url VARCHAR(500), 
	created_at DATETIME, 
	PRIMARY KEY (id)
);

-- Indexes for shop_items table
CREATE INDEX ix_shop_items_category ON shop_items (category);
CREATE INDEX ix_shop_items_price ON shop_items (price);


CREATE TABLE purchases (
	id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36) NOT NULL, 
	item_id VARCHAR(36) NOT NULL, 
	quantity INTEGER NOT NULL, 
	total_price INTEGER NOT NULL, 
	status VARCHAR(20), 
	created_at DATETIME, 
	reviewed_at DATETIME, 
	admin_comment TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(item_id) REFERENCES shop_items (id)
);

-- Indexes for purchases table
CREATE INDEX ix_purchases_user_id ON purchases (user_id);
CREATE INDEX ix_purchases_status ON purchases (status);
CREATE INDEX ix_purchases_created_at ON purchases (created_at);


CREATE TABLE reports (
	id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36) NOT NULL, 
	links JSON NOT NULL, 
	status VARCHAR(20), 
	created_at DATETIME, 
	admin_comment TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Indexes for reports table
CREATE INDEX ix_reports_user_id ON reports (user_id);
CREATE INDEX ix_reports_status ON reports (status);
CREATE INDEX ix_reports_created_at ON reports (created_at);


CREATE TABLE user_ratings (
	id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36) NOT NULL, 
	rated_user_id VARCHAR(36) NOT NULL, 
	rating INTEGER NOT NULL, 
	comment TEXT, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(rated_user_id) REFERENCES users (id)
);

-- Indexes for user_ratings table
CREATE INDEX ix_user_ratings_user_id ON user_ratings (user_id);
CREATE INDEX ix_user_ratings_rated_user_id ON user_ratings (rated_user_id);
CREATE INDEX ix_user_ratings_rating ON user_ratings (rating);
CREATE INDEX ix_user_ratings_created_at ON user_ratings (created_at);


CREATE TABLE ip_blacklist (
	id VARCHAR(36) NOT NULL, 
	ip_address VARCHAR(45) NOT NULL, 
	vk_link VARCHAR(255) NOT NULL, 
	blacklist_until DATETIME NOT NULL, 
	reason VARCHAR(255), 
	created_at DATETIME, 
	PRIMARY KEY (id)
);

-- Indexes for ip_blacklist table
CREATE INDEX ix_ip_blacklist_ip_address ON ip_blacklist (ip_address);
CREATE INDEX ix_ip_blacklist_blacklist_until ON ip_blacklist (blacklist_until);
CREATE INDEX ix_ip_blacklist_created_at ON ip_blacklist (created_at);


CREATE TABLE media_access (
	id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36) NOT NULL, 
	media_user_id VARCHAR(36) NOT NULL, 
	access_type VARCHAR(20) NOT NULL, 
	accessed_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Indexes for media_access table
CREATE INDEX ix_media_access_user_id ON media_access (user_id);
CREATE INDEX ix_media_access_media_user_id ON media_access (media_user_id);
CREATE INDEX ix_media_access_access_type ON media_access (access_type);
CREATE INDEX ix_media_access_accessed_at ON media_access (accessed_at);


CREATE TABLE notifications (
	id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	message TEXT NOT NULL, 
	type VARCHAR(20), 
	`read` BOOL, 
	created_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

-- Indexes for notifications table
CREATE INDEX ix_notifications_user_id ON notifications (user_id);
CREATE INDEX ix_notifications_read ON notifications (`read`);
CREATE INDEX ix_notifications_created_at ON notifications (created_at);
CREATE INDEX ix_notifications_type ON notifications (type);

-- Insert default admin user
INSERT INTO users (id, login, password, nickname, vk_link, channel_link, balance, admin_level, is_approved, media_type) 
VALUES ('admin-id', 'admin', 'admin123', 'Administrator', 'https://vk.com/admin', 'https://t.me/admin', 10000, 1, 1, 1);

-- Insert default shop items
INSERT INTO shop_items (id, name, description, price, category) VALUES 
('1', 'VIP статус', 'Получите VIP статус на месяц', 500, 'Премиум'),
('2', 'Премиум аккаунт', 'Доступ к премиум функциям', 1000, 'Премиум'),
('3', 'Золотой значок', 'Эксклюзивный золотой значок', 750, 'Премиум'),
('4', 'Ускорение отчетов', 'Быстрая обработка ваших отчетов', 300, 'Буст'),
('5', 'Двойные медиа-коины', 'Удвоение получаемых MC на неделю', 400, 'Буст'),
('6', 'Приоритет в очереди', 'Приоритетная обработка заявок', 350, 'Буст'),
('7', 'Кастомная тема', 'Персональная тема интерфейса', 600, 'Дизайн'),
('8', 'Анимированный аватар', 'Возможность загрузки GIF аватара', 450, 'Дизайн'),
('9', 'Уникальная рамка', 'Эксклюзивная рамка профиля', 550, 'Дизайн');

