"""Player service handling profile management and stat calculations."""
from __future__ import annotations

from typing import Any

from ..database import Database
from ..models import Item, Player, RPGClass, Skill, Trait


def _class_from_row(row: dict[str, Any]) -> RPGClass:
    return RPGClass(
        id=row["id"],
        name=row["name"],
        description=row.get("description", ""),
        constitution_multiplier=row.get("constitution_multiplier", 1.0),
        agility_multiplier=row.get("agility_multiplier", 1.0),
        defense_multiplier=row.get("defense_multiplier", 1.0),
        endurance_multiplier=row.get("endurance_multiplier", 1.0),
        dantian_multiplier=row.get("dantian_multiplier", 1.0),
        strength_multiplier=row.get("strength_multiplier", 1.0),
        spirit_multiplier=row.get("spirit_multiplier", 1.0),
    )


def _skill_from_row(row: dict[str, Any]) -> Skill:
    return Skill(
        id=row["id"],
        name=row["name"],
        description=row.get("description", ""),
        grade=row.get("grade", "Tier 1"),
        skill_type=row.get("skill_type", "physical"),
        cost=row.get("cost", 0),
        damage_multiplier=row.get("damage_multiplier", 1.0),
    )
from .lurkr import LurkrClient


class PlayerService:
    def __init__(self, db: Database, lurkr_client: LurkrClient):
        self.db = db
        self.lurkr = lurkr_client

    async def ensure_player(self, discord_id: int) -> Player:
        record = await self.db.fetch_one("SELECT * FROM users WHERE discord_id = ?", discord_id)
        if record is None:
            await self.db.execute("INSERT INTO users (discord_id) VALUES (?)", discord_id)
            record = await self.db.fetch_one("SELECT * FROM users WHERE discord_id = ?", discord_id)
        player = await self._hydrate_player(record)
        await self.sync_lurkr_level(player)
        return player

    async def sync_lurkr_level(self, player: Player) -> None:
        level = await self.lurkr.fetch_level(player.discord_id)
        if level is None or level == player.lurkr_level:
            return
        player.lurkr_level = level
        await self.db.execute(
            "UPDATE users SET lurkr_level = ? WHERE id = ?",
            level,
            player.id,
        )

    async def _hydrate_player(self, record: dict[str, Any]) -> Player:
        rpg_class = None
        if record.get("class_id"):
            class_row = await self.db.fetch_one("SELECT * FROM classes WHERE id = ?", record["class_id"])
            if class_row:
                rpg_class = _class_from_row(class_row)
        traits = [
            Trait(
                id=row["id"],
                name=row["name"],
                description=row.get("description", ""),
                modifiers=self.db.deserialize_payload(row.get("modifiers")),
            )
            for row in await self.db.fetch_all(
                """
                SELECT t.* FROM traits t
                JOIN user_traits ut ON ut.trait_id = t.id
                WHERE ut.user_id = ?
                """,
                record["id"],
            )
        ]
        items = [
            Item(
                id=row["id"],
                name=row["name"],
                description=row.get("description", ""),
                item_type=row["item_type"],
                price=row["price"],
                modifiers=self.db.deserialize_payload(row.get("modifiers")),
            )
            for row in await self.db.fetch_all(
                """
                SELECT i.* FROM items i
                JOIN inventory inv ON inv.item_id = i.id
                WHERE inv.user_id = ?
                """,
                record["id"],
            )
        ]
        skills = [
            _skill_from_row(row)
            for row in await self.db.fetch_all(
                """
                SELECT s.* FROM skills s
                JOIN class_skills cs ON cs.skill_id = s.id
                WHERE cs.class_id = ?
                """,
                record.get("class_id"),
            )
        ] if record.get("class_id") else []
        return Player(
            id=record["id"],
            discord_id=record["discord_id"],
            lurkr_level=record.get("lurkr_level", 1),
            coins=record.get("coins", 0),
            experience=record.get("experience", 0),
            rpg_class=rpg_class,
            traits=traits,
            items=items,
            skills=skills,
        )

    async def add_coins(self, player: Player, amount: int) -> None:
        player.coins += amount
        await self.db.execute("UPDATE users SET coins = ? WHERE id = ?", player.coins, player.id)

    async def spend_coins(self, player: Player, amount: int) -> bool:
        if player.coins < amount:
            return False
        await self.add_coins(player, -amount)
        return True

    async def assign_class(self, player: Player, class_id: int) -> None:
        await self.db.execute("UPDATE users SET class_id = ? WHERE id = ?", class_id, player.id)
        class_row = await self.db.fetch_one("SELECT * FROM classes WHERE id = ?", class_id)
        if class_row:
            player.rpg_class = _class_from_row(class_row)
        player.skills = [
            _skill_from_row(row)
            for row in await self.db.fetch_all(
                """
                SELECT s.* FROM skills s
                JOIN class_skills cs ON cs.skill_id = s.id
                WHERE cs.class_id = ?
                """,
                class_id,
            )
        ]

    async def grant_item(self, player: Player, item_id: int, quantity: int = 1) -> None:
        existing = await self.db.fetch_one(
            "SELECT quantity FROM inventory WHERE user_id = ? AND item_id = ?",
            player.id,
            item_id,
        )
        if existing:
            await self.db.execute(
                "UPDATE inventory SET quantity = quantity + ? WHERE user_id = ? AND item_id = ?",
                quantity,
                player.id,
                item_id,
            )
        else:
            await self.db.execute(
                "INSERT INTO inventory (user_id, item_id, quantity) VALUES (?, ?, ?)",
                player.id,
                item_id,
                quantity,
            )

    async def list_inventory(self, player: Player) -> list[Item]:
        items = await self.db.fetch_all(
            """
            SELECT i.* FROM items i
            JOIN inventory inv ON inv.item_id = i.id
            WHERE inv.user_id = ?
            """,
            player.id,
        )
        return [
            Item(
                id=row["id"],
                name=row["name"],
                description=row.get("description", ""),
                item_type=row["item_type"],
                price=row["price"],
                modifiers=self.db.deserialize_payload(row.get("modifiers")),
            )
            for row in items
        ]
