from fuel_control.database import Database


def test_database_creates_default_gazelle(tmp_path):
    db = Database(tmp_path / "test.db")
    vehicle = db.vehicles()[0]
    assert vehicle["name"] == "Газель"
    assert vehicle["summer_norm"] == 26
    assert vehicle["winter_norm"] == 29.12


def test_vehicle_update_and_record_lifecycle(tmp_path):
    db = Database(tmp_path / "test.db")
    vehicle_id = db.add_vehicle("Toyota", 12, 14)
    db.update_vehicle(vehicle_id, 11.5, 13.5)
    toyota = next(vehicle for vehicle in db.vehicles() if vehicle["id"] == vehicle_id)
    assert toyota["summer_norm"] == 11.5
    record_id = db.add_record(
        vehicle_id=vehicle_id, month="2026-09", season="summer", norm=11.5,
        mileage=1000, filled=120, opening_balance=10, closing_balance=15,
        normative_consumption=115, actual_consumption=115, difference=0,
    )
    assert db.records(vehicle_id)[0]["vehicle_name"] == "Toyota"
    db.delete_record(record_id)
    assert db.records(vehicle_id) == []
