"""Cog handling the in-game store."""
from __future__ import annotations

import discord
from discord.ext import commands


class StoreCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _ensure_player(self, author: discord.Member | discord.User):
        return await self.bot.players.ensure_player(author.id)

    @commands.hybrid_group(name="store", invoke_without_command=True, description="Browse and buy store items.")
    async def store_group(self, ctx: commands.Context) -> None:
        await ctx.send("Use `/store list` or `/store buy <item_id>` (also available with `!`).")

    @store_group.command(name="list", with_app_command=True, description="List all items available in the store.")
    async def store_list(self, ctx: commands.Context) -> None:
        items = await self.bot.store.list_items()
        if not items:
            await ctx.send("The store is empty. Check back later!")
            return
        embed = discord.Embed(title="Store", color=discord.Color.purple())
        for item in items:
            modifiers = ", ".join(f"{k.title()} x{v}" for k, v in item.modifiers.items()) or "No modifiers"
            embed.add_field(
                name=f"[{item.id}] {item.name} - {item.price} coins",
                value=f"{item.description}\n{modifiers}",
                inline=False,
            )
        await ctx.send(embed=embed)

    @store_group.command(name="buy", with_app_command=True, description="Purchase an item from the store.")
    async def store_buy(self, ctx: commands.Context, item_id: int) -> None:
        player = await self._ensure_player(ctx.author)
        item = await self.bot.store.get_item(item_id)
        if not item:
            await ctx.send("Item not found.")
            return
        if not await self.bot.players.spend_coins(player, item.price):
            await ctx.send("You cannot afford this item.")
            return
        await self.bot.players.grant_item(player, item.id)
        await ctx.send(f"Purchased {item.name} for {item.price} coins.")
