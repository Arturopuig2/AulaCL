import sqlite3

# Connect to database
conn = sqlite3.connect('aula_cl.db')
cursor = conn.cursor()

try:
    # Add is_active column to texts table
    # Default to 1 (True)
    cursor.execute("ALTER TABLE texts ADD COLUMN is_active BOOLEAN DEFAULT 1")
    conn.commit()
    print("Column 'is_active' added successfully.")
except sqlite3.OperationalError as e:
    print(f"Error: {e}")
    print("Column might already exist.")

conn.close()
