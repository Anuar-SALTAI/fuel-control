"""User-scoped data access through Supabase/PostgREST."""


class SupabaseRepository:
    """Repository whose explicit filters complement database RLS policies."""

    def __init__(self, client, user_id: str):
        self.client = client
        self.user_id = user_id

    def vehicles(self, include_archived: bool = True) -> list[dict]:
        query = self.client.table("vehicles").select("*").eq("user_id", self.user_id)
        if not include_archived:
            query = query.eq("active", True)
        return query.order("name").execute().data

    def add_vehicle(self, **vehicle):
        data = {**vehicle, "user_id": self.user_id, "active": bool(vehicle["active"])}
        return self.client.table("vehicles").insert(data).execute().data[0]["id"]

    def update_vehicle(self, vehicle_id, **vehicle) -> None:
        data = {**vehicle, "active": bool(vehicle["active"])}
        (self.client.table("vehicles").update(data).eq("id", vehicle_id)
         .eq("user_id", self.user_id).execute())

    def add_record(self, **record):
        data = {**record, "user_id": self.user_id}
        return self.client.table("records").insert(data).execute().data[0]["id"]

    def records(self, vehicle_id=None) -> list[dict]:
        query = (self.client.table("records").select("*, vehicles!inner(name)")
                 .eq("user_id", self.user_id))
        if vehicle_id is not None:
            query = query.eq("vehicle_id", vehicle_id)
        rows = query.order("end_date", desc=True).order("created_at", desc=True).execute().data
        for row in rows:
            row["vehicle_name"] = row.pop("vehicles")["name"]
        return rows

    def delete_record(self, record_id) -> None:
        (self.client.table("records").delete().eq("id", record_id)
         .eq("user_id", self.user_id).execute())
