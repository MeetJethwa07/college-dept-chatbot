import sqlite3

# Connect once
conn = sqlite3.connect("college.db")
cursor = conn.cursor()

# ================= FACULTY TABLE =================
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

# Clear old faculty data
cursor.execute("DELETE FROM faculty")

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
    ("TP", "Thulasi G Pillai", "Product Life-Cycle Management", "thulasi@somaiya.edu", "A-12"),
    ("SM", "Sandeep Shivram Mishra", "Linear Integrated Circuit", "smishra@somaiya.edu", "A-13"),
]

cursor.executemany("""
INSERT OR IGNORE INTO faculty (short_code, name, subject, email, cabin)
VALUES (?, ?, ?, ?, ?)
""", faculty_data)


# ================= TIMETABLE TABLE =================
cursor.execute("DROP TABLE IF EXISTS timetable")

cursor.execute("""
CREATE TABLE timetable (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day TEXT,
    time_from TEXT,
    time_to TEXT,
    subject TEXT,
    faculty TEXT,
    room TEXT,
    class_group TEXT
)
""")


# ================= CHATBOT LOGS =================
cursor.execute("""
CREATE TABLE IF NOT EXISTS chatbot_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_query TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# Save everything once
conn.commit()
conn.close()

print("✅ Database setup completed successfully")
