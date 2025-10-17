"""Domain models for the Discord RPG bot."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class RPGClass:
    id: int
    name: str
    description: str
    constitution_multiplier: float
    agility_multiplier: float
    defense_multiplier: float
    endurance_multiplier: float
    dantian_multiplier: float
    strength_multiplier: float
    spirit_multiplier: float


@dataclass(slots=True)
class Trait:
    id: int
    name: str
    description: str
    modifiers: dict[str, float]


@dataclass(slots=True)
class Item:
    id: int
    name: str
    description: str
    item_type: str
    price: int
    modifiers: dict[str, float]


@dataclass(slots=True)
class Skill:
    id: int
    name: str
    description: str
    grade: str
    skill_type: str
    cost: int
    damage_multiplier: float

    @property
    def resource(self) -> str:
        kind = self.skill_type.lower()
        if kind == "physical":
            return "stamina"
        if kind == "spiritual":
            return "qi"
        return "energy"

    @property
    def scaling_stat(self) -> str:
        kind = self.skill_type.lower()
        if kind == "physical":
            return "strength"
        if kind == "spiritual":
            return "spirit"
        return "power"


@dataclass(slots=True)
class Quest:
    id: int
    name: str
    description: str
    required_level: int
    rewards: dict[str, Any]


@dataclass(slots=True)
class Enemy:
    id: int
    name: str
    description: str
    level: int
    stats: dict[str, Any]
    rewards: dict[str, Any]
    is_boss: bool = False


@dataclass(slots=True)
class Player:
    id: int
    discord_id: int
    lurkr_level: int
    coins: int
    experience: int
    rpg_class: RPGClass | None = None
    traits: list[Trait] = field(default_factory=list)
    items: list[Item] = field(default_factory=list)
    skills: list[Skill] = field(default_factory=list)

    def calculate_stats(self) -> dict[str, float]:
        """Compute derived stats using Lurkr level, class multipliers and traits."""
        base_stat = max(1, self.lurkr_level)
        canonical_map = {
            "constitution": "constitution",
            "hp": "constitution",
            "agility": "agility",
            "defense": "defense",
            "endurance": "endurance",
            "stamina": "endurance",
            "attack": "strength",
            "power": "strength",
            "strength": "strength",
            "dantian_size": "dantian_size",
            "qi": "dantian_size",
            "dantian": "dantian_size",
            "spirit": "spirit",
            "will": "spirit",
            "magic": "spirit",
            "mana": "spirit",
            "intelligence": "spirit",
        }
        multipliers: dict[str, float] = {
            "constitution": 1.0,
            "agility": 1.0,
            "defense": 1.0,
            "endurance": 1.0,
            "dantian_size": 1.0,
            "strength": 1.0,
            "spirit": 1.0,
        }

        def apply_multiplier(key: str, value: float) -> None:
            canonical = canonical_map.get(key, key)
            multipliers[canonical] = multipliers.get(canonical, 1.0) * value

        if self.rpg_class:
            apply_multiplier("constitution", self.rpg_class.constitution_multiplier)
            apply_multiplier("agility", self.rpg_class.agility_multiplier)
            apply_multiplier("defense", self.rpg_class.defense_multiplier)
            apply_multiplier("endurance", self.rpg_class.endurance_multiplier)
            apply_multiplier("dantian_size", self.rpg_class.dantian_multiplier)
            apply_multiplier("strength", self.rpg_class.strength_multiplier)
            apply_multiplier("spirit", self.rpg_class.spirit_multiplier)

        for trait in self.traits:
            for key, value in trait.modifiers.items():
                apply_multiplier(key, value)
        for item in self.items:
            for key, value in item.modifiers.items():
                apply_multiplier(key, value)

        ordered_stats = {
            key: base_stat * multipliers.get(key, 1.0)
            for key in (
                "constitution",
                "agility",
                "defense",
                "endurance",
                "dantian_size",
                "strength",
                "spirit",
            )
        }
        for key, mult in multipliers.items():
            if key not in ordered_stats:
                ordered_stats[key] = base_stat * mult
        return ordered_stats
