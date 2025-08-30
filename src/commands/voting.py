"""
Voting commands for Discord Werewolf Bot
"""

import discord
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio
from src.commands.base import command, PermissionLevel
from src.core import get_config, get_logger
from src.utils.helpers import create_embed, create_error_embed, create_success_embed, format_player_list
from src.game.state import get_session, GamePhase

config = get_config()
logger = get_logger()

@command("vote", PermissionLevel.PLAYING, "Vote to lynch a player", aliases=["lynch"], game_only=True)
async def vote_command(ctx: commands.Context, target_name: str = ""):
    """Vote to lynch a player during day phase"""
    if not target_name:
        await ctx.send("❌ Please specify a target: `vote <player>`")
        return
    
    session = get_session()
    
    # Check if player is in the game
    if ctx.author.id not in session.players:
        await ctx.send("❌ You are not in the game.")
        return
    
    player = session.players[ctx.author.id]
    if not player.alive:
        await ctx.send("❌ Dead players cannot vote.")
        return
    
    # Find target player
    target_player = session.get_player_by_name(target_name)
    if not target_player:
        await ctx.send(f"❌ Player '{target_name}' not found.")
        return
    
    if not target_player.alive:
        await ctx.send("❌ You cannot vote for a dead player.")
        return
    
    # Process the vote
    if hasattr(session, 'game_manager'):
        success, message = await session.game_manager.process_vote(ctx.author.id, target_player.user_id, session)
        
        if success:
            embed = create_success_embed("Vote Cast", message)
            
            # Show current vote status
            vote_status = session.game_manager.get_vote_status(session)
            if vote_status["vote_counts"]:
                vote_summary = []
                for player_id, vote_count in sorted(vote_status["vote_counts"].items(), key=lambda x: x[1], reverse=True):
                    voted_player = session.players[player_id]
                    vote_summary.append(f"**{voted_player.name}**: {vote_count} votes")
                
                embed.add_field(name="Current Votes", value="\n".join(vote_summary[:5]), inline=False)
            
            embed.add_field(
                name="Vote Progress",
                value=f"{vote_status['voted_count']}/{vote_status['total_alive']} players have voted\n"
                      f"Majority needed: {vote_status['majority_needed']}",
                inline=False
            )
            
            await ctx.send(embed=embed)
            # If majority reached, trigger immediate lynch processing
            vote_status = session.game_manager.get_vote_status(session)
            if vote_status.get('has_majority'):
                # Call end_day_phase asynchronously (the GameManager handles checks)
                try:
                    asyncio.create_task(session.game_manager.end_day_phase())
                except Exception:
                    logger.exception('Failed to trigger immediate lynch processing')
        else:
            await ctx.send(f"❌ {message}")
    else:
        await ctx.send("❌ Game manager not available.")

@command("abstain", PermissionLevel.PLAYING, "Abstain from voting", aliases=["abs", "nolynch"], game_only=True)
async def abstain_command(ctx: commands.Context):
    """Abstain from voting during day phase"""
    session = get_session()
    
    # Check if player is in the game
    if ctx.author.id not in session.players:
        await ctx.send("❌ You are not in the game.")
        return
    
    player = session.players[ctx.author.id]
    if not player.alive:
        await ctx.send("❌ Dead players cannot vote.")
        return
    
    # Process the abstain vote
    if hasattr(session, 'game_manager'):
        success, message = await session.game_manager.process_vote(ctx.author.id, None, session)
        
        if success:
            embed = create_success_embed("Abstain Vote Cast", message)
            
            # Show current vote status
            vote_status = session.game_manager.get_vote_status(session)
            embed.add_field(
                name="Vote Progress",
                value=f"{vote_status['voted_count']}/{vote_status['total_alive']} players have voted\n"
                      f"Abstain votes: {vote_status['abstain_count']}",
                inline=False
            )
            
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ {message}")
    else:
        await ctx.send("❌ Game manager not available.")

@command("retract", PermissionLevel.PLAYING, "Retract your vote", aliases=["unvote"], game_only=True)
async def retract_command(ctx: commands.Context):
    """Retract your current vote"""
    session = get_session()
    
    # Check if player is in the game
    if ctx.author.id not in session.players:
        await ctx.send("❌ You are not in the game.")
        return
    
    player = session.players[ctx.author.id]
    if not player.alive:
        await ctx.send("❌ Dead players cannot vote.")
        return
    
    if hasattr(session, 'game_manager'):
        game_manager = session.game_manager
        
        # Check if player has voted
        if ctx.author.id not in game_manager.votes and ctx.author.id not in game_manager.abstain_votes:
            await ctx.send("❌ You haven't cast a vote to retract.")
            return
        
        # Remove vote
        if ctx.author.id in game_manager.votes:
            target_id = game_manager.votes[ctx.author.id]
            game_manager.vote_counts[target_id] -= 1
            if game_manager.vote_counts[target_id] <= 0:
                del game_manager.vote_counts[target_id]
            del game_manager.votes[ctx.author.id]
        
        if ctx.author.id in game_manager.abstain_votes:
            game_manager.abstain_votes.remove(ctx.author.id)
        
        embed = create_success_embed("Vote Retracted", "You have retracted your vote.")
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ Game manager not available.")

@command("votes", PermissionLevel.EVERYONE, "Show current vote status", aliases=["v"], game_only=True)
async def votes_command(ctx: commands.Context):
    """Show current voting status"""
    session = get_session()
    
    if not hasattr(session, 'game_manager'):
        await ctx.send("❌ Game manager not available.")
        return
    
    game_manager = session.game_manager
    
    if game_manager.phase.value != "day":
        await ctx.send("❌ Voting is only available during the day phase.")
        return
    
    vote_status = game_manager.get_vote_status(session)
    
    embed = create_embed("🗳️ Current Vote Status")
    
    if vote_status["vote_counts"]:
        vote_summary = []
        for player_id, vote_count in sorted(vote_status["vote_counts"].items(), key=lambda x: x[1], reverse=True):
            voted_player = session.players[player_id]
            vote_summary.append(f"**{voted_player.name}**: {vote_count} votes")
        
        embed.add_field(name="Current Votes", value="\n".join(vote_summary), inline=False)
    else:
        embed.add_field(name="Current Votes", value="No votes cast yet", inline=False)
    
    embed.add_field(
        name="Vote Progress",
        value=f"**{vote_status['voted_count']}**/{vote_status['total_alive']} players have voted\n"
              f"Majority needed: **{vote_status['majority_needed']}**\n"
              f"Abstain votes: **{vote_status['abstain_count']}**",
        inline=False
    )
    
    # Show who hasn't voted yet
    alive_players = session.get_alive_players()
    not_voted = []
    for player in alive_players:
        if (player.user_id not in game_manager.votes and 
            player.user_id not in game_manager.abstain_votes):
            not_voted.append(player.name)
    
    if not_voted:
        embed.add_field(
            name="Haven't Voted",
            value=", ".join(not_voted) if len(not_voted) <= 10 else f"{len(not_voted)} players",
            inline=False
        )
    
    # Calculate time remaining
    if game_manager.phase_start_time:
        elapsed = datetime.now() - game_manager.phase_start_time
        remaining = timedelta(seconds=game_manager.day_duration) - elapsed
        
        if remaining.total_seconds() > 0:
            minutes = int(remaining.total_seconds() // 60)
            seconds = int(remaining.total_seconds() % 60)
            embed.add_field(name="Time Remaining", value=f"{minutes}m {seconds}s", inline=True)
    
    await ctx.send(embed=embed)


@command("vote", PermissionLevel.PLAYING, "Vote for gamemode or startgame", aliases=[], game_only=True)
async def vote_special(ctx: commands.Context, option: str = ""):
    """Special vote subcommand handler: currently supports `startgame` to vote to start a game in lobby."""
    # This is a lightweight subhandler for `!vote startgame`
    if option.lower() != "startgame":
        return  # let normal vote_command handle other cases

    session = get_session()
    # Ensure we're in lobby and not currently playing
    if session.playing or session.phase != GamePhase.LOBBY:
        await ctx.send("❌ You can only vote to start a game from the lobby when a game isn't already running.")
        return

    # Register the vote to start
    voters = getattr(session, 'start_votes', set())
    if ctx.author.id in voters:
        await ctx.send("❌ You already voted to start the game.")
        return

    voters.add(ctx.author.id)
    session.start_votes = voters

    total_players = len(session.players)
    votes_needed = (total_players // 2) + 1

    await ctx.send(f"✅ Vote to start registered. {len(voters)}/{votes_needed} votes.")

    if len(voters) >= votes_needed:
        # Attempt to start the game
        started = session.start_game()
        if started:
            # Attach a GameManager if missing
            if not hasattr(session, 'game_manager'):
                from src.game.phases import GameManager
                session.game_manager = GameManager(ctx.bot)
            # Kick off the async start messages based on current phase
            try:
                # session.start_game() sets the session.phase (usually NIGHT)
                if session.phase == GamePhase.NIGHT:
                    asyncio.create_task(session.game_manager._start_night_phase_messages(session))
                else:
                    asyncio.create_task(session.game_manager._start_day_phase_messages(session))
            except Exception:
                logger.exception('Failed to start game flow')
            await ctx.send("🎲 Majority reached — game starting now!")
        else:
            await ctx.send("❌ Could not start the game (check player count or configuration).")

@command("votecount", PermissionLevel.ADMIN, "Force show detailed vote count", aliases=["vc"])
async def votecount_command(ctx: commands.Context):
    """Show detailed vote count (admin only)"""
    session = get_session()
    
    if not hasattr(session, 'game_manager'):
        await ctx.send("❌ Game manager not available.")
        return
    
    game_manager = session.game_manager
    
    embed = create_embed("📊 Detailed Vote Count")
    
    if game_manager.votes:
        # Group votes by target
        vote_details = {}
        for voter_id, target_id in game_manager.votes.items():
            if target_id not in vote_details:
                vote_details[target_id] = []
            voter_name = session.players[voter_id].name
            vote_details[target_id].append(voter_name)
        
        # Show detailed breakdown
        for target_id, voters in vote_details.items():
            target_name = session.players[target_id].name
            voter_list = ", ".join(voters)
            embed.add_field(
                name=f"{target_name} ({len(voters)} votes)",
                value=voter_list,
                inline=False
            )
    
    if game_manager.abstain_votes:
        abstain_names = [session.players[pid].name for pid in game_manager.abstain_votes]
        embed.add_field(
            name=f"Abstain ({len(abstain_names)} votes)",
            value=", ".join(abstain_names),
            inline=False
        )
    
    if not game_manager.votes and not game_manager.abstain_votes:
        embed.add_field(name="No Votes", value="No votes have been cast yet.", inline=False)
    
    await ctx.send(embed=embed)
