"""Combat commands for fighting enemies and bosses."""
from __future__ import annotations

import discord
from discord.ext import commands


class CombatCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _collect_party_players(self, leader: discord.Member) -> list:
        player = await self.bot.players.ensure_player(leader.id)
        membership = await self.bot.db.fetch_one(
            "SELECT party_id FROM party_members WHERE user_id = ?",
            player.id,
        )
        players = [player]
        if membership:
            party_id = membership["party_id"]
            member_rows = await self.bot.db.fetch_all(
                "SELECT u.discord_id FROM party_members pm JOIN users u ON u.id = pm.user_id WHERE pm.party_id = ?",
                party_id,
            )
            for row in member_rows:
                if row["discord_id"] == leader.id:
                    continue
                players.append(await self.bot.players.ensure_player(row["discord_id"]))
        return players

    @commands.command(name="battle")
    async def battle(self, ctx: commands.Context, enemy_id: int) -> None:
        players = await self._collect_party_players(ctx.author)
        enemy = await self.bot.combat.fetch_enemy(enemy_id)
        if not enemy:
            await ctx.send("Enemy not found. Ask an admin to create it first.")
            return
        result = await self.bot.combat.battle(players, enemy)
        for line in result.log:
            await ctx.send(line)
        if result.success and result.rewards:
            coins = result.rewards.get("coins", 0)
            items = result.rewards.get("items", [])
            share = coins // len(players) if coins else 0
            for player in players:
                if share:
                    await self.bot.players.add_coins(player, share)
                for item_id in items:
                    await self.bot.players.grant_item(player, item_id)
            summary = f"Each party member receives {share} coins" if share else "Rewards distributed"
            if items:
                summary += f" and items {items}"
            await ctx.send(summary)
