import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from fuel_control.supabase_repository import SupabaseRepository


class Query:
    def __init__(self, rows, operation="select", payload=None):
        self.rows = rows
        self.operation = operation
        self.payload = payload
        self.filters = []

    def select(self, *_):
        return self

    def insert(self, payload):
        self.operation, self.payload = "insert", payload
        return self

    def update(self, payload):
        self.operation, self.payload = "update", payload
        return self

    def delete(self):
        self.operation = "delete"
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def order(self, *_args, **_kwargs):
        return self

    def execute(self):
        if self.operation == "insert":
            row = {"id": len(self.rows) + 1, **self.payload}
            self.rows.append(row)
            return SimpleNamespace(data=[row])
        selected = [
            dict(row)
            for row in self.rows
            if all(row.get(field) == value for field, value in self.filters)
        ]
        return SimpleNamespace(data=selected)


class FakeClient:
    def __init__(self):
        self.tables = {"vehicles": []}

    def table(self, name):
        return Query(self.tables.setdefault(name, []))


def test_supabase_vehicle_operations_are_user_scoped():
    client = FakeClient()
    vehicle = dict(
        name="Van", brand="", model="", plate_number="", fuel_type="Diesel",
        summer_norm=10, winter_norm=12, active=1,
    )
    repo_a = SupabaseRepository(client, "user-a")
    repo_b = SupabaseRepository(client, "user-b")
    repo_a.add_vehicle(**vehicle)
    repo_b.add_vehicle(**vehicle)

    assert [item["user_id"] for item in repo_a.vehicles()] == ["user-a"]
    assert [item["user_id"] for item in repo_b.vehicles()] == ["user-b"]


def test_add_record_payload_is_json_compatible():
    client = FakeClient()
    repository = SupabaseRepository(client, "user-a")

    repository.add_record(
        vehicle_id=1,
        start_date=date(2026, 9, 1),
        end_date="2026-09-30",
        used_norm=Decimal("26.00"),
        note_path=Path("receipts/september.txt"),
    )

    payload = client.tables["records"][0]
    json.dumps(payload)
    assert payload["used_norm"] == 26.0
    assert payload["start_date"] == "2026-09-01"
    assert payload["note_path"] == "receipts/september.txt"
