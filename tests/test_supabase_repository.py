from types import SimpleNamespace

from fuel_control.supabase_repository import SupabaseRepository


class Query:
    def __init__(self, rows):
        self.rows, self.filters = rows, []

    def select(self, *_):
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def order(self, *_args, **_kwargs):
        return self

    def execute(self):
        rows = [
            row
            for row in self.rows
            if all(row.get(key) == value for key, value in self.filters)
        ]
        return SimpleNamespace(data=rows)


class Client:
    def __init__(self, rows):
        self.rows = rows

    def table(self, name):
        assert name == "fuel_records"
        return Query(self.rows)


def test_authenticated_user_only_receives_own_records():
    rows = [
        {
            "id": 1,
            "user_id": "user-a",
            "end_date": "2026-01-01",
            "created_at": "x",
            "vehicles": {"name": "A"},
        },
        {
            "id": 2,
            "user_id": "user-b",
            "end_date": "2026-01-01",
            "created_at": "x",
            "vehicles": {"name": "B"},
        },
    ]
    records = SupabaseRepository(Client(rows), "user-a").records()
    assert [record["id"] for record in records] == [1]


def test_admin_can_receive_all_records():
    rows = [
        {
            "id": 1,
            "user_id": "user-a",
            "end_date": "2026-01-01",
            "created_at": "x",
            "vehicles": None,
        },
        {
            "id": 2,
            "user_id": "user-b",
            "end_date": "2026-01-01",
            "created_at": "x",
            "vehicles": None,
        },
    ]
    assert len(SupabaseRepository(Client(rows), "admin", role="admin").records()) == 2
