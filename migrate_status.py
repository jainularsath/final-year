import os
import mysql.connector

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': os.getenv('DB_PASSWORD', '21Ucs017'),
    'database': 'tn_events'
}

print('Connecting to DB...')
conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()
tables = ['halls', 'catering_companies', 'luxury_cars', 'photography_services', 'decorations']
for t in tables:
    try:
        cursor.execute(f"ALTER TABLE {t} ADD COLUMN status ENUM('pending','approved','rejected') DEFAULT 'pending'")
        print(f"Added status to {t}")
    except Exception as e:
        print(e)
conn.commit()
cursor.close()
conn.close()
