"""
Role information commands for Discord Werewolf Bot
"""

import discord
from discord.ext import commands
from src.commands.base import command, PermissionLevel
from src.core import get_config, get_logger
from src.utils.helpers import create_embed, create_error_embed
from src.game.roles import ROLE_REGISTRY, GAMEMODE_CONFIGS

config = get_config()
logger = get_logger()

@command("role", PermissionLevel.EVERYONE, "Get information about a specific role", aliases=["r"])
async def role_command(ctx: commands.Context, role_name: str = ""):
    """Show information about a specific werewolf role"""
    if not role_name:
        # Show list of all roles organized by team
        embed = create_embed("🎭 Available Roles")
        
        village_roles = []
        wolf_roles = []
        neutral_roles = []
        
        for role_key, role_class in ROLE_REGISTRY.items():
            role_instance = role_class()
            if role_instance.team.value == "village":
                village_roles.append(role_instance.name)
            elif role_instance.team.value == "werewolf":
                wolf_roles.append(role_instance.name)
            else:
                neutral_roles.append(role_instance.name)
        
        embed.add_field(
            name="🏡 Village Team",
            value=", ".join(village_roles) if village_roles else "None",
            inline=False
        )
        
        embed.add_field(
            name="🐺 Werewolf Team",
            value=", ".join(wolf_roles) if wolf_roles else "None",
            inline=False
        )
        
        embed.add_field(
            name="🎭 Neutral Roles",
            value=", ".join(neutral_roles) if neutral_roles else "None",
            inline=False
        )
        
        embed.add_field(
            name="Usage",
            value=f"Use `{config.prefix}role <name>` to get detailed information about a specific role.",
            inline=False
        )
        
        await ctx.send(embed=embed)
        return
    
    # Find the role
    role_key = role_name.lower().replace(" ", "_")
    if role_key not in ROLE_REGISTRY:
        # Try to find partial matches
        matches = [key for key in ROLE_REGISTRY.keys() if role_name.lower() in key]
        if matches:
            role_key = matches[0]
        else:
            await ctx.send(f"❌ Role '{role_name}' not found. Use `{config.prefix}role` to see all available roles.")
            return
    
    # Get role information
    role_class = ROLE_REGISTRY[role_key]
    role = role_class()
    
    # Create detailed embed
    team_colors = {
        "village": 0x006400,  # Dark Green
        "werewolf": 0x8B0000,  # Dark Red
        "neutral": 0x696969   # Dim Gray
    }
    
    embed = create_embed(f"🎭 {role.name}")
    embed.color = team_colors.get(role.team.value, 0x000000)
    
    embed.add_field(name="Team", value=role.team.value.title(), inline=True)
    embed.add_field(name="Win Condition", value=role.win_condition.value, inline=True)
    
    # Action type
    action_types = []
    if role.info.night_action:
        action_types.append("Night Action")
    if role.info.day_action:
        action_types.append("Day Action") 
    if role.info.passive_ability:
        action_types.append("Passive")
    if not action_types:
        action_types.append("No Special Actions")
    
    embed.add_field(name="Action Type", value=", ".join(action_types), inline=True)
    
    if role.info.max_uses:
        embed.add_field(name="Uses", value=f"{role.info.max_uses} time(s)", inline=True)
    
    embed.add_field(name="Description", value=role.description, inline=False)
    
    await ctx.send(embed=embed)

@command("roles", PermissionLevel.EVERYONE, "List all available roles by team")
async def roles_command(ctx: commands.Context, team: str = ""):
    """List all roles, optionally filtered by team"""
    if team and team.lower() not in ["village", "werewolf", "wolf", "neutral"]:
        await ctx.send("❌ Valid teams are: village, werewolf, neutral")
        return
    
    embed = create_embed("🎭 Werewolf Roles")
    
    # Organize roles by team
    teams_to_show = []
    if team:
        if team.lower() in ["werewolf", "wolf"]:
            teams_to_show = ["werewolf"]
        else:
            teams_to_show = [team.lower()]
    else:
        teams_to_show = ["village", "werewolf", "neutral"]
    
    for team_name in teams_to_show:
        team_roles = []
        team_icons = {"village": "🏡", "werewolf": "🐺", "neutral": "🎭"}
        
        for role_key, role_class in ROLE_REGISTRY.items():
            role_instance = role_class()
            if role_instance.team.value == team_name:
                # Add action indicators
                indicators = []
                if role_instance.info.night_action:
                    indicators.append("🌙")
                if role_instance.info.day_action:
                    indicators.append("☀️")
                if role_instance.info.passive_ability:
                    indicators.append("⚡")
                
                indicator_str = "".join(indicators) if indicators else "📋"
                team_roles.append(f"{indicator_str} **{role_instance.name}**")
        
        if team_roles:
            embed.add_field(
                name=f"{team_icons.get(team_name, '❓')} {team_name.title()} Team",
                value="\n".join(team_roles),
                inline=False
            )
    
    embed.add_field(
        name="Legend",
        value="🌙 Night Action • ☀️ Day Action • ⚡ Passive • 📋 No Actions",
        inline=False
    )
    
    embed.add_field(
        name="More Info",
        value=f"Use `{config.prefix}role <name>` for detailed role information.",
        inline=False
    )
    
    await ctx.send(embed=embed)

@command("gamemodes", PermissionLevel.EVERYONE, "List available game modes", aliases=["modes", "gm"])
async def gamemodes_command(ctx: commands.Context, mode: str = ""):
    """Show information about game modes"""
    if not mode:
        embed = create_embed("🎮 Available Game Modes")
        
        for mode_name, mode_info in GAMEMODE_CONFIGS.items():
            embed.add_field(
                name=f"**{mode_name.title()}**",
                value=f"{mode_info['description']}\n"
                      f"Players: {mode_info['min_players']}-{mode_info['max_players']}",
                inline=True
            )
        
        embed.add_field(
            name="Usage",
            value=f"Use `{config.prefix}join <gamemode>` to vote for a specific mode when joining.",
            inline=False
        )
        
        await ctx.send(embed=embed)
    else:
        # Show specific gamemode info
        if mode.lower() not in GAMEMODE_CONFIGS:
            await ctx.send(f"❌ Game mode '{mode}' not found.")
            return
        
        mode_info = GAMEMODE_CONFIGS[mode.lower()]
        embed = create_embed(f"🎮 {mode.title()} Mode")
        embed.add_field(name="Description", value=mode_info['description'], inline=False)
        embed.add_field(name="Min Players", value=str(mode_info['min_players']), inline=True)
        embed.add_field(name="Max Players", value=str(mode_info['max_players']), inline=True)
        
        await ctx.send(embed=embed)

@command("gamemode", PermissionLevel.EVERYONE, "Show role distribution for a gamemode")
async def gamemode_command(ctx: commands.Context, mode: str = "default", player_count: int = 8):
    """Show role distribution for a specific gamemode and player count"""
    if mode not in GAMEMODE_CONFIGS:
        await ctx.send(f"❌ Game mode '{mode}' not found. Use `{config.prefix}gamemodes` to see available modes.")
        return
    
    mode_info = GAMEMODE_CONFIGS[mode]
    
    if player_count < mode_info['min_players'] or player_count > mode_info['max_players']:
        await ctx.send(f"❌ Player count must be between {mode_info['min_players']} and {mode_info['max_players']} for {mode} mode.")
        return
    
    # Generate sample role distribution
    from src.game.roles import _assign_default_roles
    
    # Create fake player IDs for role assignment
    fake_player_ids = list(range(player_count))
    role_assignments = _assign_default_roles(fake_player_ids, player_count)
    
    # Count roles by team
    team_counts = {"village": 0, "werewolf": 0, "neutral": 0}
    role_counts = {}
    
    for role in role_assignments.values():
        team_counts[role.team.value] += 1
        role_name = role.name
        role_counts[role_name] = role_counts.get(role_name, 0) + 1
    
    embed = create_embed(f"🎮 {mode.title()} Mode - {player_count} Players")
    embed.add_field(name="Description", value=mode_info['description'], inline=False)
    
    # Team distribution
    embed.add_field(
        name="Team Distribution",
        value=f"🏡 Village: {team_counts['village']}\n"
              f"🐺 Werewolf: {team_counts['werewolf']}\n"
              f"🎭 Neutral: {team_counts['neutral']}",
        inline=True
    )
    
    # Role breakdown
    role_list = []
    for role_name, count in sorted(role_counts.items()):
        if count > 1:
            role_list.append(f"{role_name} x{count}")
        else:
            role_list.append(role_name)
    
    embed.add_field(
        name="Roles",
        value="\n".join(role_list) if role_list else "No roles assigned",
        inline=True
    )
    
    embed.add_field(
        name="Note",
        value="⚠️ Role assignments are randomized each game. This is just one possible distribution.",
        inline=False
    )
    
    await ctx.send(embed=embed)

@command("totem", PermissionLevel.EVERYONE, "Show totem information", aliases=["totems"])
async def totem_command(ctx: commands.Context, totem_name: str = ""):
    """Show information about totems"""
    
    # Define totem information
    TOTEMS = {
        "protection": {
            "name": "Protection Totem",
            "description": "Protects the holder from being killed for one night.",
            "type": "Beneficial",
            "given_by": "Shaman"
        },
        "revealing": {
            "name": "Revealing Totem",
            "description": "When the holder dies, their role is revealed to everyone.",
            "type": "Beneficial",
            "given_by": "Shaman"
        },
        "influence": {
            "name": "Influence Totem",
            "description": "The holder's vote counts twice during lynching.",
            "type": "Beneficial", 
            "given_by": "Shaman"
        },
        "impatience": {
            "name": "Impatience Totem",
            "description": "The day phase ends early if the holder votes.",
            "type": "Beneficial",
            "given_by": "Shaman"
        },
        "pacifism": {
            "name": "Pacifism Totem",
            "description": "The holder cannot vote during lynching.",
            "type": "Harmful",
            "given_by": "Crazed Shaman, Wolf Shaman"
        },
        "death": {
            "name": "Death Totem", 
            "description": "The holder dies at the end of the night.",
            "type": "Harmful",
            "given_by": "Crazed Shaman, Wolf Shaman"
        },
        "silence": {
            "name": "Silence Totem",
            "description": "The holder cannot use their night action for one cycle.",
            "type": "Harmful",
            "given_by": "Crazed Shaman, Wolf Shaman"
        },
        "desperation": {
            "name": "Desperation Totem",
            "description": "The holder must vote for someone during the day or die.",
            "type": "Harmful",
            "given_by": "Crazed Shaman, Wolf Shaman"
        },
        "misdirection": {
            "name": "Misdirection Totem",
            "description": "Actions targeting the holder are redirected to a random player.",
            "type": "Mixed",
            "given_by": "Wolf Shaman"
        },
        "luck": {
            "name": "Luck Totem",
            "description": "Actions targeting the holder have a chance to be redirected.",
            "type": "Mixed",
            "given_by": "Wolf Shaman"
        }
    }
    
    if not totem_name:
        # Show all totems
        embed = create_embed("🔮 Werewolf Totems")
        
        beneficial = []
        harmful = []
        mixed = []
        
        for totem_info in TOTEMS.values():
            totem_str = f"**{totem_info['name']}**"
            if totem_info['type'] == "Beneficial":
                beneficial.append(totem_str)
            elif totem_info['type'] == "Harmful":
                harmful.append(totem_str)
            else:
                mixed.append(totem_str)
        
        if beneficial:
            embed.add_field(
                name="✅ Beneficial Totems",
                value="\n".join(beneficial),
                inline=True
            )
        
        if harmful:
            embed.add_field(
                name="❌ Harmful Totems", 
                value="\n".join(harmful),
                inline=True
            )
        
        if mixed:
            embed.add_field(
                name="⚖️ Mixed Totems",
                value="\n".join(mixed),
                inline=True
            )
        
        embed.add_field(
            name="How Totems Work",
            value="Shamans receive random totems each night and must give them to players. "
                  "Beneficial totems help players, while harmful totems can hurt them.",
            inline=False
        )
        
        embed.add_field(
            name="Usage",
            value=f"Use `{config.prefix}totem <name>` for detailed information about a specific totem.",
            inline=False
        )
        
        await ctx.send(embed=embed)
    else:
        # Show specific totem
        totem_key = totem_name.lower().replace(" ", "").replace("totem", "")
        
        matching_totem = None
        for key, totem_info in TOTEMS.items():
            if (totem_key in key or 
                totem_key in totem_info['name'].lower().replace(" ", "")):
                matching_totem = totem_info
                break
        
        if not matching_totem:
            embed = create_error_embed(
                "Totem Not Found",
                f"Totem '{totem_name}' not found. Use `{config.prefix}totem` to see all available totems."
            )
            await ctx.send(embed=embed)
            return
        
        # Create detailed totem embed
        type_colors = {
            "Beneficial": 0x00FF00,  # Green
            "Harmful": 0xFF0000,     # Red 
            "Mixed": 0xFFFF00        # Yellow
        }
        
        embed = create_embed(f"🔮 {matching_totem['name']}")
        embed.color = type_colors.get(matching_totem['type'], 0x000000)
        
        embed.add_field(name="Type", value=matching_totem['type'], inline=True)
        embed.add_field(name="Given By", value=matching_totem['given_by'], inline=True)
        embed.add_field(name="Effect", value=matching_totem['description'], inline=False)
        
        await ctx.send(embed=embed)
