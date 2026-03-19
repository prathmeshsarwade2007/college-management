import sqlite3

conn = sqlite3.connect("college.db")
conn.execute("""
    CREATE TABLE IF NOT EXISTS staff_attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        faculty_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY(faculty_id) REFERENCES faculty(id)
    )
""")
conn.commit()

tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print("Tables:", tables)
conn.close()
print("Done! staff_attendance table created successfully.")