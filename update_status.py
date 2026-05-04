import mysql.connector
import os
DB_CONFIG = {'host': 'localhost', 'user': 'root', 'password': os.getenv('DB_PASSWORD', '21Ucs017'), 'database': 'tn_events'}
conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()
for t in ['halls', 'catering_companies', 'luxury_cars', 'photography_services', 'decorations']:
    cursor.execute(f"UPDATE {t} SET status='approved'")
conn.commit()
print("All set to approved")
