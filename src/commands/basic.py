"""
Basic utility commands for Discord Werewolf Bot
"""

import discord
from discord.ext import commands
import platform
import psutil
import random
from datetime import datetime
from src.commands.base import command, PermissionLevel
from src.core import get_config, get_logger
from src.utils.helpers import create_embed, create_success_embed, create_error_embed, format_time_delta
from src.game.state import get_session

config = get_config()
logger = get_logger()

@command("info", PermissionLevel.EVERYONE, "Display bot information", aliases=["information", "about"])
async def info_command(ctx: commands.Context):
    """Display bot information"""
    embed = create_embed(
        "🐺 Discord Werewolf Bot",
        "A modernized version of the classic Werewolf/Mafia game for Discord"
    )
    
    embed.add_field(name="Prefix", value=f"`{config.prefix}`", inline=True)
    embed.add_field(name="Version", value="2.0 (Modernized)", inline=True)
    embed.add_field(name="Discord.py", value=discord.__version__, inline=True)
    
    # System info
    embed.add_field(name="Python", value=platform.python_version(), inline=True)
    embed.add_field(name="Platform", value=platform.system(), inline=True)
    
    # Memory usage
    process = psutil.Process()
    memory_mb = process.memory_info().rss / 1024 / 1024
    embed.add_field(name="Memory", value=f"{memory_mb:.1f} MB", inline=True)
    
    # Bot uptime
    if hasattr(ctx.bot, 'start_time'):
        uptime = datetime.now() - ctx.bot.start_time
        embed.add_field(name="Uptime", value=format_time_delta(uptime), inline=False)
    
    embed.add_field(
        name="Basic Commands",
        value=f"`{config.prefix}join` - Join the game\n"
              f"`{config.prefix}leave` - Leave the game\n"
              f"`{config.prefix}players` - Show current players\n"
              f"`{config.prefix}help` - Show help information",
        inline=False
    )
    
    embed.add_field(
        name="Links",
        value="[Source Code](https://github.com/SohamXYZDev/Discord-Werewolf) | "
              "[Original by belungawhale](https://github.com/belungawhale/Discord-Werewolf)",
        inline=False
    )
    
    await ctx.send(embed=embed)

@command("help", PermissionLevel.EVERYONE, "Show help information", aliases=["h", "commands"])
async def help_command(ctx: commands.Context, command_name: str = ""):
    """Show help information"""
    from src.commands.base import get_registry
    registry = get_registry()
    
    if command_name:
        # Show help for specific command
        cmd = registry.get_command(command_name.lower())
        if not cmd:
            await ctx.send(f"❌ Command `{command_name}` not found.")
            return
        
        embed = create_embed(f"Help: {config.prefix}{cmd.name}")
        embed.add_field(name="Description", value=cmd.description or "No description available", inline=False)
        
        if cmd.aliases:
            embed.add_field(name="Aliases", value=", ".join(f"`{config.prefix}{alias}`" for alias in cmd.aliases), inline=False)
        
        # Permission level
        perm_names = {
            PermissionLevel.EVERYONE: "Everyone",
            PermissionLevel.PLAYING: "Players in game",
            PermissionLevel.ADMIN: "Admins",
            PermissionLevel.OWNER: "Owner only"
        }
        embed.add_field(name="Permission", value=perm_names.get(cmd.permission_level, "Unknown"), inline=True)
        
        if cmd.game_only:
            embed.add_field(name="Restriction", value="Game only", inline=True)
        elif cmd.pm_only:
            embed.add_field(name="Restriction", value="PM only", inline=True)
        
        await ctx.send(embed=embed)
    else:
        # Show general help
        session = get_session()
        available_commands = registry.get_commands_for_user(ctx.author.id, session.playing)

        embed = create_embed("🐺 Werewolf Bot Commands")

        # Group commands by category
        basic_commands = []
        game_commands = []
        admin_commands = []

        for cmd in available_commands:
            cmd_str = f"`{config.prefix}{cmd.name}`"
            if cmd.permission_level == PermissionLevel.ADMIN or cmd.permission_level == PermissionLevel.OWNER:
                admin_commands.append(cmd_str)
            elif cmd.game_only or cmd.name in ['join', 'leave', 'vote', 'lynch', 'abstain', 'give']:
                game_commands.append(cmd_str)
            else:
                basic_commands.append(cmd_str)

        if basic_commands:
            embed.add_field(name="Basic Commands", value=" • ".join(basic_commands), inline=False)

        if game_commands:
            embed.add_field(name="Game Commands", value=" • ".join(game_commands), inline=False)

        if admin_commands:
            embed.add_field(name="Admin Commands", value=" • ".join(admin_commands), inline=False)

            # Notable / New features summary
            embed.add_field(
                name="Notable Features",
                value=(
                    f"• `!vote startgame` — Players can vote to start the game; majority starts it.\n"
                    f"• Werewolf communication is performed via DMs (no public wolfchat).\n"
                    f"• Phase pings: the bot pings all living players at day/night start.\n"
                    f"• Immediate transitions: day/night can end early when votes/actions complete.\n"
                    f"• Totems: use `!totem <name>` for totem details, or `{config.prefix}role <role>` for role/gamemode descriptions."
                ),
                inline=False
            )

            # Explicitly list night (PM-only) actions so players know what to use in DMs
            embed.add_field(
                name="Night Actions (PM only)",
                value=(
                    "`kill` — Wolf kill target\n"
                    "`see` — Seer/night investigator\n"
                    "`detect` — Detective night investigation\n"
                    "`protect` — Guardian Angel protection\n"
                    "`pass` — Skip your night action\n"
                    "`myrole` — Check your role and status in DMs"
                ),
                inline=False
            )

            # Role-specific and other role-action commands (may be PM-only depending on role)
            embed.add_field(
                name="Role / Action Commands",
                value=(
                    "`give` — Give a totem to a player (Shaman / Wolf Shaman)\n"
                    "`observe` — Werecrow / Sorcerer observation\n"
                    "`id` — Detective daytime identify\n"
                    "`bless` / `consecrate` — Priest abilities\n"
                    "`hex` / `curse` — Hag / Warlock abilities\n"
                    "`charm` — Piper charm players\n"
                    "`choose` — Matchmaker choose lovers\n"
                    "`clone` — Clone another player's role\n"
                    "`side` — Turncoat side selection\n"
                    "`target` / `shoot` — Assassins / shooters\n"
                    "`observe`, `detect` — alternate investigator commands"
                ),
                inline=False
            )

        embed.add_field(
            name="More Info",
            value=f"Use `{config.prefix}help <command>` for detailed information about a specific command.",
            inline=False
        )

        await ctx.send(embed=embed)

@command("ping", PermissionLevel.EVERYONE, "Test bot responsiveness")
async def ping_command(ctx: commands.Context):
    """Test bot responsiveness"""
    latency = round(ctx.bot.latency * 1000)
    
    ping_responses = [
        f"🏓 Pong! Latency: {latency}ms",
        f"🐺 *howls* Latency: {latency}ms",
        f"🌙 The wolves hear you... Latency: {latency}ms",
        f"⚡ Quick as a wolf! Latency: {latency}ms"
    ]
    
    await ctx.send(random.choice(ping_responses))

@command("version", PermissionLevel.EVERYONE, "Show bot version information", aliases=["v"])
async def version_command(ctx: commands.Context):
    """Show version information"""
    embed = create_embed("Version Information")
    embed.add_field(name="Bot Version", value="2.0 (Modernized)", inline=True)
    embed.add_field(name="Discord.py", value=discord.__version__, inline=True)
    embed.add_field(name="Python", value=platform.python_version(), inline=True)
    
    embed.add_field(
        name="Changes in v2.0",
        value="• Modernized for discord.py 2.x\n"
              "• Modular code structure\n"
              "• Better error handling\n"
              "• Improved command system\n"
              "• Enhanced logging",
        inline=False
    )
    
    await ctx.send(embed=embed)

@command("uptime", PermissionLevel.EVERYONE, "Show bot uptime")
async def uptime_command(ctx: commands.Context):
    """Show bot uptime"""
    if not hasattr(ctx.bot, 'start_time'):
        await ctx.send("❌ Uptime information not available.")
        return
    
    uptime = datetime.now() - ctx.bot.start_time
    embed = create_success_embed("Bot Uptime", format_time_delta(uptime))
    await ctx.send(embed=embed)

@command("status", PermissionLevel.EVERYONE, "Show current bot and game status", aliases=["state"])
async def status_command(ctx: commands.Context):
    """Show current status"""
    session = get_session()
    embed = create_embed("🐺 Bot Status")
    
    # Game status
    if session.playing:
        phase = "🌙 Night" if not session.is_day else "☀️ Day"
        embed.add_field(name="Game Status", value=f"Active ({phase})", inline=True)
        embed.add_field(name="Players", value=str(len(session.players)), inline=True)
        embed.add_field(name="Alive", value=str(len(session.get_alive_players())), inline=True)
        embed.add_field(name="Game Mode", value=session.gamemode or "Unknown", inline=True)
    else:
        embed.add_field(name="Game Status", value="No active game", inline=True)
        if session.players:
            embed.add_field(name="Players in Lobby", value=str(len(session.players)), inline=True)
    
    # System status
    process = psutil.Process()
    cpu_percent = process.cpu_percent()
    memory_mb = process.memory_info().rss / 1024 / 1024
    
    embed.add_field(name="CPU Usage", value=f"{cpu_percent:.1f}%", inline=True)
    embed.add_field(name="Memory Usage", value=f"{memory_mb:.1f} MB", inline=True)
    
    # Bot latency
    latency = round(ctx.bot.latency * 1000)
    embed.add_field(name="Latency", value=f"{latency}ms", inline=True)
    
    await ctx.send(embed=embed)

@command("time", PermissionLevel.EVERYONE, "Show time remaining in current phase", aliases=["t"])
async def time_command(ctx: commands.Context):
    """Show time remaining in current day/night phase"""
    session = get_session()
    
    if not session.playing:
        embed = create_error_embed("No Game", "No game is currently running!")
        await ctx.send(embed=embed)
        return
    
    # Get current phase and time remaining
    phase_name = "🌙 Night" if not session.is_day else "☀️ Day"
    
    # Calculate time remaining (this would need to be implemented in game state)
    if hasattr(session, 'phase_end_time') and session.phase_end_time:
        time_remaining = session.phase_end_time - datetime.now()
        if time_remaining.total_seconds() > 0:
            time_str = format_time_delta(time_remaining)
            embed = create_embed(f"{phase_name} Phase", f"⏰ Time remaining: **{time_str}**")
        else:
            embed = create_embed(f"{phase_name} Phase", "⏰ Time remaining: **Ending soon...**")
    else:
        embed = create_embed(f"{phase_name} Phase", "⏰ Time remaining: **Unknown**")
    
    # Add phase information
    if not session.is_day:
        embed.add_field(name="Current Phase", value="Night - Send your night actions via DM", inline=False)
    else:
        embed.add_field(name="Current Phase", value="Day - Discuss and vote to lynch a player", inline=False)
    
    await ctx.send(embed=embed)

@command("list", PermissionLevel.EVERYONE, "List current players or available commands")
async def list_command(ctx: commands.Context):
    """List current players in lobby/game or available commands"""
    session = get_session()
    
    if session.players:
        # Show player list
        embed = create_embed("🐺 Current Players")
        if session.playing:
            alive_players = session.get_alive_players()
            dead_players = [p for p in session.players if p not in alive_players]
            
            if alive_players:
                alive_list = "\n".join(f"• {player.nick}" for player in alive_players)
                embed.add_field(name="👥 Alive Players", value=alive_list, inline=False)
            
            if dead_players:
                dead_list = "\n".join(f"• ~~{player.nick}~~" for player in dead_players)
                embed.add_field(name="💀 Dead Players", value=dead_list, inline=False)
        else:
            # Lobby
            player_list = "\n".join(f"• {player.nick}" for player in session.players)
            embed.add_field(name="Players in Lobby", value=player_list, inline=False)
        
        await ctx.send(embed=embed)
    else:
        # No players, show available commands
        embed = create_embed("📝 Available Commands")
        embed.add_field(
            name="Game Commands",
            value=f"`{config.prefix}join` - Join the game\n"
                  f"`{config.prefix}help` - Show help\n"
                  f"`{config.prefix}info` - Bot information\n"
                  f"`{config.prefix}role <role>` - Role information",
            inline=False
        )
        await ctx.send(embed=embed)

# Fix the rest of the status command
def _complete_status_command():
    """Complete the status command properly"""
    pass

@command("admins", PermissionLevel.EVERYONE, "List online administrators")
async def admins_command(ctx: commands.Context):
    """List all online administrators"""
    guild = ctx.guild
    
    if not guild:
        await ctx.send("❌ This command can only be used in a server.")
        return
    
    # Get admin role
    admin_role = discord.utils.get(guild.roles, name=config.admin_role_name)
    if not admin_role:
        embed = create_error_embed("Configuration Error", f"Admin role '{config.admin_role_name}' not found.")
        await ctx.send(embed=embed)
        return
    
    # Find online admins
    online_admins = []
    offline_admins = []
    
    for member in guild.members:
        if admin_role in member.roles:
            if member.status != discord.Status.offline:
                online_admins.append(f"🟢 {member.display_name}")
            else:
                offline_admins.append(f"⚫ {member.display_name}")
    
    embed = create_embed("👑 Administrators")
    
    if online_admins:
        embed.add_field(
            name="🟢 Online Admins",
            value="\n".join(online_admins),
            inline=False
        )
    
    if offline_admins:
        embed.add_field(
            name="⚫ Offline Admins", 
            value="\n".join(offline_admins),
            inline=False
        )
    
    if not online_admins and not offline_admins:
        embed.add_field(
            name="No Admins Found",
            value="No administrators are currently configured.",
            inline=False
        )
    
    embed.add_field(
        name="Total",
        value=f"{len(online_admins)} online • {len(offline_admins)} offline",
        inline=False
    )
    
    await ctx.send(embed=embed)