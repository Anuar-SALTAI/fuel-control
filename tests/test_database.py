import pickle
import sqlite3

from fuel_control.database import Database


def vehicle_data(name="Toyota"):
    return dict(name=name, brand="Toyota", model="Hiace", plate_number="123ABC01",
                fuel_type="Petrol", summer_norm=12, winter_norm=14, active=1)


def record_data(vehicle_id):
    return dict(vehicle_id=vehicle_id, start_date="2026-09-01", end_date="2026-09-07",
                start_odometer=1000, end_odometer=1200, distance_km=200, start_fuel=10,
                refueled_fuel=30, season="summer", used_norm=12, normative_consumption=24,
                calculated_balance=16, actual_end_fuel=None, difference=None, note="Week")


def test_default_vehicle_and_full_vehicle_profile(tmp_path):
    db = Database(tmp_path / "test.db")
    gazelle = db.vehicles()[0]
    assert (gazelle["summer_norm"], gazelle["winter_norm"]) == (26, 29.12)
    vehicle_id = db.add_vehicle(**vehicle_data())
    db.update_vehicle(vehicle_id, **{**vehicle_data(), "active": 0})
    saved = next(item for item in db.vehicles() if item["id"] == vehicle_id)
    assert saved["plate_number"] == "123ABC01"
    assert saved["active"] == 0


def test_date_range_record_lifecycle_and_pickle_regression(tmp_path):
    db = Database(tmp_path / "test.db")
    vehicle_id = db.add_vehicle(**vehicle_data())
    record_id = db.add_record(**record_data(vehicle_id))
    records = db.records(vehicle_id)
    assert records[0]["start_date"] == "2026-09-01"
    assert records[0]["actual_end_fuel"] is None
    assert all(type(item) is dict for item in db.vehicles())
    assert all(type(item) is dict for item in records)
    pickle.dumps((db.vehicles(), records))
    db.delete_record(record_id)
    assert db.records(vehicle_id) == []


def test_legacy_monthly_database_is_migrated_without_data_loss(tmp_path):
    path = tmp_path / "legacy.db"
    connection = sqlite3.connect(path)
    connection.executescript("""
      CREATE TABLE vehicles (id INTEGER PRIMARY KEY, name TEXT UNIQUE NOT NULL,
        summer_norm REAL NOT NULL, winter_norm REAL NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
      INSERT INTO vehicles VALUES (1, 'Газель', 26, 29.12, CURRENT_TIMESTAMP);
      CREATE TABLE records (id INTEGER PRIMARY KEY, vehicle_id INTEGER NOT NULL, month TEXT NOT NULL,
        season TEXT NOT NULL, norm REAL NOT NULL, mileage REAL NOT NULL, filled REAL NOT NULL,
        opening_balance REAL NOT NULL, closing_balance REAL NOT NULL, normative_consumption REAL NOT NULL,
        actual_consumption REAL NOT NULL, difference REAL NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
      INSERT INTO records VALUES (1, 1, '2026-08', 'summer', 26, 100, 20, 10, 4, 26, 26, 0, CURRENT_TIMESTAMP);
    """)
    connection.close()

    migrated = Database(path).records()[0]
    assert migrated["start_date"] == "2026-08-01"
    assert migrated["distance_km"] == 100
    assert migrated["actual_end_fuel"] == 4
    assert migrated["difference"] == 0
