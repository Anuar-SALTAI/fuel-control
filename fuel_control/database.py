"""SQLite persistence and backwards-compatible schema migration."""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DEFAULT_DB_PATH = Path(os.getenv("FUEL_CONTROL_DB", "data/fuel_control.db"))

RECORDS_SCHEMA = """
CREATE TABLE records (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 vehicle_id INTEGER NOT NULL REFERENCES vehicles(id),
 start_date TEXT NOT NULL, end_date TEXT NOT NULL,
 start_odometer REAL NOT NULL, end_odometer REAL NOT NULL, distance_km REAL NOT NULL,
 start_fuel REAL NOT NULL, refueled_fuel REAL NOT NULL,
 season TEXT NOT NULL CHECK (season IN ('summer', 'winter')), used_norm REAL NOT NULL,
 normative_consumption REAL NOT NULL, calculated_balance REAL NOT NULL,
 actual_end_fuel REAL, difference REAL, note TEXT NOT NULL DEFAULT '',
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);"""


class Database:
    def __init__(self, path: str | Path = DEFAULT_DB_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.execute("""CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE,
                summer_norm REAL NOT NULL CHECK(summer_norm >= 0),
                winter_norm REAL NOT NULL CHECK(winter_norm >= 0),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
            vehicle_columns = {row["name"] for row in connection.execute("PRAGMA table_info(vehicles)")}
            for name, definition in (
                ("brand", "TEXT NOT NULL DEFAULT ''"), ("model", "TEXT NOT NULL DEFAULT ''"),
                ("plate_number", "TEXT NOT NULL DEFAULT ''"), ("fuel_type", "TEXT NOT NULL DEFAULT ''"),
                ("active", "INTEGER NOT NULL DEFAULT 1"),
            ):
                if name not in vehicle_columns:
                    connection.execute(f"ALTER TABLE vehicles ADD COLUMN {name} {definition}")
            connection.execute(
                "INSERT OR IGNORE INTO vehicles(name, summer_norm, winter_norm) VALUES (?, ?, ?)",
                ("Газель", 26, 29.12),
            )
            self._migrate_records(connection)

    @staticmethod
    def _migrate_records(connection: sqlite3.Connection) -> None:
        exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='records'"
        ).fetchone()
        if not exists:
            connection.execute(RECORDS_SCHEMA)
            return
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(records)")}
        if "start_date" in columns:
            return
        connection.execute("ALTER TABLE records RENAME TO records_legacy")
        connection.execute(RECORDS_SCHEMA)
        connection.execute("""INSERT INTO records (
            id, vehicle_id, start_date, end_date, start_odometer, end_odometer, distance_km,
            start_fuel, refueled_fuel, season, used_norm, normative_consumption,
            calculated_balance, actual_end_fuel, difference, note, created_at, updated_at)
            SELECT id, vehicle_id, month || '-01', month || '-01', 0, mileage, mileage,
            opening_balance, filled, season, norm, normative_consumption,
            opening_balance + filled - normative_consumption, closing_balance, difference, '',
            created_at, created_at FROM records_legacy""")

    def vehicles(self, include_archived: bool = True) -> list[dict]:
        query = "SELECT * FROM vehicles" + ("" if include_archived else " WHERE active = 1") + " ORDER BY name"
        with self.connect() as connection:
            return [dict(row) for row in connection.execute(query)]

    def add_vehicle(self, **vehicle) -> int:
        fields = ("name", "brand", "model", "plate_number", "fuel_type", "summer_norm", "winter_norm", "active")
        with self.connect() as connection:
            cursor = connection.execute(
                f"INSERT INTO vehicles ({', '.join(fields)}) VALUES ({', '.join('?' for _ in fields)})",
                tuple(vehicle[field] for field in fields),
            )
            return cursor.lastrowid

    def update_vehicle(self, vehicle_id: int, **vehicle) -> None:
        fields = ("name", "brand", "model", "plate_number", "fuel_type", "summer_norm", "winter_norm", "active")
        with self.connect() as connection:
            connection.execute(
                f"UPDATE vehicles SET {', '.join(f'{field} = ?' for field in fields)} WHERE id = ?",
                (*[vehicle[field] for field in fields], vehicle_id),
            )

    def add_record(self, **record) -> int:
        fields = ("vehicle_id", "start_date", "end_date", "start_odometer", "end_odometer", "distance_km",
                  "start_fuel", "refueled_fuel", "season", "used_norm", "normative_consumption",
                  "calculated_balance", "actual_end_fuel", "difference", "note")
        with self.connect() as connection:
            cursor = connection.execute(
                f"INSERT INTO records ({', '.join(fields)}) VALUES ({', '.join('?' for _ in fields)})",
                tuple(record[field] for field in fields),
            )
            return cursor.lastrowid

    def records(self, vehicle_id: int | None = None) -> list[dict]:
        query = "SELECT r.*, v.name AS vehicle_name FROM records r JOIN vehicles v ON v.id = r.vehicle_id"
        params = ()
        if vehicle_id is not None:
            query += " WHERE r.vehicle_id = ?"
            params = (vehicle_id,)
        query += " ORDER BY r.end_date DESC, r.created_at DESC, r.id DESC"
        with self.connect() as connection:
            return [dict(row) for row in connection.execute(query, params)]

    def delete_record(self, record_id: int) -> None:
        with self.connect() as connection:
            connection.execute("DELETE FROM records WHERE id = ?", (record_id,))
