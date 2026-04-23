-- MySQL Database Setup for LocEats Backend
-- Run this in phpMyAdmin or MySQL CLI

CREATE DATABASE IF NOT EXISTS loceats_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE loceats_db;

-- Categories
CREATE TABLE IF NOT EXISTS restaurants_category (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Restaurants
CREATE TABLE IF NOT EXISTS restaurants_restaurant (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    address VARCHAR(300) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    description LONGTEXT,
    rating DECIMAL(2,1) DEFAULT 0.0,
    image VARCHAR(100),
    category_id BIGINT,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (category_id) REFERENCES restaurants_category(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tables
CREATE TABLE IF NOT EXISTS restaurants_table (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    restaurant_id BIGINT NOT NULL,
    table_number VARCHAR(10) NOT NULL,
    capacity INT DEFAULT 4,
    is_available BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants_restaurant(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Bookings
CREATE TABLE IF NOT EXISTS restaurants_booking (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    restaurant_id BIGINT NOT NULL,
    table_id BIGINT NOT NULL,
    customer_name VARCHAR(100) NOT NULL,
    customer_phone VARCHAR(20) NOT NULL,
    booking_date DATE NOT NULL,
    booking_time TIME NOT NULL,
    guest_count INT DEFAULT 2,
    note LONGTEXT,
    is_confirmed BOOLEAN DEFAULT FALSE,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants_restaurant(id) ON DELETE CASCADE,
    FOREIGN KEY (table_id) REFERENCES restaurants_table(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Sample Data
INSERT INTO restaurants_category (name) VALUES 
('Milliy'),
('Evropa'),
('Fast Food'),
('Kafe');

INSERT INTO restaurants_restaurant (name, address, phone, description, rating, category_id, latitude, longitude) VALUES 
('Samarqand Registon Oshxonasi', 'Registon ko''chasi 15', '+998662345678', 'Samarqandning eng mashhur milliy oshxonasida Registon yaqinida. Ustalarimizning maxsus osh retsepti', 4.9, 1, 39.6542, 66.9597),
('Bibixonim Kafe', 'Islom Karimov ko''chasi 45', '+998662345679', 'An''anaviy manti va shashlik. Oilaviy tadbirlar uchun qulay', 4.7, 1, 39.6500, 66.9750),
('Empire Restaurant', 'Dagbitskaya ko''chasi 8', '+998662345680', 'Zamonaviy yevropacha dizayn va yuqori sifatli taomlar', 4.6, 2, 39.6520, 66.9600);
