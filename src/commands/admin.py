"""
Administrative commands for Discord Werewolf Bot
"""

import discord
from discord.ext import commands
import asyncio
import traceback
import sys
from io import StringIO
from src.commands.base import command, PermissionLevel
from src.core import get_config, get_logger
from src.utils.helpers import create_embed, create_success_embed, create_error_embed
from src.game.state import get_session, get_persistent_data

config = get_config()
logger = get_logger()

@command("shutdown", PermissionLevel.OWNER, "Shutdown the bot", aliases=["exit"])
async def shutdown_command(ctx: commands.Context, options: str = ""):
    """Shutdown the bot (owner only)"""
    # Handle additional options
    if "-stop" in options:
        # Stop the current game first
        session = get_session()
        if session.playing or session.players:
            await stop_game_for_shutdown(ctx)
    
    embed = create_success_embed("Shutting Down", "Bot is shutting down...")
    await ctx.send(embed=embed)
    
    logger.info(f"Bot shutdown initiated by {ctx.author.display_name}")
    await ctx.bot.close()

async def stop_game_for_shutdown(ctx):
    """Helper function to stop game during shutdown"""
    from src.commands.game import stop_command
    await stop_command(ctx, "-force")

@command("eval", PermissionLevel.OWNER, "Evaluate Python code", aliases=["evaluate"])
async def eval_command(ctx: commands.Context, *, code: str):
    """Evaluate Python code (owner only)"""
    if not code:
        await ctx.send("❌ Please provide code to evaluate.")
        return
    
    try:
        # Create a safe evaluation environment
        env = {
            'ctx': ctx,
            'bot': ctx.bot,
            'discord': discord,
            'session': get_session(),
            'persistent_data': get_persistent_data(),
            'config': config,
            'logger': logger
        }
        
        result = eval(code, env)
        
        # Handle coroutines
        if asyncio.iscoroutine(result):
            result = await result
        
        # Format output
        output = str(result)
        if len(output) > 1900:
            output = output[:1900] + "... (truncated)"
        
        embed = create_embed("Evaluation Result")
        embed.add_field(name="Code", value=f"```python\n{code}\n```", inline=False)
        embed.add_field(name="Result", value=f"```python\n{output}\n```", inline=False)
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        error_msg = str(traceback.format_exc())
        if len(error_msg) > 1900:
            error_msg = error_msg[:1900] + "... (truncated)"
        
        embed = create_error_embed("Evaluation Error")
        embed.add_field(name="Code", value=f"```python\n{code}\n```", inline=False)
        embed.add_field(name="Error", value=f"```python\n{error_msg}\n```", inline=False)
        
        await ctx.send(embed=embed)

@command("exec", PermissionLevel.OWNER, "Execute Python code", aliases=["execute"])
async def exec_command(ctx: commands.Context, *, code: str):
    """Execute Python code (owner only)"""
    if not code:
        await ctx.send("❌ Please provide code to execute.")
        return
    
    # Capture stdout
    old_stdout = sys.stdout
    redirected_output = sys.stdout = StringIO()
    
    try:
        # Create execution environment
        env = {
            'ctx': ctx,
            'bot': ctx.bot,
            'discord': discord,
            'session': get_session(),
            'persistent_data': get_persistent_data(),
            'config': config,
            'logger': logger
        }
        
        exec(code, env)
        
        # Get output
        output = redirected_output.getvalue()
        if not output:
            output = "✅ Code executed successfully (no output)"
        elif len(output) > 1900:
            output = output[:1900] + "... (truncated)"
        
        embed = create_success_embed("Execution Result")
        embed.add_field(name="Code", value=f"```python\n{code}\n```", inline=False)
        embed.add_field(name="Output", value=f"```\n{output}\n```", inline=False)
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        error_msg = str(traceback.format_exc())
        if len(error_msg) > 1900:
            error_msg = error_msg[:1900] + "... (truncated)"
        
        embed = create_error_embed("Execution Error")
        embed.add_field(name="Code", value=f"```python\n{code}\n```", inline=False)
        embed.add_field(name="Error", value=f"```python\n{error_msg}\n```", inline=False)
        
        await ctx.send(embed=embed)
        
    finally:
        sys.stdout = old_stdout

@command("reload", PermissionLevel.OWNER, "Reload bot components")
async def reload_command(ctx: commands.Context, component: str = "all"):
    """Reload bot components (owner only)"""
    try:
        if component.lower() in ["all", "config"]:
            # Reload configuration
            import importlib
            import src.core
            importlib.reload(src.core)
            
        if component.lower() in ["all", "commands"]:
            # TODO: Implement command reloading
            pass
        
        embed = create_success_embed("Reload Complete", f"Successfully reloaded: {component}")
        await ctx.send(embed=embed)
        
    except Exception as e:
        embed = create_error_embed("Reload Failed", str(e))
        await ctx.send(embed=embed)

@command("setstatus", PermissionLevel.ADMIN, "Set bot status")
async def setstatus_command(ctx: commands.Context, status: str, *, activity: str = ""):
    """Set bot status (admin only)"""
    status_map = {
        "online": discord.Status.online,
        "idle": discord.Status.idle,
        "dnd": discord.Status.dnd,
        "invisible": discord.Status.invisible
    }
    
    if status.lower() not in status_map:
        await ctx.send(f"❌ Invalid status. Options: {', '.join(status_map.keys())}")
        return
    
    try:
        if activity:
            game_activity = discord.Game(name=activity)
            await ctx.bot.change_presence(status=status_map[status.lower()], activity=game_activity)
        else:
            await ctx.bot.change_presence(status=status_map[status.lower()])
        
        embed = create_success_embed("Status Updated", f"Status set to **{status}**" + (f" playing **{activity}**" if activity else ""))
        await ctx.send(embed=embed)
        
    except Exception as e:
        embed = create_error_embed("Status Update Failed", str(e))
        await ctx.send(embed=embed)

@command("stasis", PermissionLevel.ADMIN, "Manage user stasis")
async def stasis_command(ctx: commands.Context, action: str, user: discord.Member = None, amount: int = 1):
    """Manage user stasis (admin only)"""
    if not user:
        await ctx.send("❌ Please specify a user.")
        return
    
    persistent_data = get_persistent_data()
    
    if action.lower() == "add":
        persistent_data.add_stasis(user.id, amount)
        embed = create_success_embed(
            "Stasis Added",
            f"Added **{amount}** stasis to {user.mention}.\n"
            f"Total stasis: **{persistent_data.get_stasis(user.id)}**"
        )
    elif action.lower() == "remove":
        remaining = persistent_data.remove_stasis(user.id, amount)
        embed = create_success_embed(
            "Stasis Removed",
            f"Removed **{amount}** stasis from {user.mention}.\n"
            f"Remaining stasis: **{remaining}**"
        )
    elif action.lower() == "check":
        stasis_count = persistent_data.get_stasis(user.id)
        embed = create_embed(
            "Stasis Check",
            f"{user.mention} has **{stasis_count}** stasis."
        )
    elif action.lower() == "clear":
        persistent_data.stasis[user.id] = 0
        persistent_data.save_stasis()
        embed = create_success_embed("Stasis Cleared", f"Cleared all stasis for {user.mention}.")
    else:
        await ctx.send("❌ Invalid action. Use: add, remove, check, clear")
        return
    
    await ctx.send(embed=embed)

@command("logs", PermissionLevel.ADMIN, "View recent logs")
async def logs_command(ctx: commands.Context, lines: int = 20):
    """View recent log entries (admin only)"""
    try:
        with open(config.log_file, 'r') as f:
            log_lines = f.readlines()
        
        # Get last N lines
        recent_lines = log_lines[-lines:] if len(log_lines) > lines else log_lines
        log_content = ''.join(recent_lines)
        
        # Truncate if too long
        if len(log_content) > 1900:
            log_content = log_content[-1900:] + "... (truncated)"
        
        embed = create_embed(f"Recent Logs ({len(recent_lines)} lines)")
        embed.add_field(name="Content", value=f"```\n{log_content}\n```", inline=False)
        
        await ctx.send(embed=embed)
        
    except FileNotFoundError:
        await ctx.send("❌ Log file not found.")
    except Exception as e:
        await ctx.send(f"❌ Error reading logs: {e}")

@command("cleanup", PermissionLevel.ADMIN, "Clean up roles and channels")
async def cleanup_command(ctx: commands.Context, component: str = "roles"):
    """Clean up bot-related roles and channels (admin only)"""
    guild = ctx.guild
    
    if component.lower() == "roles":
        # Remove player roles from all members
        player_role = discord.utils.get(guild.roles, name=config.players_role_name)
        if player_role:
            removed_count = 0
            for member in guild.members:
                if player_role in member.roles:
                    try:
                        await member.remove_roles(player_role, reason="Admin cleanup")
                        removed_count += 1
                    except Exception as e:
                        logger.error(f"Failed to remove role from {member.display_name}: {e}")
            
            embed = create_success_embed("Role Cleanup", f"Removed player role from **{removed_count}** members.")
        else:
            embed = create_error_embed("Role Cleanup", "Player role not found.")
    else:
        embed = create_error_embed("Invalid Component", "Available options: roles")
    
    await ctx.send(embed=embed)

@command("admins", PermissionLevel.EVERYONE, "List available admins")
async def admins_command(ctx: commands.Context):
    """List available admins"""
    guild = ctx.guild
    online_admins = []
    offline_admins = []
    
    # Check owner
    if config.owner_id:
        owner = guild.get_member(config.owner_id)
        if owner:
            if owner.status != discord.Status.offline:
                online_admins.append(f"👑 {owner.display_name} (Owner)")
            else:
                offline_admins.append(f"👑 {owner.display_name} (Owner)")
    
    # Check admins
    for admin_id in config.admins:
        admin = guild.get_member(admin_id)
        if admin:
            if admin.status != discord.Status.offline:
                online_admins.append(f"🛡️ {admin.display_name}")
            else:
                offline_admins.append(f"🛡️ {admin.display_name}")
    
    embed = create_embed("🛡️ Bot Administrators")
    
    if online_admins:
        embed.add_field(name="Online", value="\n".join(online_admins), inline=False)
    
    if offline_admins:
        embed.add_field(name="Offline", value="\n".join(offline_admins), inline=False)
    
    if not online_admins and not offline_admins:
        embed.add_field(name="No Admins Found", value="No administrators are configured or found in this server.", inline=False)
    
    await ctx.send(embed=embed)

@command("notify", PermissionLevel.EVERYONE, "Manage notification list")
async def notify_command(ctx: commands.Context, action: str = ""):
    """Manage notification list for game announcements"""
    persistent_data = get_persistent_data()
    user_id = ctx.author.id
    
    if not action:
        # Show current status
        is_subscribed = persistent_data.is_on_notify_list(user_id)
        status = "subscribed to" if is_subscribed else "not subscribed to"
        embed = create_embed(
            "📢 Notification Status",
            f"You are **{status}** game notifications.\n\n"
            f"Use `{config.prefix}notify on` to subscribe\n"
            f"Use `{config.prefix}notify off` to unsubscribe"
        )
        await ctx.send(embed=embed)
        return
    
    if action.lower() in ["on", "true", "yes", "enable"]:
        if persistent_data.is_on_notify_list(user_id):
            embed = create_embed("📢 Notification Status", "You are already subscribed to notifications.")
        else:
            persistent_data.add_to_notify_list(user_id)
            embed = create_success_embed(
                "📢 Notifications Enabled",
                "You will now receive notifications when games start."
            )
    elif action.lower() in ["off", "false", "no", "disable"]:
        if not persistent_data.is_on_notify_list(user_id):
            embed = create_embed("📢 Notification Status", "You are not subscribed to notifications.")
        else:
            persistent_data.remove_from_notify_list(user_id)
            embed = create_success_embed(
                "📢 Notifications Disabled",
                "You will no longer receive game notifications."
            )
    else:
        embed = create_error_embed(
            "Invalid Option",
            f"Use `{config.prefix}notify on` or `{config.prefix}notify off`"
        )
    
    await ctx.send(embed=embed)

@command("fstart", PermissionLevel.ADMIN, "Force start the game", aliases=["forcestart"])
async def fstart_command(ctx: commands.Context):
    """Force start the game bypassing vote requirements (admin only)"""
    session = get_session()
    
    if session.playing:
        embed = create_error_embed("Game Running", "A game is already in progress!")
        await ctx.send(embed=embed)
        return
    
    if len(session.players) < 4:
        embed = create_error_embed("Not Enough Players", "At least 4 players are required to start a game.")
        await ctx.send(embed=embed)
        return
    
    try:
        # Force start the game
        await session.start_game()
        embed = create_success_embed(
            "🐺 Game Force Started!",
            f"Game started by admin {ctx.author.mention} with {len(session.players)} players."
        )
        await ctx.send(embed=embed)
        logger.info(f"Game force started by admin {ctx.author.display_name}")
        
    except Exception as e:
        embed = create_error_embed("Start Failed", f"Failed to start game: {str(e)}")
        await ctx.send(embed=embed)
        logger.error(f"Force start failed: {e}")

@command("fstop", PermissionLevel.ADMIN, "Force stop the current game", aliases=["forcestop"])
async def fstop_command(ctx: commands.Context, *, reason: str = ""):
    """Force stop the current game (admin only)"""
    session = get_session()
    
    if not session.playing:
        embed = create_error_embed("No Game", "No game is currently running!")
        await ctx.send(embed=embed)
        return
    
    try:
        # Stop the game
        session.stop_game()
        
        reason_text = f" Reason: {reason}" if reason else ""
        embed = create_success_embed(
            "🛑 Game Force Stopped",
            f"Game stopped by admin {ctx.author.mention}.{reason_text}"
        )
        await ctx.send(embed=embed)
        logger.info(f"Game force stopped by admin {ctx.author.display_name}: {reason}")
        
    except Exception as e:
        embed = create_error_embed("Stop Failed", f"Failed to stop game: {str(e)}")
        await ctx.send(embed=embed)
        logger.error(f"Force stop failed: {e}")

@command("fsay", PermissionLevel.ADMIN, "Make the bot say a message", aliases=["say"])
async def fsay_command(ctx: commands.Context, *, message: str):
    """Make the bot say a message in the channel (admin only)"""
    if not message:
        await ctx.send("❌ Please provide a message to send.")
        return
    
    try:
        # Delete the command message
        await ctx.message.delete()
    except:
        pass  # Ignore if we can't delete
    
    # Send the message
    await ctx.send(message)
    logger.info(f"Admin {ctx.author.display_name} made bot say: {message}")

@command("sync", PermissionLevel.ADMIN, "Sync player permissions with bot state")
async def sync_command(ctx: commands.Context):
    """Synchronize player roles and permissions with bot state (admin only)"""
    session = get_session()
    guild = ctx.guild
    
    if not guild:
        await ctx.send("❌ This command can only be used in a server.")
        return
    
    try:
        synced_count = 0
        errors = []
        
        # Get the player role
        player_role = discord.utils.get(guild.roles, name=config.players_role_name)
        if not player_role:
            embed = create_error_embed("Sync Failed", f"Player role '{config.players_role_name}' not found.")
            await ctx.send(embed=embed)
            return
        
        # Sync player roles
        for player in session.players:
            try:
                member = guild.get_member(player.id)
                if member:
                    if session.playing:
                        # Add player role if in game
                        if player_role not in member.roles:
                            await member.add_roles(player_role, reason="Sync with bot state")
                            synced_count += 1
                    else:
                        # Remove player role if not in game
                        if player_role in member.roles:
                            await member.remove_roles(player_role, reason="Sync with bot state")
                            synced_count += 1
            except Exception as e:
                errors.append(f"{player.nick}: {str(e)}")
        
        # Clean up role from non-players
        if not session.playing:
            for member in guild.members:
                if (player_role in member.roles and 
                    not any(p.id == member.id for p in session.players)):
                    try:
                        await member.remove_roles(player_role, reason="Sync cleanup")
                        synced_count += 1
                    except Exception as e:
                        errors.append(f"{member.display_name}: {str(e)}")
        
        embed = create_success_embed(
            "🔄 Sync Complete",
            f"Synchronized {synced_count} player role assignments."
        )
        
        if errors:
            error_text = "\n".join(errors[:5])  # Show first 5 errors
            if len(errors) > 5:
                error_text += f"\n... and {len(errors) - 5} more errors"
            embed.add_field(name="Errors", value=error_text, inline=False)
        
        await ctx.send(embed=embed)
        logger.info(f"Sync completed by {ctx.author.display_name}: {synced_count} changes, {len(errors)} errors")
        
    except Exception as e:
        embed = create_error_embed("Sync Failed", f"Failed to sync permissions: {str(e)}")
        await ctx.send(embed=embed)
        logger.error(f"Sync failed: {e}")

@command("revealroles", PermissionLevel.ADMIN, "Show all player roles", aliases=["rr"])
async def revealroles_command(ctx: commands.Context):
    """Show all player roles to admin (admin only)"""
    session = get_session()
    
    if not session.playing:
        embed = create_error_embed("No Game", "No game is currently running!")
        await ctx.send(embed=embed)
        return
    
    embed = create_embed("🕵️ Player Roles (Admin View)")
    
    alive_roles = []
    dead_roles = []
    
    alive_players = session.get_alive_players()
    
    for player in session.players:
        role_info = f"**{player.nick}**: {player.role.name if player.role else 'None'}"
        
        if player in alive_players:
            alive_roles.append(role_info)
        else:
            dead_roles.append(f"~~{role_info}~~")
    
    if alive_roles:
        embed.add_field(name="👥 Alive Players", value="\n".join(alive_roles), inline=False)
    
    if dead_roles:
        embed.add_field(name="💀 Dead Players", value="\n".join(dead_roles), inline=False)
    
    embed.add_field(
        name="⚠️ Admin Only",
        value="This information is only visible to administrators.",
        inline=False
    )
    
    # Send via DM for security
    try:
        await ctx.author.send(embed=embed)
        await ctx.send("📋 Role information sent to your DMs.")
    except:
        # If DM fails, send in channel but with warning
        embed.add_field(
            name="🚨 Warning",
            value="Could not send DM - displaying in channel! Delete this message quickly.",
            inline=False
        )
        await ctx.send(embed=embed)

@command("op", PermissionLevel.ADMIN, "Grant admin status to yourself")
async def op_command(ctx: commands.Context):
    """Grant admin role to yourself (admin only)"""
    guild = ctx.guild
    
    if not guild:
        await ctx.send("❌ This command can only be used in a server.")
        return
    
    admin_role = discord.utils.get(guild.roles, name=config.admin_role_name)
    if not admin_role:
        embed = create_error_embed("Admin Role Not Found", f"Admin role '{config.admin_role_name}' not found.")
        await ctx.send(embed=embed)
        return
    
    if admin_role in ctx.author.roles:
        embed = create_embed("Already Admin", "You already have admin privileges.")
        await ctx.send(embed=embed)
        return
    
    try:
        await ctx.author.add_roles(admin_role, reason="Self-granted admin")
        embed = create_success_embed(
            "🛡️ Admin Granted",
            f"{ctx.author.mention} has been granted admin privileges."
        )
        await ctx.send(embed=embed)
        logger.info(f"Admin role granted to {ctx.author.display_name}")
        
    except Exception as e:
        embed = create_error_embed("Failed", f"Failed to grant admin role: {str(e)}")
        await ctx.send(embed=embed)

@command("deop", PermissionLevel.EVERYONE, "Remove admin status from yourself")
async def deop_command(ctx: commands.Context):
    """Remove admin role from yourself"""
    guild = ctx.guild
    
    if not guild:
        await ctx.send("❌ This command can only be used in a server.")
        return
    
    admin_role = discord.utils.get(guild.roles, name=config.admin_role_name)
    if not admin_role:
        embed = create_error_embed("Admin Role Not Found", f"Admin role '{config.admin_role_name}' not found.")
        await ctx.send(embed=embed)
        return
    
    if admin_role not in ctx.author.roles:
        embed = create_embed("Not Admin", "You don't have admin privileges to remove.")
        await ctx.send(embed=embed)
        return
    
    try:
        await ctx.author.remove_roles(admin_role, reason="Self-removed admin")
        embed = create_success_embed(
            "🛡️ Admin Removed",
            f"{ctx.author.mention} has removed their admin privileges."
        )
        await ctx.send(embed=embed)
        logger.info(f"Admin role removed from {ctx.author.display_name}")
        
    except Exception as e:
        embed = create_error_embed("Failed", f"Failed to remove admin role: {str(e)}")
        await ctx.send(embed=embed)

@command("fjoin", PermissionLevel.ADMIN, "Force join players to the game")
async def fjoin_command(ctx: commands.Context, *players):
    """Force join players to the game (admin only)"""
    if not players:
        embed = create_error_embed("Missing Players", f"Usage: `{config.prefix}fjoin <player1> [player2] ...`")
        await ctx.send(embed=embed)
        return
    
    session = get_session()
    
    if session.playing:
        embed = create_error_embed("Game Running", "Cannot force join players while a game is active!")
        await ctx.send(embed=embed)
        return
    
    guild = ctx.guild
    if not guild:
        await ctx.send("❌ This command can only be used in a server.")
        return
    
    joined_players = []
    failed_players = []
    
    for player_name in players:
        # Try to find the member
        member = None
        
        # Try by mention first
        if player_name.startswith('<@') and player_name.endswith('>'):
            user_id = int(player_name.strip('<@!>'))
            member = guild.get_member(user_id)
        else:
            # Try by name/nickname
            member = discord.utils.find(
                lambda m: m.display_name.lower() == player_name.lower() or 
                         m.name.lower() == player_name.lower(),
                guild.members
            )
        
        if not member:
            failed_players.append(f"{player_name} (not found)")
            continue
        
        # Check if already in game
        if session.get_player_by_id(member.id):
            failed_players.append(f"{member.display_name} (already in game)")
            continue
        
        try:
            # Force add player
            session.add_player(member.id, member.display_name)
            joined_players.append(member.display_name)
            logger.info(f"Admin {ctx.author.display_name} force joined {member.display_name}")
        except Exception as e:
            failed_players.append(f"{member.display_name} (error: {str(e)})")
    
    embed = create_embed("👥 Force Join Results")
    
    if joined_players:
        embed.add_field(
            name="✅ Successfully Joined",
            value="\n".join(f"• {player}" for player in joined_players),
            inline=False
        )
    
    if failed_players:
        embed.add_field(
            name="❌ Failed to Join",
            value="\n".join(f"• {player}" for player in failed_players),
            inline=False
        )
    
    embed.add_field(
        name="Current Lobby",
        value=f"{len(session.players)} players",
        inline=True
    )
    
    await ctx.send(embed=embed)

@command("fleave", PermissionLevel.ADMIN, "Force remove players from the game")
async def fleave_command(ctx: commands.Context, *players):
    """Force remove players from the game (admin only)"""
    if not players:
        embed = create_error_embed("Missing Players", f"Usage: `{config.prefix}fleave <player1> [player2] ...`")
        await ctx.send(embed=embed)
        return
    
    session = get_session()
    
    if not session.players:
        embed = create_error_embed("No Players", "No players in the lobby to remove!")
        await ctx.send(embed=embed)
        return
    
    removed_players = []
    failed_players = []
    
    for player_name in players:
        # Find player in session
        player = session.get_player_by_nick(player_name)
        
        if not player:
            failed_players.append(f"{player_name} (not in game)")
            continue
        
        try:
            # Force remove player
            session.remove_player(player.id)
            removed_players.append(player.nick)
            logger.info(f"Admin {ctx.author.display_name} force removed {player.nick}")
        except Exception as e:
            failed_players.append(f"{player.nick} (error: {str(e)})")
    
    embed = create_embed("👥 Force Leave Results")
    
    if removed_players:
        embed.add_field(
            name="✅ Successfully Removed",
            value="\n".join(f"• {player}" for player in removed_players),
            inline=False
        )
    
    if failed_players:
        embed.add_field(
            name="❌ Failed to Remove",
            value="\n".join(f"• {player}" for player in failed_players),
            inline=False
        )
    
    embed.add_field(
        name="Current Lobby",
        value=f"{len(session.players)} players",
        inline=True
    )
    
    await ctx.send(embed=embed)

@command("fday", PermissionLevel.ADMIN, "Force transition to day phase")
async def fday_command(ctx: commands.Context):
    """Force transition to day phase (admin only)"""
    session = get_session()
    
    if not session.playing:
        embed = create_error_embed("No Game", "No game is currently running!")
        await ctx.send(embed=embed)
        return
    
    if session.is_day:
        embed = create_error_embed("Already Day", "It's already day phase!")
        await ctx.send(embed=embed)
        return
    
    try:
        # Force day transition
        session.is_day = True
        session.current_phase = "day"
        
        embed = create_success_embed(
            "☀️ Day Phase Forced",
            f"Admin {ctx.author.mention} has forced the transition to day phase."
        )
        await ctx.send(embed=embed)
        logger.info(f"Admin {ctx.author.display_name} forced day phase")
        
    except Exception as e:
        embed = create_error_embed("Force Failed", f"Failed to force day phase: {str(e)}")
        await ctx.send(embed=embed)

@command("fnight", PermissionLevel.ADMIN, "Force transition to night phase")
async def fnight_command(ctx: commands.Context):
    """Force transition to night phase (admin only)"""
    session = get_session()
    
    if not session.playing:
        embed = create_error_embed("No Game", "No game is currently running!")
        await ctx.send(embed=embed)
        return
    
    if not session.is_day:
        embed = create_error_embed("Already Night", "It's already night phase!")
        await ctx.send(embed=embed)
        return
    
    try:
        # Force night transition
        session.is_day = False
        session.current_phase = "night"
        
        embed = create_success_embed(
            "🌙 Night Phase Forced",
            f"Admin {ctx.author.mention} has forced the transition to night phase."
        )
        await ctx.send(embed=embed)
        logger.info(f"Admin {ctx.author.display_name} forced night phase")
        
    except Exception as e:
        embed = create_error_embed("Force Failed", f"Failed to force night phase: {str(e)}")
        await ctx.send(embed=embed)

@command("fgame", PermissionLevel.ADMIN, "Force set gamemode", aliases=["fgamemode"])
async def fgame_command(ctx: commands.Context, gamemode: str = None):
    """Force set gamemode (admin only)"""
    if not gamemode:
        embed = create_error_embed("Missing Gamemode", f"Usage: `{config.prefix}fgame <gamemode>`")
        await ctx.send(embed=embed)
        return
    
    session = get_session()
    
    # List of available gamemodes (simplified)
    available_modes = [
        "random", "classic", "foolish", "mad", "lycan", "villagergame",
        "drunkfire", "huntergame", "valentines", "mudgame", "masked"
    ]
    
    if gamemode.lower() not in available_modes:
        embed = create_error_embed(
            "Invalid Gamemode",
            f"Available modes: {', '.join(available_modes)}"
        )
        await ctx.send(embed=embed)
        return
    
    try:
        old_mode = session.gamemode
        session.gamemode = gamemode.lower()
        
        embed = create_success_embed(
            "🎮 Gamemode Changed",
            f"Gamemode changed from **{old_mode or 'none'}** to **{gamemode.lower()}**"
        )
        await ctx.send(embed=embed)
        logger.info(f"Admin {ctx.author.display_name} changed gamemode to {gamemode.lower()}")
        
    except Exception as e:
        embed = create_error_embed("Change Failed", f"Failed to change gamemode: {str(e)}")
        await ctx.send(embed=embed)

@command("frole", PermissionLevel.ADMIN, "Force change player role", aliases=["fsetrole"])
async def frole_command(ctx: commands.Context, player_name: str = None, role_name: str = None):
    """Force change player role (admin only)"""
    if not player_name or not role_name:
        embed = create_error_embed(
            "Missing Parameters",
            f"Usage: `{config.prefix}frole <player> <role>`"
        )
        await ctx.send(embed=embed)
        return
    
    session = get_session()
    
    if not session.playing:
        embed = create_error_embed("No Game", "No game is currently running!")
        await ctx.send(embed=embed)
        return
    
    # Find player
    player = session.get_player_by_nick(player_name)
    if not player:
        embed = create_error_embed("Player Not Found", f"Player '{player_name}' not found in the game!")
        await ctx.send(embed=embed)
        return
    
    try:
        old_role = player.role.name if player.role else "None"
        
        # TODO: Implement proper role assignment logic
        # This is a simplified version
        player.role_name = role_name
        
        embed = create_success_embed(
            "🎭 Role Changed",
            f"**{player.nick}**'s role changed from **{old_role}** to **{role_name}**"
        )
        await ctx.send(embed=embed)
        logger.info(f"Admin {ctx.author.display_name} changed {player.nick}'s role to {role_name}")
        
    except Exception as e:
        embed = create_error_embed("Change Failed", f"Failed to change role: {str(e)}")
        await ctx.send(embed=embed)

@command("ftemplate", PermissionLevel.ADMIN, "Manage player templates", aliases=["ftmpl"])
async def ftemplate_command(ctx: commands.Context, action: str = None, template: str = None, *targets):
    """Manage player templates (admin only)"""
    if not action:
        embed = create_error_embed(
            "Missing Action",
            f"Usage: `{config.prefix}ftemplate <add/remove/list> [template] [players...]`"
        )
        await ctx.send(embed=embed)
        return
    
    session = get_session()
    
    if action.lower() == "list":
        # List available templates
        templates = ["cursed", "blessed", "lycanthrope", "gunner", "sharpshooter"]
        embed = create_embed("📋 Available Templates")
        embed.add_field(
            name="Templates",
            value="\n".join(f"• {tmpl}" for tmpl in templates),
            inline=False
        )
        await ctx.send(embed=embed)
        return
    
    if not template:
        embed = create_error_embed("Missing Template", "Please specify a template name.")
        await ctx.send(embed=embed)
        return
    
    if not targets:
        embed = create_error_embed("Missing Targets", "Please specify target players.")
        await ctx.send(embed=embed)
        return
    
    if action.lower() == "add":
        # Add template to players
        success_players = []
        failed_players = []
        
        for target in targets:
            player = session.get_player_by_nick(target)
            if player:
                # TODO: Implement template application logic
                success_players.append(player.nick)
                logger.info(f"Admin {ctx.author.display_name} added {template} template to {player.nick}")
            else:
                failed_players.append(target)
        
        embed = create_embed("📋 Template Application Results")
        if success_players:
            embed.add_field(
                name="✅ Template Added",
                value="\n".join(f"• {player}" for player in success_players),
                inline=False
            )
        if failed_players:
            embed.add_field(
                name="❌ Failed",
                value="\n".join(f"• {player} (not found)" for player in failed_players),
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    elif action.lower() == "remove":
        # Remove template from players
        embed = create_success_embed(
            "📋 Template Removed",
            f"Removed **{template}** template from specified players."
        )
        await ctx.send(embed=embed)
        logger.info(f"Admin {ctx.author.display_name} removed {template} template")
    
    else:
        embed = create_error_embed("Invalid Action", "Use 'add', 'remove', or 'list'.")
        await ctx.send(embed=embed)

@command("fstasis", PermissionLevel.ADMIN, "Force manage player stasis", aliases=["fstase"])
async def fstasis_command(ctx: commands.Context, action: str = None, *players):
    """Force manage stasis (admin only)"""
    if not action:
        embed = create_error_embed(
            "Missing Action",
            f"Usage: `{config.prefix}fstasis <add/remove/list> [players...]`"
        )
        await ctx.send(embed=embed)
        return
    
    if action.lower() == "list":
        # List players in stasis
        persistent_data = get_persistent_data()
        stasis_list = persistent_data.get("stasis", [])
        
        if not stasis_list:
            embed = create_embed("📋 Stasis List", "No players are currently in stasis.")
        else:
            embed = create_embed("📋 Players in Stasis")
            embed.add_field(
                name="Stasis List",
                value="\n".join(f"• {player}" for player in stasis_list),
                inline=False
            )
        
        await ctx.send(embed=embed)
        return
    
    if not players:
        embed = create_error_embed("Missing Players", "Please specify player names.")
        await ctx.send(embed=embed)
        return
    
    persistent_data = get_persistent_data()
    stasis_list = persistent_data.get("stasis", [])
    
    if action.lower() == "add":
        added_players = []
        for player in players:
            if player not in stasis_list:
                stasis_list.append(player)
                added_players.append(player)
        
        persistent_data["stasis"] = stasis_list
        
        embed = create_success_embed(
            "📋 Stasis Added",
            f"Added {len(added_players)} players to stasis: {', '.join(added_players)}"
        )
        await ctx.send(embed=embed)
        logger.info(f"Admin {ctx.author.display_name} added players to stasis: {added_players}")
    
    elif action.lower() == "remove":
        removed_players = []
        for player in players:
            if player in stasis_list:
                stasis_list.remove(player)
                removed_players.append(player)
        
        persistent_data["stasis"] = stasis_list
        
        embed = create_success_embed(
            "📋 Stasis Removed",
            f"Removed {len(removed_players)} players from stasis: {', '.join(removed_players)}"
        )
        await ctx.send(embed=embed)
        logger.info(f"Admin {ctx.author.display_name} removed players from stasis: {removed_players}")
    
    else:
        embed = create_error_embed("Invalid Action", "Use 'add', 'remove', or 'list'.")
        await ctx.send(embed=embed)

@command("frevive", PermissionLevel.ADMIN, "Revive a dead player", aliases=["resurrect"])
async def frevive_command(ctx: commands.Context, player_name: str = None):
    """Revive dead player (admin only)"""
    if not player_name:
        embed = create_error_embed(
            "Missing Player",
            f"Usage: `{config.prefix}frevive <player>`"
        )
        await ctx.send(embed=embed)
        return
    
    session = get_session()
    
    if not session.playing:
        embed = create_error_embed("No Game", "No game is currently running!")
        await ctx.send(embed=embed)
        return
    
    # Find player
    player = session.get_player_by_nick(player_name)
    if not player:
        embed = create_error_embed("Player Not Found", f"Player '{player_name}' not found in the game!")
        await ctx.send(embed=embed)
        return
    
    # Check if player is actually dead
    alive_players = session.get_alive_players()
    if player in alive_players:
        embed = create_error_embed("Already Alive", f"**{player.nick}** is already alive!")
        await ctx.send(embed=embed)
        return
    
    try:
        # TODO: Implement actual revival logic
        # For now, just add back to alive players list
        
        embed = create_success_embed(
            "⚰️ Player Revived",
            f"**{player.nick}** has been brought back to life by admin powers!"
        )
        await ctx.send(embed=embed)
        logger.info(f"Admin {ctx.author.display_name} revived {player.nick}")
        
    except Exception as e:
        embed = create_error_embed("Revival Failed", f"Failed to revive player: {str(e)}")
        await ctx.send(embed=embed)
