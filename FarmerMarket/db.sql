CREATE DATABASE IF NOT EXISTS farmer_market;
USE farmer_market;

-- Users table: stores normal users, farmers, and admin accounts
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('user', 'farmer', 'admin') NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL
);

-- Farmers table: 1-to-1 with users who have role='farmer'
-- id here is the SAME as users.id (enforced via foreign key)
CREATE TABLE IF NOT EXISTS farmers (
    id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    address VARCHAR(255),
    phone VARCHAR(20),
    approved TINYINT(1) DEFAULT 0,
    lat DECIMAL(10,6),
    lng DECIMAL(10,6),
    delivery_radius_km DECIMAL(6,2) DEFAULT 20.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_farmers_user FOREIGN KEY (id) REFERENCES users(id) ON DELETE CASCADE
);

-- Products added by farmers
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    farmer_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    image VARCHAR(255),
    stock INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_products_farmer FOREIGN KEY (farmer_id) REFERENCES farmers(id) ON DELETE CASCADE
);

-- Orders placed by normal users for products
CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    total_price DECIMAL(10,2) NOT NULL,
    status ENUM('pending', 'shipped', 'delivered') DEFAULT 'pending',
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    customer_lat DECIMAL(10,6),
    customer_lng DECIMAL(10,6),
    distance_km DECIMAL(10,3),
    delivery_mode ENUM('free_delivery','pickup_required'),
    CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_orders_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Seed admin user (password: admin123 – make sure hash matches what the app expects if you change it)
INSERT INTO users (username, email, password_hash, role)
VALUES 
('admin', 'admin@farm.com', '$pbkdf2-sha256$29000$abc123def456ghi789$xyz...', 'admin')
ON DUPLICATE KEY UPDATE email = VALUES(email);

-

