"""Lightweight combat simulation utilities."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable

from ..database import Database
from ..models import Enemy, Player


@dataclass(slots=True)
class BattleResult:
    success: bool
    log: list[str]
    rewards: dict[str, int | list[int]]


class CombatService:
    def __init__(self, db: Database):
        self.db = db

    async def fetch_enemy(self, enemy_id: int) -> Enemy | None:
        row = await self.db.fetch_one("SELECT * FROM enemies WHERE id = ?", enemy_id)
        if not row:
            return None
        return Enemy(
            id=row["id"],
            name=row["name"],
            description=row.get("description", ""),
            level=row["level"],
            stats=self.db.deserialize_payload(row.get("stats")),
            rewards=self.db.deserialize_payload(row.get("rewards")),
            is_boss=bool(row.get("is_boss")),
        )

    async def battle(self, players: Iterable[Player], enemy: Enemy) -> BattleResult:
        player_stat_blocks = [player.calculate_stats() for player in players]
        total_constitution = sum(stats.get("constitution", 0.0) for stats in player_stat_blocks)
        total_agility = sum(stats.get("agility", 0.0) for stats in player_stat_blocks)
        total_defense = sum(stats.get("defense", 0.0) for stats in player_stat_blocks)
        total_endurance = sum(stats.get("endurance", 0.0) for stats in player_stat_blocks)
        total_dantian = sum(stats.get("dantian_size", 0.0) for stats in player_stat_blocks)
        total_strength = sum(stats.get("strength", 0.0) for stats in player_stat_blocks)
        total_spirit = sum(stats.get("spirit", 0.0) for stats in player_stat_blocks)

        player_power = (
            total_strength
            + total_spirit
            + (total_agility * 0.5)
            + (total_endurance * 0.25)
            + (total_dantian * 0.25)
        )
        player_resilience = total_constitution + total_defense

        def enemy_stat(key: str, *aliases: str, default: float) -> float:
            for candidate in (key, *aliases):
                if candidate in enemy.stats:
                    try:
                        return float(enemy.stats[candidate])
                    except (TypeError, ValueError):
                        break
            return default

        enemy_strength = enemy_stat("strength", "power", "attack", default=enemy.level * 8)
        enemy_spirit = enemy_stat("spirit", "magic", default=enemy.level * 6)
        enemy_agility = enemy_stat("agility", default=enemy.level * 4)
        enemy_endurance = enemy_stat("endurance", default=enemy.level * 5)
        enemy_dantian = enemy_stat("dantian_size", "qi", default=enemy.level * 3)
        enemy_defense = enemy_stat("defense", default=enemy.level * 5)
        enemy_constitution = enemy_stat("constitution", "hp", default=enemy.level * 12)

        enemy_effective_power = (
            enemy_strength
            + enemy_spirit
            + (enemy_agility * 0.5)
            + (enemy_endurance * 0.25)
            + (enemy_dantian * 0.25)
        )
        enemy_resilience = enemy_constitution + enemy_defense

        log = [f"Encountered {enemy.name} (Lv {enemy.level})."]
        chance = (player_power + player_resilience) / max(1.0, enemy_effective_power + enemy_resilience)
        chance = min(0.95, max(0.05, chance))
        roll = random.random()
        log.append(f"Party power ratio {chance:.2f}, roll {roll:.2f}.")
        success = roll <= chance
        if success:
            log.append("Enemy defeated! Loot distributed among party members.")
            rewards = enemy.rewards or {}
        else:
            log.append("The party was defeated and retreats to recover.")
            rewards = {}
        return BattleResult(success=success, log=log, rewards=rewards)
