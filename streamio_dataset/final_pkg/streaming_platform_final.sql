-- =========================================================
-- STREAMING PLATFORM MANAGEMENT SYSTEM  (MySQL 8.x)
-- Phase 2: DDL (normalized to 3NF) + DML (sample dataset)
-- =========================================================

DROP DATABASE IF EXISTS streaming_platform_db;
CREATE DATABASE streaming_platform_db;
USE streaming_platform_db;

-- =========================================================
-- DDL
-- =========================================================

-- 1. USER
CREATE TABLE user (
    user_id     INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    email       VARCHAR(100) NOT NULL UNIQUE,
    password    VARCHAR(255) NOT NULL,
    phone       VARCHAR(15),
    country     VARCHAR(50),
    role        ENUM('ADMIN','EDITOR','USER') NOT NULL DEFAULT 'USER'
);

-- 2. PLAN  (NEW - removes the plan_name -> price dependency from subscription, 3NF)
CREATE TABLE plan (
    plan_id         INT AUTO_INCREMENT PRIMARY KEY,
    plan_name       VARCHAR(50) NOT NULL UNIQUE,
    price           DECIMAL(8,2) NOT NULL CHECK (price >= 0),
    duration_months INT NOT NULL CHECK (duration_months > 0)
);

-- 3. SUBSCRIPTION  (user 1:N subscription, plan 1:N subscription)
CREATE TABLE subscription (
    subscription_id INT AUTO_INCREMENT PRIMARY KEY,
    start_date      DATE NOT NULL,
    end_date        DATE,
    status          ENUM('active','expired','cancelled') NOT NULL DEFAULT 'active',
    user_id         INT NOT NULL,
    plan_id         INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user(user_id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES plan(plan_id) ON DELETE RESTRICT,
    CHECK (end_date IS NULL OR end_date >= start_date)
);

-- 4. PAYMENT  (subscription 1:N payment)
CREATE TABLE payment (
    payment_number  INT AUTO_INCREMENT PRIMARY KEY,
    payment_date    DATE NOT NULL,
    payment_amount  DECIMAL(8,2) NOT NULL CHECK (payment_amount >= 0),
    payment_method  VARCHAR(30),
    status          ENUM('success','failed','refunded') NOT NULL DEFAULT 'success',
    subscription_id INT NOT NULL,
    FOREIGN KEY (subscription_id) REFERENCES subscription(subscription_id) ON DELETE CASCADE
);

-- 5. CATEGORY
CREATE TABLE category (
    category_id    INT AUTO_INCREMENT PRIMARY KEY,
    category_name  VARCHAR(50) NOT NULL UNIQUE,
    description    VARCHAR(255)
);

-- 6. CONTENT  (category 1:N content)
CREATE TABLE content (
    content_id     INT AUTO_INCREMENT PRIMARY KEY,
    title          VARCHAR(150) NOT NULL,
    release_year   YEAR,
    duration       INT COMMENT 'duration in minutes',
    rating         DECIMAL(3,1) COMMENT 'editorial rating 0-10',
    language       VARCHAR(30),
    category_id    INT,
    FOREIGN KEY (category_id) REFERENCES category(category_id) ON DELETE SET NULL,
    CHECK (rating IS NULL OR rating BETWEEN 0 AND 10)
);

-- 7. WATCHLIST  (user M:N content)
CREATE TABLE watchlist (
    watchlist_id   INT AUTO_INCREMENT PRIMARY KEY,
    added_date     DATE NOT NULL,
    user_id        INT NOT NULL,
    content_id     INT NOT NULL,
    FOREIGN KEY (user_id)    REFERENCES user(user_id)       ON DELETE CASCADE,
    FOREIGN KEY (content_id) REFERENCES content(content_id) ON DELETE CASCADE,
    UNIQUE (user_id, content_id)
);

-- 8. WATCH_HISTORY
CREATE TABLE watch_history (
    history_id     INT AUTO_INCREMENT PRIMARY KEY,
    watch_date     DATE NOT NULL,
    watch_time     TIME,
    progress       DECIMAL(5,2) COMMENT 'percentage watched',
    completed      BOOLEAN DEFAULT FALSE,
    user_id        INT NOT NULL,
    content_id     INT NOT NULL,
    FOREIGN KEY (user_id)    REFERENCES user(user_id)       ON DELETE CASCADE,
    FOREIGN KEY (content_id) REFERENCES content(content_id) ON DELETE CASCADE,
    CHECK (progress IS NULL OR progress BETWEEN 0 AND 100)
);

-- 9. REVIEW  (one review per user per content)
CREATE TABLE review (
    review_id      INT AUTO_INCREMENT PRIMARY KEY,
    rating         DECIMAL(3,1) NOT NULL CHECK (rating BETWEEN 0 AND 10),
    comment        VARCHAR(500),
    review_date    DATE NOT NULL,
    user_id        INT NOT NULL,
    content_id     INT NOT NULL,
    FOREIGN KEY (user_id)    REFERENCES user(user_id)       ON DELETE CASCADE,
    FOREIGN KEY (content_id) REFERENCES content(content_id) ON DELETE CASCADE,
    UNIQUE (user_id, content_id)
);

-- Indexes for common dashboard queries
CREATE INDEX idx_content_category  ON content(category_id);
CREATE INDEX idx_history_user      ON watch_history(user_id);
CREATE INDEX idx_history_content   ON watch_history(content_id);
CREATE INDEX idx_payment_sub       ON payment(subscription_id);

-- =========================================================
-- DML: SAMPLE DATASET
-- (passwords are bcrypt hashes; demo logins are listed in README.md)
-- =========================================================

INSERT INTO user (name, email, password, phone, country, role) VALUES
('Admin',         'admin@streamio.com',  '$2b$10$bAbdGD2Z4kF2mP6NJw4lUuVfNp7IKUfH8fo3E/lKpEelWkM/Ma3ga', NULL,         'India',  'ADMIN'),
('Content Editor','editor@streamio.com', '$2b$10$7XVhceTrcAwfUoXYM5igoOOKxThX/z8RI9rX5MRx2WBHeUyiigvjW',  NULL,         'India',  'EDITOR'),
('Aarav Sharma',  'aarav@example.com',   '$2b$10$y6guZLnSaYtYWnd8qOeixumx.8qht0Ble9ltb1c92vEk0sc6Cq8Fi',     '9876543210', 'India',  'USER'),
('Riya Kapoor',   'riya@example.com',    '$2b$10$XUtDlhB23LLZHZbbvIQ3aOefJkU6lD/VSb2U2VBbZuC0jnPdA4Z36',     '9876543211', 'India',  'USER'),
('John Smith',    'john@example.com',    '$2b$10$w1.3JzMZrGMoVGdgrOgyx.ZXbOwiCsPlWJGnimo3Ri8VEUzjkr2oW',     '4085551234', 'USA',    'USER'),
('Emma Watson',   'emma@example.com',    '$2b$10$kuTYEk/QpCRcPJnd7cWaVu/8nzRmx44YBGOuqOhM12v4j87BDHGqO',     '4415551234', 'UK',     'USER'),
('Vikram Singh',  'vikram@example.com',  '$2b$10$lwgQL2ScivhGkN58oG7ZuO1dC7AfLr.jGFwRr5ns6TgQX1PhxEUSa',     '9876543212', 'India',  'USER'),
('Priya Nair',    'priya@example.com',   '$2b$10$LYKKgwsMMfIiyykof8FJweEy4QNn5fBMNk./2Rn7bx.sfjKHxDWTW',     '9876543213', 'India',  'USER'),
('Liam Johnson',  'liam@example.com',    '$2b$10$uMO.1X9/9USg9QQgKzQnU.Jla/y7WGB5nPLd4Zg.OP2Z52NbJHP9K',     '6475551234', 'Canada', 'USER'),
('Sofia Garcia',  'sofia@example.com',   '$2b$10$cVR5i8zuSLpUM9ZOeiFDI.lGyNnj11hczlp8AIvJBmfHNGnlbv5am',     '3415551234', 'Spain',  'USER'),
('Mohammed Ali',  'ali@example.com',     '$2b$10$k/Sud/FOk4yM5uMvrEnVz.r09kKrKkhr6dlHTZlR1PadfCkOLGMNa',     '5015551234', 'UAE',    'USER'),
('Ananya Iyer',   'ananya@example.com',  '$2b$10$ab.mL5XBLafwPet0lys1a.1.F3.GR7q9uxLdXR1VuSkzZNFky/BFu',     '9876543214', 'India',  'USER');

INSERT INTO plan (plan_name, price, duration_months) VALUES
('Basic',    199.00,  6),
('Standard', 399.00, 12),
('Premium',  649.00, 12);

INSERT INTO category (category_name, description) VALUES
('Action',      'High energy, thrilling content'),
('Drama',       'Emotional and character-driven stories'),
('Comedy',      'Light-hearted, humorous content'),
('Documentary', 'Factual and educational content'),
('Thriller',    'Suspenseful, edge-of-your-seat stories'),
('Sci-Fi',      'Science fiction and futuristic worlds'),
('Romance',     'Love stories and relationships'),
('Horror',      'Scary and spine-chilling content'),
('Animation',   'Animated films and shows for all ages');

INSERT INTO content (title, release_year, duration, rating, language, category_id) VALUES
('The Last Horizon',        2023, 128, 8.2, 'English', 1),
('Iron Monsoon',            2024, 141, 7.6, 'Hindi',   1),
('Crimson Highway',         2022, 117, 7.1, 'English', 1),
('Desert Blade',            2021, 133, 6.9, 'English', 1),
('Monsoon Diaries',         2022, 110, 7.8, 'Hindi',   2),
('A Quiet Harbour',         2023, 124, 8.4, 'English', 2),
('Letters from Jaipur',     2024, 118, 8.0, 'Hindi',   2),
('The Weight of Rain',      2020, 132, 8.6, 'English', 2),
('Laugh Riot',              2024,  95, 7.0, 'English', 3),
('Chai Time Chaos',         2023, 104, 7.3, 'Hindi',   3),
('The Wedding Planner Wars',2022,  99, 6.8, 'English', 3),
('Office Olympics',         2025,  92, 7.2, 'English', 3),
('Deep Blue World',         2021, 102, 8.9, 'English', 4),
('Rivers of India',         2023,  88, 8.3, 'Hindi',   4),
('The Last Glacier',        2022,  96, 8.1, 'English', 4),
('Midnight Ledger',         2024, 112, 7.9, 'English', 5),
('The Silent Witness',      2023, 108, 7.5, 'English', 5),
('Cold Signal',             2025, 121, 8.0, 'English', 5),
('Parallel Dawn',           2025, 138, 8.5, 'English', 6),
('Orbit Zero',              2022, 126, 7.7, 'English', 6),
('The Memory Engine',       2024, 115, 8.1, 'English', 6),
('Neon Tomorrow',           2021, 130, 7.0, 'English', 6),
('Two Monsoons',            2023, 119, 7.4, 'Hindi',   7),
('Paris in Autumn',         2022, 107, 7.2, 'English', 7),
('The Long Way to You',     2024, 113, 7.8, 'English', 7),
('The Hollow House',        2023, 101, 6.7, 'English', 8),
('Whispers at 3 AM',        2024,  94, 7.0, 'English', 8),
('Little Cloud Adventures', 2024,  86, 8.0, 'English', 9),
('Rangeela Rockets',        2023,  91, 7.6, 'Hindi',   9),
('The Paper Dragon',        2022,  98, 8.2, 'English', 9);

-- user_id 3..12 are the customers (1 = admin, 2 = editor)
INSERT INTO subscription (start_date, end_date, status, user_id, plan_id) VALUES
('2026-01-01', '2027-01-01', 'active',    3, 3),   -- Aarav   Premium
('2026-03-15', '2026-09-15', 'expired',   4, 1),   -- Riya    Basic (ended)
('2026-02-01', '2027-02-01', 'active',    5, 2),   -- John    Standard
('2026-05-10', '2027-05-10', 'active',    6, 3),   -- Emma    Premium
('2026-06-20', '2027-06-20', 'active',    7, 2),   -- Vikram  Standard
('2026-01-10', '2026-07-10', 'expired',   8, 1),   -- Priya   Basic (ended)
('2026-04-05', '2027-04-05', 'cancelled', 9, 3),   -- Liam    Premium (cancelled)
('2026-08-01', '2027-02-01', 'active',   10, 1),   -- Sofia   Basic
('2026-09-15', '2027-09-15', 'active',   11, 2),   -- Ali     Standard
('2026-07-01', '2027-07-01', 'active',   12, 3);   -- Ananya  Premium

INSERT INTO payment (payment_date, payment_amount, payment_method, status, subscription_id) VALUES
('2026-01-01', 649.00, 'Credit Card', 'success',  1),
('2026-03-15', 199.00, 'UPI',         'success',  2),
('2026-02-01', 399.00, 'Debit Card',  'success',  3),
('2026-05-10', 649.00, 'UPI',         'success',  4),
('2026-06-19', 399.00, 'Credit Card', 'failed',   5),
('2026-06-20', 399.00, 'UPI',         'success',  5),
('2026-01-10', 199.00, 'Net Banking', 'success',  6),
('2026-04-05', 649.00, 'Credit Card', 'success',  7),
('2026-04-15', 649.00, 'Credit Card', 'refunded', 7),
('2026-08-01', 199.00, 'Wallet',      'success',  8),
('2026-09-15', 399.00, 'UPI',         'success',  9),
('2026-07-01', 649.00, 'Debit Card',  'success', 10);

INSERT INTO watchlist (added_date, user_id, content_id) VALUES
('2026-06-01',  3,  1),
('2026-06-02',  3,  3),
('2026-06-05',  4,  5),
('2026-07-01',  5, 13),
('2026-07-04',  6,  9),
('2026-07-10',  6, 19),
('2026-08-02',  7,  2),
('2026-08-05',  8,  7),
('2026-08-09',  8, 14),
('2026-08-15',  9, 16),
('2026-09-01', 10, 28),
('2026-09-03', 10, 23),
('2026-09-20', 11, 20),
('2026-09-22', 12,  6),
('2026-09-25', 12, 30);

INSERT INTO watch_history (watch_date, watch_time, progress, completed, user_id, content_id) VALUES
('2026-07-10', '20:15:00', 100.00, TRUE,   3,  1),
('2026-07-12', '21:00:00',  45.50, FALSE,  4,  5),
('2026-07-15', '19:30:00', 100.00, TRUE,   5, 13),
('2026-07-18', '22:00:00',  70.00, FALSE,  6,  9),
('2026-08-03', '18:45:00',  20.00, FALSE,  7,  2),
('2026-08-06', '23:10:00',  88.25, FALSE,  8,  7),
('2026-08-20', '20:00:00', 100.00, TRUE,   9, 16),
('2026-09-02', '19:15:00', 100.00, TRUE,  10, 28),
('2026-09-10', '21:30:00',  75.00, FALSE, 11, 20),
('2026-09-14', '20:45:00', 100.00, TRUE,  12,  6),
('2026-09-18', '22:20:00',  60.00, FALSE,  3, 19),
('2026-09-25', '17:30:00', 100.00, TRUE,   6, 19);

INSERT INTO review (rating, comment, review_date, user_id, content_id) VALUES
(9.0, 'Absolutely thrilling from start to finish!', '2026-07-11',  3,  1),
(7.5, 'Good story but slow in the middle.',         '2026-07-16',  5, 13),
(8.0, 'Hilarious, watched it twice already.',       '2026-07-19',  6,  9),
(7.0, 'A bit predictable, still worth a watch.',    '2026-08-07',  8,  7),
(8.5, 'Great performances by the whole cast.',      '2026-08-21',  9, 16),
(9.5, 'Beautifully shot, the soundtrack is amazing.','2026-09-03',10, 28),
(8.0, 'Perfect for a relaxed weekend evening.',     '2026-09-11', 11, 20),
(9.0, 'One of the best things I have seen this year.','2026-09-15',12,  6),
(8.5, 'Did not expect that twist!',                 '2026-09-26',  6, 19);

-- =========================================================
-- VERIFICATION QUERIES
-- =========================================================

-- Users with their subscription plan
SELECT u.name, u.email, p.plan_name, p.price, s.status
FROM user u
JOIN subscription s ON u.user_id = s.user_id
JOIN plan p         ON s.plan_id = p.plan_id;

-- Content list with category
SELECT c.title, c.release_year, cat.category_name, c.rating
FROM content c
JOIN category cat ON c.category_id = cat.category_id;

-- Watch history with user and content name
SELECT u.name, c.title, wh.progress, wh.completed
FROM watch_history wh
JOIN user u    ON wh.user_id = u.user_id
JOIN content c ON wh.content_id = c.content_id;

-- Average user rating per content
SELECT c.title, ROUND(AVG(r.rating), 1) AS avg_rating, COUNT(r.review_id) AS num_reviews
FROM content c
LEFT JOIN review r ON c.content_id = r.content_id
GROUP BY c.content_id, c.title;

-- Total revenue (successful payments only)
SELECT SUM(payment_amount) AS total_revenue FROM payment WHERE status = 'success';

-- Net revenue after refunds
SELECT SUM(CASE WHEN status = 'success'  THEN payment_amount
                WHEN status = 'refunded' THEN -payment_amount
                ELSE 0 END) AS net_revenue
FROM payment;

-- Revenue by plan
SELECT p.plan_name, COUNT(*) AS payments, SUM(pay.payment_amount) AS revenue
FROM payment pay
JOIN subscription s ON pay.subscription_id = s.subscription_id
JOIN plan p         ON s.plan_id = p.plan_id
WHERE pay.status = 'success'
GROUP BY p.plan_name;

-- Most watched content
SELECT c.title, COUNT(*) AS views
FROM watch_history wh
JOIN content c ON wh.content_id = c.content_id
GROUP BY c.content_id, c.title
ORDER BY views DESC;
