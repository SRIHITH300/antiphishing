import sqlite3
from typing import Optional, Dict
import re


class UserDB:
    def __init__(self, db_path: str = "phishing_detection.db"):
        self.db_path = db_path
        self._init_core_tables()

    def _init_core_tables(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
            """
        )
        conn.commit()
        conn.close()

    def _table_name_for_user(self, user_id: int) -> str:
        return f"user_flags_{int(user_id)}"

    def ensure_user_table(self, user_id: int):
        table = self._table_name_for_user(user_id)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table} (
                url_hash TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                flagged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{table}_hash ON {table}(url_hash)"
        )
        conn.commit()
        conn.close()

    def create_user(self, email: str, password_hash: str) -> Optional[int]:
        if not self._is_safe_email(email):
            return None
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, password_hash),
            )
            user_id = cursor.lastrowid
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return None
        self.ensure_user_table(user_id)
        conn.close()
        return user_id

    def get_user(self, email: str) -> Optional[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, email, password_hash FROM users WHERE email = ?", (email,)
        )
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        return {"id": row[0], "email": row[1], "password_hash": row[2]}

    def flag_url(self, user_id: int, url_hash: str, url: str) -> bool:
        table = self._table_name_for_user(user_id)
        self.ensure_user_table(user_id)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                f"INSERT OR IGNORE INTO {table} (url_hash, url) VALUES (?, ?)",
                (url_hash, url),
            )
            conn.commit()
            inserted = cursor.rowcount > 0
        finally:
            conn.close()
        return inserted

    def is_flagged(self, user_id: int, url_hash: str) -> bool:
        table = self._table_name_for_user(user_id)
        self.ensure_user_table(user_id)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT 1 FROM {table} WHERE url_hash = ?", (url_hash,))
        row = cursor.fetchone()
        conn.close()
        return row is not None

    def exists_in_main_db(self, url_hash: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM url_hashes WHERE hash = ?", (url_hash,))
        row = cursor.fetchone()
        conn.close()
        return row is not None
    
    def exists_phishing_in_main_db(self, url_hash: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 1 FROM url_hashes
            WHERE hash = ?
              AND (
                    is_phishing = 1
                 OR is_phishing = '1'
                 OR LOWER(CAST(is_phishing AS TEXT)) IN ('true', 't', 'yes', 'y')
              )
            """,
            (url_hash,),
        )
        row = cursor.fetchone()
        conn.close()
        return row is not None

    def _is_safe_email(self, email: str) -> bool:
        pattern = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
        return bool(pattern.match(email))
