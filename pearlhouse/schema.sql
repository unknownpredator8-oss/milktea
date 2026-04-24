-- PearlHouse Milk Tea POS — MySQL Schema
CREATE DATABASE IF NOT EXISTS pearlhouse CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE pearlhouse;

CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) UNIQUE NOT NULL,
  password VARCHAR(255) NOT NULL,
  display_name VARCHAR(100),
  role ENUM('admin','staff') DEFAULT 'staff',
  image LONGTEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS menu_items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  category VARCHAR(50) DEFAULT 'Milk Tea',
  emoji VARCHAR(10) DEFAULT '🧋',
  stock INT DEFAULT 0,
  available TINYINT(1) DEFAULT 1,
  image LONGTEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ingredients (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  emoji VARCHAR(10) DEFAULT '🧉',
  unit VARCHAR(20) DEFAULT 'pcs',
  stock DECIMAL(10,3) DEFAULT 0,
  threshold DECIMAL(10,3) DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS item_ingredients (
  id INT AUTO_INCREMENT PRIMARY KEY,
  menu_item_id INT NOT NULL,
  ingredient_id INT NOT NULL,
  qty DECIMAL(10,4) NOT NULL DEFAULT 0,
  FOREIGN KEY (menu_item_id) REFERENCES menu_items(id) ON DELETE CASCADE,
  FOREIGN KEY (ingredient_id) REFERENCES ingredients(id) ON DELETE CASCADE,
  UNIQUE KEY unique_link (menu_item_id, ingredient_id)
);

CREATE TABLE IF NOT EXISTS orders (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_num INT NOT NULL,
  total DECIMAL(10,2) NOT NULL,
  payment ENUM('cash','gcash') DEFAULT 'cash',
  status ENUM('preparing','ready','served') DEFAULT 'preparing',
  staff VARCHAR(50),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
  id INT AUTO_INCREMENT PRIMARY KEY,
  order_id INT NOT NULL,
  menu_item_id INT,
  name VARCHAR(100) NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  qty INT NOT NULL DEFAULT 1,
  emoji VARCHAR(10) DEFAULT '🧋',
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50),
  role VARCHAR(20),
  action VARCHAR(100) DEFAULT 'login',
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS settings (
  id INT AUTO_INCREMENT PRIMARY KEY,
  key_name VARCHAR(100) UNIQUE NOT NULL,
  value_text LONGTEXT
);

-- Default admin user (password: admin123)
INSERT IGNORE INTO users (username, password, display_name, role)
VALUES ('admin', 'admin123', 'Administrator', 'admin'),
       ('staff', 'staff123', 'Staff User', 'staff');

-- Default menu items
INSERT IGNORE INTO menu_items (id, name, price, category, emoji, stock, available) VALUES
(1,'Classic Pearl Milk Tea',85,'Milk Tea','🧋',50,1),
(2,'Taro Milk Tea',95,'Milk Tea','💜',45,1),
(3,'Brown Sugar Boba',100,'Milk Tea','🤎',40,1),
(4,'Matcha Latte',110,'Milk Tea','🍵',35,1),
(5,'Mango Fruit Tea',85,'Fruit Tea','🥭',50,1),
(6,'Strawberry Tea',90,'Fruit Tea','🍓',48,1),
(7,'Lychee Tea',88,'Fruit Tea','🍈',42,1),
(8,'Passion Fruit Tea',92,'Fruit Tea','🍊',38,1),
(9,'Mango Slush',95,'Slush','🧊',30,1),
(10,'Strawberry Slush',95,'Slush','🌸',30,1);

-- Default ingredients
INSERT IGNORE INTO ingredients (id, name, emoji, unit, stock, threshold) VALUES
(101,'Tapioca Pearls','⚫','kg',5,1),
(102,'Fresh Milk','🥛','L',12,3),
(103,'Black Tea','🍃','kg',2,0.5),
(104,'Taro Powder','💜','kg',3,0.5),
(105,'Brown Sugar Syrup','🍯','bottles',8,2),
(106,'Matcha Powder','🍵','kg',1.5,0.3),
(107,'Mango Puree','🥭','kg',4,1),
(108,'Strawberry Puree','🍓','kg',3,1),
(109,'Lychee Syrup','🍈','bottles',5,2),
(110,'Passion Fruit Syrup','🍊','bottles',4,2),
(111,'Sugar Syrup','🍬','L',6,1),
(112,'Cups & Lids','🥤','pcs',500,100);

-- Ingredient links
INSERT IGNORE INTO item_ingredients (menu_item_id, ingredient_id, qty) VALUES
(1,101,0.05),(1,102,0.3),(1,103,0.01),(1,111,0.02),(1,112,1),
(2,101,0.05),(2,102,0.3),(2,104,0.02),(2,111,0.02),(2,112,1),
(3,101,0.05),(3,102,0.3),(3,105,0.05),(3,112,1),
(4,102,0.3),(4,106,0.015),(4,111,0.02),(4,112,1),
(5,107,0.1),(5,103,0.01),(5,111,0.02),(5,112,1),
(6,108,0.1),(6,103,0.01),(6,111,0.02),(6,112,1),
(7,109,0.05),(7,103,0.01),(7,111,0.02),(7,112,1),
(8,110,0.05),(8,103,0.01),(8,111,0.02),(8,112,1),
(9,107,0.12),(9,111,0.02),(9,112,1),
(10,108,0.12),(10,111,0.02),(10,112,1);
