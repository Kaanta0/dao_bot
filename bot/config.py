"""Configuration handling for the RPG bot."""
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


def _load_env_file(path: str = ".env") -> None:
    """Populate ``os.environ`` with key/value pairs from a ``.env`` file.

    The helper mirrors the tiny subset of python-dotenv we need so that users
    can provide secrets through a local file instead of exporting environment
    variables manually. Only the first ``key=value`` pair per line is
    considered, and existing environment variables always take precedence.
    """

    env_path = Path(path)
    if not env_path.is_file():
        return

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue

        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass(slots=True)
class Settings:
    """Runtime configuration loaded from environment variables."""

    discord_token: str
    database_path: str = "rpg.db"
    lurkr_api_base_url: str | None = None
    lurkr_api_token: str | None = None

    @classmethod
    def load(cls) -> "Settings":
        _load_env_file()

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
