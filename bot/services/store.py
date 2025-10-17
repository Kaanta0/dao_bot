"""Storefront utilities for buying and selling items."""
from __future__ import annotations

from ..database import Database
from ..models import Item


class StoreService:
    def __init__(self, db: Database):
        self.db = db

    async def list_items(self) -> list[Item]:
        rows = await self.db.fetch_all("SELECT * FROM items ORDER BY price ASC")
        return [
            Item(
                id=row["id"],
                name=row["name"],
                description=row.get("description", ""),
                item_type=row["item_type"],
                price=row["price"],
                modifiers=self.db.deserialize_payload(row.get("modifiers")),
            )
            for row in rows
        ]

    async def get_item(self, item_id: int) -> Item | None:
        row = await self.db.fetch_one("SELECT * FROM items WHERE id = ?", item_id)
        if not row:
            return None
        return Item(
            id=row["id"],
            name=row["name"],
            description=row.get("description", ""),
            item_type=row["item_type"],
            price=row["price"],
            modifiers=self.db.deserialize_payload(row.get("modifiers")),
        )
