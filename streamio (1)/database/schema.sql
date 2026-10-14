CREATE DATABASE IF NOT EXISTS streaming_platform_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_0900_ai_ci;

USE streaming_platform_db;

CREATE TABLE IF NOT EXISTS `user` (
  user_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(100) NOT NULL UNIQUE,
  password VARCHAR(255) NULL,
  phone VARCHAR(15) NULL,
  country VARCHAR(50) NULL,
  role ENUM('ADMIN', 'EDITOR', 'USER') NOT NULL DEFAULT 'USER'
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS plan (
  plan_id INT AUTO_INCREMENT PRIMARY KEY,
  plan_name VARCHAR(50) NOT NULL UNIQUE,
  price DECIMAL(8, 2) NOT NULL CHECK (price >= 0),
  duration_months INT NOT NULL CHECK (duration_months > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS category (
  category_id INT AUTO_INCREMENT PRIMARY KEY,
  category_name VARCHAR(50) NOT NULL UNIQUE,
  description VARCHAR(255) NULL
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS content (
  content_id INT AUTO_INCREMENT PRIMARY KEY,
  title VARCHAR(150) NOT NULL,
  release_year YEAR NULL,
  duration INT NULL COMMENT 'duration in minutes',
  rating DECIMAL(3, 1) NULL COMMENT 'editorial rating from 0 to 10',
  language VARCHAR(30) NULL,
  category_id INT NULL,
  INDEX idx_content_category (category_id),
  CONSTRAINT fk_content_category FOREIGN KEY (category_id)
    REFERENCES category(category_id) ON DELETE SET NULL,
  CONSTRAINT chk_content_rating CHECK (rating IS NULL OR rating BETWEEN 0 AND 10)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS subscription (
  subscription_id INT AUTO_INCREMENT PRIMARY KEY,
  start_date DATE NOT NULL,
  end_date DATE NULL,
  status ENUM('active', 'expired', 'cancelled') NOT NULL DEFAULT 'active',
  user_id INT NOT NULL,
  plan_id INT NOT NULL,
  INDEX idx_subscription_user (user_id),
  INDEX idx_subscription_plan (plan_id),
  CONSTRAINT fk_subscription_user FOREIGN KEY (user_id)
    REFERENCES `user`(user_id) ON DELETE CASCADE,
  CONSTRAINT fk_subscription_plan FOREIGN KEY (plan_id)
    REFERENCES plan(plan_id) ON DELETE RESTRICT,
  CONSTRAINT chk_subscription_dates CHECK (end_date IS NULL OR end_date >= start_date)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS payment (
  payment_number INT AUTO_INCREMENT PRIMARY KEY,
  payment_date DATE NOT NULL,
  payment_amount DECIMAL(8, 2) NOT NULL CHECK (payment_amount >= 0),
  payment_method VARCHAR(30) NULL,
  status ENUM('success', 'failed', 'refunded') NOT NULL DEFAULT 'success',
  subscription_id INT NOT NULL,
  INDEX idx_payment_subscription (subscription_id),
  CONSTRAINT fk_payment_subscription FOREIGN KEY (subscription_id)
    REFERENCES subscription(subscription_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS watchlist (
  watchlist_id INT AUTO_INCREMENT PRIMARY KEY,
  added_date DATE NOT NULL,
  user_id INT NOT NULL,
  content_id INT NOT NULL,
  UNIQUE KEY uq_watchlist_user_content (user_id, content_id),
  CONSTRAINT fk_watchlist_user FOREIGN KEY (user_id)
    REFERENCES `user`(user_id) ON DELETE CASCADE,
  CONSTRAINT fk_watchlist_content FOREIGN KEY (content_id)
    REFERENCES content(content_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS watch_history (
  history_id INT AUTO_INCREMENT PRIMARY KEY,
  watch_date DATE NOT NULL,
  watch_time TIME NULL,
  progress DECIMAL(5, 2) NULL COMMENT 'percentage watched',
  completed BOOLEAN NOT NULL DEFAULT FALSE,
  user_id INT NOT NULL,
  content_id INT NOT NULL,
  INDEX idx_watch_history_user (user_id),
  INDEX idx_watch_history_content (content_id),
  CONSTRAINT fk_watch_history_user FOREIGN KEY (user_id)
    REFERENCES `user`(user_id) ON DELETE CASCADE,
  CONSTRAINT fk_watch_history_content FOREIGN KEY (content_id)
    REFERENCES content(content_id) ON DELETE CASCADE,
  CONSTRAINT chk_watch_history_progress CHECK (progress IS NULL OR progress BETWEEN 0 AND 100)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS review (
  review_id INT AUTO_INCREMENT PRIMARY KEY,
  rating DECIMAL(3, 1) NOT NULL,
  comment VARCHAR(500) NULL,
  review_date DATE NOT NULL,
  user_id INT NOT NULL,
  content_id INT NOT NULL,
  UNIQUE KEY uq_review_user_content (user_id, content_id),
  INDEX idx_review_content (content_id),
  CONSTRAINT fk_review_user FOREIGN KEY (user_id)
    REFERENCES `user`(user_id) ON DELETE CASCADE,
  CONSTRAINT fk_review_content FOREIGN KEY (content_id)
    REFERENCES content(content_id) ON DELETE CASCADE,
  CONSTRAINT chk_review_rating CHECK (rating BETWEEN 0 AND 10)
) ENGINE=InnoDB;

-- This migration also supports the original supplied schema, where password
-- was NOT NULL. Admin-created users do not receive a fabricated password.
ALTER TABLE `user` MODIFY COLUMN password VARCHAR(255) NULL;