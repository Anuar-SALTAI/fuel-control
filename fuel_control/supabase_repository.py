"""User-scoped Supabase PostgreSQL repository."""


class SupabaseRepository:
    def __init__(self, client, user_id: str, role: str = "user"):
        self.client, self.user_id, self.role = client, user_id, role

    def _scope(self, query):
        return query if self.role == "admin" else query.eq("user_id", self.user_id)

    def vehicles(self, include_archived: bool = True) -> list[dict]:
        query = self._scope(self.client.table("vehicles").select("*"))
        if not include_archived:
            query = query.eq("is_active", True)
        rows = query.order("name").execute().data
        return [{**row, "active": int(row.get("is_active", True))} for row in rows]

    def ensure_default_vehicle(self):
        if not self.vehicles():
            self.add_vehicle(
                name="Газель",
                brand="ГАЗ",
                model="",
                plate_number="",
                fuel_type="",
                summer_norm=26,
                winter_norm=29.12,
                active=1,
            )

    def add_vehicle(self, **vehicle):
        active = vehicle.pop("active")
        payload = {**vehicle, "user_id": self.user_id, "is_active": bool(active)}
        return self.client.table("vehicles").insert(payload).execute().data[0]["id"]

    def update_vehicle(self, vehicle_id, **vehicle):
        active = vehicle.pop("active")
        payload = {**vehicle, "is_active": bool(active)}
        self._scope(
            self.client.table("vehicles").update(payload).eq("id", vehicle_id)
        ).execute()

    def add_record(self, **record):
        payload = {**record, "user_id": self.user_id}
        return self.client.table("fuel_records").insert(payload).execute().data[0]["id"]

    def records(self, vehicle_id=None) -> list[dict]:
        query = self._scope(
            self.client.table("fuel_records").select("*, vehicles(name)")
        )
        if vehicle_id is not None:
            query = query.eq("vehicle_id", vehicle_id)
        rows = (
            query.order("end_date", desc=True)
            .order("created_at", desc=True)
            .execute()
            .data
        )
        return [
            {**row, "vehicle_name": (row.get("vehicles") or {}).get("name", "")}
            for row in rows
        ]

    def delete_record(self, record_id):
        self._scope(
            self.client.table("fuel_records").delete().eq("id", record_id)
        ).execute()

    def profiles(self):
        if self.role != "admin":
            raise PermissionError("Admin access required")
        return (
            self.client.table("profiles")
            .select("id,full_name,email,role,is_active,created_at")
            .execute()
            .data
        )

    def set_profile_active(self, profile_id, active):
        if self.role != "admin":
            raise PermissionError("Admin access required")
        self.client.table("profiles").update({"is_active": active}).eq(
            "id", profile_id
        ).execute()
