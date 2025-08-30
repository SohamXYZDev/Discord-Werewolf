Discord Werewolf (Fork) - Updated

This repository is a modernized Discord Werewolf/Mafia bot. This README documents recent feature updates, commands, configuration keys, and quick setup instructions.

Highlights

- Vote-to-start: players can use `!vote startgame` to vote to begin the game; a majority starts it.
- Immediate transitions: the game progresses immediately to day once night actions are all submitted, and to night when a lynch occurs.
- Werewolf DM chat: werewolf coordination and prompts are sent via DMs; there is no public wolfchat.
- Phase pings: the bot pings living players at the start of each day and night to prompt actions.
- Totems: Shaman-style totems exist and are canonicalized; use `!totem <name>` for info.
- Log relay: terminal logs can be relayed to a configured Discord channel.

Commands (summary)

- Basic

  - `!help [command]` — show command help and notable features
  - `!info` — bot information
  - `!ping` — bot responsiveness
  - `!version` — bot version
  - `!status` — current game and bot status

- Lobby / Game

  - `!join` / `!leave` — join or leave the lobby
  - `!players` — list players
  - `!vote <player>` — cast lynch vote during day
  - `!vote startgame` — startgame vote (majority to begin)
  - `!abstain` — abstain from lynch voting
  - `!give <player> <totem>` — give a totem to a player (role dependent)
  - `!totem <name>` — show totem details
    Discord Werewolf - Full Reference

  This document is a full reference for the Discord Werewolf bot in this repository. It lists commands, roles, totems, configuration, and run instructions.

  Table of contents

  - Overview
  - Quick start
  - Configuration
  - Commands (complete)
    - Basic
    - Lobby & Game
    - Night (PM-only) actions
    - Role / Action commands
    - Admin / Owner commands
  - Roles (names)
  - Totems (canonical list)
  - Totem givers (who can give which totems)
  - Notes on gameplay behavior
  - Troubleshooting & testing

  Overview
  This bot runs a Werewolf/Mafia style game in Discord. It supports many roles, totems (shaman items), configurable gamemodes, DM-based night actions, vote-to-start, immediate phase transitions, and optional log relays to Discord. Werewolf messaging is private via DMs.

  Quick start

  1. Create virtualenv and install requirements:

  ```bash
  python -m venv .venv
  source .venv/bin/activate  # Windows: .venv\Scripts\activate
  pip install -r requirements.txt
  ```

  2. Copy `settings.py.example` -> `settings.py` and provide values for `TOKEN`, `game_channel_id`, and (optionally) `logging_channel_id`.

  3. Run the bot:

  ```bash
  python bot.py
  ```

  Configuration (keys used by the bot)

  - `prefix` - command prefix (default `!`)
  - `TOKEN` - Discord bot token (in settings)
  - `game_channel` or `game_channel_id` - where game messages will be sent
  - `logging_channel_id` or `debug_channel` - optional channel id where terminal logs will be relayed
  - `admin_role_name` - role used for admin commands

  Commands (complete)

  Basic commands

  - `!help [command]` - show help and lists (this command)
  - `!info` - bot information and basic usage
  - `!ping` - latency check
  - `!version` - bot version info
  - `!status` - current bot and game status
  - `!uptime` - bot uptime
  - `!list` - list players or commands
  - `!admins` - list online admins

  Lobby & Game commands

  - `!join` / `!leave` - join/leave the lobby
  - `!players` - show current players
  - `!start` - start the game (admin or startgame majority)
  - `!vote <player>` - cast lynch vote during day
  - `!vote startgame` - vote to start the game; majority starts it
  - `!abstain` - abstain from voting
  - `!retract` - retract your vote
  - `!votes` / `!votecount` - show current votes
  - `!give <player> <totem>` - give a totem (Shaman / Wolf Shaman)
  - `!totem <name>` - show totem info
  - `!role <role>` - show role info
  - `!players` / `!list` - players and lobby lists
  - `!stop` - stop/cancel the current game (admin)
  - `!kick`, `!replace`, `!forcevote`, `!roles` - moderator commands

  Night (PM-only) actions (players should DM these to the bot)

  Players should send these commands to the bot via DM during the night phase. The bot's help command now dynamically lists the authoritative set of PM-only/night commands available for your current game and role.

  - `kill <player>` — werewolf/team kill (PM-only)
  - `see <player>` — Seer / Seer-like investigator (PM-only)
  - `detect <player>` — Detective / Detective-like investigator (PM-only)
  - `protect <player>` or `guard <player>` — Guardian Angel / Bodyguard protections (PM-only)
  - `visit <player>` — Visit-type actions (Harlot, Succubus, etc.) (PM-only)
  - `pass` — Skip your night action (PM-only)
  - `myrole` — Check your role and night-action availability (PM-only)

  Note: Some commands have aliases or appear in multiple command modules (for example `protect` vs `guard`, or `kill` in both `night_actions.py` and `game.py`). Use `!help <command>` while in-game (or DM the bot) to see which PM-only commands are available to you based on your assigned role.

  Role / Action commands (examples)

  - `give` — Shaman/Wolf Shaman to give totems
  - `observe` — Werecrow / Sorcerer observation
  - `id` — Detective daytime identification
  - `bless` / `consecrate` — Priest abilities
  - `hex` / `curse` — Hag / Warlock abilities
  - `charm` — Piper charm players
  - `choose` — Matchmaker choose lovers
  - `clone` — Clone another player's role
  - `side` — Turncoat side selection
  - `target` / `shoot` — Shooter / Assassin commands
  - Other role-specific commands exist; use `!help <command>` for details.

  Admin / Owner commands (requires admin/owner permission)

  - `shutdown`, `eval`, `exec`, `reload` — owner-only utilities
  - `setstatus`, `stasis`, `logs`, `cleanup` — admin utilities
  - `fstart`, `fstop`, `fjoin`, `fleave`, `fday`, `fnight` — force operations for testing
  - `revealroles`, `frevive` — reveal or revive players (admin)

  Roles (names)
  The bot includes many roles. Use `!role <name>` for details. Examples of role names supported:

  - Village: Villager, Seer, Oracle, Detective, Guardian Angel, Bodyguard, Hunter, Priest, Shaman, Harlot, Mystic, Matchmaker, Augur, Village Drunk, Mad Scientist, Time Lord
  - Wolves: Werewolf, Werecrow, Wolf Cub, Werekitten, Wolf Shaman, Traitor, Sorcerer, Minion, Hag, Warlock, Wolf Mystic, Doomsayer, Cultist
  - Neutrals: Jester, Fool, Serial Killer, Piper, Succubus, Executioner, Crazed Shaman, Monster, Amnesiac, Vengeful Ghost, Clone, Lycan, Turncoat, Hot Potato

  Totems (canonical list)

  - death — Death Totem: recipient dies at end of night
  - protection — Protection Totem: protects one night
  - revealing — Revealing Totem: prevents lynch death and reveals role
  - influence — Influence Totem: vote counts double
  - impatience — Impatience Totem: holder's vote may end the day early
  - pacifism — Pacifism Totem: holder forced to abstain
  - cursed — Cursed Totem: appears wolf to investigations
  - lycanthropy — Lycanthropy Totem: converts if targeted by wolves
  - retribution — Retribution Totem: kills a wolf that killed the holder
  - blinding — Blinding Totem: injures the holder; cannot vote
  - deceit — Deceit Totem: investigations return misleading info
  - misdirection — Misdirection Totem: night targets may be redirected
  - luck — Luck Totem: random redirect chance
  - silence — Silence Totem: disables abilities for day/night
  - pestilence — Pestilence Totem: kills wolves' ability to kill following night
  - desperation — Desperation Totem: holder may die if they fail to vote

  Totem givers

  - Shaman can give: death, protection, revealing, influence, impatience, pacifism, silence, desperation
  - Wolf Shaman can give: protection, cursed, lycanthropy, retribution, blinding, deceit, misdirection, luck

  Notes on gameplay behavior

  - Vote-to-start: use `!vote startgame` to cast a start vote. When a majority of the lobby votes to start, the game begins.
  - Immediate transitions:
    - Night -> Day: If all players with night actions submit their actions, the night ends immediately and day begins.
    - Day -> Night: If a lynch occurs during a day resolution, the bot proceeds to night immediately.
  - Werewolf communication: wolves receive DM prompts listing teammates and suggested targets. There is no persistent wolf chat in a server channel.
  - Totem interactions: the game logic uses canonical totem keys; totems may be single-use or persistent based on their semantics (see totem descriptions). Pestilence is persisted via `session.wolves_sick` and prevents wolves from killing the following night when triggered.
  - Double-messaging mitigation: all public sends go through helper wrappers that dedupe messages within a short window to avoid duplicates.
  - Log relay: enable `logging_channel_id` in settings to have the bot forward log messages to a Discord channel.

  Troubleshooting & testing

  - Ensure bot can DM users and has send-message permission in the configured game channel.
  - To test log relay, provide `logging_channel_id` in settings and restart the bot.
  - If night actions or votes aren't triggering immediate transitions, ensure the `GameManager` is attached to `session.game_manager` and that players submit actions via PM.

  If you want, I can:

  - Add per-command usage examples in README (detailed signatures)
  - Generate a small unit test harness to simulate a short game and exercise vote-to-start, immediate transitions, and totem effects
  - Create examples for popular gamemodes and recommended role lists

  ***

  Updated: August 30, 2025
