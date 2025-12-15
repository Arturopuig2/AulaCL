import sqlite3

conn = sqlite3.connect('aula_cl.db')
cursor = conn.cursor()

print("--- TEXTS ---")
cursor.execute("SELECT id, title, is_active FROM texts")
for row in cursor.fetchall():
    print(row)

conn.close()
