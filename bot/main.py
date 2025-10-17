"""Entry point for running the Discord RPG bot."""
from __future__ import annotations

import asyncio

from .bot import run_bot
from .config import Settings


def main() -> None:
    settings = Settings.load()
    asyncio.run(run_bot(settings))


if __name__ == "__main__":
    main()
