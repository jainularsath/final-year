from db import get_db

def update_db():
    conn = get_db()
    cursor = conn.cursor()
    try:
        # 1. Update time column
        print("Updating time column to VARCHAR(50)...")
        cursor.execute("ALTER TABLE bookings MODIFY COLUMN time VARCHAR(50)")
        
        # 2. Update status enum
        print("Updating status enum...")
        cursor.execute("ALTER TABLE bookings MODIFY COLUMN status ENUM('pending','paid','confirmed','completed','cancelled') DEFAULT 'pending'")
        
        conn.commit()
        print("Database updated successfully!")
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    update_db()
