"""Shared DB helper for all three Flask servers."""
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def get_db():
    """Return a new MySQL connection."""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    load_dotenv(env_path)
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', '21Ucs017'),
        database=os.getenv('DB_NAME', 'tn_events'),
        autocommit=False
    )

def query(sql, params=None, fetchone=False, fetchall=False, commit=False):
    """Utility for quick DB queries."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(sql, params or ())
        if commit:
            conn.commit()
            return cursor.lastrowid
        if fetchone:
            return cursor.fetchone()
        if fetchall:
            return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()
