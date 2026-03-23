import sqlite3
import os

paths = [
    os.path.join(os.getcwd(), 'instance', 'database.db'),
    os.path.join(os.getcwd(), 'database.db')
]

for p in paths:
    if os.path.exists(p):
        print("Found DB at", p)
        try:
            conn = sqlite3.connect(p)
            conn.execute("ALTER TABLE user ADD COLUMN father_name VARCHAR(150) DEFAULT ''")
            conn.execute("ALTER TABLE user ADD COLUMN mother_name VARCHAR(150) DEFAULT ''")
            conn.commit()
            conn.close()
            print("Successfully migrated schema on:", p)
        except Exception as e:
            print("Already migrated or error on", p, ":", e)
