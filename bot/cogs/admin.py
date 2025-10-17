"""Administrative commands for managing RPG content."""
from __future__ import annotations

import json

from discord import app_commands
from discord.ext import commands


class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _parse_modifiers(self, modifiers: str | None) -> dict[str, float]:
        if not modifiers:
            return {}
        try:
            return json.loads(modifiers)
        except json.JSONDecodeError as exc:  # noqa: PERF203
            raise commands.BadArgument("Invalid JSON for modifiers.") from exc

    @commands.hybrid_group(
        name="admin",
        invoke_without_command=True,
        description="Administrative commands for managing RPG content.",
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def admin_group(self, ctx: commands.Context) -> None:
        await ctx.send(
            "Available subcommands: class, skill, trait, item, enemy, quest, currency."
            " Use them via `/admin ...` or `!admin ...`."
        )

    @admin_group.group(
        name="class",
        invoke_without_command=True,
        with_app_command=True,
        description="Create and configure RPG classes.",
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def admin_class(self, ctx: commands.Context) -> None:
        await ctx.send(
            "Use `/admin class create <name> <constitution> <agility> <defense> <endurance> <dantian_size> <strength> <spirit> [description...]`."
        )

    @admin_class.command(
        name="create",
        with_app_command=True,
        description="Create a new RPG class with stat multipliers.",
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def class_create(
        self,
        ctx: commands.Context,
        name: str,
        constitution: float,
        agility: float,
        defense: float,
        endurance: float,
        dantian_size: float,
        strength: float,
        spirit: float,
        *,
        description: str = "",
    ) -> None:
        class_id = await self.bot.admin.create_class(
            name,
            description,
            constitution,
            agility,
            defense,
            endurance,
            dantian_size,
            strength,
            spirit,
        )
        await ctx.send(f"Created class {name} with id {class_id}.")

    @admin_group.group(
        name="skill",
        invoke_without_command=True,
        with_app_command=True,
        description="Manage skills available to classes.",
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def admin_skill(self, ctx: commands.Context) -> None:
        await ctx.send(
            "Use `/admin skill create <name> <grade> <type> <cost> <damage_multiplier> [description...]`"
            " (damage multiplier example: 1.5 for 150%)."
        )

    @admin_skill.command(
        name="create",
        with_app_command=True,
        description="Create a new skill that classes can use.",
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def skill_create(
        self,
        ctx: commands.Context,
        name: str,
        grade: str,
        skill_type: str,
        cost: int,
        damage_multiplier: float,
        *,
        description: str = "",
    ) -> None:
        try:
            normalized_damage = damage_multiplier / 100 if damage_multiplier > 10 else damage_multiplier
            skill_id = await self.bot.admin.create_skill(
                name,
                description,
                grade,
                skill_type,
                cost,
                normalized_damage,
            )
        except ValueError as exc:
            await ctx.send(str(exc))
            return
        await ctx.send(f"Created skill {name} with id {skill_id}.")

    @admin_skill.command(
        name="assign",
        with_app_command=True,
        description="Assign a skill to a class.",
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def skill_assign(self, ctx: commands.Context, class_id: int, skill_id: int) -> None:
        await self.bot.admin.assign_skill_to_class(class_id, skill_id)
        await ctx.send(f"Assigned skill {skill_id} to class {class_id}.")

    @admin_group.group(
        name="trait",
        invoke_without_command=True,
        with_app_command=True,
        description="Manage traits that modify player stats.",
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def admin_trait(self, ctx: commands.Context) -> None:
        await ctx.send("Use `/admin trait create <name> <json_modifiers> [description...]`.")

    @admin_trait.command(
        name="create",
        with_app_command=True,
        description="Create a new trait with stat modifiers.",
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def trait_create(self, ctx: commands.Context, name: str, modifiers: str, *, description: str = "") -> None:
        mod_data = await self._parse_modifiers(modifiers)
        trait_id = await self.bot.admin.create_trait(name, description, mod_data)
        await ctx.send(f"Created trait {name} with id {trait_id}.")

    @admin_group.group(
        name="item",
        invoke_without_command=True,
        with_app_command=True,
        description="Manage items available in the world and store.",
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def admin_item(self, ctx: commands.Context) -> None:
        await ctx.send("Use `/admin item create <name> <type> <price> <json_modifiers> [description...]`.")

    @admin_item.command(
        name="create",
        with_app_command=True,
        description="Create a new item.",
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def item_create(
        self,
        ctx: commands.Context,
        name: str,
        item_type: str,
        price: int,
        modifiers: str,
        *,
        description: str = "",
    ) -> None:
        mod_data = await self._parse_modifiers(modifiers)
        item_id = await self.bot.admin.create_item(name, description, item_type, price, mod_data)
        await ctx.send(f"Created item {name} with id {item_id}.")

    @admin_group.group(
        name="enemy",
        invoke_without_command=True,
        with_app_command=True,
        description="Create enemies and bosses.",
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def admin_enemy(self, ctx: commands.Context) -> None:
        await ctx.send("Use `/admin enemy create <name> <level> <json_stats> <json_rewards> [description...]`.")

    @admin_enemy.command(
        name="create",
        with_app_command=True,
        description="Create a standard enemy.",
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def enemy_create(
        self,
        ctx: commands.Context,
        name: str,
        level: int,
        stats: str,
        rewards: str,
        *,
        description: str = "",
    ) -> None:
        stats_data = await self._parse_modifiers(stats)
        rewards_data = await self._parse_modifiers(rewards)
        enemy_id = await self.bot.admin.create_enemy(name, description, level, stats_data, rewards_data, is_boss=False)
        await ctx.send(f"Created enemy {name} with id {enemy_id}.")

    @admin_enemy.command(
        name="boss",
        with_app_command=True,
        description="Create a boss enemy.",
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def enemy_boss(
        self,
        ctx: commands.Context,
        name: str,
        level: int,
        stats: str,
        rewards: str,
        *,
        description: str = "",
    ) -> None:
        stats_data = await self._parse_modifiers(stats)
        rewards_data = await self._parse_modifiers(rewards)
        enemy_id = await self.bot.admin.create_enemy(name, description, level, stats_data, rewards_data, is_boss=True)
        await ctx.send(f"Created boss {name} with id {enemy_id}.")

    @admin_group.group(
        name="quest",
        invoke_without_command=True,
        with_app_command=True,
        description="Create quests for players.",
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def admin_quest(self, ctx: commands.Context) -> None:
        await ctx.send("Use `/admin quest create <name> <level> <json_rewards> [description...]`.")

    @admin_quest.command(
        name="create",
        with_app_command=True,
        description="Create a new quest.",
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def quest_create(
        self,
        ctx: commands.Context,
        name: str,
        level: int,
        rewards: str,
        *,
        description: str = "",
    ) -> None:
        reward_data = await self._parse_modifiers(rewards)
        quest_id = await self.bot.admin.create_quest(name, description, level, reward_data)
        await ctx.send(f"Created quest {name} with id {quest_id}.")

    @admin_group.group(
        name="currency",
        invoke_without_command=True,
        with_app_command=True,
        description="Create currencies for rewards or stores.",
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def admin_currency(self, ctx: commands.Context) -> None:
        await ctx.send("Use `/admin currency create <name> [is_premium] [description...]`.")

    @admin_currency.command(
        name="create",
        with_app_command=True,
        description="Create a new currency.",
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def currency_create(
        self,
        ctx: commands.Context,
        name: str,
        is_premium: bool = False,
        *,
        description: str = "",
    ) -> None:
        currency_id = await self.bot.admin.create_currency(name, description, is_premium)
        await ctx.send(f"Created currency {name} with id {currency_id}.")
