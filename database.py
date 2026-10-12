import sqlite3
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "attendance.db")


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            employee_id TEXT NOT NULL UNIQUE,
            email TEXT,
            phone TEXT,
            department TEXT,
            face_image TEXT,
            face_embedding BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            attendance_date DATE NOT NULL,
            attendance_time TIME NOT NULL,
            status TEXT DEFAULT 'Present',
            UNIQUE(user_id, attendance_date),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    # Existing database ke liye embedding column add karo
    columns = conn.execute(
        "PRAGMA table_info(users)"
    ).fetchall()

    column_names = [column["name"] for column in columns]

    if "face_embedding" not in column_names:
        conn.execute("""
            ALTER TABLE users
            ADD COLUMN face_embedding BLOB
        """)

    conn.commit()
    conn.close()

def create_user(
    name,
    employee_id,
    email,
    phone,
    department,
    face_image,
    face_embedding
):

    conn = get_db()

    cursor = conn.execute("""
        INSERT INTO users
        (
            name,
            employee_id,
            email,
            phone,
            department,
            face_image,
            face_embedding
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        employee_id,
        email,
        phone,
        department,
        face_image,
        face_embedding
    ))

    conn.commit()

    user_id = cursor.lastrowid

    conn.close()

    return user_id