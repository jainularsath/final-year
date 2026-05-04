import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', '21Ucs017'),
    'database': os.getenv('DB_NAME', 'tn_events'),
}

def migrate():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    tables_to_update = {
        'halls': ['image_url VARCHAR(255)', 'location_url VARCHAR(255)'],
        'catering_companies': ['image_url VARCHAR(255)', 'location_url VARCHAR(255)'],
        'photography_services': ['image_url VARCHAR(255)', 'location_url VARCHAR(255)'],
        'decorations': ['image_url VARCHAR(255)', 'location_url VARCHAR(255)'],
        'luxury_cars': ['location_url VARCHAR(255)'] # image_url already exists
    }
    
    for table, columns in tables_to_update.items():
        for col in columns:
            col_name = col.split(' ')[0]
            try:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col}")
                print(f"Added {col_name} to {table}")
            except Exception as e:
                print(f"Skipping {col_name} in {table}: {e}")
                
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == '__main__':
    migrate()
