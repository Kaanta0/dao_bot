"""Client for interacting with the Lurkr leveling API."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp


log = logging.getLogger(__name__)


class LurkrClient:
    """Minimal HTTP client for retrieving player level data from Lurkr."""

    def __init__(self, base_url: str | None, api_token: str | None) -> None:
        self.base_url = base_url.rstrip("/") if base_url else None
        self.api_token = api_token

    async def fetch_level(self, discord_id: int) -> int | None:
        """Return the current Lurkr level for the given Discord member."""
        if not self.base_url or not self.api_token:
            log.warning("Lurkr API configuration missing; skipping level lookup for %s", discord_id)
            return None
        url = f"{self.base_url}/levels/{discord_id}"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        async with aiohttp.ClientSession(headers=headers) as session:
            try:
                async with session.get(url, timeout=10) as response:
                    response.raise_for_status()
                    payload: dict[str, Any] = await response.json()
            except Exception as exc:  # noqa: BLE001
                log.exception("Failed fetching Lurkr level for %s: %s", discord_id, exc)
                return None
        level = payload.get("level")
        if not isinstance(level, int):
            log.error("Unexpected Lurkr response for %s: %s", discord_id, payload)
            return None
        return level
