import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "birthdays.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                birth_date TEXT NOT NULL,
                subject_template TEXT NOT NULL DEFAULT 'Happy Birthday, {name}! 🎉',
                body_template TEXT NOT NULL DEFAULT 'Hi {name},\n\nWishing you a very Happy Birthday! Have an amazing day ahead.\n\nBest wishes,\nBirthday Wisher',
                active INTEGER NOT NULL DEFAULT 1,
                last_sent_year INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def list_contacts():
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM contacts ORDER BY substr(birth_date, 6, 5), name COLLATE NOCASE"
        ).fetchall()


def add_contact(name, email, birth_date, subject_template, body_template, active):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO contacts (name, email, birth_date, subject_template, body_template, active)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, email, birth_date, subject_template, body_template, int(active)),
        )


def update_contact(contact_id, name, email, birth_date, subject_template, body_template, active):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE contacts
            SET name=?, email=?, birth_date=?, subject_template=?, body_template=?, active=?
            WHERE id=?
            """,
            (name, email, birth_date, subject_template, body_template, int(active), contact_id),
        )


def delete_contact(contact_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM contacts WHERE id=?", (contact_id,))


def mark_sent(contact_id, year):
    with get_connection() as conn:
        conn.execute("UPDATE contacts SET last_sent_year=? WHERE id=?", (year, contact_id))


def reset_sent_year(contact_id=None):
    with get_connection() as conn:
        if contact_id is None:
            conn.execute("UPDATE contacts SET last_sent_year=NULL")
        else:
            conn.execute("UPDATE contacts SET last_sent_year=NULL WHERE id=?", (contact_id,))
