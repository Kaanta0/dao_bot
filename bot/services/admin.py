"""Administrative helpers for creating content."""
from __future__ import annotations

from typing import Any

from ..database import Database


class AdminService:
    def __init__(self, db: Database):
        self.db = db

    async def create_class(
        self,
        name: str,
        description: str,
        constitution_multiplier: float,
        agility_multiplier: float,
        defense_multiplier: float,
        endurance_multiplier: float,
        dantian_multiplier: float,
        strength_multiplier: float,
        spirit_multiplier: float,
    ) -> int:
        cursor = await self.db.execute(
            """
            INSERT INTO classes (
                name,
                description,
                constitution_multiplier,
                agility_multiplier,
                defense_multiplier,
                endurance_multiplier,
                dantian_multiplier,
                strength_multiplier,
                spirit_multiplier
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            name,
            description,
            constitution_multiplier,
            agility_multiplier,
            defense_multiplier,
            endurance_multiplier,
            dantian_multiplier,
            strength_multiplier,
            spirit_multiplier,
        )
        return cursor.lastrowid

    async def create_skill(
        self,
        name: str,
        description: str,
        grade: str,
        skill_type: str,
        cost: int,
        damage_multiplier: float,
    ) -> int:
        normalized_type = skill_type.lower()
        if normalized_type not in {"physical", "spiritual"}:
            raise ValueError("skill_type must be either 'physical' or 'spiritual'")
        cursor = await self.db.execute(
            """
            INSERT INTO skills (name, description, grade, skill_type, cost, damage_multiplier)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            name,
            description,
            grade,
            normalized_type,
            cost,
            damage_multiplier,
        )
        return cursor.lastrowid

    async def assign_skill_to_class(self, class_id: int, skill_id: int) -> None:
        await self.db.execute(
            "INSERT OR IGNORE INTO class_skills (class_id, skill_id) VALUES (?, ?)",
            class_id,
            skill_id,
        )

    async def create_trait(self, name: str, description: str, modifiers: dict[str, float]) -> int:
        cursor = await self.db.execute(
            "INSERT INTO traits (name, description, modifiers) VALUES (?, ?, ?)",
            name,
            description,
            self.db.serialize_payload(modifiers),
        )
        return cursor.lastrowid

    async def create_item(
        self,
        name: str,
        description: str,
        item_type: str,
        price: int,
        modifiers: dict[str, float],
    ) -> int:
        cursor = await self.db.execute(
            "INSERT INTO items (name, description, item_type, price, modifiers) VALUES (?, ?, ?, ?, ?)",
            name,
            description,
            item_type,
            price,
            self.db.serialize_payload(modifiers),
        )
        return cursor.lastrowid

    async def create_enemy(
        self,
        name: str,
        description: str,
        level: int,
        stats: dict[str, Any],
        rewards: dict[str, Any],
        is_boss: bool = False,
    ) -> int:
        cursor = await self.db.execute(
            "INSERT INTO enemies (name, description, level, stats, rewards, is_boss) VALUES (?, ?, ?, ?, ?, ?)",
            name,
            description,
            level,
            self.db.serialize_payload(stats),
            self.db.serialize_payload(rewards),
            int(is_boss),
        )
        return cursor.lastrowid

    async def create_quest(
        self,
        name: str,
        description: str,
        required_level: int,
        rewards: dict[str, Any],
    ) -> int:
        cursor = await self.db.execute(
            "INSERT INTO quests (name, description, required_level, rewards) VALUES (?, ?, ?, ?)",
            name,
            description,
            required_level,
            self.db.serialize_payload(rewards),
        )
        return cursor.lastrowid

    async def create_currency(self, name: str, description: str, is_premium: bool = False) -> int:
        cursor = await self.db.execute(
            "INSERT INTO currencies (name, description, is_premium) VALUES (?, ?, ?)",
            name,
            description,
            int(is_premium),
        )
        return cursor.lastrowid
