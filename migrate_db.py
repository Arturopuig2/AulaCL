import sqlite3
import os

DB_PATH = 'aula_cl.db'

if not os.path.exists(DB_PATH):
    print(f'Database {DB_PATH} not found.')
    exit(1)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

try:
    cursor.execute('ALTER TABLE subusers ADD COLUMN login_code_display VARCHAR')
    conn.commit()
    print('Column login_code_display added successfully.')
except sqlite3.OperationalError as e:
    if 'duplicate column name' in str(e):
        print('Column already exists.')
    else:
        print(f'Error: {e}')
finally:
    conn.close()

