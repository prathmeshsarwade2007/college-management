import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "college.db")

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = connect()
    cur = conn.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )""")

    cur.execute("SELECT COUNT(*) FROM admin")
    if cur.fetchone()[0] == 0:
        cur.execute("INSERT INTO admin(username,password) VALUES(?,?)", ("admin","admin123"))

    cur.execute("""CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        department TEXT NOT NULL,
        year INTEGER NOT NULL,
        roll_no TEXT UNIQUE NOT NULL,
        enrollment_no TEXT
    )""")

    # Safe migration for existing databases
    existing_columns = [row[1] for row in cur.execute("PRAGMA table_info(students)")]
    if "enrollment_no" not in existing_columns:
        cur.execute("ALTER TABLE students ADD COLUMN enrollment_no TEXT")

    cur.execute("""CREATE TABLE IF NOT EXISTS faculty (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        subject TEXT NOT NULL,
        dept TEXT NOT NULL
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_name TEXT NOT NULL,
        faculty_id INTEGER,
        FOREIGN KEY(faculty_id) REFERENCES faculty(id)
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('Present','Absent')),
        FOREIGN KEY(student_id) REFERENCES students(id)
    )""")

    cur.execute("""CREATE TABLE IF NOT EXISTS marks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        subject TEXT NOT NULL,
        marks REAL NOT NULL,
        max_marks REAL NOT NULL DEFAULT 100,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )""")

    # ✅ Staff attendance table
    cur.execute("""CREATE TABLE IF NOT EXISTS staff_attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        faculty_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        status TEXT NOT NULL CHECK(status IN ('Present','Absent')),
        FOREIGN KEY(faculty_id) REFERENCES faculty(id)
    )""")

    conn.commit()
    conn.close()