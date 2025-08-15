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
)

;


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
)

;


CREATE TABLE shop_items (
	id VARCHAR(36) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	description TEXT NOT NULL, 
	price INTEGER NOT NULL, 
	category VARCHAR(100) NOT NULL, 
	image_url VARCHAR(500), 
	created_at DATETIME, 
	PRIMARY KEY (id)
)

;


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
)

;


CREATE TABLE reports (
	id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36) NOT NULL, 
	links JSON NOT NULL, 
	status VARCHAR(20), 
	created_at DATETIME, 
	admin_comment TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;


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
)

;


CREATE TABLE ip_blacklist (
	id VARCHAR(36) NOT NULL, 
	ip_address VARCHAR(45) NOT NULL, 
	vk_link VARCHAR(255) NOT NULL, 
	blacklist_until DATETIME NOT NULL, 
	reason VARCHAR(255), 
	created_at DATETIME, 
	PRIMARY KEY (id)
)

;


CREATE TABLE media_access (
	id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36) NOT NULL, 
	media_user_id VARCHAR(36) NOT NULL, 
	access_type VARCHAR(20) NOT NULL, 
	accessed_at DATETIME, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;


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
)

;

