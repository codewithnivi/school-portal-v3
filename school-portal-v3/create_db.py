
import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('school.db')
c = conn.cursor()

# Remove existing demo tables and records
c.execute('DROP TABLE IF EXISTS users')
c.execute('DROP TABLE IF EXISTS students')
c.execute('DROP TABLE IF EXISTS teachers')
c.execute('DROP TABLE IF EXISTS attendance')
c.execute('DROP TABLE IF EXISTS assignments')
c.execute('DROP TABLE IF EXISTS notices')

# Create tables
c.execute('''CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    role TEXT
)''')

c.execute('''CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT,
    roll_no TEXT,
    class_name TEXT,
    email TEXT
)''')

c.execute('''CREATE TABLE teachers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT,
    subject TEXT,
    email TEXT
)''')

c.execute('''CREATE TABLE attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER,
    date TEXT,
    status TEXT
)''')

c.execute('''CREATE TABLE assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    class_name TEXT,
    subject TEXT,
    title TEXT,
    description TEXT,
    due_date TEXT,
    posted_by TEXT
)''')

c.execute('''CREATE TABLE notices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    message TEXT,
    date TEXT,
    posted_by TEXT
)''')

# Create only Admin account
c.execute(
    'INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
    ('Admin', 'admin@school.com',
     generate_password_hash('admin123'), 'admin')
)

conn.commit()
conn.close()

print("School database created successfully!")
print("Only Admin account created.")
print("Email: admin@school.com")
print("Password: admin123")
