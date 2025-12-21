import sqlite3

# Connect to SQLite DB (creates file if not exists)
conn = sqlite3.connect("college.db")
cursor = conn.cursor()

# Create faculty table
cursor.execute("""
CREATE TABLE IF NOT EXISTS faculty (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    short_code TEXT,
    name TEXT,
    subject TEXT,
    email TEXT UNIQUE,
    cabin TEXT
)
""")

cursor.execute("DELETE FROM faculty")


# Insert faculty data (REAL data)
faculty_data = [
    ("PK", "Pradnya Vijay Kamble", "Mobile Communication System", "pkamble@somaiya.edu", "A-01"),
    ("SR", "Sarika Yuvraj Mane", "Signal And System", "sarika@somaiya.edu", "A-02"),
    ("VS", "Vidya Ravindra Sagvekar", "Physics", "vsagvekar@somaiya.edu", "A-03"),
    ("PD", "Pankaj Vinayak Deshmukh", "Python", "pankaj@somaiya.edu", "A-04"),
    ("GP", "Ghanashyam Ramchandra Phadke", "Placement", "ghanashyam.p@somaiya.edu", "A-05"),
    ("RA", "Rashmi Ramesh Adatkar", "DSA", "rashmi@somaiya.edu", "A-06"),
    ("SS", "Swati Hemant Shinde", "Microcontroller", "swati.shinde@somaiya.edu", "A-07"),
    ("VW", "Vaishali Rama Wadhe", "Chemistry", "vwadhe@somaiya.edu", "A-08"),
    ("SK", "Sandhya Devendra Kadam", "A.I", "sandhyakadam@somaiya.edu", "A-09"),
    ("JK", "Jayashree Vivekanand Khanapuri", "Image Processing", "jayashreek@somaiya.edu", "A-10"),
    ("SP", "Sunil Devidas Patil", "Random Signal Analysis", "sunilpatil@somaiya.edu", "A-11"),
    ("TP", "Thulasi G Pillai", "Product Life-Cycle Management", "hulasi@somaiya.edu", "A-12"),
    ("SM", "Sandeep Shivram Mishra", "Linear Integrated Circuit", "smishra@somaiya.edu", "A-13"),
]

cursor.executemany("""
INSERT OR IGNORE INTO faculty (short_code, name, subject, email, cabin)
VALUES (?, ?, ?, ?, ?)
""", faculty_data)

# Create notices table
cursor.execute("""
CREATE TABLE IF NOT EXISTS notices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    description TEXT,
    category TEXT,
    posted_on DATE
)
""")

notices_data = [
    ("Unit Test 1", "UT-1 starts from 20 September", "Exam", "2025-09-15"),
    ("Project Review", "Final year project review on 25 September", "Academic", "2025-09-20"),
    ("Holiday", "Ganesh Chaturthi holiday", "General", "2025-09-18")
]

cursor.executemany("""
INSERT INTO notices (title, description, category, posted_on)
VALUES (?, ?, ?, ?)
""", notices_data)

# Create timetable table
cursor.execute("""
CREATE TABLE IF NOT EXISTS timetable (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_name TEXT,
    day TEXT,
    time TEXT,
    subject TEXT,
    room TEXT,
    teacher TEXT
)
""")
timetable_data = [
    ("EXTC A", "monday", "9:00-10:00", "Microcontroller", "Lab-1", "Swati Shinde"),
    ("EXTC A", "monday", "10:00-11:00", "Python", "Room-204", "Pankaj Deshmukh"),
    ("EXTC A", "tuesday", "9:00-10:00", "DSA", "Room-203", "Rashmi Adatkar"),
]

cursor.executemany("""
INSERT INTO timetable (class_name, day, time, subject, room, teacher)
VALUES (?, ?, ?, ?, ?, ?)
""", timetable_data)


conn.commit()
conn.close()

print("✅ Faculty database created successfully!")
