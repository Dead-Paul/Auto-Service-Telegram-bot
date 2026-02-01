import sqlite3
from typing import Any

from .SQLite3 import SQLite


class SQL_Queries:
    def __init__(self, sqlite_db: SQLite):
        self.sqlite_db: SQLite = sqlite_db


    def register_new_user(self, user_id: int, phone_number: str, user_fullname: str) -> bool:
        try:
            self.sqlite_db.cursor().execute("""INSERT INTO "user" VALUES (?, ?, ?)""", [user_id, phone_number, user_fullname])
            return True
        except sqlite3.IntegrityError:
            return False

    def is_registered_user(self, user_id: int) -> bool:
        user: Any|None = self.sqlite_db.cursor().execute("""SELECT 1 FROM "user" WHERE id = ?""", [user_id]).fetchone()
        return True if user is not None else False

    def get_user(self, user_id: int) -> dict|None:
        try:
            return dict(self.sqlite_db.cursor().execute("""SELECT * FROM 'user' WHERE id = ?""", [user_id]).fetchone())
        except sqlite3.Error:
            return None

