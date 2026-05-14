import sqlite3
import os

os.makedirs('static/uploads/profiles', exist_ok=True)
db_path = 'instance/database.db' if os.path.exists('instance/database.db') else 'database.db'

try:
    conn = sqlite3.connect(db_path)
    conn.execute("ALTER TABLE user ADD COLUMN profile_pic VARCHAR(255) DEFAULT ''")
    conn.commit()
    conn.close()
    print("Database Schema Upgraded Successfully.")
except Exception as e:
    print("DB Upgrade ignored or failed:", str(e))
