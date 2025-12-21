import sqlite3

conn = sqlite3.connect("college.db")
cursor = conn.cursor()

cursor.execute("SELECT name, subject FROM faculty")
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()
