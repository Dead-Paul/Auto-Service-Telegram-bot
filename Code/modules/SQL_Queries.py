import sqlite3
from typing import Any
from datetime import datetime

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

    def cancel_appointment(self, appointment_id: int) -> bool:
        self.sqlite_db.cursor().execute("""UPDATE appointment SET status = -1 WHERE id = ? AND status = 0""", [appointment_id])
        return True

    def add_service(self, name: str, img_src: str, price: float, currency: str, duration_min: float, description: str) -> bool:
        try:
            self.sqlite_db.cursor().execute("""INSERT INTO "service" (name, img_src, price, currency, duration_min, description) VALUES (?, ?, ?, ?, ?, ?)""",
                                            [name, img_src, price, currency, duration_min, description]
            )
            return True
        except sqlite3.Error:
            return False

    def get_service(self, service_id: int) -> dict | None:
        try:
            row = self.sqlite_db.cursor().execute("""SELECT * FROM "service" WHERE id = ?""", [service_id]).fetchone()
            return dict(row) if row else None
        except sqlite3.Error:
            return None

    def get_all_services(self) -> list[dict]:
        rows = self.sqlite_db.cursor().execute("""SELECT * FROM service ORDER BY id""").fetchall()
        return [dict(row) for row in rows]

    def get_future_appointments(self, user_id: int) -> list[dict]:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        rows = self.sqlite_db.cursor().execute(
            """
            SELECT a.id, a.appointment_ts, a.status, s.name, s.duration_min, s.price, s.currency
            FROM "appointment" a
            JOIN "service" s ON a.service_id = s.id
            WHERE a.user_id = ? AND a.status = 0 AND a.appointment_ts > ?
            ORDER BY a.appointment_ts
            """,
            [user_id, now]
        ).fetchall()
        return [dict(row) for row in rows]

    def get_past_appointments(self, user_id: int) -> list[dict]:
        rows = self.sqlite_db.cursor().execute(
            """
            SELECT a.id, a.appointment_ts, a.status, s.name, s.duration_min, s.price, s.currency
            FROM appointment a
            JOIN service s ON a.service_id = s.id
            WHERE a.user_id = ? AND a.status IN (-1, 1)
            ORDER BY a.appointment_ts DESC
            """,
            [user_id]
        ).fetchall()
        return [dict(row) for row in rows]