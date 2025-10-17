"""Database layer for the Discord RPG bot."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import aiosqlite


SCHEMA = (
    """
    PRAGMA foreign_keys = ON;

    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        discord_id INTEGER UNIQUE NOT NULL,
        lurkr_level INTEGER NOT NULL DEFAULT 1,
        class_id INTEGER,
        coins INTEGER NOT NULL DEFAULT 0,
        experience INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY(class_id) REFERENCES classes(id)
    );

    CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        constitution_multiplier REAL NOT NULL DEFAULT 1.0,
        agility_multiplier REAL NOT NULL DEFAULT 1.0,
        defense_multiplier REAL NOT NULL DEFAULT 1.0,
        endurance_multiplier REAL NOT NULL DEFAULT 1.0,
        dantian_multiplier REAL NOT NULL DEFAULT 1.0,
        strength_multiplier REAL NOT NULL DEFAULT 1.0,
        spirit_multiplier REAL NOT NULL DEFAULT 1.0
    );

    CREATE TABLE IF NOT EXISTS skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        grade TEXT NOT NULL DEFAULT 'Tier 1',
        skill_type TEXT NOT NULL DEFAULT 'physical',
        cost INTEGER NOT NULL DEFAULT 0,
        damage_multiplier REAL NOT NULL DEFAULT 1.0
    );

    CREATE TABLE IF NOT EXISTS class_skills (
        class_id INTEGER NOT NULL,
        skill_id INTEGER NOT NULL,
        PRIMARY KEY (class_id, skill_id),
        FOREIGN KEY(class_id) REFERENCES classes(id) ON DELETE CASCADE,
        FOREIGN KEY(skill_id) REFERENCES skills(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS traits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        modifiers TEXT NOT NULL DEFAULT '{}'
    );

    CREATE TABLE IF NOT EXISTS user_traits (
        user_id INTEGER NOT NULL,
        trait_id INTEGER NOT NULL,
        PRIMARY KEY (user_id, trait_id),
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(trait_id) REFERENCES traits(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        item_type TEXT NOT NULL,
        price INTEGER NOT NULL DEFAULT 0,
        modifiers TEXT NOT NULL DEFAULT '{}'
    );

    CREATE TABLE IF NOT EXISTS inventory (
        user_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 0,
        equipped INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (user_id, item_id),
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS quests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        required_level INTEGER NOT NULL DEFAULT 1,
        rewards TEXT NOT NULL DEFAULT '{}'
    );

    CREATE TABLE IF NOT EXISTS user_quests (
        user_id INTEGER NOT NULL,
        quest_id INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'active',
        progress TEXT NOT NULL DEFAULT '{}',
        PRIMARY KEY (user_id, quest_id),
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(quest_id) REFERENCES quests(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS enemies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        level INTEGER NOT NULL DEFAULT 1,
        stats TEXT NOT NULL DEFAULT '{}',
        rewards TEXT NOT NULL DEFAULT '{}',
        is_boss INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS parties (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        leader_user_id INTEGER NOT NULL,
        is_open INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY(leader_user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS party_members (
        party_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        PRIMARY KEY (party_id, user_id),
        FOREIGN KEY(party_id) REFERENCES parties(id) ON DELETE CASCADE,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS currencies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT,
        is_premium INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS user_currencies (
        user_id INTEGER NOT NULL,
        currency_id INTEGER NOT NULL,
        amount INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY (user_id, currency_id),
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(currency_id) REFERENCES currencies(id) ON DELETE CASCADE
    );
    """
)


class Database:
    """Simple asynchronous SQLite wrapper used by services."""

    def __init__(self, path: str):
        self.path = Path(path)
        self._conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self._conn = await aiosqlite.connect(self.path)
        self._conn.row_factory = aiosqlite.Row
        await self._conn.executescript(SCHEMA)
        await self._conn.commit()

    async def close(self) -> None:
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    @property
    def connection(self) -> aiosqlite.Connection:
        if self._conn is None:
            raise RuntimeError("Database connection accessed before initialization")
        return self._conn

    async def execute(self, query: str, *params: Any) -> aiosqlite.Cursor:
        cursor = await self.connection.execute(query, params)
        await self.connection.commit()
        return cursor

    async def fetch_one(self, query: str, *params: Any) -> dict[str, Any] | None:
        cursor = await self.connection.execute(query, params)
        row = await cursor.fetchone()
        await cursor.close()
        return dict(row) if row else None

    async def fetch_all(self, query: str, *params: Any) -> list[dict[str, Any]]:
        cursor = await self.connection.execute(query, params)
        rows = await cursor.fetchall()
        await cursor.close()
        return [dict(row) for row in rows]

    @staticmethod
    def serialize_payload(payload: dict[str, Any]) -> str:
        return json.dumps(payload, separators=(",", ":"))

    @staticmethod
    def deserialize_payload(raw: str | None) -> dict[str, Any]:
        if not raw:
            return {}
        return json.loads(raw)
