import csv
import sqlite3

conn = sqlite3.connect("college.db")
cursor = conn.cursor()

# clear old data
cursor.execute("DELETE FROM subjects")
cursor.execute("DELETE FROM faculty_new")
cursor.execute("DELETE FROM faculty_subjects")

# ---- subjects ----
with open("subjects.csv", newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)
    for code, name in reader:
        cursor.execute(
            "INSERT INTO subjects VALUES (?, ?)",
            (code, name)
        )

# ---- faculty ----
with open("faculty.csv", newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)
    for code, name, email, cabin in reader:
        cursor.execute(
            "INSERT INTO faculty_new VALUES (?, ?, ?, ?)",
            (code, name, email, cabin)
        )

# ---- mapping ----
with open("faculty_subjects.csv", newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)
    for fcode, scode, role in reader:
        cursor.execute(
            "INSERT INTO faculty_subjects VALUES (?, ?, ?)",
            (fcode, scode, role)
        )

conn.commit()
conn.close()

print("✅ Faculty & subjects imported successfully!")
