Dao RPG Discord Bot
===================

Dao RPG is a Discord bot that layers a full party-based RPG on top of Lurkr's leveling data. Player growth, combat, and quest rewards all lean on Lurkr profiles while introducing rich stats, items, and narrative hooks for your server.

Key Systems
-----------
- **Lurkr level sync**: Pull player levels from Lurkr so character stats track their community activity.
- **Expanded attributes**: Constitution, agility, defense, endurance, dantian size, strength, and spirit govern survivability, stamina, qi, and damage scaling.
- **Classes and traits**: Combine class multipliers and special traits to shape unique stat profiles and skill access.
- **Skills and resources**: Physical and spiritual skills consume stamina or qi and scale off strength or spirit for impactful combat decisions.
- **Parties and co-op**: Form parties to tackle quests, enemies, and bosses together while sharing the spoils.
- **Loot and store**: Equip items, earn currency, and spend coins in the store for gear upgrades and consumables.
- **Admin tooling**: Create and manage items, quests, enemies, bosses, skills, currencies, classes, and special traits directly from Discord.

Project Layout
--------------
- `bot/` – Bot package with configuration loading, database access, gameplay models, and Discord cogs.
- `requirements.txt` – Python dependencies required to run the bot.

Getting Started
---------------
1. Install Python 3.10 or newer.
2. Create and activate a virtual environment.
3. Install dependencies with `pip install -r requirements.txt`.
4. Copy `.env.example` to `.env` and fill in your credentials **or** export the variables manually.
5. Ensure `DISCORD_TOKEN` is set (via `.env` or your shell). Optionally set `DATABASE_PATH`, `LURKR_API_BASE_URL`, and `LURKR_API_TOKEN` for custom storage or Lurkr integration.
6. Launch the bot with `python -m bot.main`.

Content Management
------------------
Game content is persisted in SQLite. Use the Discord admin commands to seed classes, items, quests, enemies, bosses, skills, currencies, and traits. Admin commands include safeguards and validation to keep data consistent.

Testing
-------
Run `python -m compileall bot` or extend with your preferred tooling such as pytest or mypy depending on your workflow.

Support
-------
Open issues or contributions through pull requests to collaborate on new features, balance tweaks, and documentation improvements.
