"""Cog for managing player parties."""
from __future__ import annotations

import discord
from discord.ext import commands


class PartyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def _require_player(self, member: discord.Member | discord.User):
        return await self.bot.players.ensure_player(member.id)

    @commands.hybrid_group(name="party", invoke_without_command=True, description="Manage your adventuring party.")
    async def party_group(self, ctx: commands.Context) -> None:
        await ctx.send("Use `/party create`, `/party join`, or `/party leave` (commands also available with `!`).")

    @party_group.command(name="create", with_app_command=True, description="Create a new party with the given name.")
    async def create_party(self, ctx: commands.Context, *, name: str) -> None:
        player = await self._require_player(ctx.author)
        record = await self.bot.db.fetch_one(
            "SELECT party_id FROM party_members WHERE user_id = ?",
            player.id,
        )
        if record:
            await ctx.send("You are already in a party.")
            return
        party_id = await self.bot.parties.create_party(player.id, name)
        await ctx.send(f"Created party `{name}` with ID {party_id}.")

    @party_group.command(name="join", with_app_command=True, description="Join a party by its ID.")
    async def join_party(self, ctx: commands.Context, party_id: int) -> None:
        player = await self._require_player(ctx.author)
        if not await self.bot.db.fetch_one("SELECT id FROM parties WHERE id = ?", party_id):
            await ctx.send("Party not found.")
            return
        await self.bot.parties.join_party(party_id, player.id)
        await ctx.send(f"Joined party {party_id}.")

    @party_group.command(name="leave", with_app_command=True, description="Leave your current party.")
    async def leave_party(self, ctx: commands.Context) -> None:
        player = await self._require_player(ctx.author)
        membership = await self.bot.db.fetch_one(
            "SELECT party_id FROM party_members WHERE user_id = ?",
            player.id,
        )
        if not membership:
            await ctx.send("You are not in a party.")
            return
        party_id = membership["party_id"]
        await self.bot.parties.leave_party(party_id, player.id)
        remaining = await self.bot.parties.list_members(party_id)
        if not remaining:
            await self.bot.parties.disband_party(party_id)
            await ctx.send("You left the party. It has been disbanded because it became empty.")
        else:
            await ctx.send("You left the party.")

    @party_group.command(name="members", with_app_command=True, description="List members of a party by ID.")
    async def members(self, ctx: commands.Context, party_id: int) -> None:
        rows = await self.bot.db.fetch_all(
            """
            SELECT u.discord_id FROM party_members pm
            JOIN users u ON u.id = pm.user_id
            WHERE pm.party_id = ?
            """,
            party_id,
        )
        if not rows:
            await ctx.send("Party not found or empty.")
            return
        mentions = []
        for row in rows:
            member = ctx.guild.get_member(row["discord_id"]) if ctx.guild else None
            mentions.append(member.mention if member else f"<@{row['discord_id']}>")
        await ctx.send(f"Party {party_id} members: {', '.join(mentions)}")
