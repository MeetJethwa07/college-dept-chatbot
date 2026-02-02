import csv
import sqlite3

conn = sqlite3.connect("college.db")
cursor = conn.cursor()

# Clear old data (important so it doesn't duplicate)
cursor.execute("DELETE FROM timetable")

with open("timetable.csv", newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)  # skip header row

    for row in reader:
        if len(row) < 7:
            continue

        day, time_from, time_to, subject, faculty, room, class_group = row

        cursor.execute("""
            INSERT INTO timetable
            (day, time_from, time_to, subject, faculty, room, class_group)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (day, time_from, time_to, subject, faculty, room, class_group))

conn.commit()
conn.close()

print("✅ Timetable imported successfully!")
