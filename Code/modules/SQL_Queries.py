import sqlite3
from typing import Any

from .Utils import SQLite


class SQL_Queries:
    def __init__(self, sqlite_db: SQLite):
        self.sqlite_db: SQLite = sqlite_db


    def register_new_user(self, user_id: int, phone_number: str, user_fullname: str) -> bool:
        try:
            self.sqlite_db.cursor().execute("""INSERT INTO "user" (id, phone, fullname) VALUES (?, ?, ?)""", [user_id, phone_number, user_fullname])
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

    def create_appointment(self, user_id: int, service_id: int, appointment_ts: str) -> bool:
        try:
            self.sqlite_db.cursor().execute("""INSERT INTO "appointment" (user_id, service_id, appointment_ts, status) VALUES (?, ?, ?, 0)""", [user_id, service_id, appointment_ts])
            return True
        except sqlite3.Error:
            return False


    def is_timeslot_taken(self, appointment_ts: str) -> bool:
        appointment: Any|None = self.sqlite_db.cursor().execute("""SELECT 1 FROM "appointment" WHERE appointment_ts = ? AND status = 0""", [appointment_ts]).fetchone()
        return True if appointment is not None else False


    def get_future_appointments(self, user_id: int) -> list[dict]:
        rows = self.sqlite_db.cursor().execute("""SELECT * FROM "appointment" WHERE user_id = ? AND status = 0 AND appointment_ts >= datetime('now') ORDER BY appointment_ts""", [user_id]).fetchall()
        return [dict(row) for row in rows]


    def get_past_appointments(self, user_id: int) -> list[dict]:
        rows = self.sqlite_db.cursor().execute("""SELECT * FROM "appointment" WHERE user_id = ? AND status != 0 ORDER BY appointment_ts DESC""", [user_id]).fetchall()
        return [dict(row) for row in rows]


    def cancel_appointment(self, appointment_id: int) -> bool:
        self.sqlite_db.cursor().execute("""UPDATE appointment SET status = -1 WHERE id = ? AND status = 0""", [appointment_id])
        return True