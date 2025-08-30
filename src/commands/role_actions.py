"""
Role-specific action commands for the Discord Werewolf Bot
"""

import discord
from discord.ext import commands
import logging
from src.commands.base import command, PermissionLevel
from src.utils.helpers import create_embed, create_error_embed, create_success_embed
from src.game.state import get_session
from src.core import get_config

try:
    config = get_config()
except:
    # Fallback config for testing
    class DummyConfig:
        prefix = "!"
        admin_role_name = "Admin"
    config = DummyConfig()

logger = logging.getLogger(__name__)

@command("give", PermissionLevel.PLAYING, "Give a totem to a player", aliases=["gift"])
async def give_command(ctx: commands.Context, target: str = None, totem: str = None):
    """Shaman/Wolf Shaman totem distribution"""
    session = get_session()
    
    if not session.playing:
        embed = create_error_embed("No Game", "No game is currently running!")
        await ctx.send(embed=embed)
        return
    
    player = session.get_player_by_id(ctx.author.id)
    if not player:
        embed = create_error_embed("Not Playing", "You are not in the current game!")
        await ctx.send(embed=embed)
        return
    
    if not player.role or player.role.name.lower() not in ["shaman", "wolf shaman"]:
        embed = create_error_embed("Invalid Role", "Only Shamans and Wolf Shamans can give totems!")
        await ctx.send(embed=embed)
        return
    
    if not target or not totem:
        embed = create_error_embed(
            "Missing Parameters", 
            f"Usage: `{config.prefix}give <player> <totem>`\n"
            "Example: `!give John pacifism`"
        )
        await ctx.send(embed=embed)
        return
    
    # Find target player
    target_player = session.get_player_by_nick(target)
    if not target_player:
        embed = create_error_embed("Player Not Found", f"Player '{target}' not found in the game!")
        await ctx.send(embed=embed)
        return
    
    if target_player not in session.get_alive_players():
        embed = create_error_embed("Invalid Target", "You can only give totems to living players!")
        await ctx.send(embed=embed)
        return
    
    # Normalize totem name
    tkey = totem.lower().strip()

    # Assign the totem as a template on the target player (simple representation)
    try:
        if not hasattr(target_player, 'templates'):
            target_player.templates = set()
        target_player.templates.add(tkey)

        # DM the recipient to inform them
        try:
            await ctx.author.send(embed=create_success_embed("🎁 Totem Given", f"You gave **{totem}** to **{target_player.name}**."))
        except Exception:
            # ignore DM failures
            pass

        try:
            await target_player.user.send(embed=create_embed("🔮 You received a Totem", f"You have received the **{totem}** totem. Its effects may be applied during the game."))
        except Exception:
            # ignore DM failures
            pass

        embed = create_success_embed(
            "🎁 Totem Given",
            f"{player.nick} gave the **{totem}** totem to **{target_player.name}**."
        )
        await ctx.send(embed=embed)
        logger.info(f"{player.nick} gave {totem} totem to {target_player.name}")
    except Exception as e:
        logger.exception(f"Failed to give totem: {e}")
        await ctx.send(embed=create_error_embed("Error", "Failed to give totem; please try again."))

@command("observe", PermissionLevel.PLAYING, "Observe a player at night", aliases=["watch"])
async def observe_command(ctx: commands.Context, target: str = None):
    """Werecrow/Sorcerer observation"""
    session = get_session()
    
    if not session.playing:
        embed = create_error_embed("No Game", "No game is currently running!")
        await ctx.send(embed=embed)
        return
    
    player = session.get_player_by_id(ctx.author.id)
    if not player:
        embed = create_error_embed("Not Playing", "You are not in the current game!")
        await ctx.send(embed=embed)
        return
    
    if not player.role or player.role.name.lower() not in ["werecrow", "sorcerer"]:
        embed = create_error_embed("Invalid Role", "Only Werecrows and Sorcerers can observe!")
        await ctx.send(embed=embed)
        return
    
    if session.is_day:
        embed = create_error_embed("Wrong Phase", "You can only observe during the night!")
        await ctx.send(embed=embed)
        return
    
    if not target:
        embed = create_error_embed(
            "Missing Target", 
            f"Usage: `{config.prefix}observe <player>`"
        )
        await ctx.send(embed=embed)
        return
    
    # Find target player
    target_player = session.get_player_by_nick(target)
    if not target_player:
        embed = create_error_embed("Player Not Found", f"Player '{target}' not found in the game!")
        await ctx.send(embed=embed)
        return
    
    if target_player not in session.get_alive_players():
        embed = create_error_embed("Invalid Target", "You can only observe living players!")
        await ctx.send(embed=embed)
        return
    
    if target_player == player:
        embed = create_error_embed("Invalid Target", "You cannot observe yourself!")
        await ctx.send(embed=embed)
        return
    
    # TODO: Implement actual observation logic
    embed = create_success_embed(
        "👁️ Observation Set",
        f"You will observe **{target_player.nick}** tonight."
    )
    await ctx.author.send(embed=embed)
    
    # Confirm in channel
    await ctx.send(f"✅ {player.nick} is observing someone tonight.")
    logger.info(f"{player.nick} is observing {target_player.nick}")

@command("id", PermissionLevel.PLAYING, "Identify a player during the day", aliases=["identify"])
async def id_command(ctx: commands.Context, target: str = None):
    """Detective investigation (daytime)"""
    session = get_session()
    
    if not session.playing:
        embed = create_error_embed("No Game", "No game is currently running!")
        await ctx.send(embed=embed)
        return
    
    player = session.get_player_by_id(ctx.author.id)
    if not player:
        embed = create_error_embed("Not Playing", "You are not in the current game!")
        await ctx.send(embed=embed)
        return
    
    if not player.role or player.role.name.lower() not in ["detective"]:
        embed = create_error_embed("Invalid Role", "Only Detectives can use ID!")
        await ctx.send(embed=embed)
        return
    
    if not session.is_day:
        embed = create_error_embed("Wrong Phase", "You can only ID during the day!")
        await ctx.send(embed=embed)
        return
    
    if not target:
        embed = create_error_embed(
            "Missing Target", 
            f"Usage: `{config.prefix}id <player>`"
        )
        await ctx.send(embed=embed)
        return
    
    # Find target player
    target_player = session.get_player_by_nick(target)
    if not target_player:
        embed = create_error_embed("Player Not Found", f"Player '{target}' not found in the game!")
        await ctx.send(embed=embed)
        return
    
    if target_player not in session.get_alive_players():
        embed = create_error_embed("Invalid Target", "You can only ID living players!")
        await ctx.send(embed=embed)
        return
    
    if target_player == player:
        embed = create_error_embed("Invalid Target", "You cannot ID yourself!")
        await ctx.send(embed=embed)
        return
    
    # TODO: Implement actual ID logic
    embed = create_success_embed(
        "🔍 Investigation Complete",
        f"**{target_player.nick}** appears to be on the **village** side."
    )
    await ctx.author.send(embed=embed)
    
    # Confirm in channel
    await ctx.send(f"✅ {player.nick} investigates someone.")
    logger.info(f"{player.nick} investigated {target_player.nick}")

@command("bless", PermissionLevel.PLAYING, "Bless a player during the day")
async def bless_command(ctx: commands.Context, target: str = None):
    """Priest blessing (daytime)"""
    session = get_session()
    
    if not session.playing:
        embed = create_error_embed("No Game", "No game is currently running!")
        await ctx.send(embed=embed)
        return
    
    player = session.get_player_by_id(ctx.author.id)
    if not player:
        embed = create_error_embed("Not Playing", "You are not in the current game!")
        await ctx.send(embed=embed)
        return
    
    if not player.role or player.role.name.lower() not in ["priest"]:
        embed = create_error_embed("Invalid Role", "Only Priests can bless!")
        await ctx.send(embed=embed)
        return
    
    if not session.is_day:
        embed = create_error_embed("Wrong Phase", "You can only bless during the day!")
        await ctx.send(embed=embed)
        return
    
    if not target:
        embed = create_error_embed(
            "Missing Target", 
            f"Usage: `{config.prefix}bless <player>`"
        )
        await ctx.send(embed=embed)
        return
    
    # Find target player
    target_player = session.get_player_by_nick(target)
    if not target_player:
        embed = create_error_embed("Player Not Found", f"Player '{target}' not found in the game!")
        await ctx.send(embed=embed)
        return
    
    if target_player not in session.get_alive_players():
        embed = create_error_embed("Invalid Target", "You can only bless living players!")
        await ctx.send(embed=embed)
        return
    
    # TODO: Implement actual blessing logic
    embed = create_success_embed(
        "✨ Blessing Cast",
        f"**{target_player.nick}** has been blessed and protected from evil."
    )
    await ctx.send(embed=embed)
    logger.info(f"{player.nick} blessed {target_player.nick}")

@command("consecrate", PermissionLevel.PLAYING, "Consecrate a location during the day")
async def consecrate_command(ctx: commands.Context):
    """Priest consecration (daytime)"""
    session = get_session()
    
    if not session.playing:
        embed = create_error_embed("No Game", "No game is currently running!")
        await ctx.send(embed=embed)
        return
    
    player = session.get_player_by_id(ctx.author.id)
    if not player:
        embed = create_error_embed("Not Playing", "You are not in the current game!")
        await ctx.send(embed=embed)
        return
    
    if not player.role or player.role.name.lower() not in ["priest"]:
        embed = create_error_embed("Invalid Role", "Only Priests can consecrate!")
        await ctx.send(embed=embed)
        return
    
    if not session.is_day:
        embed = create_error_embed("Wrong Phase", "You can only consecrate during the day!")
        await ctx.send(embed=embed)
        return
    
    # TODO: Implement actual consecration logic
    embed = create_success_embed(
        "⛪ Ground Consecrated",
        f"**{player.nick}** has consecrated the ground. Evil spirits are weakened."
    )
    await ctx.send(embed=embed)
    logger.info(f"{player.nick} consecrated the ground")

@command("hex", PermissionLevel.PLAYING, "Hex a player at night")
async def hex_command(ctx: commands.Context, target: str = None):
    """Hag hexing ability"""
    session = get_session()
    
    if not session.playing:
        embed = create_error_embed("No Game", "No game is currently running!")
        await ctx.send(embed=embed)
        return
    
    player = session.get_player_by_id(ctx.author.id)
    if not player:
        embed = create_error_embed("Not Playing", "You are not in the current game!")
        await ctx.send(embed=embed)
        return
    
    if not player.role or player.role.name.lower() not in ["hag"]:
        embed = create_error_embed("Invalid Role", "Only Hags can hex!")
        await ctx.send(embed=embed)
        return
    
    if session.is_day:
        embed = create_error_embed("Wrong Phase", "You can only hex during the night!")
        await ctx.send(embed=embed)
        return
    
    if not target:
        embed = create_error_embed(
            "Missing Target", 
            f"Usage: `{config.prefix}hex <player>`"
        )
        await ctx.send(embed=embed)
        return
    
    # Find target player
    target_player = session.get_player_by_nick(target)
    if not target_player:
        embed = create_error_embed("Player Not Found", f"Player '{target}' not found in the game!")
        await ctx.send(embed=embed)
        return
    
    if target_player not in session.get_alive_players():
        embed = create_error_embed("Invalid Target", "You can only hex living players!")
        await ctx.send(embed=embed)
        return
    
    if target_player == player:
        embed = create_error_embed("Invalid Target", "You cannot hex yourself!")
        await ctx.send(embed=embed)
        return
    
    # TODO: Implement actual hex logic
    embed = create_success_embed(
        "🔮 Hex Cast",
        f"You have hexed **{target_player.nick}**. They will be vulnerable tomorrow."
    )
    await ctx.author.send(embed=embed)
    
    # Confirm in channel
    await ctx.send(f"✅ {player.nick} casts a hex.")
    logger.info(f"{player.nick} hexed {target_player.nick}")

@command("curse", PermissionLevel.PLAYING, "Curse a player")
async def curse_command(ctx: commands.Context, target: str = None):
    """Warlock cursing ability"""
    session = get_session()
    
    if not session.playing:
        embed = create_error_embed("No Game", "No game is currently running!")
        await ctx.send(embed=embed)
        return
    
    player = session.get_player_by_id(ctx.author.id)
    if not player:
        embed = create_error_embed("Not Playing", "You are not in the current game!")
        await ctx.send(embed=embed)
        return
    
    if not player.role or player.role.name.lower() not in ["warlock"]:
        embed = create_error_embed("Invalid Role", "Only Warlocks can curse!")
        await ctx.send(embed=embed)
        return
    
    if not target:
        embed = create_error_embed(
            "Missing Target", 
            f"Usage: `{config.prefix}curse <player>`"
        )
        await ctx.send(embed=embed)
        return
    
    # Find target player
    target_player = session.get_player_by_nick(target)
    if not target_player:
        embed = create_error_embed("Player Not Found", f"Player '{target}' not found in the game!")
        await ctx.send(embed=embed)
        return
    
    if target_player not in session.get_alive_players():
        embed = create_error_embed("Invalid Target", "You can only curse living players!")
        await ctx.send(embed=embed)
        return
    
    if target_player == player:
        embed = create_error_embed("Invalid Target", "You cannot curse yourself!")
        await ctx.send(embed=embed)
        return
    
    # TODO: Implement actual curse logic
    embed = create_success_embed(
        "💀 Curse Placed",
        f"You have cursed **{target_player.nick}**. They will die in 2 days."
    )
    await ctx.author.send(embed=embed)
    
    # Confirm in channel
    await ctx.send(f"✅ {player.nick} places a curse.")
    logger.info(f"{player.nick} cursed {target_player.nick}")

@command("charm", PermissionLevel.PLAYING, "Charm a player", aliases=["pipe"])
async def charm_command(ctx: commands.Context, target: str = None):
    """Piper charming ability"""
    session = get_session()
    
    if not session.playing:
        embed = create_error_embed("No Game", "No game is currently running!")
        await ctx.send(embed=embed)
        return
    
    player = session.get_player_by_id(ctx.author.id)
    if not player:
        embed = create_error_embed("Not Playing", "You are not in the current game!")
        await ctx.send(embed=embed)
        return
    
    if not player.role or player.role.name.lower() not in ["piper"]:
        embed = create_error_embed("Invalid Role", "Only Pipers can charm!")
        await ctx.send(embed=embed)
        return
    
    if session.is_day:
        embed = create_error_embed("Wrong Phase", "You can only charm during the night!")
        await ctx.send(embed=embed)
        return
    
    if not target:
        embed = create_error_embed(
            "Missing Target", 
            f"Usage: `{config.prefix}charm <player>`"
        )
        await ctx.send(embed=embed)
        return
    
    # Find target player
    target_player = session.get_player_by_nick(target)
    if not target_player:
        embed = create_error_embed("Player Not Found", f"Player '{target}' not found in the game!")
        await ctx.send(embed=embed)
        return
    
    if target_player not in session.get_alive_players():
        embed = create_error_embed("Invalid Target", "You can only charm living players!")
        await ctx.send(embed=embed)
        return
    
    if target_player == player:
        embed = create_error_embed("Invalid Target", "You cannot charm yourself!")
        await ctx.send(embed=embed)
        return
    
    # TODO: Implement actual charm logic
    embed = create_success_embed(
        "🎵 Player Charmed",
        f"You have charmed **{target_player.nick}**. They are now under your influence."
    )
    await ctx.author.send(embed=embed)
    
    # Confirm in channel
    await ctx.send(f"✅ {player.nick} plays a haunting melody.")
    logger.info(f"{player.nick} charmed {target_player.nick}")

@command("choose", PermissionLevel.PLAYING, "Choose lovers", aliases=["match"])
async def choose_command(ctx: commands.Context, player1: str = None, player2: str = None):
    """Matchmaker lover selection"""
    session = get_session()
    
    if not session.playing:
        embed = create_error_embed("No Game", "No game is currently running!")
        await ctx.send(embed=embed)
        return
    
    player = session.get_player_by_id(ctx.author.id)
    if not player:
        embed = create_error_embed("Not Playing", "You are not in the current game!")
        await ctx.send(embed=embed)
        return
    
    if not player.role or player.role.name.lower() not in ["matchmaker"]:
        embed = create_error_embed("Invalid Role", "Only Matchmakers can choose lovers!")
        await ctx.send(embed=embed)
        return
    
    if not player1 or not player2:
        embed = create_error_embed(
            "Missing Parameters", 
            f"Usage: `{config.prefix}choose <player1> <player2>`"
        )
        await ctx.send(embed=embed)
        return
    
    # Find target players
    target1 = session.get_player_by_nick(player1)
    target2 = session.get_player_by_nick(player2)
    
    if not target1:
        embed = create_error_embed("Player Not Found", f"Player '{player1}' not found in the game!")
        await ctx.send(embed=embed)
        return
    
    if not target2:
        embed = create_error_embed("Player Not Found", f"Player '{player2}' not found in the game!")
        await ctx.send(embed=embed)
        return
    
    if target1 == target2:
        embed = create_error_embed("Invalid Selection", "You must choose two different players!")
        await ctx.send(embed=embed)
        return
    
    # TODO: Implement actual lover pairing logic
    embed = create_success_embed(
        "💕 Lovers Chosen",
        f"**{target1.nick}** and **{target2.nick}** are now lovers!"
    )
    await ctx.send(embed=embed)
    logger.info(f"{player.nick} made {target1.nick} and {target2.nick} lovers")

@command("clone", PermissionLevel.PLAYING, "Clone another player's role")
async def clone_command(ctx: commands.Context, target: str = None):
    """Clone role copying"""
    session = get_session()
    
    if not session.playing:
        embed = create_error_embed("No Game", "No game is currently running!")
        await ctx.send(embed=embed)
        return
    
    player = session.get_player_by_id(ctx.author.id)
    if not player:
        embed = create_error_embed("Not Playing", "You are not in the current game!")
        await ctx.send(embed=embed)
        return
    
    if not player.role or player.role.name.lower() not in ["clone"]:
        embed = create_error_embed("Invalid Role", "Only Clones can copy roles!")
        await ctx.send(embed=embed)
        return
    
    if not target:
        embed = create_error_embed(
            "Missing Target", 
            f"Usage: `{config.prefix}clone <player>`"
        )
        await ctx.send(embed=embed)
        return
    
    # Find target player
    target_player = session.get_player_by_nick(target)
    if not target_player:
        embed = create_error_embed("Player Not Found", f"Player '{target}' not found in the game!")
        await ctx.send(embed=embed)
        return
    
    if target_player == player:
        embed = create_error_embed("Invalid Target", "You cannot clone yourself!")
        await ctx.send(embed=embed)
        return
    
    # TODO: Implement actual cloning logic
    embed = create_success_embed(
        "🎭 Role Cloned",
        f"You have successfully cloned **{target_player.nick}**'s abilities!"
    )
    await ctx.author.send(embed=embed)
    
    # Confirm in channel
    await ctx.send(f"✅ {player.nick} mimics someone.")
    logger.info(f"{player.nick} cloned {target_player.nick}")

@command("side", PermissionLevel.PLAYING, "Switch sides", aliases=["turn"])
async def side_command(ctx: commands.Context, new_side: str = None):
    """Turncoat side switching"""
    session = get_session()
    
    if not session.playing:
        embed = create_error_embed("No Game", "No game is currently running!")
        await ctx.send(embed=embed)
        return
    
    player = session.get_player_by_id(ctx.author.id)
    if not player:
        embed = create_error_embed("Not Playing", "You are not in the current game!")
        await ctx.send(embed=embed)
        return
    
    if not player.role or player.role.name.lower() not in ["turncoat"]:
        embed = create_error_embed("Invalid Role", "Only Turncoats can switch sides!")
        await ctx.send(embed=embed)
        return
    
    if not new_side:
        embed = create_error_embed(
            "Missing Side", 
            f"Usage: `{config.prefix}side <village/wolf>`"
        )
        await ctx.send(embed=embed)
        return
    
    if new_side.lower() not in ["village", "wolf", "wolves"]:
        embed = create_error_embed("Invalid Side", "You can only switch to 'village' or 'wolf' side!")
        await ctx.send(embed=embed)
        return
    
    # TODO: Implement actual side switching logic
    side_name = "wolves" if new_side.lower() in ["wolf", "wolves"] else "village"
    embed = create_success_embed(
        "🔄 Side Switched",
        f"You have switched to the **{side_name}** side!"
    )
    await ctx.author.send(embed=embed)
    
    # Confirm in channel
    await ctx.send(f"✅ {player.nick} has made a decision.")
    logger.info(f"{player.nick} switched to {side_name} side")

@command("target", PermissionLevel.PLAYING, "Set assassination target")
async def target_command(ctx: commands.Context, target: str = None):
    """Assassin target selection"""
    session = get_session()
    
    if not session.playing:
        embed = create_error_embed("No Game", "No game is currently running!")
        await ctx.send(embed=embed)
        return
    
    player = session.get_player_by_id(ctx.author.id)
    if not player:
        embed = create_error_embed("Not Playing", "You are not in the current game!")
        await ctx.send(embed=embed)
        return
    
    if not player.role or player.role.name.lower() not in ["assassin"]:
        embed = create_error_embed("Invalid Role", "Only Assassins can set targets!")
        await ctx.send(embed=embed)
        return
    
    if not target:
        embed = create_error_embed(
            "Missing Target", 
            f"Usage: `{config.prefix}target <player>`"
        )
        await ctx.send(embed=embed)
        return
    
    # Find target player
    target_player = session.get_player_by_nick(target)
    if not target_player:
        embed = create_error_embed("Player Not Found", f"Player '{target}' not found in the game!")
        await ctx.send(embed=embed)
        return
    
    if target_player not in session.get_alive_players():
        embed = create_error_embed("Invalid Target", "You can only target living players!")
        await ctx.send(embed=embed)
        return
    
    if target_player == player:
        embed = create_error_embed("Invalid Target", "You cannot target yourself!")
        await ctx.send(embed=embed)
        return
    
    # TODO: Implement actual targeting logic
    embed = create_success_embed(
        "🎯 Target Acquired",
        f"You have marked **{target_player.nick}** for assassination."
    )
    await ctx.author.send(embed=embed)
    
    # Confirm in channel
    await ctx.send(f"✅ {player.nick} studies someone carefully.")
    logger.info(f"{player.nick} targeted {target_player.nick}")

@command("shoot", PermissionLevel.PLAYING, "Shoot a player during the day")
async def shoot_command(ctx: commands.Context, target: str = None):
    """Gunner/Sharpshooter shooting (daytime)"""
    session = get_session()
    
    if not session.playing:
        embed = create_error_embed("No Game", "No game is currently running!")
        await ctx.send(embed=embed)
        return
    
    player = session.get_player_by_id(ctx.author.id)
    if not player:
        embed = create_error_embed("Not Playing", "You are not in the current game!")
        await ctx.send(embed=embed)
        return
    
    if not player.role or player.role.name.lower() not in ["gunner", "sharpshooter"]:
        embed = create_error_embed("Invalid Role", "Only Gunners and Sharpshooters can shoot!")
        await ctx.send(embed=embed)
        return
    
    if not session.is_day:
        embed = create_error_embed("Wrong Phase", "You can only shoot during the day!")
        await ctx.send(embed=embed)
        return
    
    if not target:
        embed = create_error_embed(
            "Missing Target", 
            f"Usage: `{config.prefix}shoot <player>`"
        )
        await ctx.send(embed=embed)
        return
    
    # Find target player
    target_player = session.get_player_by_nick(target)
    if not target_player:
        embed = create_error_embed("Player Not Found", f"Player '{target}' not found in the game!")
        await ctx.send(embed=embed)
        return
    
    if target_player not in session.get_alive_players():
        embed = create_error_embed("Invalid Target", "You can only shoot living players!")
        await ctx.send(embed=embed)
        return
    
    if target_player == player:
        embed = create_error_embed("Invalid Target", "You cannot shoot yourself!")
        await ctx.send(embed=embed)
        return
    
    # TODO: Implement actual shooting logic
    embed = create_success_embed(
        "💥 Shot Fired!",
        f"**{player.nick}** shoots **{target_player.nick}**!"
    )
    await ctx.send(embed=embed)
    logger.info(f"{player.nick} shot {target_player.nick}")

@command("detect", PermissionLevel.PLAYING, "Alternative detective command", aliases=["investigate"])
async def detect_command(ctx: commands.Context, target: str = None):
    """Alternative detective command"""
    # Just redirect to the see command for now
    await see_command_alternative(ctx, target)

async def see_command_alternative(ctx: commands.Context, target: str = None):
    """Alternative implementation for detective work"""
    session = get_session()
    
    if not session.playing:
        embed = create_error_embed("No Game", "No game is currently running!")
        await ctx.send(embed=embed)
        return
    
    player = session.get_player_by_id(ctx.author.id)
    if not player:
        embed = create_error_embed("Not Playing", "You are not in the current game!")
        await ctx.send(embed=embed)
        return
    
    if not player.role or player.role.name.lower() not in ["seer", "oracle", "detective"]:
        embed = create_error_embed("Invalid Role", "Only Seers, Oracles, and Detectives can detect!")
        await ctx.send(embed=embed)
        return
    
    if session.is_day and player.role.name.lower() != "detective":
        embed = create_error_embed("Wrong Phase", "You can only detect during the night (except Detectives)!")
        await ctx.send(embed=embed)
        return
    
    if not target:
        embed = create_error_embed(
            "Missing Target", 
            f"Usage: `{config.prefix}detect <player>`"
        )
        await ctx.send(embed=embed)
        return
    
    # Find target player
    target_player = session.get_player_by_nick(target)
    if not target_player:
        embed = create_error_embed("Player Not Found", f"Player '{target}' not found in the game!")
        await ctx.send(embed=embed)
        return
    
    if target_player not in session.get_alive_players():
        embed = create_error_embed("Invalid Target", "You can only detect living players!")
        await ctx.send(embed=embed)
        return
    
    if target_player == player:
        embed = create_error_embed("Invalid Target", "You cannot detect yourself!")
        await ctx.send(embed=embed)
        return
    
    # TODO: Implement actual detection logic
    embed = create_success_embed(
        "🔍 Detection Complete",
        f"**{target_player.nick}** appears to be on the **village** side."
    )
    await ctx.author.send(embed=embed)
    
    # Confirm in channel
    await ctx.send(f"✅ {player.nick} investigates someone.")
    logger.info(f"{player.nick} detected {target_player.nick}")
