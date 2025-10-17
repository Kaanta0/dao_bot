"""Discord bot setup."""
from __future__ import annotations

import logging

import discord
from discord.ext import commands

from .config import Settings
from .database import Database
from .services.admin import AdminService
from .services.combat import CombatService
from .services.lurkr import LurkrClient
from .services.parties import PartyService
from .services.players import PlayerService
from .services.quests import QuestService
from .services.store import StoreService

log = logging.getLogger(__name__)


class RPGBot(commands.Bot):
    def __init__(self, settings: Settings, intents: discord.Intents | None = None) -> None:
        intents = intents or discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)
        self.settings = settings
        self.db = Database(settings.database_path)
        self.lurkr = LurkrClient(settings.lurkr_api_base_url, settings.lurkr_api_token)
        self.players = PlayerService(self.db, self.lurkr)
        self.parties = PartyService(self.db)
        self.quests = QuestService(self.db)
        self.store = StoreService(self.db)
        self.admin = AdminService(self.db)
        self.combat = CombatService(self.db)

    async def setup_hook(self) -> None:
        await self.db.connect()
        from .cogs import admin as admin_cog
        from .cogs import combat as combat_cog
        from .cogs import parties as parties_cog
        from .cogs import quests as quests_cog
        from .cogs import store as store_cog
        from .cogs import users as users_cog

        await self.add_cog(users_cog.UsersCog(self))
        await self.add_cog(store_cog.StoreCog(self))
        await self.add_cog(parties_cog.PartyCog(self))
        await self.add_cog(quests_cog.QuestCog(self))
        await self.add_cog(admin_cog.AdminCog(self))
        await self.add_cog(combat_cog.CombatCog(self))

    async def close(self) -> None:
        await super().close()
        await self.db.close()


async def run_bot(settings: Settings) -> None:
    logging.basicConfig(level=logging.INFO)
    bot = RPGBot(settings)
    try:
        await bot.start(settings.discord_token)
    finally:
        await bot.close()
