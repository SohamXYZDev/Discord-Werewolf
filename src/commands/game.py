"""
Game-related commands for Discord Werewolf Bot
Enhanced with comprehensive game state integration
"""

import discord
from discord.ext import commands
import random
from datetime import datetime, timedelta
from src.commands.base import command, PermissionLevel
from src.core import get_config, get_logger
from src.utils.helpers import (create_embed, create_error_embed, create_success_embed, 
                              format_player_list, send_to_game_channel, add_player_role, 
                              remove_player_role, get_guild, get_rate_limiter)
from src.game.state import game_session, GamePhase
from src.game.phase_manager import PhaseManager

# Initialize configuration if not already done
try:
    config = get_config()
    logger = get_logger()
except RuntimeError:
    # Configuration not initialized yet, import the initializer
    from src.core import initialize_config, initialize_logger
    config = initialize_config()
    logger = initialize_logger()

# Global phase manager instance (will be initialized when bot starts)
phase_manager = None

def initialize_phase_manager(bot):
    """Initialize the phase manager with bot reference"""
    global phase_manager
    phase_manager = PhaseManager(bot, game_session)

@command("join", PermissionLevel.EVERYONE, "Join the werewolf game", aliases=["j"])
async def join_command(ctx: commands.Context, gamemode: str = ""):
    """Join the werewolf game"""
    # Check if game is already running
    if game_session.playing:
        embed = create_error_embed(
            "Game in Progress",
            "A game is already running! Wait for it to finish before joining."
        )
        await ctx.send(embed=embed)
        return
    
    # Check if user is already in the game
    if ctx.author.id in game_session.players:
        embed = create_error_embed(
            "Already Joined",
            f"{ctx.author.mention}, you're already in the game!"
        )
        await ctx.send(embed=embed)
        return
    
    # Check lobby capacity
    if len(game_session.players) >= 24:  # Max players
        embed = create_error_embed(
            "Lobby Full",
            "The lobby is full! Maximum 24 players allowed."
        )
        await ctx.send(embed=embed)
        return
    
    # Add player to the game
    success = game_session.add_player(ctx.author)
    if not success:
        embed = create_error_embed(
            "Join Failed",
            "Failed to join the game. Please try again."
        )
        await ctx.send(embed=embed)
        return
    
    # Add player role
    await add_player_role(ctx.author)
    
    # Handle gamemode vote if specified
    if gamemode and gamemode in ["default", "foolish", "charming", "chaos", "classic"]:
        if gamemode not in game_session.gamemode_votes:
            game_session.gamemode_votes[gamemode] = set()
        game_session.gamemode_votes[gamemode].add(ctx.author.id)
    
    # Create join announcement
    embed = create_success_embed(
        "Player Joined!",
        f"{ctx.author.mention} has joined the game!"
    )
    
    player_count = len(game_session.players)
    embed.add_field(
        name="Players",
        value=f"{player_count}/24 players",
        inline=True
    )
    
    can_start, reason = game_session.can_start_game()
    if can_start:
        embed.add_field(
            name="Ready to Start",
            value="Use `!start` to begin the game!",
            inline=True
        )
    else:
        embed.add_field(
            name="Status",
            value=reason,
            inline=True
        )
    
    # Show gamemode votes if any
    if game_session.gamemode_votes:
        gamemode_info = []
        for mode, voters in game_session.gamemode_votes.items():
            gamemode_info.append(f"{mode}: {len(voters)} votes")
        
        embed.add_field(
            name="Gamemode Votes",
            value="\\n".join(gamemode_info),
            inline=False
        )
    
    await ctx.send(embed=embed)
    logger.info(f"{ctx.author.display_name} joined the game")

@command("leave", PermissionLevel.EVERYONE, "Leave the werewolf game", aliases=["l", "quit", "q"])
async def leave_command(ctx: commands.Context):
    """Leave the werewolf game"""
    if ctx.author.id not in game_session.players:
        embed = create_error_embed(
            "Not in Game",
            "You're not currently in a game!"
        )
        await ctx.send(embed=embed)
        return
    
    # Remove player
    success = game_session.remove_player(ctx.author.id)
    if not success:
        embed = create_error_embed(
            "Leave Failed",
            "Failed to leave the game. Please try again."
        )
        await ctx.send(embed=embed)
        return
    
    # Remove player role
    await remove_player_role(ctx.author)
    
    # Create leave announcement
    if game_session.playing:
        embed = create_embed(
            title="Player Left During Game",
            description=f"{ctx.author.mention} has left the game and been killed!",
            color=discord.Color.red()
        )
        embed.add_field(
            name="Penalty",
            value="Leaving during a game results in stasis penalties.",
            inline=False
        )
    else:
        embed = create_embed(
            title="Player Left",
            description=f"{ctx.author.mention} has left the game.",
            color=discord.Color.orange()
        )
    
    player_count = len(game_session.players)
    embed.add_field(
        name="Players Remaining",
        value=f"{player_count}/24 players",
        inline=True
    )
    
    await ctx.send(embed=embed)
    logger.info(f"{ctx.author.display_name} left the game")

@command("start", PermissionLevel.EVERYONE, "Start the werewolf game", aliases=["begin"])
async def start_command(ctx: commands.Context, gamemode: str = ""):
    """Start the werewolf game"""
    # Check if game can be started
    can_start, reason = game_session.can_start_game()
    if not can_start:
        embed = create_error_embed("Cannot Start Game", reason)
        await ctx.send(embed=embed)
        return
    
    # Check if user is in the game
    if ctx.author.id not in game_session.players:
        embed = create_error_embed(
            "Not in Game",
            "You must be in the game to start it!"
        )
        await ctx.send(embed=embed)
        return
    
    # Determine gamemode
    if gamemode:
        selected_gamemode = gamemode
    elif game_session.gamemode_votes:
        # Use most voted gamemode
        max_votes = 0
        selected_gamemode = "default"
        for mode, voters in game_session.gamemode_votes.items():
            if len(voters) > max_votes:
                max_votes = len(voters)
                selected_gamemode = mode
    else:
        selected_gamemode = "default"
    
    # Start the game
    success = game_session.start_game(selected_gamemode)
    if not success:
        embed = create_error_embed(
            "Start Failed",
            "Failed to start the game. Please try again."
        )
        await ctx.send(embed=embed)
        return
    
    # Send game start announcement
    embed = create_success_embed(
        "🎮 Game Started!",
        f"The werewolf game has begun with **{len(game_session.players)}** players using **{selected_gamemode}** gamemode!"
    )
    
    embed.add_field(
        name="Players",
        value="\\n".join([f"• {p.name}" for p in game_session.players.values()]),
        inline=False
    )
    
    embed.add_field(
        name="What's Next",
        value="Roles have been assigned via DM. The game begins with Night 1.",
        inline=False
    )
    
    await ctx.send(embed=embed)
    
    # Start the game flow
    if phase_manager:
        await phase_manager.start_game_flow()
    
    logger.info(f"Game started by {ctx.author.display_name} with {len(game_session.players)} players")

@command("vote", PermissionLevel.EVERYONE, "Vote to lynch a player during day phase", aliases=["lynch"])
async def vote_command(ctx: commands.Context, *, target: str = ""):
    """Vote to lynch a player"""
    if not game_session.playing:
        embed = create_error_embed("No Game", "No game is currently running!")
        await ctx.send(embed=embed)
        return
    
    if game_session.phase != GamePhase.DAY:
        embed = create_error_embed("Wrong Phase", "You can only vote during the day phase!")
        await ctx.send(embed=embed)
        return
    
    if ctx.author.id not in game_session.players:
        embed = create_error_embed("Not Playing", "You're not in the current game!")
        await ctx.send(embed=embed)
        return
    
    voter = game_session.players[ctx.author.id]
    if not voter.can_vote():
        embed = create_error_embed("Cannot Vote", "You cannot vote right now!")
        await ctx.send(embed=embed)
        return
    
    if not target:
        embed = create_error_embed("No Target", "You must specify who to vote for!")
        await ctx.send(embed=embed)
        return
    
    # Find target player
    target_player = game_session.get_player_by_name(target)
    if not target_player:
        embed = create_error_embed("Player Not Found", f"Could not find player '{target}'")
        await ctx.send(embed=embed)
        return
    
    if not target_player.alive:
        embed = create_error_embed("Invalid Target", "You cannot vote for a dead player!")
        await ctx.send(embed=embed)
        return
    
    # Cast vote
    success = game_session.cast_vote(ctx.author.id, target_player.user_id)
    if not success:
        embed = create_error_embed("Vote Failed", "Failed to cast vote. Please try again.")
        await ctx.send(embed=embed)
        return
    
    # Announce vote
    embed = create_embed(
        title="Vote Cast",
        description=f"{ctx.author.mention} voted to lynch **{target_player.name}**",
        color=discord.Color.blue()
    )
    
    # Show current vote counts
    if game_session.vote_counts:
        vote_info = []
        for player_id, count in sorted(game_session.vote_counts.items(), key=lambda x: x[1], reverse=True):
            player_name = game_session.players[player_id].name
            vote_info.append(f"{player_name}: {count} votes")
        
        embed.add_field(
            name="Current Votes",
            value="\\n".join(vote_info),
            inline=False
        )
    
    await ctx.send(embed=embed)

@command("retract", PermissionLevel.EVERYONE, "Retract your vote", aliases=["unvote"])
async def retract_command(ctx: commands.Context):
    """Retract your vote"""
    if not game_session.playing or game_session.phase != GamePhase.DAY:
        embed = create_error_embed("Wrong Phase", "You can only retract votes during the day phase!")
        await ctx.send(embed=embed)
        return
    
    if ctx.author.id not in game_session.players:
        embed = create_error_embed("Not Playing", "You're not in the current game!")
        await ctx.send(embed=embed)
        return
    
    success = game_session.retract_vote(ctx.author.id)
    if not success:
        embed = create_error_embed("No Vote", "You don't have a vote to retract!")
        await ctx.send(embed=embed)
        return
    
    embed = create_success_embed(
        "Vote Retracted",
        f"{ctx.author.mention} retracted their vote."
    )
    await ctx.send(embed=embed)

@command("abstain", PermissionLevel.EVERYONE, "Abstain from voting", aliases=["abs", "nolynch", "nl"])
async def abstain_command(ctx: commands.Context):
    """Abstain from voting"""
    if not game_session.playing or game_session.phase != GamePhase.DAY:
        embed = create_error_embed("Wrong Phase", "You can only abstain during the day phase!")
        await ctx.send(embed=embed)
        return
    
    if ctx.author.id not in game_session.players:
        embed = create_error_embed("Not Playing", "You're not in the current game!")
        await ctx.send(embed=embed)
        return
    
    success = game_session.abstain_vote(ctx.author.id)
    if not success:
        embed = create_error_embed("Cannot Abstain", "You cannot abstain on the first day!")
        await ctx.send(embed=embed)
        return
    
    embed = create_success_embed(
        "Abstained",
        f"{ctx.author.mention} abstained from voting."
    )
    await ctx.send(embed=embed)

@command("votes", PermissionLevel.EVERYONE, "Show current vote counts", aliases=["votecount", "vc"])
async def votes_command(ctx: commands.Context):
    """Show current vote counts"""
    if not game_session.playing:
        embed = create_error_embed("No Game", "No game is currently running!")
        await ctx.send(embed=embed)
        return
    
    if game_session.phase != GamePhase.DAY:
        embed = create_error_embed("Wrong Phase", "Vote counts are only shown during day phase!")
        await ctx.send(embed=embed)
        return
    
    embed = create_embed(
        title=f"📊 Vote Count - Day {game_session.day_count}",
        color=discord.Color.blue()
    )
    
    if game_session.vote_counts:
        vote_info = []
        for player_id, count in sorted(game_session.vote_counts.items(), key=lambda x: x[1], reverse=True):
            player_name = game_session.players[player_id].name
            vote_info.append(f"**{player_name}**: {count} votes")
        
        embed.add_field(
            name="Current Votes",
            value="\\n".join(vote_info),
            inline=False
        )
    else:
        embed.add_field(
            name="Current Votes",
            value="No votes cast yet.",
            inline=False
        )
    
    # Show abstainers
    if game_session.abstain_votes:
        abstainers = [game_session.players[p_id].name for p_id in game_session.abstain_votes]
        embed.add_field(
            name="Abstaining",
            value=", ".join(abstainers),
            inline=False
        )
    
    # Show who hasn't voted
    living_players = game_session.get_living_players()
    voted_players = set(game_session.votes.keys()) | game_session.abstain_votes
    not_voted = [p.name for p in living_players if p.user_id not in voted_players and p.can_vote()]
    
    if not_voted:
        embed.add_field(
            name="Haven't Voted",
            value=", ".join(not_voted),
            inline=False
        )
    
    await ctx.send(embed=embed)

@command("players", PermissionLevel.EVERYONE, "Show current players", aliases=["status", "stats"])
async def players_command(ctx: commands.Context):
    """Show current players and game status"""
    if not game_session.players:
        embed = create_embed(
            title="No Players",
            description="No one has joined the game yet. Use `!join` to start a lobby!",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        return
    
    if game_session.playing:
        embed = create_embed(
            title=f"🎮 Game Status - {game_session.phase.value.title()} {game_session.day_count if game_session.phase == GamePhase.DAY else game_session.night_count}",
            color=discord.Color.green()
        )
        
        # Living players
        living = game_session.get_living_players()
        if living:
            embed.add_field(
                name=f"Living Players ({len(living)})",
                value="\\n".join([f"❤️ {p.name}" for p in living]),
                inline=True
            )
        
        # Dead players
        dead = game_session.get_dead_players()
        if dead:
            embed.add_field(
                name=f"Dead Players ({len(dead)})",
                value="\\n".join([f"💀 {p.name}" for p in dead]),
                inline=True
            )
    else:
        embed = create_embed(
            title="🏛️ Game Lobby",
            description=f"Players waiting to start ({len(game_session.players)}/24)",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Players",
            value="\\n".join([f"• {p.name}" for p in game_session.players.values()]),
            inline=False
        )
        
        can_start, reason = game_session.can_start_game()
        embed.add_field(
            name="Status",
            value=reason,
            inline=False
        )
    
    await ctx.send(embed=embed)

# Night action commands (called via DM)
@command("kill", PermissionLevel.EVERYONE, "Submit kill action", pm_only=True)
async def kill_command(ctx: commands.Context, *, target: str = ""):
    """Submit a kill action (Werewolf, Hunter, Serial Killer)"""
    await _handle_night_action(ctx, "kill", target)

@command("see", PermissionLevel.EVERYONE, "Submit investigation action", pm_only=True)
async def see_command(ctx: commands.Context, *, target: str = ""):
    """Submit an investigation action (Seer, Oracle, Augur)"""
    await _handle_night_action(ctx, "see", target)

@command("guard", PermissionLevel.EVERYONE, "Submit protection action", pm_only=True)
async def guard_command(ctx: commands.Context, *, target: str = ""):
    """Submit a protection action (Guardian Angel, Bodyguard)"""
    await _handle_night_action(ctx, "guard", target)

@command("visit", PermissionLevel.EVERYONE, "Submit visit action", pm_only=True)
async def visit_command(ctx: commands.Context, *, target: str = ""):
    """Submit a visit action (Harlot, Succubus)"""
    await _handle_night_action(ctx, "visit", target)

@command("pass", PermissionLevel.EVERYONE, "Skip your night action", pm_only=True)
async def pass_command(ctx: commands.Context):
    """Skip your night action"""
    await _handle_night_action(ctx, "pass", None)

async def _handle_night_action(ctx: commands.Context, action: str, target: str):
    """Handle night action submission"""
    if not game_session.playing or game_session.phase != GamePhase.NIGHT:
        embed = create_error_embed("Wrong Phase", "Night actions can only be submitted during the night phase!")
        await ctx.send(embed=embed)
        return
    
    if ctx.author.id not in game_session.players:
        embed = create_error_embed("Not Playing", "You're not in the current game!")
        await ctx.send(embed=embed)
        return
    
    player = game_session.players[ctx.author.id]
    if not player.can_act("night"):
        embed = create_error_embed("Cannot Act", "You cannot perform night actions!")
        await ctx.send(embed=embed)
        return
    
    target_id = None
    if target and action != "pass":
        target_player = game_session.get_player_by_name(target)
        if not target_player:
            embed = create_error_embed("Player Not Found", f"Could not find player '{target}'")
            await ctx.send(embed=embed)
            return
        target_id = target_player.user_id
    
    # Submit the action
    success = game_session.submit_night_action(ctx.author.id, action, target_id)
    if not success:
        embed = create_error_embed("Action Failed", "Failed to submit night action!")
        await ctx.send(embed=embed)
        return
    
    if action == "pass":
        embed = create_success_embed(
            "Action Submitted",
            "You chose to pass your night action."
        )
    else:
        target_name = game_session.players[target_id].name if target_id else "Unknown"
        embed = create_success_embed(
            "Action Submitted",
            f"You submitted: **{action}** {target_name}"
        )
    
    await ctx.send(embed=embed)

@command("myrole", PermissionLevel.EVERYONE, "View your role information", pm_only=True)
async def myrole_command(ctx: commands.Context):
    """View your role information"""
    if not game_session.playing:
        embed = create_error_embed("No Game", "No game is currently running!")
        await ctx.send(embed=embed)
        return
    
    if ctx.author.id not in game_session.players:
        embed = create_error_embed("Not Playing", "You're not in the current game!")
        await ctx.send(embed=embed)
        return
    
    player = game_session.players[ctx.author.id]
    if not player.role:
        embed = create_error_embed("No Role", "You don't have a role assigned yet!")
        await ctx.send(embed=embed)
        return
    
    role = player.role
    embed = create_embed(
        title=f"🎭 Your Role: {role.name}",
        description=role.description,
        color=discord.Color.purple()
    )
    
    # Add team information
    team_colors = {
        "village": "🏡 Village Team",
        "werewolf": "🐺 Werewolf Team", 
        "neutral": "⚖️ Neutral"
    }
    embed.add_field(
        name="Team",
        value=team_colors.get(role.team.value, role.team.value),
        inline=True
    )
    
    embed.add_field(
        name="Win Condition",
        value=role.win_condition.value,
        inline=True
    )
    
    # Add ability information
    abilities = []
    if role.info.night_action:
        abilities.append("Night Action")
    if role.info.day_action:
        abilities.append("Day Action")
    if role.info.passive_ability:
        abilities.append("Passive Ability")
    
    if abilities:
        embed.add_field(
            name="Abilities",
            value=", ".join(abilities),
            inline=True
        )
    
    await ctx.send(embed=embed)

@command("stop", PermissionLevel.MODERATOR, "Stop the current game", aliases=["end", "cancel"])
async def stop_command(ctx: commands.Context):
    """Stop the current game"""
    if not game_session.playing and not game_session.players:
        embed = create_error_embed("No Game", "No game is currently running or in lobby!")
        await ctx.send(embed=embed)
        return
    
    # End the game
    game_session.end_game("stopped")
    
    # Remove all player roles
    for player in game_session.players.values():
        await remove_player_role(player.user)
    
    embed = create_embed(
        title="🛑 Game Stopped",
        description=f"The game has been stopped by {ctx.author.mention}.",
        color=discord.Color.red()
    )
    
    await ctx.send(embed=embed)
    logger.info(f"Game stopped by {ctx.author.display_name}")

@command("kick", PermissionLevel.MODERATOR, "Kick a player from the game")
async def kick_command(ctx: commands.Context, *, target: str):
    """Kick a player from the game"""
    if not game_session.players:
        embed = create_error_embed("No Game", "No players are currently in the game!")
        await ctx.send(embed=embed)
        return
    
    # Find target player
    target_player = game_session.get_player_by_name(target)
    if not target_player:
        embed = create_error_embed("Player Not Found", f"Could not find player '{target}'")
        await ctx.send(embed=embed)
        return
    
    # Remove player
    success = game_session.remove_player(target_player.user_id)
    if not success:
        embed = create_error_embed("Kick Failed", "Failed to kick player. Please try again.")
        await ctx.send(embed=embed)
        return
    
    # Remove player role
    await remove_player_role(target_player.user)
    
    embed = create_embed(
        title="👢 Player Kicked",
        description=f"**{target_player.name}** has been kicked from the game by {ctx.author.mention}.",
        color=discord.Color.orange()
    )
    
    await ctx.send(embed=embed)
    logger.info(f"{target_player.name} kicked by {ctx.author.display_name}")

@command("replace", PermissionLevel.MODERATOR, "Replace a player with another user")
async def replace_command(ctx: commands.Context, old_player: str, new_player: discord.Member):
    """Replace a player with another user"""
    if not game_session.playing:
        embed = create_error_embed("No Game", "No game is currently running!")
        await ctx.send(embed=embed)
        return
    
    # Find old player
    old_player_obj = game_session.get_player_by_name(old_player)
    if not old_player_obj:
        embed = create_error_embed("Player Not Found", f"Could not find player '{old_player}'")
        await ctx.send(embed=embed)
        return
    
    # Check if new player is already in game
    if new_player.id in game_session.players:
        embed = create_error_embed("Already in Game", f"{new_player.mention} is already in the game!")
        await ctx.send(embed=embed)
        return
    
    # Replace player
    success = game_session.replace_player(old_player_obj.user_id, new_player)
    if not success:
        embed = create_error_embed("Replace Failed", "Failed to replace player. Please try again.")
        await ctx.send(embed=embed)
        return
    
    # Update roles
    await remove_player_role(old_player_obj.user)
    await add_player_role(new_player)
    
    embed = create_embed(
        title="🔄 Player Replaced",
        description=f"**{old_player_obj.name}** has been replaced by {new_player.mention}.",
        color=discord.Color.blue()
    )
    
    await ctx.send(embed=embed)
    logger.info(f"{old_player_obj.name} replaced by {new_player.display_name}")

@command("forcevote", PermissionLevel.MODERATOR, "Force a vote for a player")
async def forcevote_command(ctx: commands.Context, voter: str, target: str):
    """Force a vote from one player to another"""
    if not game_session.playing or game_session.phase != GamePhase.DAY:
        embed = create_error_embed("Wrong Phase", "Votes can only be forced during the day phase!")
        await ctx.send(embed=embed)
        return
    
    # Find voter and target
    voter_player = game_session.get_player_by_name(voter)
    target_player = game_session.get_player_by_name(target)
    
    if not voter_player:
        embed = create_error_embed("Voter Not Found", f"Could not find player '{voter}'")
        await ctx.send(embed=embed)
        return
    
    if not target_player:
        embed = create_error_embed("Target Not Found", f"Could not find player '{target}'")
        await ctx.send(embed=embed)
        return
    
    # Force the vote
    success = game_session.cast_vote(voter_player.user_id, target_player.user_id, forced=True)
    if not success:
        embed = create_error_embed("Force Vote Failed", "Failed to force vote. Please try again.")
        await ctx.send(embed=embed)
        return
    
    embed = create_embed(
        title="⚖️ Vote Forced",
        description=f"{ctx.author.mention} forced **{voter_player.name}** to vote for **{target_player.name}**",
        color=discord.Color.orange()
    )
    
    await ctx.send(embed=embed)

@command("roles", PermissionLevel.MODERATOR, "Show all player roles", pm_only=True)
async def roles_command(ctx: commands.Context):
    """Show all player roles (moderator only)"""
    if not game_session.playing:
        embed = create_error_embed("No Game", "No game is currently running!")
        await ctx.send(embed=embed)
        return
    
    embed = create_embed(
        title="🎭 All Player Roles",
        color=discord.Color.purple()
    )
    
    # Group players by team
    teams = {"village": [], "werewolf": [], "neutral": []}
    
    for player in game_session.players.values():
        if player.role:
            team = player.role.team.value
            status = "💀" if not player.alive else "❤️"
            teams[team].append(f"{status} **{player.name}** - {player.role.name}")
    
    # Add team fields
    team_colors = {
        "village": "🏡 Village Team",
        "werewolf": "🐺 Werewolf Team",
        "neutral": "⚖️ Neutral Players"
    }
    
    for team, title in team_colors.items():
        if teams[team]:
            embed.add_field(
                name=title,
                value="\\n".join(teams[team]),
                inline=False
            )
    
    await ctx.send(embed=embed)

# Dev/Admin commands for testing
@command("teststart", PermissionLevel.ADMIN, "Start a test game with bots")
async def teststart_command(ctx: commands.Context, player_count: int = 8):
    """Start a test game with bot players"""
    if game_session.playing:
        embed = create_error_embed("Game Running", "A game is already running!")
        await ctx.send(embed=embed)
        return
    
    # Clear existing players
    game_session.players.clear()
    
    # Add real player
    game_session.add_player(ctx.author)
    
    # Add bot players
    bot_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry", 
                "Ivy", "Jack", "Kate", "Liam", "Mia", "Noah", "Olivia", "Paul"]
    
    for i in range(min(player_count - 1, len(bot_names))):
        # Create mock user object
        bot_user = type('MockUser', (), {
            'id': 900000000 + i,
            'display_name': bot_names[i],
            'mention': f"@{bot_names[i]}"
        })()
        
        game_session.add_player(bot_user)
    
    # Start the game
    success = game_session.start_game("default")
    if success:
        embed = create_success_embed(
            "🧪 Test Game Started",
            f"Test game started with {len(game_session.players)} players!"
        )
        await ctx.send(embed=embed)
        
        if phase_manager:
            await phase_manager.start_game_flow()
    else:
        embed = create_error_embed("Start Failed", "Failed to start test game.")
        await ctx.send(embed=embed)

@command("phase", PermissionLevel.ADMIN, "Change game phase")
async def phase_command(ctx: commands.Context, new_phase: str):
    """Change the current game phase"""
    if not game_session.playing:
        embed = create_error_embed("No Game", "No game is currently running!")
        await ctx.send(embed=embed)
        return
    
    valid_phases = ["day", "night", "lobby"]
    if new_phase.lower() not in valid_phases:
        embed = create_error_embed("Invalid Phase", f"Valid phases: {', '.join(valid_phases)}")
        await ctx.send(embed=embed)
        return
    
    old_phase = game_session.phase
    
    if new_phase.lower() == "day":
        game_session.phase = GamePhase.DAY
    elif new_phase.lower() == "night":
        game_session.phase = GamePhase.NIGHT
    elif new_phase.lower() == "lobby":
        game_session.phase = GamePhase.LOBBY
    
    embed = create_embed(
        title="🔄 Phase Changed",
        description=f"Game phase changed from **{old_phase.value}** to **{game_session.phase.value}**",
        color=discord.Color.blue()
    )
    
    await ctx.send(embed=embed)

# Register all commands when module is imported
async def setup_commands(bot):
    """Setup game commands"""
    global phase_manager
    initialize_phase_manager(bot)
    logger.info("Game commands registered successfully")
    if not session.add_player(ctx.author):
        await ctx.send("❌ Failed to join the game. Please try again.")
        return
    
    # Add player role
    guild = get_guild(ctx.bot)
    if guild:
        player_role = discord.utils.get(guild.roles, name=config.players_role_name)
        if player_role:
            await add_player_role(ctx.author, player_role)
    
    # Determine if this is the first player
    if len(session.players) == 1:
        # First player - start the lobby
        embed = create_success_embed(
            "🐺 Game Lobby Created!",
            f"**{ctx.author.display_name}** started a new game!\n\n"
            f"Use `{config.prefix}join` to join the game.\n"
            f"Use `{config.prefix}start` when ready to begin.\n"
            f"Minimum players: {config.min_players}"
        )
        
        # Set bot status to idle
        activity = discord.Game(name=f"{config.prefix}join to play Werewolf!")
        await ctx.bot.change_presence(status=discord.Status.idle, activity=activity)
        
        logger.info(f"Game lobby created by {ctx.author.display_name}")
    else:
        embed = create_success_embed(
            "Player Joined!",
            f"**{ctx.author.display_name}** joined the game!\n"
            f"Players: **{len(session.players)}/{config.max_players}**"
        )
    
    # Add current players list
    players_list = format_player_list(list(session.players.values()))
    embed.add_field(name="Current Players", value=players_list, inline=False)
    
    await ctx.send(embed=embed)
    
    # If gamemode was specified, also vote for it
    if gamemode:
        # TODO: Implement gamemode voting
        await ctx.send(f"🗳️ Gamemode voting will be implemented soon! (You voted for: {gamemode})")

@command("leave", PermissionLevel.EVERYONE, "Leave the werewolf game", aliases=["quit", "q"])
async def leave_command(ctx: commands.Context, force: str = ""):
    """Leave the werewolf game"""
    session = get_session()
    persistent_data = get_persistent_data()
    
    # Check if user is in the game
    if ctx.author.id not in session.players:
        await ctx.send("❌ You're not in the game!")
        return
    
    player = session.players[ctx.author.id]
    
    # Handle leaving during an active game
    if session.playing and player.alive:
        if force != "-force":
            embed = create_embed(
                "⚠️ Confirm Leaving",
                f"Are you sure you want to quit during the game?\n"
                f"This will result in **{config.quit_game_stasis}** games of stasis.\n\n"
                f"Use `{config.prefix}leave -force` to confirm."
            )
            await ctx.send(embed=embed)
            return
        
        # Player is leaving during an active game
        session.kill_player(ctx.author.id, "quit")
        persistent_data.add_stasis(ctx.author.id, config.quit_game_stasis)
        
        embed = create_error_embed(
            "Player Quit",
            f"**{ctx.author.display_name}** has quit the game.\n"
            f"They have been given **{config.quit_game_stasis}** games of stasis."
        )
        
        # TODO: Check win conditions and continue game
        
        logger.info(f"{ctx.author.display_name} quit during active game")
    else:
        # Player is leaving the lobby
        session.remove_player(ctx.author.id)
        
        embed = create_success_embed(
            "Left Game",
            f"**{ctx.author.display_name}** left the game.\n"
            f"Players remaining: **{len(session.players)}/{config.max_players}**"
        )
        
        logger.info(f"{ctx.author.display_name} left the lobby")
    
    # Remove player role
    guild = get_guild(ctx.bot)
    if guild:
        player_role = discord.utils.get(guild.roles, name=config.players_role_name)
        if player_role:
            await remove_player_role(ctx.author, player_role)
    
    # If no players left, reset bot status
    if len(session.players) == 0:
        activity = discord.Game(name=config.playing_message)
        await ctx.bot.change_presence(status=discord.Status.online, activity=activity)
        embed.add_field(name="Lobby Empty", value="The lobby is now empty.", inline=False)
    elif not session.playing:
        # Update players list for lobby
        players_list = format_player_list(list(session.players.values()))
        embed.add_field(name="Remaining Players", value=players_list, inline=False)
    
    await ctx.send(embed=embed)

@command("players", PermissionLevel.EVERYONE, "Show current players", aliases=["list", "who"])
async def players_command(ctx: commands.Context):
    """Show current players in the game"""
    session = get_session()
    
    if not session.players:
        embed = create_embed("No Players", "No one is currently in the game.")
        embed.add_field(name="How to Join", value=f"Use `{config.prefix}join` to start a new game!", inline=False)
        await ctx.send(embed=embed)
        return
    
    embed = create_embed("🐺 Current Players")
    
    if session.playing:
        # Game is active - show alive/dead players
        alive_players = session.get_alive_players()
        dead_players = session.get_dead_players()
        
        embed.add_field(name="Game Status", value=f"Active - {session.gamemode}", inline=False)
        embed.add_field(name="Phase", value="🌙 Night" if not session.is_day else "☀️ Day", inline=True)
        embed.add_field(name="Total Players", value=str(len(session.players)), inline=True)
        
        if alive_players:
            alive_list = format_player_list(alive_players)
            embed.add_field(name=f"Alive Players ({len(alive_players)})", value=alive_list, inline=False)
        
        if dead_players:
            dead_list = format_player_list(dead_players, show_roles=True)
            embed.add_field(name=f"Dead Players ({len(dead_players)})", value=dead_list, inline=False)
    else:
        # Game is not active - show lobby
        embed.add_field(name="Lobby Status", value=f"{len(session.players)}/{config.max_players} players", inline=True)
        embed.add_field(name="Minimum to Start", value=str(config.min_players), inline=True)
        
        players_list = format_player_list(list(session.players.values()))
        embed.add_field(name="Players in Lobby", value=players_list, inline=False)
        
        if len(session.players) >= config.min_players:
            embed.add_field(name="Ready to Start!", value=f"Use `{config.prefix}start` to begin the game.", inline=False)
    
    await ctx.send(embed=embed)

@command("start", PermissionLevel.EVERYONE, "Start the werewolf game")
async def start_command(ctx: commands.Context, gamemode: str = "default"):
    """Start the werewolf game"""
    session = get_session()
    
    # Set bot and channel for integration
    session.bot = ctx.bot
    session.channel = ctx.channel
    
    # Check if game is already running
    if session.playing:
        await ctx.send("❌ A game is already in progress!")
        return
    
    # Check if user is in the game
    if ctx.author.id not in session.players:
        await ctx.send("❌ You must join the game first!")
        return
    
    # Check minimum players
    if len(session.players) < config.min_players:
        await ctx.send(f"❌ Need at least {config.min_players} players to start! Current: {len(session.players)}")
        return
    
    # Rate limit start command to prevent spam
    rate_limiter = get_rate_limiter()
    if rate_limiter.is_on_cooldown(ctx.author.id, "start", 5):
        remaining = rate_limiter.get_remaining_cooldown(ctx.author.id, "start", 5)
        await ctx.send(f"⏱️ Please wait {remaining:.1f} seconds before starting again.")
        return
    
    # Start the game
    if not session.start_game(gamemode):
        await ctx.send("❌ Failed to start the game. Please try again.")
        return
    
    # Update bot status
    activity = discord.Game(name=f"Werewolf ({len(session.players)} players)")
    await ctx.bot.change_presence(status=discord.Status.dnd, activity=activity)
    
    embed = create_success_embed(
        "🐺 Game Started!",
        f"The game has begun with **{len(session.players)}** players!\n"
        f"Mode: **{gamemode}**"
    )
    
    players_list = format_player_list(list(session.players.values()))
    embed.add_field(name="Players", value=players_list, inline=False)
    
    embed.add_field(
        name="What's Next?",
        value="Roles are being assigned and the game will begin shortly.\n"
              "Check your DMs for your role information!",
        inline=False
    )
    
    await ctx.send(embed=embed)
    
    # Start the night phase
    if hasattr(session, 'game_manager'):
        try:
            # Send role DMs to players
            for player in session.players.values():
                try:
                    user = ctx.bot.get_user(player.user_id)
                    if user:
                        role = player.role
                        embed = create_embed(f"🎭 Your Role: {role.name}")
                        embed.add_field(name="Description", value=role.description, inline=False)
                        embed.add_field(name="Team", value=role.team.value.title(), inline=True)
                        embed.add_field(name="Win Condition", value=role.win_condition.value, inline=True)
                        embed.color = 0x8B0000 if role.team.value == "werewolf" else 0x006400
                        await user.send(embed=embed)
                except Exception as e:
                    logger.error(f"Failed to send role to {player.name}: {e}")
            
            # Start night phase
            await session.game_manager.start_night_phase(session)
            
            # Announce night phase started
            embed = create_embed("🌙 Night Falls")
            embed.add_field(
                name="Night Phase Begins",
                value="Players with night actions should check their DMs.\n"
                      "The night phase will last 2 minutes.",
                inline=False
            )
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error starting night phase: {e}")
            await ctx.send("⚠️ Game started but there was an error beginning the night phase.")
    
    logger.info(f"Game started by {ctx.author.display_name} with {len(session.players)} players, mode: {gamemode}")

@command("stop", PermissionLevel.ADMIN, "Stop the current game", aliases=["end"])
async def stop_command(ctx: commands.Context, force: str = ""):
    """Stop the current game (admin only)"""
    session = get_session()
    
    if not session.playing and not session.players:
        await ctx.send("❌ No game is currently running.")
        return
    
    if force != "-force" and session.playing:
        embed = create_embed(
            "⚠️ Confirm Stop",
            "Are you sure you want to stop the current game?\n"
            f"Use `{config.prefix}stop -force` to confirm."
        )
        await ctx.send(embed=embed)
        return
    
    # Stop the game
    player_count = len(session.players)
    session.end_game()
    
    # Reset bot status
    activity = discord.Game(name=config.playing_message)
    await ctx.bot.change_presence(status=discord.Status.online, activity=activity)
    
    # Remove player roles
    guild = get_guild(ctx.bot)
    if guild:
        player_role = discord.utils.get(guild.roles, name=config.players_role_name)
        if player_role:
            for member in guild.members:
                if player_role in member.roles:
                    await remove_player_role(member, player_role)
    
    embed = create_success_embed(
        "Game Stopped",
        f"The game has been stopped by {ctx.author.mention}.\n"
        f"**{player_count}** players were removed from the game."
    )
    
    await ctx.send(embed=embed)
    logger.info(f"Game stopped by {ctx.author.display_name}")
