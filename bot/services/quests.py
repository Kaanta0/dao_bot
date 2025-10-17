"""Quest handling utilities."""
from __future__ import annotations

from typing import Any

from ..database import Database
from ..models import Quest


class QuestService:
    def __init__(self, db: Database):
        self.db = db

    async def list_available(self, level: int) -> list[Quest]:
        rows = await self.db.fetch_all(
            "SELECT * FROM quests WHERE required_level <= ?",
            level,
        )
        return [
            Quest(
                id=row["id"],
                name=row["name"],
                description=row.get("description", ""),
                required_level=row["required_level"],
                rewards=self.db.deserialize_payload(row.get("rewards")),
            )
            for row in rows
        ]

    async def assign(self, user_id: int, quest_id: int) -> None:
        await self.db.execute(
            "INSERT OR IGNORE INTO user_quests (user_id, quest_id) VALUES (?, ?)",
            user_id,
            quest_id,
        )

    async def complete(self, user_id: int, quest_id: int) -> dict[str, Any]:
        quest_row = await self.db.fetch_one("SELECT * FROM quests WHERE id = ?", quest_id)
        if not quest_row:
            raise ValueError("Quest not found")
        await self.db.execute(
            "UPDATE user_quests SET status = 'completed' WHERE user_id = ? AND quest_id = ?",
            user_id,
            quest_id,
        )
        return self.db.deserialize_payload(quest_row.get("rewards"))
