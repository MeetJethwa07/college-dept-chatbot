import sqlite3

conn = sqlite3.connect("college.db")
cursor = conn.cursor()

print("Faculty count:", cursor.execute("SELECT COUNT(*) FROM faculty").fetchone()[0])
print("Timetable count:", cursor.execute("SELECT COUNT(*) FROM timetable").fetchone()[0])

conn.close()