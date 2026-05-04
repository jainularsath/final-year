"""
Run this once to initialize the database and create all tables.
Usage: python init_db.py
"""
import mysql.connector
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '21Ucs017'),
}
DB_NAME = os.getenv('DB_NAME', 'tn_events')

DDL = [
    f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
    f"USE `{DB_NAME}`;",

    """CREATE TABLE IF NOT EXISTS users (
      id INT AUTO_INCREMENT PRIMARY KEY,
      name VARCHAR(100) NOT NULL,
      email VARCHAR(100) UNIQUE NOT NULL,
      phone VARCHAR(15),
      password_hash VARCHAR(255) NOT NULL,
      role ENUM('user','vendor','admin') DEFAULT 'user',
      vendor_service_type ENUM('hall','catering','luxury_car','decoration','photography') DEFAULT NULL,
      status ENUM('active','inactive','pending') DEFAULT 'active',
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    ) ENGINE=InnoDB;""",

    """CREATE TABLE IF NOT EXISTS halls (
      id INT AUTO_INCREMENT PRIMARY KEY,
      name VARCHAR(100) NOT NULL,
      city VARCHAR(100),
      capacity INT,
      amenities TEXT,
      price_per_night DECIMAL(10,2),
      address LONGTEXT,
      latitude DECIMAL(10,8),
      longitude DECIMAL(10,8),
      vendor_id INT,
      FOREIGN KEY (vendor_id) REFERENCES users(id) ON DELETE SET NULL
    ) ENGINE=InnoDB;""",

    """CREATE TABLE IF NOT EXISTS catering_companies (
      id INT AUTO_INCREMENT PRIMARY KEY,
      user_id INT,
      company_name VARCHAR(100) NOT NULL,
      city VARCHAR(100),
      veg_non_veg ENUM('veg','non_veg','both') DEFAULT 'both',
      price_per_plate DECIMAL(10,2),
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    ) ENGINE=InnoDB;""",

    """CREATE TABLE IF NOT EXISTS catering_menu (
      id INT AUTO_INCREMENT PRIMARY KEY,
      catering_id INT,
      dish_name VARCHAR(100) NOT NULL,
      category ENUM('main','side','snack','beverage','ice_cream') DEFAULT 'main',
      price_per_item DECIMAL(10,2),
      FOREIGN KEY (catering_id) REFERENCES catering_companies(id) ON DELETE CASCADE
    ) ENGINE=InnoDB;""",

    """CREATE TABLE IF NOT EXISTS luxury_cars (
      id INT AUTO_INCREMENT PRIMARY KEY,
      user_id INT,
      car_name VARCHAR(100) NOT NULL,
      car_model VARCHAR(100),
      city VARCHAR(100),
      image_url VARCHAR(255),
      rate_per_km DECIMAL(10,2),
      per_day_rent DECIMAL(10,2) DEFAULT '0',
      km_limit INT DEFAULT '0',
      capacity INT,
      with_decorations BOOLEAN DEFAULT FALSE,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    ) ENGINE=InnoDB;""",

    """CREATE TABLE IF NOT EXISTS photography_services (
      id INT AUTO_INCREMENT PRIMARY KEY,
      city VARCHAR(100),
      service_name VARCHAR(100) NOT NULL,
      base_price DECIMAL(10,2),
      price_per_hour DECIMAL(10,2),
      user_id INT,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    ) ENGINE=InnoDB;""",

    """CREATE TABLE IF NOT EXISTS decorations (
      id INT AUTO_INCREMENT PRIMARY KEY,
      user_id INT,
      theme_name VARCHAR(100) NOT NULL,
      religion_style VARCHAR(50),
      culture_style VARCHAR(50),
      base_price DECIMAL(10,2),
      city VARCHAR(100),
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    ) ENGINE=InnoDB;""",

    """CREATE TABLE IF NOT EXISTS bookings (
      id INT AUTO_INCREMENT PRIMARY KEY,
      user_id INT,
      service_type ENUM('hall','catering','luxury_car','photography','decorations'),
      service_id INT,
      date DATE,
      time TIME,
      total_people INT,
      total_amount DECIMAL(10,2),
      advance_amount DECIMAL(10,2),
      status ENUM('pending','confirmed','completed','cancelled') DEFAULT 'pending',
      notes TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    ) ENGINE=InnoDB;""",

    """CREATE TABLE IF NOT EXISTS vendor_approvals (
      id INT AUTO_INCREMENT PRIMARY KEY,
      vendor_id INT,
      approved_by_admin_id INT,
      approved_at DATETIME,
      status ENUM('approved','rejected','pending') DEFAULT 'pending'
    ) ENGINE=InnoDB;""",
]

def seed_admin(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE role='admin' LIMIT 1")
    if cursor.fetchone():
        print("Admin already exists. Skipping seed.")
        cursor.close()
        return
    admin_password = os.getenv('ADMIN_DEFAULT_PASSWORD', 'Admin@TN2024!')
    hashed = bcrypt.hashpw(admin_password.encode(), bcrypt.gensalt()).decode()
    cursor.execute(
        "INSERT INTO users (name, email, phone, password_hash, role, status) VALUES (%s,%s,%s,%s,'admin','active')",
        ('Super Admin', 'admin@tnevents.com', '9000000000', hashed)
    )
    conn.commit()
    cursor.close()
    print(f"✅ Admin created: admin@tnevents.com / {admin_password}")

def seed_sample_data(conn):
    cursor = conn.cursor()
    # Sample vendor user
    cursor.execute("SELECT id FROM users WHERE email='vendor@tnevents.com' LIMIT 1")
    if not cursor.fetchone():
        hashed = bcrypt.hashpw(b'Vendor@123', bcrypt.gensalt()).decode()
        cursor.execute(
            "INSERT INTO users (name, email, phone, password_hash, role, status) VALUES (%s,%s,%s,%s,'vendor','active')",
            ('Sample Vendor', 'vendor@tnevents.com', '9000000001', hashed)
        )
        vendor_id = cursor.lastrowid

        # Sample halls
        halls = [
            ('Sri Murugan Mahal', 'Chennai', 500, 'AC, Parking, Stage', 50000.00, '12 Anna Salai, Chennai', 13.0827, 80.2707, vendor_id),
            ('Royal Palace Hall', 'Madurai', 800, 'AC, Catering, Parking', 75000.00, '45 Meenakshi St, Madurai', 9.9252, 78.1198, vendor_id),
            ('Vijaya Convention', 'Coimbatore', 600, 'AC, AV System, Parking', 60000.00, '7 RS Puram, Coimbatore', 11.0168, 76.9558, vendor_id),
            ('Lakshmi Gardens', 'Salem', 400, 'Open Air, Generator', 35000.00, '23 Omalur Rd, Salem', 11.6643, 78.1460, vendor_id),
            ('Karthikeya Grand', 'Trichy', 700, 'AC, Stage, Parking', 65000.00, '8 Lawsons Rd, Trichy', 10.7905, 78.7047, vendor_id),
        ]
        cursor.executemany(
            "INSERT INTO halls (name,city,capacity,amenities,price_per_night,address,latitude,longitude,vendor_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            halls
        )

        # Sample catering
        cursor.execute(
            "INSERT INTO catering_companies (user_id,company_name,city,veg_non_veg,price_per_plate) VALUES (%s,%s,%s,%s,%s)",
            (vendor_id, 'Annapoorna Catering', 'Chennai', 'veg', 350.00)
        )
        cat_id = cursor.lastrowid
        menu_items = [
            (cat_id, 'Sambar Rice', 'main', 80.00),
            (cat_id, 'Pongal', 'main', 60.00),
            (cat_id, 'Vadai', 'snack', 30.00),
            (cat_id, 'Filter Coffee', 'beverage', 25.00),
            (cat_id, 'Ice Cream', 'ice_cream', 50.00),
        ]
        cursor.executemany(
            "INSERT INTO catering_menu (catering_id,dish_name,category,price_per_item) VALUES (%s,%s,%s,%s)",
            menu_items
        )

        # Sample cars
        cars = [
            (vendor_id, 'Mercedes Benz', 'S-Class', 'Chennai', '/static/img/car1.jpg', 45.00, 4, True),
            (vendor_id, 'BMW', '7-Series', 'Chennai', '/static/img/car2.jpg', 50.00, 4, False),
            (vendor_id, 'Rolls Royce', 'Ghost', 'Madurai', '/static/img/car3.jpg', 120.00, 4, True),
        ]
        cursor.executemany(
            "INSERT INTO luxury_cars (user_id,car_name,car_model,city,image_url,rate_per_km,capacity,with_decorations) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            cars
        )

        # Sample photography
        photos = [
            ('Chennai', 'Wedding Photography Pro', 15000.00, 2000.00, vendor_id),
            ('Madurai', 'Candid Moments Studio', 12000.00, 1500.00, vendor_id),
        ]
        cursor.executemany(
            "INSERT INTO photography_services (city,service_name,base_price,price_per_hour,user_id) VALUES (%s,%s,%s,%s,%s)",
            photos
        )

        # Sample decorations
        decors = [
            (vendor_id, 'Classic Hindu Wedding', 'Hindu', 'Tamil', 25000.00, 'Chennai'),
            (vendor_id, 'Royal Christian Theme', 'Christian', 'Western', 30000.00, 'Chennai'),
            (vendor_id, 'Elegant Muslim Decor', 'Muslim', 'Traditional', 22000.00, 'Madurai'),
        ]
        cursor.executemany(
            "INSERT INTO decorations (user_id,theme_name,religion_style,culture_style,base_price,city) VALUES (%s,%s,%s,%s,%s,%s)",
            decors
        )

        conn.commit()
        print("✅ Sample vendor, halls, catering, cars, photography, decorations seeded.")

    cursor.close()

if __name__ == '__main__':
    print("🚀 Initializing TN Events Database...")
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    for stmt in DDL:
        try:
            cursor.execute(stmt)
            conn.commit()
        except Exception as e:
            print(f"  Warning: {e}")
    cursor.close()
    conn.database = DB_NAME
    seed_admin(conn)
    seed_sample_data(conn)
    conn.close()
    print("✅ Database initialization complete!")
