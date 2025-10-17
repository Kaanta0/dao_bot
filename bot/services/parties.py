"""Party management utilities."""
from __future__ import annotations

from ..database import Database


class PartyService:
    def __init__(self, db: Database):
        self.db = db

    async def create_party(self, leader_user_id: int, name: str) -> int:
        cursor = await self.db.execute(
            "INSERT INTO parties (name, leader_user_id) VALUES (?, ?)",
            name,
            leader_user_id,
        )
        party_id = cursor.lastrowid
        await self.db.execute(
            "INSERT INTO party_members (party_id, user_id) VALUES (?, ?)",
            party_id,
            leader_user_id,
        )
        return party_id

    async def join_party(self, party_id: int, user_id: int) -> None:
        await self.db.execute(
            "INSERT OR IGNORE INTO party_members (party_id, user_id) VALUES (?, ?)",
            party_id,
            user_id,
        )

    async def leave_party(self, party_id: int, user_id: int) -> None:
        await self.db.execute(
            "DELETE FROM party_members WHERE party_id = ? AND user_id = ?",
            party_id,
            user_id,
        )

    async def list_members(self, party_id: int) -> list[int]:
        rows = await self.db.fetch_all(
            "SELECT user_id FROM party_members WHERE party_id = ?",
            party_id,
        )
        return [row["user_id"] for row in rows]

    async def disband_party(self, party_id: int) -> None:
        await self.db.execute("DELETE FROM parties WHERE id = ?", party_id)
