"""Cog exposing player utilities."""
from __future__ import annotations

import discord
from discord.ext import commands

from ..models import Player


class UsersCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _ensure_player(self, member: discord.Member | discord.User) -> Player:
        return await self.bot.players.ensure_player(member.id)

    @commands.hybrid_command(name="profile", description="Display your RPG profile.")
    async def profile(self, ctx: commands.Context) -> None:
        """Display the calling user's RPG profile."""
        player = await self._ensure_player(ctx.author)
        stats = player.calculate_stats()
        embed = discord.Embed(title=f"{ctx.author.display_name}'s RPG Profile", color=discord.Color.gold())
        embed.add_field(name="Lurkr Level", value=str(player.lurkr_level))
        embed.add_field(name="Coins", value=str(player.coins))
        embed.add_field(
            name="Class",
            value=player.rpg_class.name if player.rpg_class else "Unassigned",
        )
        embed.add_field(
            name="Stats",
            value="\n".join(
                f"{key.replace('_', ' ').title()}: {value:.1f}" for key, value in stats.items()
            ),
            inline=False,
        )
        if player.skills:
            embed.add_field(
                name="Skills",
                value="\n".join(
                    (
                        f"{skill.name} [{skill.grade}] - {skill.skill_type.title()} "
                        f"({skill.cost} {skill.resource.title()}) | Damage: {skill.damage_multiplier * 100:.0f}% {skill.scaling_stat.title()}"
                    )
                    for skill in player.skills
                ),
                inline=False,
            )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="sync", description="Sync your Lurkr level with the game data.")
    async def sync(self, ctx: commands.Context) -> None:
        """Force refresh of Lurkr level."""
        player = await self._ensure_player(ctx.author)
        before = player.lurkr_level
        await self.bot.players.sync_lurkr_level(player)
        if before == player.lurkr_level:
            await ctx.send("Your level is already up to date with Lurkr.")
        else:
            await ctx.send(f"Synced your Lurkr level to {player.lurkr_level}.")

    @commands.hybrid_group(name="class", invoke_without_command=True, description="Manage your RPG class.")
    async def class_group(self, ctx: commands.Context) -> None:
        await ctx.send("Use `/class choose <class_id>` or `!class choose <class_id>` to pick a class.")

    @class_group.command(name="list", with_app_command=True, description="List all available RPG classes.")
    async def list_classes(self, ctx: commands.Context) -> None:
        rows = await self.bot.db.fetch_all("SELECT * FROM classes")
        if not rows:
            await ctx.send("No classes available yet. Ask an admin to create some!")
            return
        embed = discord.Embed(title="Available Classes", color=discord.Color.green())
        for row in rows:
            embed.add_field(
                name=f"[{row['id']}] {row['name']}",
                value=(
                    f"{row.get('description', '')}\n"
                    f"CON x{row['constitution_multiplier']} | AGI x{row['agility_multiplier']} | "
                    f"DEF x{row['defense_multiplier']} | END x{row['endurance_multiplier']} | "
                    f"DNT x{row['dantian_multiplier']} | STR x{row.get('strength_multiplier', 1.0)} | "
                    f"SPR x{row.get('spirit_multiplier', 1.0)}"
                ),
                inline=False,
            )
        await ctx.send(embed=embed)

    @class_group.command(name="choose", with_app_command=True, description="Choose an RPG class by its ID.")
    async def choose_class(self, ctx: commands.Context, class_id: int) -> None:
        player = await self._ensure_player(ctx.author)
        class_row = await self.bot.db.fetch_one("SELECT * FROM classes WHERE id = ?", class_id)
        if not class_row:
            await ctx.send("Class not found.")
            return
        await self.bot.players.assign_class(player, class_id)
        await ctx.send(f"You are now a {class_row['name']}!")

    @commands.hybrid_command(name="commands", description="List all available bot commands.")
    async def list_commands(self, ctx: commands.Context) -> None:
        """Display all available commands grouped by cog."""
        command_entries = {}
        seen_commands = set()
        for command in sorted(self.bot.walk_commands(), key=lambda cmd: cmd.qualified_name):
            if command.hidden or not command.enabled:
                continue
            if command.qualified_name in seen_commands:
                continue
            seen_commands.add(command.qualified_name)
            signature = command.qualified_name
            if command.signature:
                signature = f"{signature} {command.signature}"
            description = command.description or command.help or "No description provided."
            cog_name = command.cog_name or "General"
            command_entries.setdefault(cog_name, []).append(f"`{signature}` - {description}")

        if not command_entries:
            await ctx.send("No commands are currently available.")
            return

        message_chunks = []
        for cog_name in sorted(command_entries):
            entries = "\n".join(command_entries[cog_name])
            chunk = f"**{cog_name} Commands**\n{entries}"
            message_chunks.append(chunk)

        output = "\n\n".join(message_chunks)
        if len(output) <= 2000:
            await ctx.send(output)
            return

        # Fallback to sending in multiple messages if we exceed Discord's limit
        for chunk in message_chunks:
            if len(chunk) <= 2000:
                await ctx.send(chunk)
                continue

            partial = ""
            for line in chunk.split("\n"):
                addition = line if not partial else f"\n{line}"
                if len(partial) + len(addition) > 2000:
                    if partial:
                        await ctx.send(partial)
                    partial = line
                else:
                    partial += addition
            if partial:
                await ctx.send(partial)

    @commands.hybrid_command(name="inventory", description="Show the items in your inventory.")
    async def inventory(self, ctx: commands.Context) -> None:
        player = await self._ensure_player(ctx.author)
        items = await self.bot.players.list_inventory(player)
        if not items:
            await ctx.send("Your inventory is empty.")
            return
        embed = discord.Embed(title="Inventory", color=discord.Color.blurple())
        for item in items:
            mods = ", ".join(f"{k.title()} x{v}" for k, v in item.modifiers.items()) or "No modifiers"
            embed.add_field(
                name=f"[{item.id}] {item.name}",
                value=f"{item.description}\nType: {item.item_type}\nModifiers: {mods}",
                inline=False,
            )
        await ctx.send(embed=embed)
