"""Quest management commands."""
from __future__ import annotations

import discord
from discord.ext import commands


class QuestCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _ensure_player(self, author: discord.Member | discord.User):
        return await self.bot.players.ensure_player(author.id)

    @commands.hybrid_group(name="quest", invoke_without_command=True, description="View and manage quests.")
    async def quest_group(self, ctx: commands.Context) -> None:
        await ctx.send("Use `/quest list`, `/quest accept <id>`, or `/quest complete <id>` (commands also available with `!`).")

    @quest_group.command(name="list", with_app_command=True, description="List quests you can accept.")
    async def quest_list(self, ctx: commands.Context) -> None:
        player = await self._ensure_player(ctx.author)
        quests = await self.bot.quests.list_available(player.lurkr_level)
        if not quests:
            await ctx.send("No quests available for your level yet.")
            return
        embed = discord.Embed(title="Available Quests", color=discord.Color.orange())
        for quest in quests:
            embed.add_field(
                name=f"[{quest.id}] {quest.name}",
                value=f"Lvl {quest.required_level}+\n{quest.description}",
                inline=False,
            )
        await ctx.send(embed=embed)

    @quest_group.command(name="accept", with_app_command=True, description="Accept a quest by its ID.")
    async def quest_accept(self, ctx: commands.Context, quest_id: int) -> None:
        player = await self._ensure_player(ctx.author)
        quest = await self.bot.db.fetch_one("SELECT * FROM quests WHERE id = ?", quest_id)
        if not quest:
            await ctx.send("Quest not found.")
            return
        if player.lurkr_level < quest["required_level"]:
            await ctx.send("You do not meet the level requirement for this quest.")
            return
        await self.bot.quests.assign(player.id, quest_id)
        await ctx.send(f"Accepted quest {quest['name']}.")

    @quest_group.command(name="complete", with_app_command=True, description="Complete a quest you have accepted.")
    async def quest_complete(self, ctx: commands.Context, quest_id: int) -> None:
        player = await self._ensure_player(ctx.author)
        try:
            rewards = await self.bot.quests.complete(player.id, quest_id)
        except ValueError:
            await ctx.send("Quest not found.")
            return
        coins = rewards.get("coins", 0)
        if coins:
            await self.bot.players.add_coins(player, coins)
        items = rewards.get("items", [])
        for item_id in items:
            await self.bot.players.grant_item(player, item_id)
        await ctx.send(
            f"Quest completed! Rewards: {coins} coins" + (f", Items: {items}" if items else "")
        )
