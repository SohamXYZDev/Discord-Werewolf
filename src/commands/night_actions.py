"""
Night action commands for Discord Werewolf Bot
"""

import discord
from discord.ext import commands
from src.commands.base import command, PermissionLevel
from src.core import get_config, get_logger
from src.utils.helpers import create_embed, create_error_embed, create_success_embed, send_dm
from src.game.state import get_session
from src.game.roles import Team

config = get_config()
logger = get_logger()

@command("kill", PermissionLevel.PLAYING, "Wolf kill command", pm_only=True, game_only=True)
async def kill_command(ctx: commands.Context, target_name: str = ""):
    """Wolf kill command (PM only)"""
    if not target_name:
        await ctx.send("❌ Please specify a target: `kill <player>`")
        return
    
    session = get_session()
    player = session.players.get(ctx.author.id)
    
    if not player or not player.alive:
        await ctx.send("❌ You are not alive in the game.")
        return
    
    # Check if player is a wolf
    if not player.role or player.role.info.team != Team.WOLF:
        await ctx.send("❌ Only wolves can use this command.")
        return
    
    # Check if it's night phase
    if hasattr(session, 'game_manager') and session.game_manager.phase.value != "night":
        await ctx.send("❌ You can only kill during the night phase.")
        return
    
    # Find target player
    target_player = session.get_player_by_name(target_name)
    if not target_player:
        await ctx.send(f"❌ Player '{target_name}' not found.")
        return
    
    if not target_player.alive:
        await ctx.send("❌ You cannot target a dead player.")
        return
    
    if target_player.user_id == ctx.author.id:
        await ctx.send("❌ You cannot target yourself.")
        return
    
    # Check if target is a fellow wolf
    if target_player.role and target_player.role.info.team == Team.WOLF:
        await ctx.send("❌ You cannot kill a fellow wolf.")
        return
    
    # Submit the kill action
    if hasattr(session, 'game_manager'):
        action_data = {"action": "kill", "target": target_player.user_id}
        success, message = await session.game_manager.process_night_action(ctx.author.id, action_data, session)
        
        if success:
            embed = create_success_embed("Kill Target Set", f"You have chosen to kill **{target_player.name}** tonight.")
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ {message}")
    else:
        await ctx.send("❌ Game manager not available.")

@command("see", PermissionLevel.PLAYING, "Seer investigation command", pm_only=True, game_only=True)
async def see_command(ctx: commands.Context, target_name: str = ""):
    """Seer investigation command (PM only)"""
    if not target_name:
        await ctx.send("❌ Please specify a target: `see <player>`")
        return
    
    session = get_session()
    player = session.players.get(ctx.author.id)
    
    if not player or not player.alive:
        await ctx.send("❌ You are not alive in the game.")
        return
    
    # Check if player is a seer
    if not player.role or player.role.info.name != "Seer":
        await ctx.send("❌ Only seers can use this command.")
        return
    
    # Check if it's night phase
    if hasattr(session, 'game_manager') and session.game_manager.phase.value != "night":
        await ctx.send("❌ You can only investigate during the night phase.")
        return
    
    # Find target player
    target_player = session.get_player_by_name(target_name)
    if not target_player:
        await ctx.send(f"❌ Player '{target_name}' not found.")
        return
    
    if not target_player.alive:
        await ctx.send("❌ You cannot investigate a dead player.")
        return
    
    if target_player.user_id == ctx.author.id:
        await ctx.send("❌ You cannot investigate yourself.")
        return
    
    # Submit the investigation action
    if hasattr(session, 'game_manager'):
        action_data = {"action": "see", "target": target_player.user_id}
        success, message = await session.game_manager.process_night_action(ctx.author.id, action_data, session)
        
        if success:
            embed = create_success_embed("Investigation Target Set", f"You will investigate **{target_player.name}** tonight.")
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ {message}")
    else:
        await ctx.send("❌ Game manager not available.")

@command("detect", PermissionLevel.PLAYING, "Detective investigation command", pm_only=True, game_only=True)
async def detect_command(ctx: commands.Context, target_name: str = ""):
    """Detective investigation command (PM only)"""
    if not target_name:
        await ctx.send("❌ Please specify a target: `detect <player>`")
        return
    
    session = get_session()
    player = session.players.get(ctx.author.id)
    
    if not player or not player.alive:
        await ctx.send("❌ You are not alive in the game.")
        return
    
    # Check if player is a detective
    if not player.role or player.role.info.name != "Detective":
        await ctx.send("❌ Only detectives can use this command.")
        return
    
    # Check if it's night phase
    if hasattr(session, 'game_manager') and session.game_manager.phase.value != "night":
        await ctx.send("❌ You can only investigate during the night phase.")
        return
    
    # Find target player
    target_player = session.get_player_by_name(target_name)
    if not target_player:
        await ctx.send(f"❌ Player '{target_name}' not found.")
        return
    
    if not target_player.alive:
        await ctx.send("❌ You cannot investigate a dead player.")
        return
    
    if target_player.user_id == ctx.author.id:
        await ctx.send("❌ You cannot investigate yourself.")
        return
    
    # Submit the investigation action
    if hasattr(session, 'game_manager'):
        action_data = {"action": "detect", "target": target_player.user_id}
        success, message = await session.game_manager.process_night_action(ctx.author.id, action_data, session)
        
        if success:
            embed = create_success_embed("Investigation Target Set", f"You will investigate **{target_player.name}** tonight.")
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ {message}")
    else:
        await ctx.send("❌ Game manager not available.")

@command("protect", PermissionLevel.PLAYING, "Guardian Angel protection command", pm_only=True, game_only=True)
async def protect_command(ctx: commands.Context, target_name: str = ""):
    """Guardian Angel protection command (PM only)"""
    if not target_name:
        await ctx.send("❌ Please specify a target: `protect <player>`")
        return
    
    session = get_session()
    player = session.players.get(ctx.author.id)
    
    if not player or not player.alive:
        await ctx.send("❌ You are not alive in the game.")
        return
    
    # Check if player is a guardian angel
    if not player.role or player.role.info.name != "Guardian Angel":
        await ctx.send("❌ Only guardian angels can use this command.")
        return
    
    # Check if it's night phase
    if hasattr(session, 'game_manager') and session.game_manager.phase.value != "night":
        await ctx.send("❌ You can only protect during the night phase.")
        return
    
    # Find target player
    target_player = session.get_player_by_name(target_name)
    if not target_player:
        await ctx.send(f"❌ Player '{target_name}' not found.")
        return
    
    if not target_player.alive:
        await ctx.send("❌ You cannot protect a dead player.")
        return
    
    # Check if they protected this player last night
    if hasattr(player.role, 'last_protected') and player.role.last_protected == target_player.user_id:
        await ctx.send("❌ You cannot protect the same player on consecutive nights.")
        return
    
    # Submit the protection action
    if hasattr(session, 'game_manager'):
        action_data = {"action": "protect", "target": target_player.user_id}
        success, message = await session.game_manager.process_night_action(ctx.author.id, action_data, session)
        
        if success:
            embed = create_success_embed("Protection Target Set", f"You will protect **{target_player.name}** tonight.")
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ {message}")
    else:
        await ctx.send("❌ Game manager not available.")

@command("pass", PermissionLevel.PLAYING, "Pass on night action", pm_only=True, game_only=True)
async def pass_command(ctx: commands.Context):
    """Pass on using night action (PM only)"""
    session = get_session()
    player = session.players.get(ctx.author.id)
    
    if not player or not player.alive:
        await ctx.send("❌ You are not alive in the game.")
        return
    
    # Check if it's night phase
    if hasattr(session, 'game_manager') and session.game_manager.phase.value != "night":
        await ctx.send("❌ You can only pass during the night phase.")
        return
    
    # Check if player has a night action
    if not player.role or not player.role.can_act("night"):
        await ctx.send("❌ You don't have a night action to pass on.")
        return
    
    # Submit the pass action
    if hasattr(session, 'game_manager'):
        action_data = {"action": "pass"}
        success, message = await session.game_manager.process_night_action(ctx.author.id, action_data, session)
        
        if success:
            embed = create_success_embed("Action Passed", "You have chosen not to use your ability tonight.")
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"❌ {message}")
    else:
        await ctx.send("❌ Game manager not available.")

@command("myrole", PermissionLevel.PLAYING, "Check your role", pm_only=True, game_only=True)
async def myrole_command(ctx: commands.Context):
    """Check your role information (PM only)"""
    session = get_session()
    player = session.players.get(ctx.author.id)
    
    if not player:
        await ctx.send("❌ You are not in the game.")
        return
    
    if not player.role:
        await ctx.send("❌ You don't have a role assigned yet.")
        return
    
    role = player.role
    embed = create_embed(f"Your Role: {role.info.name}")
    
    embed.add_field(name="Team", value=role.info.team.value.title(), inline=True)
    embed.add_field(name="Status", value="Alive" if player.alive else "Dead", inline=True)
    embed.add_field(name="Description", value=role.info.description, inline=False)
    
    if role.info.night_action:
        embed.add_field(
            name="Night Action",
            value="You have a night action available." if role.can_act("night") else "You have already used your action.",
            inline=False
        )
    
    # Add team-specific information
    if role.info.team == Team.WOLF:
        # Show other wolves
        wolves = []
        for other_player in session.players.values():
            if (other_player.user_id != player.user_id and 
                other_player.role and 
                other_player.role.info.team == Team.WOLF and
                other_player.alive):
                wolves.append(other_player.name)
        
        if wolves:
            embed.add_field(name="Fellow Wolves", value="\n".join(wolves), inline=False)
        else:
            embed.add_field(name="Fellow Wolves", value="None alive", inline=False)
    
    await ctx.send(embed=embed)
