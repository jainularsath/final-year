
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '21Ucs017'),
    'database': os.getenv('DB_NAME', 'tn_events')
}

def migrate():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    try:
        # Add vendor_service_type to users
        cursor.execute("ALTER TABLE users ADD COLUMN vendor_service_type ENUM('hall','catering','luxury_car','decoration','photography') DEFAULT NULL AFTER role")
        conn.commit()
        print("✅ Added vendor_service_type to users table.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    migrate()
