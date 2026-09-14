"""SQLite persistence for vehicles and monthly fuel records."""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path


DEFAULT_DB_PATH = Path(os.getenv("FUEL_CONTROL_DB", "data/fuel_control.db"))


class Database:
    def __init__(self, path: str | Path = DEFAULT_DB_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS vehicles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    summer_norm REAL NOT NULL CHECK (summer_norm >= 0),
                    winter_norm REAL NOT NULL CHECK (winter_norm >= 0),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicle_id INTEGER NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
                    month TEXT NOT NULL,
                    season TEXT NOT NULL CHECK (season IN ('summer', 'winter')),
                    norm REAL NOT NULL,
                    mileage REAL NOT NULL,
                    filled REAL NOT NULL,
                    opening_balance REAL NOT NULL,
                    closing_balance REAL NOT NULL,
                    normative_consumption REAL NOT NULL,
                    actual_consumption REAL NOT NULL,
                    difference REAL NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            connection.execute(
                "INSERT OR IGNORE INTO vehicles(name, summer_norm, winter_norm) VALUES (?, ?, ?)",
                ("Газель", 26, 29.12),
            )

    def vehicles(self) -> list[dict]:
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM vehicles ORDER BY name").fetchall()
            return [dict(row) for row in rows]

    def add_vehicle(self, name: str, summer_norm: float, winter_norm: float) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO vehicles(name, summer_norm, winter_norm) VALUES (?, ?, ?)",
                (name.strip(), summer_norm, winter_norm),
            )
            return cursor.lastrowid

    def update_vehicle(self, vehicle_id: int, summer_norm: float, winter_norm: float) -> None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE vehicles SET summer_norm = ?, winter_norm = ? WHERE id = ?",
                (summer_norm, winter_norm, vehicle_id),
            )

    def add_record(self, **record) -> int:
        fields = (
            "vehicle_id", "month", "season", "norm", "mileage", "filled",
            "opening_balance", "closing_balance", "normative_consumption",
            "actual_consumption", "difference",
        )
        with self.connect() as connection:
            cursor = connection.execute(
                f"INSERT INTO records ({', '.join(fields)}) VALUES ({', '.join('?' for _ in fields)})",
                tuple(record[field] for field in fields),
            )
            return cursor.lastrowid

    def records(self, vehicle_id: int | None = None) -> list[dict]:
        query = """SELECT r.*, v.name AS vehicle_name FROM records r
                   JOIN vehicles v ON v.id = r.vehicle_id"""
        params: tuple = ()
        if vehicle_id is not None:
            query += " WHERE r.vehicle_id = ?"
            params = (vehicle_id,)
        query += " ORDER BY r.month DESC, r.created_at DESC, r.id DESC"
        with self.connect() as connection:
            rows = connection.execute(query, params).fetchall()
            return [dict(row) for row in rows]

    def delete_record(self, record_id: int) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM records WHERE id = ?", (record_id,))
