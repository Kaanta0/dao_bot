"""Configuration handling for the RPG bot."""
from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(slots=True)
class Settings:
    """Runtime configuration loaded from environment variables."""

    discord_token: str
    database_path: str = "rpg.db"
    lurkr_api_base_url: str | None = None
    lurkr_api_token: str | None = None

    @classmethod
    def load(cls) -> "Settings":
        token = os.getenv("DISCORD_TOKEN")
        if not token:
            raise RuntimeError(
                "Missing DISCORD_TOKEN environment variable required to start the bot."
            )
        return cls(
            discord_token=token,
            database_path=os.getenv("DATABASE_PATH", "rpg.db"),
            lurkr_api_base_url=os.getenv("LURKR_API_BASE_URL"),
            lurkr_api_token=os.getenv("LURKR_API_TOKEN"),
        )
