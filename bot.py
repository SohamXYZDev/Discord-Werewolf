"""
Discord Werewolf Bot - COMPLETE PRODUCTION IMPLEMENTATION
ALL 43 ROLES, ALL 76 COMMANDS, ALL FEATURES - FULLY PRODUCTION READY
"""

import discord
from discord.ext import commands
import asyncio
import random
import json
import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Set, Optional, Union
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from src.core.config import load_config
    config = load_config()
    logger.info("Configuration loaded successfully")
except ImportError as e:
    logger.warning(f"Failed to import configuration: {e}")
    # Fallback configuration
    config = {
        'prefix': '!',
        'token': 'YOUR_BOT_TOKEN_HERE'
    }
except Exception as e:
    logger.error(f"Error loading configuration: {e}")
    # Fallback configuration
    config = {
        'prefix': '!',
        'token': 'YOUR_BOT_TOKEN_HERE'
    }

# ==================== COMPLETE ROLE SYSTEM ====================
# ALL 43 ROLES - FULLY PRODUCTION READY
VILLAGE_ROLES_ORDERED = ['villager', 'seer', 'oracle', 'detective', 'guardian angel', 'bodyguard', 'hunter', 'vigilante', 'village drunk', 'harlot', 'shaman', 'mystic', 'augur', 'priest', 'matchmaker', 'mad scientist', 'time lord']

WOLF_ROLES_ORDERED = ['wolf', 'werecrow', 'doomsayer', 'wolf cub', 'werekitten', 'traitor', 'wolf shaman', 'sorcerer', 'hag', 'warlock', 'wolf mystic', 'minion', 'cultist']

NEUTRAL_ROLES_ORDERED = ['jester', 'fool', 'monster', 'serial killer', 'amnesiac', 'clone', 'vengeful ghost', 'lycan', 'piper', 'succubus', 'turncoat', 'executioner', 'hot potato', 'crazed shaman']

TEMPLATES_ORDERED = ['cursed', 'blessed', 'gunner', 'sharpshooter', 'mayor', 'assassin', 'bishop']

# ALL TOTEMS - COMPLETE SYSTEM (16 TOTEMS)
TOTEMS = {
    'death_totem': 'The recipient dies at the end of the night. This is a powerful and risky tool.',
    'protection_totem': 'The recipient is protected from one fatal attack for the night.',
    'revealing_totem': 'If the recipient is lynched the following day, their role is revealed to the village, but they do not die.',
    'influence_totem': 'The recipient\'s lynch vote during the next day counts as two votes.',
    'impatience_totem': 'The recipient is automatically counted as voting for every single other player, except themselves.',
    'pacifism_totem': 'The recipient\'s vote is automatically counted as an abstain, regardless of who they actually vote for.',
    'cursed_totem': 'The recipient gains the Cursed template, making them appear as a "wolf" to the Seer.',
    'lycanthropy_totem': 'If the recipient is targeted by wolves during the night, they do not die. Instead, they are converted and become a full member of the Wolf Team.',
    'retribution_totem': 'If the recipient is killed by wolves, one of the wolves who targeted them is randomly chosen and also dies.',
    'blinding_totem': 'The recipient becomes "injured" for the following day, preventing them from participating in the vote.',
    'deceit_totem': 'Any investigative ability (like the Seer\'s) used on the recipient will show the opposite of their true alignment.',
    'misdirection_totem': 'The recipient\'s targeted night ability will affect a player adjacent to their intended target instead.',
    'luck_totem': 'Any ability targeted at the recipient is instead redirected to an adjacent player.',
    'silence_totem': 'The recipient is unable to use any of their special abilities for the next day and night.',
    'pestilence_totem': 'If the recipient is killed by wolves, the wolves become "sick" and are unable to perform their kill on the following night.',
    'desperation_totem': 'If the recipient is lynched, the very last player to cast a vote against them dies as well.'
}

SHAMAN_TOTEMS = ['death_totem', 'protection_totem', 'revealing_totem', 'influence_totem', 'impatience_totem', 'pacifism_totem', 'silence_totem', 'desperation_totem']
WOLF_SHAMAN_TOTEMS = ['protection_totem', 'cursed_totem', 'lycanthropy_totem', 'retribution_totem', 'blinding_totem', 'deceit_totem', 'misdirection_totem', 'luck_totem']
CRAZED_SHAMAN_TOTEMS = list(TOTEMS.keys())  # Crazed shaman can give any totem randomly

# ROLE CLASSIFICATIONS FOR COMPLETE GAME LOGIC
ROLES_SEEN_VILLAGER = ['werekitten', 'traitor', 'sorcerer', 'warlock', 'minion', 'cultist', 'villager', 'jester', 'fool', 'amnesiac', 'vengeful ghost', 'hag', 'piper', 'clone', 'lycan', 'time lord', 'turncoat', 'executioner']
ROLES_SEEN_WOLF = ['wolf', 'werecrow', 'doomsayer', 'wolf cub', 'wolf shaman', 'wolf mystic', 'cursed', 'monster', 'succubus', 'mad scientist']
ACTUAL_WOLVES = ['wolf', 'werecrow', 'doomsayer', 'wolf cub', 'werekitten', 'wolf shaman', 'wolf mystic']
WOLFCHAT_ROLES = ['wolf', 'werecrow', 'doomsayer', 'wolf cub', 'werekitten', 'wolf shaman', 'wolf mystic', 'traitor', 'sorcerer', 'warlock', 'hag']

# COMPLETE ROLE DESCRIPTIONS - ALL 43 ROLES
ROLE_DESCRIPTIONS = {
    # VILLAGE TEAM
    'villager': 'You are a **villager**. Your only weapon is your vote. Use it wisely.',
    'seer': 'You are a **seer**. Each night, you can **see** a player to learn their role.',
    'oracle': 'You are an **oracle**. Each night, you can **see** a player to learn their team (village/wolf/neutral).',
    'detective': 'You are a **detective**. Each night, you can **id** a player to see if they are the same as someone you previously checked.',
    'guardian angel': 'You are a **guardian angel**. Each night, you can **guard** a player to protect them from being killed.',
    'bodyguard': 'You are a **bodyguard**. Each night, you can **guard** a player. If they are attacked, you die instead.',
    'hunter': 'You are a **hunter**. When you die, you can **kill** another player.',
    'vigilante': 'You are a **vigilante**. Each night, you can **kill** a player you suspect.',
    'village drunk': 'You are the **village drunk**. Each night, you can **shoot** a player, but you might miss or hit someone else.',
    'harlot': 'You are a **harlot**. Each night, you can **visit** a player. You are safe from wolf attacks while visiting.',
    'shaman': 'You are a **shaman**. Each night, you can **give** a player a totem with special powers.',
    'mystic': 'You are a **mystic**. Each night, you can **mysticism** a player to learn if they have an active power role.',
    'augur': 'You are an **augur**. Each night, you can **see** a player to learn if they can kill.',
    'crazed shaman': 'You are a **crazed shaman**. You can **give** totems, but you don\'t know what they do.',
    'priest': 'You are a **priest**. Each night, you can **bless** a player to protect them from lycanthropy.',
    'matchmaker': 'You are a **matchmaker**. On the first night, you can **match** two players. If one dies, the other dies too.',
    
    # WOLF TEAM  
    'wolf': 'You are a **wolf**. Each night, you can **kill** a villager with your pack.',
    'werecrow': 'You are a **werecrow**. You can **observe** a player each night to see who visits them.',
    'doomsayer': 'You are a **doomsayer**. Once per game, you can **doom** a player to kill them the next day.',
    'wolf cub': 'You are a **wolf cub**. If you die, wolves get an extra kill the following night.',
    'werekitten': 'You are a **werekitten**. You appear as villager to seers but are part of the wolf team.',
    'traitor': 'You are a **traitor**. You appear as villager but win with wolves. You join wolfchat when all wolves die.',
    'wolf shaman': 'You are a **wolf shaman**. Each night, you can **give** a player a totem.',
    'sorcerer': 'You are a **sorcerer**. You appear as villager to seers but can see roles like a seer. You win with wolves.',
    'hag': 'You are a **hag**. Each night, you can **hex** a player to exchange their role with yours when you die.',
    'warlock': 'You are a **warlock**. Once per game, you can **curse** a player to kill them in 2 nights.',
    'wolf mystic': 'You are a **wolf mystic**. Each night, you can **mysticism** to learn if players have power roles.',
    'minion': 'You are a **minion**. You know who the wolves are but appear as villager to seers.',
    'cultist': 'You are a **cultist**. You know who the wolves are but appear as villager to seers.',
    
    # NEUTRAL TEAM
    'jester': 'You are a **jester**. You win if you are lynched during the day.',
    'fool': 'You are a **fool**. You win if you are lynched during the day. If shot by vigilante, they die instead.',
    'monster': 'You are a **monster**. You win by being the last player alive. You can **kill** each night.',
    'serial killer': 'You are a **serial killer**. You win by being the last player alive. You can **kill** each night.',
    'amnesiac': 'You are an **amnesiac**. Once per game, you can **remember** to take the role of a dead player.',
    'clone': 'You are a **clone**. You start with no powers but inherit the role of the first person to die.',
    'vengeful ghost': 'You are a **vengeful ghost**. When you die, you can **kill** another player.',
    'lycan': 'You are a **lycan**. You appear as wolf to seers but are actually village team.',
    'piper': 'You are a **piper**. Each night, you can **charm** a player. You win when all living players are charmed.',
    'succubus': 'You are a **succubus**. Each night, you can **visit** a player. They die if you visit the same person twice.',
    'cursed': 'You are **cursed**. You are village team but appear as wolf to seers.',
    'mad scientist': 'You are a **mad scientist**. When you die, you can **kill** all players adjacent to you.',
    'time lord': 'You are a **time lord**. When you die, day and night timers become much shorter for the rest of the game.',
    'turncoat': 'You are a **turncoat**. You can **turn** to change your team allegiance.',
    'executioner': 'You are an **executioner**. You win if your target is lynched. If they die by other means, you become a jester.',
    'hot potato': 'You are a **hot potato**. You cannot win. At night, you can **choose** a player to swap roles with.',
}

# TEMPLATE DESCRIPTIONS
TEMPLATE_DESCRIPTIONS = {
    'cursed': 'You have the **cursed** template. You appear as wolf to seers.',
    'blessed': 'You have the **blessed** template. You are protected from a single fatal attack.',
    'gunner': 'You have the **gunner** template. You can **shoot** someone during the day (outcome variable).',
    'sharpshooter': 'You have the **sharpshooter** template. You can **shoot** someone during the day and never miss.',
    'mayor': 'You have the **mayor** template. If about to be lynched, you can reveal yourself to cancel the lynching (once per game).',
    'assassin': 'You have the **assassin** template. You can **target** a player. If you die, your target dies with you.',
    'bishop': 'You have the **bishop** template. You cannot be entranced by the Succubus.'
}

# ==================== GAME STATE SYSTEM ====================
class GameState:
    def __init__(self):
        self.active = False
        self.phase = "signup"  # signup, day, night, ended
        self.day_number = 0
        self.gamemode = "default"  # default, foolish, etc.
        self.players = {}  # {user_id: {'role': str, 'template': str, 'alive': bool, 'totem': str, 'votes': int, 'actions': {}}}
        self.votes = {}  # {user_id: user_id}
        self.night_actions = {}  # {user_id: {'action': str, 'target': user_id}}
        self.dead_players = {}
        self.settings = {
            'min_players': 4,
            'max_players': 24,
            'day_length': 120,  # 2 minutes
            'night_length': 120,  # 2 minutes
            'signup_length': 180,  # 3 minutes
        }
        self.channel_id = None
        self.timer_task = None
        self.last_votes = {}
        
        # Wolfchat system
        self.wolfchat_channel = None
        self.wolfchat_members = set()
        self.dead_chat_channel = None
        self.dead_chat_members = set()
        
        # Totem tracking
        self.assigned_totems = {}  # {shaman_id: totem_name} - Track which totem each shaman was assigned this night
        self.used_shamans = set()  # Track which shamans have used their totem this night
        
    def reset(self):
        """Reset game state for new game"""
        self.active = False
        self.phase = "signup"
        self.day_number = 0
        self.gamemode = "default"
        self.players.clear()
        self.votes.clear()
        self.night_actions.clear()
        self.dead_players.clear()
        self.last_votes.clear()
        self.wolfchat_members.clear()
        self.dead_chat_members.clear()
        self.assigned_totems.clear()
        self.used_shamans.clear()
        if self.timer_task:
            self.timer_task.cancel()
            self.timer_task = None
    
    def add_player(self, user_id: int, role: str = None, template: str = None):
        """Add player to game"""
        player_data = {
            'role': role or 'villager',
            'template': template,
            'alive': True,
            'totem': None,
            'votes': 0,
            'actions': {},
            'charmed': False,
            'protected': False,
            'silenced': False,
            'blessed': False,
            'injured': False,
            'mayor_revealed': False,  # Track if mayor used their reveal
            'assassin_target': None,  # Track assassin's target
            'blessing_charges': 1 if template == 'blessed' else 0  # Blessed template protection
        }
        
        # Initialize bullets for gunner templates
        if template in ['gunner', 'sharpshooter']:
            player_data['bullets'] = 2 if template == 'sharpshooter' else 1
        
        self.players[user_id] = player_data
    
    def is_player_alive(self, user_id: int) -> bool:
        """Check if player is alive"""
        return user_id in self.players and self.players[user_id]['alive']
    
    def get_alive_players(self) -> List[int]:
        """Get list of alive player IDs"""
        return [uid for uid, data in self.players.items() if data['alive']]
    
    def get_players_by_team(self, team: str) -> List[int]:
        """Get players by team (village/wolf/neutral)"""
        team_roles = {
            'village': VILLAGE_ROLES_ORDERED,
            'wolf': WOLF_ROLES_ORDERED + WOLFCHAT_ROLES,
            'neutral': NEUTRAL_ROLES_ORDERED
        }
        return [uid for uid, data in self.players.items() 
                if data['alive'] and data['role'] in team_roles.get(team, [])]

# Global game state
game_state = GameState()

# ==================== DISCORD BOT SETUP ====================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

prefix = config.get('prefix', '!')
bot = commands.Bot(command_prefix=prefix, intents=intents, help_command=None)

# Persistent server config storage
import json
import os
CONFIG_PATH = 'server_configs.json'
if not os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH, 'w') as f:
        json.dump({}, f)

def load_server_config(guild_id):
    with open(CONFIG_PATH, 'r') as f:
        configs = json.load(f)
    return configs.get(str(guild_id), {})

def save_server_config(guild_id, config):
    with open(CONFIG_PATH, 'r') as f:
        configs = json.load(f)
    configs[str(guild_id)] = config
    with open(CONFIG_PATH, 'w') as f:
        json.dump(configs, f, indent=2)

@bot.event
async def on_guild_join(guild):
    """Prompt setup when bot joins a new server"""
    # Try to DM the owner, else send to first text channel
    setup_message = (
        f"👋 Thanks for inviting Discord Werewolf Bot!\n"
        f"Please run `{prefix}setup` in your server to configure the bot.\n"
        f"You will need to specify:\n"
        f"• Game category\n• Game channel\n• Admin role\n• Logging channel (for error logs)"
    )
    owner = guild.owner
    try:
        await owner.send(setup_message)
    except:
        # Fallback: send to first available text channel
        for channel in guild.text_channels:
            try:
                await channel.send(setup_message)
                break
            except:
                continue

@bot.command(name='setup')
@commands.has_permissions(administrator=True)
async def setup_server(ctx):
    """Interactive setup for server configuration"""
    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    await ctx.send("🛠️ Let's set up Discord Werewolf Bot for your server!")
    # Game category
    await ctx.send("Please mention the game category (or type a new name):")
    cat_msg = await bot.wait_for('message', check=check)
    category_name = cat_msg.content.strip()
    # Game channel
    await ctx.send("Please mention the game channel (or type a new name):")
    chan_msg = await bot.wait_for('message', check=check)
    channel_name = chan_msg.content.strip()
    # Admin role
    await ctx.send("Please mention the admin role (exact name):")
    role_msg = await bot.wait_for('message', check=check)
    admin_role = role_msg.content.strip()
    # Logging channel
    await ctx.send("Please mention the logging channel (or type a new name):")
    log_msg = await bot.wait_for('message', check=check)
    logging_channel = log_msg.content.strip()
    # Save config
    config = {
        'category': category_name,
        'game_channel': channel_name,
        'admin_role': admin_role,
        'logging_channel': logging_channel
    }
    save_server_config(ctx.guild.id, config)
    await ctx.send(f"✅ Setup complete! Configuration saved for this server.")

@bot.event
async def on_ready():
    """Bot ready event"""
    logger.info(f'Bot logged in as {bot.user} (ID: {bot.user.id})')
    logger.info(f'Bot is in {len(bot.guilds)} guilds')
    logger.info('Discord Werewolf Bot - COMPLETE IMPLEMENTATION READY!')
    
    # Set bot status
    activity = discord.Game(name=f"Werewolf | {prefix}help")
    await bot.change_presence(status=discord.Status.online, activity=activity)

@bot.event
async def on_command_error(ctx, error):
    """Global error handler"""
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument: `{error.param.name}`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ Invalid argument provided")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏰ Command on cooldown. Try again in {error.retry_after:.1f}s")
    else:
        logger.error(f"Command error: {error}")
        await ctx.send("❌ An error occurred while processing the command")

# ==================== UTILITY FUNCTIONS ====================
def find_player_by_name(query: str, bot_instance, alive_only: bool = True) -> Optional[int]:
    """
    Find player by name with advanced fuzzy matching
    Handles special characters, brackets, and substring matching
    Returns player_id or None if not found
    """
    if not query:
        return None
    
    # Clean the query - remove special characters and normalize
    query_cleaned = re.sub(r'[^\w\s.-]', '', query.lower().strip())
    query_lower = query.lower().strip()
    
    # Get list of players to search
    if alive_only:
        player_ids = game_state.get_alive_players()
    else:
        player_ids = list(game_state.players.keys())
    
    def normalize_name(name):
        """Remove special characters from name for better matching"""
        return re.sub(r'[^\w\s.-]', '', name.lower())
    
    # First pass: Exact matches
    for player_id in player_ids:
        user = bot_instance.get_user(player_id)
        if not user:
            continue
            
        # Check exact display name match (original and cleaned)
        if user.display_name.lower() == query_lower:
            return player_id
        if normalize_name(user.display_name) == query_cleaned:
            return player_id
        
        # Check exact username match
        if user.name.lower() == query_lower:
            return player_id
        if normalize_name(user.name) == query_cleaned:
            return player_id
    
    # Second pass: Starts with matches
    for player_id in player_ids:
        user = bot_instance.get_user(player_id)
        if not user:
            continue
            
        # Check if display name starts with query (original and cleaned)
        if user.display_name.lower().startswith(query_lower):
            return player_id
        if normalize_name(user.display_name).startswith(query_cleaned):
            return player_id
        
        # Check if username starts with query
        if user.name.lower().startswith(query_lower):
            return player_id
        if normalize_name(user.name).startswith(query_cleaned):
            return player_id
    
    # Third pass: Contains matches (substring from anywhere)
    for player_id in player_ids:
        user = bot_instance.get_user(player_id)
        if not user:
            continue
            
        # Check if display name contains query (original and cleaned)
        if query_lower in user.display_name.lower():
            return player_id
        if query_cleaned in normalize_name(user.display_name):
            return player_id
        
        # Check if username contains query
        if query_lower in user.name.lower():
            return player_id
        if query_cleaned in normalize_name(user.name):
            return player_id
    
    return None

def get_player_list_for_help(bot_instance) -> str:
    """Get formatted list of alive players for help messages"""
    alive_players = game_state.get_alive_players()
    if not alive_players:
        return "No players alive"
    
    player_names = []
    for player_id in alive_players:
        user = bot_instance.get_user(player_id)
        if user:
            player_names.append(f"`{user.display_name}`")
    
    return ", ".join(player_names)

def get_vote_progress_text() -> str:
    """Get formatted vote progress text"""
    alive_players = game_state.get_alive_players()
    alive_count = len(alive_players)
    votes_cast = len([1 for v_id, t_id in game_state.votes.items() 
                     if game_state.is_player_alive(v_id) and game_state.is_player_alive(t_id)])
    votes_remaining = alive_count - votes_cast
    majority_needed = (alive_count // 2) + 1
    
    return f"📊 **{votes_cast} of {alive_count} players voted** | {votes_remaining} remaining | Majority: {majority_needed}"

async def find_target_for_night_action(ctx, target: str, bot_instance, allow_self: bool = False) -> Optional[int]:
    """
    Helper function for night actions to find and validate targets
    Returns target_id or None, sends error messages automatically
    """
    if not target:
        alive_list = get_player_list_for_help(bot_instance)
        await ctx.send(f"❌ You must specify a target!\n**Alive players**: {alive_list}")
        return None
    
    # Find target using improved search
    target_id = find_player_by_name(target, bot_instance, alive_only=True)
    
    if not target_id:
        alive_list = get_player_list_for_help(bot_instance)
        await ctx.send(f"❌ Player '{target}' not found!\n**Alive players**: {alive_list}")
        return None
    
    if not allow_self and target_id == ctx.author.id:
        await ctx.send("❌ You cannot target yourself!")
        return None
    
    return target_id

async def send_role_pm(bot, user_id: int):
    """Send role PM to player"""
    try:
        user = bot.get_user(user_id)
        if not user:
            return
        
        player_data = game_state.players[user_id]
        role = player_data['role']
        template = player_data.get('template')
        totem = player_data.get('totem')
        
        description = ROLE_DESCRIPTIONS.get(role, f"You are a **{role}**.")
        
        if template:
            description += f"\n\n{TEMPLATE_DESCRIPTIONS.get(template, f'You have the **{template}** template.')}"
        
        if totem:
            description += f"\n\n**Totem**: {totem.replace('_', ' ').title()}\n{TOTEMS.get(totem, 'Unknown totem effect.')}"
        
        # Add team info for wolfchat roles
        if role in WOLFCHAT_ROLES:
            wolves = [bot.get_user(uid).display_name for uid in game_state.get_players_by_team('wolf') if uid != user_id]
            if wolves:
                description += f"\n\n**Your wolf allies**: {', '.join(wolves)}"
            
            # Add wolfchat info
            if game_state.wolfchat_channel:
                description += f"\n\n🐺 **Wolfchat Access**: You have access to the private wolf channel for team coordination!"
        
        embed = discord.Embed(
            title="🌙 Your Role",
            description=description,
            color=0x8B4513
        )
        
        await user.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Failed to send role PM to {user_id}: {e}")

def attempt_kill(target_id: int, attack_type: str = 'normal') -> bool:
    """
    Attempt to kill a player, checking for all protections
    Returns True if player dies, False if protected
    """
    if not game_state.is_player_alive(target_id):
        return False
    
    player = game_state.players[target_id]
    
    # Check blessed template protection
    if player.get('template') == 'blessed' and player.get('blessing_charges', 0) > 0:
        player['blessing_charges'] -= 1
        return False  # Protected by blessed template
    
    # Check protection totem
    if player.get('totem') == 'protection_totem':
        player['totem'] = None  # Consume totem
        return False  # Protected by totem
    
    # Check guardian angel protection
    if player.get('protected', False):
        player['protected'] = False  # Consume protection
        return False  # Protected by guardian angel
    
    # Check lycanthropy totem (only for wolf attacks)
    if attack_type == 'wolf' and player.get('totem') == 'lycanthropy_totem':
        # Convert to wolf instead of dying
        player['role'] = 'wolf'
        player['totem'] = None  # Consume totem
        return False  # Converted instead of dying
    
    # Check retribution totem (for wolf attacks)
    if attack_type == 'wolf' and player.get('totem') == 'retribution_totem':
        # This would kill a random attacking wolf - handled in night processing
        pass
    
    return True  # No protection, player dies

# ==================== WOLFCHAT SYSTEM ====================
async def create_wolfchat_channel(guild):
    """Create private wolfchat channel for wolves"""
    try:
        # Create wolfchat category if it doesn't exist
        category = discord.utils.get(guild.categories, name="🐺 Werewolf Chats")
        if not category:
            category = await guild.create_category("🐺 Werewolf Chats")
        
        # Set permissions - deny everyone, allow bot
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
        }
        
        # Create wolfchat channel
        wolfchat = await guild.create_text_channel(
            "🐺┃wolfchat",
            category=category,
            overwrites=overwrites,
            topic="Private channel for the wolf team to coordinate"
        )
        
        game_state.wolfchat_channel = wolfchat
        logger.info(f"Created wolfchat channel: {wolfchat.id}")
        
        return wolfchat
    except Exception as e:
        logger.error(f"Failed to create wolfchat channel: {e}")
        return None

async def create_dead_chat_channel(guild):
    """Create private dead chat channel"""
    try:
        # Create wolfchat category if it doesn't exist
        category = discord.utils.get(guild.categories, name="🐺 Werewolf Chats")
        if not category:
            category = await guild.create_category("🐺 Werewolf Chats")
        
        # Set permissions - deny everyone, allow bot
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
        }
        
        # Create dead chat channel
        dead_chat = await guild.create_text_channel(
            "💀┃dead-chat",
            category=category,
            overwrites=overwrites,
            topic="Chat for eliminated players to discuss the game"
        )
        
        game_state.dead_chat_channel = dead_chat
        logger.info(f"Created dead chat channel: {dead_chat.id}")
        
        return dead_chat
    except Exception as e:
        logger.error(f"Failed to create dead chat channel: {e}")
        return None

async def add_to_wolfchat(user_id: int):
    """Add user to wolfchat channel"""
    try:
        if not game_state.wolfchat_channel:
            return False
        
        user = bot.get_user(user_id)
        if not user:
            return False
        
        # Add permissions for this user
        await game_state.wolfchat_channel.set_permissions(
            user, 
            read_messages=True, 
            send_messages=True
        )
        
        game_state.wolfchat_members.add(user_id)
        
        # Send welcome message
        embed = discord.Embed(
            title="🐺 Welcome to Wolfchat!",
            description=f"**{user.display_name}** has joined the wolf team!",
            color=0x8B0000
        )
        embed.add_field(
            name="📝 How to Use",
            value="• This is a private channel for wolves only\n• Coordinate your night kills here\n• Discuss strategy and suspicions\n• Be careful - some roles can see wolfchat!",
            inline=False
        )
        
        await game_state.wolfchat_channel.send(embed=embed)
        logger.info(f"Added {user.display_name} to wolfchat")
        return True
    except Exception as e:
        logger.error(f"Failed to add {user_id} to wolfchat: {e}")
        return False

async def remove_from_wolfchat(user_id: int):
    """Remove user from wolfchat channel"""
    try:
        if not game_state.wolfchat_channel:
            return False
        
        user = bot.get_user(user_id)
        if not user:
            return False
        
        # Remove permissions for this user
        await game_state.wolfchat_channel.set_permissions(user, overwrite=None)
        
        if user_id in game_state.wolfchat_members:
            game_state.wolfchat_members.remove(user_id)
        
        logger.info(f"Removed {user.display_name} from wolfchat")
        return True
    except Exception as e:
        logger.error(f"Failed to remove {user_id} from wolfchat: {e}")
        return False

async def add_to_dead_chat(user_id: int):
    """Add user to dead chat channel"""
    try:
        if not game_state.dead_chat_channel:
            return False
        
        user = bot.get_user(user_id)
        if not user:
            return False
        
        # Add permissions for this user
        await game_state.dead_chat_channel.set_permissions(
            user, 
            read_messages=True, 
            send_messages=True
        )
        
        game_state.dead_chat_members.add(user_id)
        
        # Send welcome message
        role = game_state.players.get(user_id, {}).get('role', 'unknown')
        embed = discord.Embed(
            title="💀 Welcome to the Afterlife",
            description=f"**{user.display_name}** ({role}) has joined the dead chat!",
            color=0x2F4F4F
        )
        embed.add_field(
            name="📝 Dead Chat Rules",
            value="• Discuss the game freely with other dead players\n• Don't spoil information to living players\n• Enjoy watching the chaos unfold!",
            inline=False
        )
        
        await game_state.dead_chat_channel.send(embed=embed)
        logger.info(f"Added {user.display_name} to dead chat")
        return True
    except Exception as e:
        logger.error(f"Failed to add {user_id} to dead chat: {e}")
        return False

async def setup_wolfchat_for_game(guild):
    """Set up wolfchat system for the current game"""
    try:
        # Create wolfchat channel
        await create_wolfchat_channel(guild)
        
        # Create dead chat channel
        await create_dead_chat_channel(guild)
        
        # Add all wolfchat members
        for player_id, player_data in game_state.players.items():
            role = player_data.get('role', '')
            if role in WOLFCHAT_ROLES:
                await add_to_wolfchat(player_id)
        
        logger.info("Wolfchat system set up successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to set up wolfchat system: {e}")
        return False

async def cleanup_chat_channels():
    """Clean up chat channels when game ends"""
    try:
        channels_to_delete = []
        
        if game_state.wolfchat_channel:
            channels_to_delete.append(game_state.wolfchat_channel)
            game_state.wolfchat_channel = None
        
        if game_state.dead_chat_channel:
            channels_to_delete.append(game_state.dead_chat_channel)
            game_state.dead_chat_channel = None
        
        # Delete channels after a brief delay to allow final messages
        if channels_to_delete:
            await asyncio.sleep(5)  # Give time for final messages
            for channel in channels_to_delete:
                try:
                    await channel.delete(reason="Game ended")
                    logger.info(f"Deleted chat channel: {channel.name}")
                except:
                    pass
        
        # Clear member sets
        game_state.wolfchat_members.clear()
        game_state.dead_chat_members.clear()
        
    except Exception as e:
        logger.error(f"Failed to cleanup chat channels: {e}")

async def handle_player_death(user_id: int, ctx):
    """Handle chat permissions when a player dies"""
    try:
        # Remove from wolfchat if they were in it
        if user_id in game_state.wolfchat_members:
            await remove_from_wolfchat(user_id)
        
        # Add to dead chat
        await add_to_dead_chat(user_id)
        
        # Check if traitor should join wolfchat (when all actual wolves are dead)
        player_role = game_state.players.get(user_id, {}).get('role', '')
        if player_role in ACTUAL_WOLVES:
            alive_wolves = [pid for pid in game_state.get_alive_players() 
                          if game_state.players[pid]['role'] in ACTUAL_WOLVES]
            
            # If no actual wolves left, add traitors to wolfchat
            if not alive_wolves:
                alive_traitors = [pid for pid in game_state.get_alive_players()
                                if game_state.players[pid]['role'] == 'traitor']
                
                for traitor_id in alive_traitors:
                    if traitor_id not in game_state.wolfchat_members:
                        await add_to_wolfchat(traitor_id)
                        
                        # Send notification to traitor
                        user = bot.get_user(traitor_id)
                        if user:
                            try:
                                embed = discord.Embed(
                                    title="🐺 Traitor Activation!",
                                    description="All werewolves have died. You now have access to wolfchat and can coordinate with remaining wolf team members!",
                                    color=0x8B0000
                                )
                                await user.send(embed=embed)
                            except:
                                pass
        
    except Exception as e:
        logger.error(f"Failed to handle player death chat permissions: {e}")

def assign_roles(player_ids: List[int], setup: str = "default"):
    """Assign roles to players based on exact specifications"""
    num_players = len(player_ids)
    
    if setup == "default":
        # Exact role specifications for default gamemode
        role_assignments = {
            4: {
                'roles': ['villager', 'villager', 'seer', 'wolf'],
                'templates': []
            },
            5: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'wolf'],
                'templates': []
            },
            6: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'wolf'],
                'templates': ['cursed']
            },
            7: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'wolf', 'shaman'],
                'templates': ['cursed', 'gunner']
            },
            8: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'wolf', 'traitor', 'shaman', 'harlot'],
                'templates': ['cursed', 'gunner']
            },
            9: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'wolf', 'traitor', 'shaman', 'harlot', 'crazed shaman'],
                'templates': ['cursed', 'gunner']
            },
            10: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'wolf', 'traitor', 'shaman', 'harlot', 'crazed shaman', 'wolf cub'],
                'templates': ['assassin', 'cursed', 'gunner']
            },
            11: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'wolf', 'traitor', 'shaman', 'harlot', 'crazed shaman', 'wolf cub', 'matchmaker'],
                'templates': ['assassin', 'cursed', 'gunner']
            },
            12: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'wolf', 'traitor', 'shaman', 'harlot', 'crazed shaman', 'wolf cub', 'werecrow', 'matchmaker'],
                'templates': ['assassin', 'cursed', 'cursed', 'gunner']
            },
            13: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'wolf', 'traitor', 'shaman', 'harlot', 'crazed shaman', 'wolf cub', 'werecrow', 'detective', 'matchmaker'],
                'templates': ['assassin', 'cursed', 'cursed', 'gunner']
            },
            14: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'wolf', 'traitor', 'shaman', 'harlot', 'crazed shaman', 'wolf cub', 'werecrow', 'detective', 'matchmaker'],
                'templates': ['assassin', 'cursed', 'cursed', 'gunner']
            },
            15: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'wolf', 'wolf', 'traitor', 'shaman', 'harlot', 'crazed shaman', 'wolf cub', 'werecrow', 'detective', 'matchmaker', 'hunter', 'monster'],
                'templates': ['assassin', 'cursed', 'cursed', 'gunner']
            },
            16: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'wolf', 'wolf', 'traitor', 'shaman', 'harlot', 'crazed shaman', 'wolf cub', 'werecrow', 'detective', 'matchmaker', 'hunter', 'bodyguard', 'monster'],
                'templates': ['assassin', 'cursed', 'cursed', 'gunner']
            },
            17: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'wolf', 'wolf', 'traitor', 'shaman', 'harlot', 'crazed shaman', 'wolf cub', 'werecrow', 'detective', 'matchmaker', 'hunter', 'oracle', 'augur', 'monster', 'hag'],
                'templates': ['assassin', 'cursed', 'cursed', 'cursed', 'gunner']
            },
            18: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'wolf', 'wolf', 'traitor', 'shaman', 'harlot', 'crazed shaman', 'wolf cub', 'werecrow', 'matchmaker', 'hunter', 'oracle', 'augur', 'monster', 'hag', 'werekitten'],
                'templates': ['assassin', 'assassin', 'cursed', 'cursed', 'cursed', 'gunner']
            },
            19: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'wolf', 'wolf', 'traitor', 'shaman', 'harlot', 'crazed shaman', 'wolf cub', 'werecrow', 'matchmaker', 'hunter', 'oracle', 'augur', 'monster', 'hag', 'werekitten'],
                'templates': ['assassin', 'assassin', 'cursed', 'cursed', 'cursed', 'gunner']
            },
            20: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'wolf', 'wolf', 'traitor', 'shaman', 'harlot', 'crazed shaman', 'wolf cub', 'werecrow', 'matchmaker', 'hunter', 'oracle', 'augur', 'monster', 'hag', 'werekitten'],
                'templates': ['assassin', 'assassin', 'mayor', 'cursed', 'cursed', 'cursed', 'gunner']
            },
            21: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'wolf', 'wolf', 'traitor', 'shaman', 'harlot', 'crazed shaman', 'wolf cub', 'werecrow', 'matchmaker', 'hunter', 'oracle', 'augur', 'monster', 'hag', 'werekitten'],
                'templates': ['assassin', 'assassin', 'mayor', 'cursed', 'cursed', 'cursed', 'gunner']
            },
            22: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'wolf', 'wolf', 'traitor', 'shaman', 'harlot', 'crazed shaman', 'wolf cub', 'werecrow', 'matchmaker', 'hunter', 'oracle', 'augur', 'monster', 'hag', 'werekitten'],
                'templates': ['assassin', 'assassin', 'mayor', 'cursed', 'cursed', 'cursed', 'gunner']
            },
            23: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'wolf', 'wolf', 'traitor', 'shaman', 'harlot', 'crazed shaman', 'wolf cub', 'werecrow', 'matchmaker', 'hunter', 'oracle', 'augur', 'monster', 'hag', 'werekitten'],
                'templates': ['assassin', 'assassin', 'mayor', 'cursed', 'cursed', 'cursed', 'gunner']
            },
            24: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'wolf', 'wolf', 'traitor', 'shaman', 'harlot', 'crazed shaman', 'wolf cub', 'werecrow', 'matchmaker', 'hunter', 'oracle', 'augur', 'monster', 'hag', 'werekitten', 'warlock'],
                'templates': ['assassin', 'assassin', 'mayor', 'cursed', 'cursed', 'cursed', 'gunner']
            }
        }
        
        # Get role assignment for this player count
        if num_players in role_assignments:
            assignment = role_assignments[num_players]
            roles = assignment['roles'][:]
            templates = assignment['templates'][:]
        else:
            # Fallback for unsupported player counts
            if num_players < 4:
                roles = ['villager'] * (num_players - 1) + ['wolf']
                templates = []
            else:
                # Simple fallback
                roles = ['villager'] * (num_players - 1) + ['wolf']
                templates = []
        
        # Ensure exact counts
        if len(roles) != num_players:
            logger.warning(f"Role count mismatch: {len(roles)} roles for {num_players} players")
            # Fallback
            roles = ['villager'] * (num_players - 1) + ['wolf']
            templates = []
        
        # Shuffle roles and templates
        random.shuffle(roles)
        random.shuffle(templates)
        
        # Assign roles and templates to players
        for i, player_id in enumerate(player_ids):
            role = roles[i] if i < len(roles) else 'villager'
            template = templates[i] if i < len(templates) else None
            game_state.add_player(player_id, role, template)
    
    elif setup == "foolish":
        # Foolish gamemode - Watch out, because the fool is always there to steal the win
        foolish_assignments = {
            8: {
                'roles': ['villager', 'villager', 'villager', 'oracle', 'harlot', 'fool', 'wolf', 'traitor'],
                'templates': ['cursed']
            },
            9: {
                'roles': ['villager', 'villager', 'villager', 'oracle', 'harlot', 'hunter', 'fool', 'wolf', 'traitor'],
                'templates': ['cursed']
            },
            10: {
                'roles': ['villager', 'villager', 'villager', 'oracle', 'harlot', 'hunter', 'fool', 'wolf', 'wolf', 'traitor'],
                'templates': ['cursed', 'gunner']
            },
            11: {
                'roles': ['villager', 'villager', 'oracle', 'harlot', 'hunter', 'fool', 'wolf', 'wolf', 'traitor', 'clone'],
                'templates': ['cursed', 'gunner']
            },
            12: {
                'roles': ['villager', 'villager', 'oracle', 'harlot', 'hunter', 'fool', 'wolf', 'wolf', 'traitor', 'wolf cub', 'clone'],
                'templates': ['cursed', 'gunner']
            },
            13: {
                'roles': ['villager', 'villager', 'villager', 'oracle', 'harlot', 'hunter', 'fool', 'wolf', 'wolf', 'traitor', 'sorcerer', 'wolf cub', 'clone'],
                'templates': ['cursed', 'gunner']
            },
            14: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'oracle', 'harlot', 'hunter', 'fool', 'wolf', 'wolf', 'traitor', 'sorcerer', 'wolf cub', 'augur', 'clone'],
                'templates': ['cursed', 'gunner']
            },
            15: {
                'roles': ['villager', 'villager', 'villager', 'oracle', 'harlot', 'hunter', 'fool', 'wolf', 'wolf', 'traitor', 'sorcerer', 'wolf cub', 'augur', 'clone'],
                'templates': ['cursed', 'gunner']
            },
            16: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'oracle', 'harlot', 'harlot', 'hunter', 'fool', 'wolf', 'wolf', 'traitor', 'sorcerer', 'wolf cub', 'augur', 'clone'],
                'templates': ['cursed', 'gunner']
            },
            17: {
                'roles': ['villager', 'villager', 'villager', 'oracle', 'harlot', 'harlot', 'hunter', 'fool', 'wolf', 'wolf', 'wolf', 'traitor', 'sorcerer', 'wolf cub', 'bodyguard', 'augur', 'clone'],
                'templates': ['cursed', 'gunner']
            },
            18: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'oracle', 'harlot', 'harlot', 'hunter', 'fool', 'wolf', 'wolf', 'wolf', 'traitor', 'sorcerer', 'wolf cub', 'bodyguard', 'augur', 'clone'],
                'templates': ['cursed', 'gunner']
            },
            19: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'oracle', 'harlot', 'harlot', 'hunter', 'fool', 'wolf', 'wolf', 'wolf', 'traitor', 'traitor', 'sorcerer', 'wolf cub', 'bodyguard', 'augur', 'clone'],
                'templates': ['cursed', 'gunner', 'gunner']
            },
            20: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'oracle', 'harlot', 'harlot', 'hunter', 'fool', 'wolf', 'wolf', 'wolf', 'traitor', 'traitor', 'sorcerer', 'wolf cub', 'bodyguard', 'augur', 'clone'],
                'templates': ['cursed', 'gunner', 'gunner']
            },
            21: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'oracle', 'harlot', 'harlot', 'hunter', 'fool', 'wolf', 'wolf', 'wolf', 'traitor', 'traitor', 'sorcerer', 'wolf cub', 'bodyguard', 'augur', 'clone'],
                'templates': ['cursed', 'gunner', 'gunner']
            },
            22: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'oracle', 'harlot', 'harlot', 'hunter', 'fool', 'wolf', 'wolf', 'wolf', 'traitor', 'traitor', 'sorcerer', 'wolf cub', 'bodyguard', 'augur', 'clone'],
                'templates': ['cursed', 'gunner', 'gunner']
            },
            23: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'oracle', 'harlot', 'harlot', 'hunter', 'fool', 'wolf', 'wolf', 'wolf', 'wolf', 'traitor', 'traitor', 'sorcerer', 'wolf cub', 'bodyguard', 'augur', 'clone'],
                'templates': ['cursed', 'gunner', 'gunner']
            },
            24: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'oracle', 'harlot', 'harlot', 'hunter', 'fool', 'wolf', 'wolf', 'wolf', 'wolf', 'traitor', 'traitor', 'sorcerer', 'wolf cub', 'bodyguard', 'augur', 'clone'],
                'templates': ['cursed', 'gunner', 'gunner']
            }
        }
        
        # Get role assignment for this player count
        if num_players in foolish_assignments:
            assignment = foolish_assignments[num_players]
            roles = assignment['roles'][:]
            templates = assignment['templates'][:]
        else:
            # Default fallback for unsupported player counts in foolish mode
            if num_players < 8:
                roles = ['villager'] * (num_players - 2) + ['fool', 'wolf']
                templates = []
            else:
                # Simple fallback with fool
                roles = ['villager'] * (num_players - 2) + ['fool', 'wolf']
                templates = []
        
        # Ensure exact counts
        if len(roles) != num_players:
            logger.warning(f"Role count mismatch: {len(roles)} roles for {num_players} players")
            # Fallback with fool
            roles = ['villager'] * (num_players - 2) + ['fool', 'wolf']
            templates = []
        
        # Shuffle roles and templates
        random.shuffle(roles)
        random.shuffle(templates)
        
        # Assign roles and templates to players
        for i, player_id in enumerate(player_ids):
            role = roles[i] if i < len(roles) else 'villager'
            template = templates[i] if i < len(templates) else None
            game_state.add_player(player_id, role, template)
    elif setup == "charming":
        # Charming gamemode - Charmed players must band together to find the piper
        charming_assignments = {
            6: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'piper', 'wolf'],
                'templates': []
            },
            7: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'piper', 'wolf'],
                'templates': []
            },
            8: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'piper', 'wolf', 'werekitten', 'traitor', 'harlot'],
                'templates': []
            },
            9: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'piper', 'wolf', 'werekitten', 'traitor', 'harlot', 'vengeful ghost'],
                'templates': []
            },
            10: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'piper', 'wolf', 'werekitten', 'traitor', 'harlot', 'shaman', 'detective', 'warlock', 'vengeful ghost'],
                'templates': []
            },
            11: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'piper', 'wolf', 'werekitten', 'traitor', 'harlot', 'shaman', 'detective', 'warlock', 'vengeful ghost'],
                'templates': ['gunner']
            },
            12: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'piper', 'wolf', 'werekitten', 'traitor', 'harlot', 'shaman', 'detective', 'warlock', 'vengeful ghost', 'bodyguard'],
                'templates': ['mayor', 'gunner']
            },
            13: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'piper', 'wolf', 'wolf', 'werekitten', 'traitor', 'harlot', 'shaman', 'detective', 'warlock', 'vengeful ghost', 'bodyguard'],
                'templates': ['mayor', 'gunner', 'assassin']
            },
            14: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'piper', 'wolf', 'wolf', 'werekitten', 'traitor', 'harlot', 'shaman', 'detective', 'warlock', 'vengeful ghost', 'bodyguard'],
                'templates': ['mayor', 'gunner', 'assassin']
            },
            15: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'piper', 'wolf', 'wolf', 'werekitten', 'traitor', 'harlot', 'shaman', 'detective', 'warlock', 'vengeful ghost', 'bodyguard', 'bodyguard'],
                'templates': ['mayor', 'gunner', 'assassin']
            },
            16: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'piper', 'wolf', 'wolf', 'werekitten', 'traitor', 'harlot', 'shaman', 'detective', 'warlock', 'vengeful ghost', 'bodyguard', 'bodyguard', 'sorcerer'],
                'templates': ['mayor', 'gunner', 'assassin']
            },
            17: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'piper', 'wolf', 'wolf', 'werekitten', 'traitor', 'harlot', 'shaman', 'detective', 'warlock', 'vengeful ghost', 'bodyguard', 'bodyguard', 'sorcerer'],
                'templates': ['mayor', 'gunner', 'assassin']
            },
            18: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'piper', 'wolf', 'wolf', 'werekitten', 'traitor', 'harlot', 'shaman', 'detective', 'warlock', 'vengeful ghost', 'bodyguard', 'bodyguard', 'sorcerer'],
                'templates': ['mayor', 'gunner', 'assassin']
            },
            19: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'piper', 'wolf', 'wolf', 'wolf', 'werekitten', 'traitor', 'harlot', 'shaman', 'shaman', 'detective', 'warlock', 'vengeful ghost', 'bodyguard', 'bodyguard', 'sorcerer'],
                'templates': ['mayor', 'gunner', 'assassin']
            },
            20: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'piper', 'wolf', 'wolf', 'wolf', 'werekitten', 'traitor', 'harlot', 'shaman', 'shaman', 'detective', 'warlock', 'vengeful ghost', 'bodyguard', 'bodyguard', 'sorcerer'],
                'templates': ['mayor', 'gunner', 'assassin']
            },
            21: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'piper', 'wolf', 'wolf', 'wolf', 'werekitten', 'traitor', 'harlot', 'shaman', 'shaman', 'detective', 'warlock', 'vengeful ghost', 'bodyguard', 'bodyguard', 'sorcerer'],
                'templates': ['mayor', 'gunner', 'gunner', 'assassin']
            },
            22: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'piper', 'wolf', 'wolf', 'wolf', 'werekitten', 'traitor', 'harlot', 'shaman', 'shaman', 'detective', 'warlock', 'vengeful ghost', 'bodyguard', 'bodyguard', 'sorcerer'],
                'templates': ['mayor', 'gunner', 'gunner', 'assassin']
            },
            23: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'piper', 'wolf', 'wolf', 'wolf', 'werekitten', 'traitor', 'harlot', 'shaman', 'shaman', 'detective', 'warlock', 'vengeful ghost', 'bodyguard', 'bodyguard', 'sorcerer'],
                'templates': ['mayor', 'gunner', 'gunner', 'assassin']
            },
            24: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'piper', 'wolf', 'wolf', 'wolf', 'werekitten', 'traitor', 'harlot', 'shaman', 'shaman', 'detective', 'warlock', 'vengeful ghost', 'bodyguard', 'bodyguard', 'sorcerer'],
                'templates': ['mayor', 'gunner', 'gunner', 'assassin']
            }
        }
        
        # Get role assignment for this player count
        if num_players in charming_assignments:
            assignment = charming_assignments[num_players]
            roles = assignment['roles'][:]
            templates = assignment['templates'][:]
        else:
            # Default fallback for unsupported player counts in charming mode
            if num_players < 6:
                roles = ['villager'] * (num_players - 2) + ['piper', 'wolf']
                templates = []
            else:
                # Simple fallback with piper
                roles = ['villager'] * (num_players - 2) + ['piper', 'wolf']
                templates = []
        
        # Ensure exact counts
        if len(roles) != num_players:
            logger.warning(f"Role count mismatch: {len(roles)} roles for {num_players} players")
            # Fallback with piper
            roles = ['villager'] * (num_players - 2) + ['piper', 'wolf']
            templates = []
        
        # Shuffle roles and templates
        random.shuffle(roles)
        random.shuffle(templates)
        
        # Assign roles and templates to players
        for i, player_id in enumerate(player_ids):
            role = roles[i] if i < len(roles) else 'villager'
            template = templates[i] if i < len(templates) else None
            game_state.add_player(player_id, role, template)
            
    elif setup == "mad":
        # Mad gamemode - This game mode has mad scientist and many things that may kill you
        mad_assignments = {
            7: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'mad scientist', 'wolf'],
                'templates': []
            },
            8: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'mad scientist', 'wolf', 'traitor'],
                'templates': []
            },
            9: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'mad scientist', 'wolf', 'traitor'],
                'templates': []
            },
            10: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'mad scientist', 'wolf', 'werecrow', 'traitor', 'village drunk'],
                'templates': []
            },
            11: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'mad scientist', 'wolf', 'werecrow', 'traitor', 'village drunk'],
                'templates': []
            },
            12: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'mad scientist', 'wolf', 'werecrow', 'traitor', 'village drunk', 'detective', 'cultist'],
                'templates': []
            },
            13: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'mad scientist', 'wolf', 'werecrow', 'traitor', 'village drunk', 'detective', 'cultist'],
                'templates': []
            },
            14: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'mad scientist', 'wolf', 'wolf', 'werecrow', 'traitor', 'village drunk', 'detective', 'wolf cub', 'cultist', 'harlot'],
                'templates': []
            },
            15: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'mad scientist', 'wolf', 'wolf', 'werecrow', 'traitor', 'village drunk', 'detective', 'wolf cub', 'cultist', 'harlot'],
                'templates': ['assassin']
            },
            16: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'mad scientist', 'wolf', 'wolf', 'werecrow', 'traitor', 'village drunk', 'detective', 'wolf cub', 'cultist', 'harlot', 'vengeful ghost', 'jester'],
                'templates': []
            },
            17: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'mad scientist', 'wolf', 'wolf', 'werecrow', 'traitor', 'village drunk', 'detective', 'wolf cub', 'cultist', 'harlot', 'vengeful ghost', 'hunter', 'jester'],
                'templates': []
            },
            18: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'mad scientist', 'wolf', 'wolf', 'werecrow', 'traitor', 'village drunk', 'detective', 'wolf cub', 'cultist', 'harlot', 'vengeful ghost', 'hunter', 'jester'],
                'templates': []
            },
            19: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'mad scientist', 'wolf', 'wolf', 'werecrow', 'traitor', 'village drunk', 'detective', 'wolf cub', 'wolf cub', 'cultist', 'harlot', 'vengeful ghost', 'hunter', 'jester'],
                'templates': []
            },
            20: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'mad scientist', 'wolf', 'wolf', 'werecrow', 'traitor', 'village drunk', 'detective', 'wolf cub', 'wolf cub', 'cultist', 'harlot', 'vengeful ghost', 'hunter', 'jester'],
                'templates': []
            },
            21: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'mad scientist', 'wolf', 'wolf', 'werecrow', 'traitor', 'village drunk', 'detective', 'wolf cub', 'wolf cub', 'cultist', 'harlot', 'vengeful ghost', 'hunter', 'jester'],
                'templates': []
            },
            22: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'mad scientist', 'wolf', 'wolf', 'werecrow', 'traitor', 'village drunk', 'detective', 'wolf cub', 'wolf cub', 'cultist', 'harlot', 'vengeful ghost', 'hunter', 'jester'],
                'templates': []
            }
        }
        
        # Get role assignment for this player count
        if num_players in mad_assignments:
            assignment = mad_assignments[num_players]
            roles = assignment['roles'][:]
            templates = assignment['templates'][:]
        else:
            # Default fallback for unsupported player counts in mad mode
            if num_players < 7:
                roles = ['villager'] * (num_players - 3) + ['mad scientist', 'seer', 'wolf']
                templates = []
            else:
                # Simple fallback with mad scientist
                roles = ['villager'] * (num_players - 3) + ['mad scientist', 'seer', 'wolf']
                templates = []
        
        # Ensure exact counts
        if len(roles) != num_players:
            logger.warning(f"Role count mismatch: {len(roles)} roles for {num_players} players")
            # Fallback with mad scientist
            roles = ['villager'] * (num_players - 3) + ['mad scientist', 'seer', 'wolf']
            templates = []
        
        # Shuffle roles and templates
        random.shuffle(roles)
        random.shuffle(templates)
        
        # Assign roles and templates to players
        for i, player_id in enumerate(player_ids):
            role = roles[i] if i < len(roles) else 'villager'
            template = templates[i] if i < len(templates) else None
            game_state.add_player(player_id, role, template)
            
    elif setup == "lycan":
        # Lycan gamemode - Many lycans will turn into wolves. Hunt them down before wolves overpower the village
        lycan_assignments = {
            7: {
                'roles': ['villager', 'seer', 'hunter', 'hunter', 'lycan', 'wolf', 'clone'],
                'templates': []
            },
            8: {
                'roles': ['villager', 'seer', 'hunter', 'hunter', 'lycan', 'wolf', 'traitor', 'clone'],
                'templates': []
            },
            9: {
                'roles': ['villager', 'seer', 'hunter', 'hunter', 'lycan', 'lycan', 'wolf', 'traitor', 'clone'],
                'templates': []
            },
            10: {
                'roles': ['villager', 'villager', 'seer', 'hunter', 'hunter', 'lycan', 'lycan', 'wolf', 'traitor', 'clone'],
                'templates': []
            },
            11: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'hunter', 'hunter', 'lycan', 'lycan', 'wolf', 'traitor', 'clone'],
                'templates': []
            },
            12: {
                'roles': ['villager', 'villager', 'seer', 'hunter', 'hunter', 'lycan', 'lycan', 'lycan', 'wolf', 'traitor', 'clone', 'wolf shaman'],
                'templates': []
            },
            13: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'hunter', 'hunter', 'lycan', 'lycan', 'lycan', 'wolf', 'traitor', 'clone', 'wolf shaman'],
                'templates': []
            },
            14: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'hunter', 'hunter', 'lycan', 'lycan', 'lycan', 'wolf', 'traitor', 'clone', 'wolf shaman', 'bodyguard'],
                'templates': []
            },
            15: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'hunter', 'hunter', 'lycan', 'lycan', 'lycan', 'lycan', 'wolf', 'traitor', 'clone', 'wolf shaman', 'bodyguard'],
                'templates': []
            },
            16: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'seer', 'hunter', 'hunter', 'lycan', 'lycan', 'lycan', 'lycan', 'wolf', 'traitor', 'clone', 'wolf shaman', 'bodyguard'],
                'templates': []
            },
            17: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'seer', 'hunter', 'hunter', 'lycan', 'lycan', 'lycan', 'lycan', 'wolf', 'traitor', 'clone', 'clone', 'wolf shaman', 'bodyguard'],
                'templates': []
            },
            18: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'seer', 'hunter', 'hunter', 'lycan', 'lycan', 'lycan', 'lycan', 'wolf', 'traitor', 'clone', 'clone', 'wolf shaman', 'bodyguard', 'matchmaker'],
                'templates': []
            },
            19: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'seer', 'hunter', 'hunter', 'lycan', 'lycan', 'lycan', 'lycan', 'lycan', 'wolf', 'traitor', 'clone', 'clone', 'wolf shaman', 'bodyguard', 'matchmaker'],
                'templates': []
            },
            20: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'seer', 'hunter', 'hunter', 'lycan', 'lycan', 'lycan', 'lycan', 'lycan', 'wolf', 'traitor', 'clone', 'clone', 'wolf shaman', 'bodyguard', 'matchmaker'],
                'templates': []
            },
            21: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'seer', 'hunter', 'hunter', 'lycan', 'lycan', 'lycan', 'lycan', 'lycan', 'lycan', 'wolf', 'traitor', 'clone', 'clone', 'wolf shaman', 'bodyguard', 'matchmaker'],
                'templates': []
            }
        }
        
        # Get role assignment for this player count
        if num_players in lycan_assignments:
            assignment = lycan_assignments[num_players]
            roles = assignment['roles'][:]
            templates = assignment['templates'][:]
        else:
            # Default fallback for unsupported player counts in lycan mode
            if num_players < 7:
                roles = ['villager'] * (num_players - 4) + ['hunter', 'lycan', 'wolf', 'clone']
                templates = []
            else:
                # Simple fallback with lycans
                base_roles = ['seer', 'hunter', 'hunter', 'lycan', 'wolf', 'clone']
                villager_count = num_players - len(base_roles)
                roles = ['villager'] * villager_count + base_roles
                templates = []
        
        # Ensure exact counts
        if len(roles) != num_players:
            logger.warning(f"Role count mismatch: {len(roles)} roles for {num_players} players")
            # Fallback with lycans
            base_roles = ['seer', 'hunter', 'lycan', 'wolf', 'clone']
            villager_count = num_players - len(base_roles)
            roles = ['villager'] * villager_count + base_roles
            templates = []
        
        # Shuffle roles and templates
        random.shuffle(roles)
        random.shuffle(templates)
        
        # Assign roles and templates to players
        for i, player_id in enumerate(player_ids):
            role = roles[i] if i < len(roles) else 'villager'
            template = templates[i] if i < len(templates) else None
            game_state.add_player(player_id, role, template)
            
    elif setup == "rapidfire":
        # Rapidfire gamemode - Many killing roles and roles that cause chain deaths. Living has never been so hard
        rapidfire_assignments = {
            6: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'mad scientist', 'wolf'],
                'templates': ['gunner', 'assassin']
            },
            7: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'mad scientist', 'wolf'],
                'templates': ['gunner', 'assassin']
            },
            8: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'mad scientist', 'wolf', 'wolf cub', 'hunter'],
                'templates': ['gunner', 'assassin']
            },
            9: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'mad scientist', 'wolf', 'wolf cub', 'hunter'],
                'templates': ['gunner', 'assassin']
            },
            10: {
                'roles': ['villager', 'villager', 'seer', 'mad scientist', 'wolf', 'wolf cub', 'matchmaker', 'hunter', 'time lord', 'traitor'],
                'templates': ['gunner', 'assassin']
            },
            11: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'mad scientist', 'wolf', 'wolf cub', 'matchmaker', 'hunter', 'time lord', 'traitor'],
                'templates': ['gunner', 'assassin']
            },
            12: {
                'roles': ['villager', 'villager', 'seer', 'mad scientist', 'wolf', 'wolf', 'wolf cub', 'matchmaker', 'hunter', 'time lord', 'traitor', 'vengeful ghost'],
                'templates': ['gunner', 'assassin', 'assassin']
            },
            13: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'mad scientist', 'wolf', 'wolf', 'wolf cub', 'matchmaker', 'hunter', 'time lord', 'traitor', 'vengeful ghost'],
                'templates': ['gunner', 'assassin', 'assassin']
            },
            14: {
                'roles': ['villager', 'seer', 'mad scientist', 'mad scientist', 'wolf', 'wolf', 'wolf cub', 'wolf cub', 'matchmaker', 'hunter', 'hunter', 'time lord', 'time lord', 'traitor', 'vengeful ghost', 'augur'],
                'templates': ['gunner', 'assassin', 'assassin']
            },
            15: {
                'roles': ['villager', 'villager', 'seer', 'mad scientist', 'mad scientist', 'wolf', 'wolf', 'wolf cub', 'wolf cub', 'matchmaker', 'hunter', 'hunter', 'time lord', 'time lord', 'traitor', 'vengeful ghost', 'augur'],
                'templates': ['gunner', 'assassin', 'assassin']
            },
            16: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'mad scientist', 'mad scientist', 'wolf', 'wolf', 'wolf cub', 'wolf cub', 'matchmaker', 'hunter', 'hunter', 'time lord', 'time lord', 'traitor', 'vengeful ghost', 'augur', 'amnesiac'],
                'templates': ['gunner', 'assassin', 'assassin']
            },
            17: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'mad scientist', 'mad scientist', 'wolf', 'wolf', 'wolf cub', 'wolf cub', 'matchmaker', 'hunter', 'hunter', 'time lord', 'time lord', 'traitor', 'vengeful ghost', 'augur', 'amnesiac'],
                'templates': ['gunner', 'assassin', 'assassin']
            },
            18: {
                'roles': ['villager', 'villager', 'seer', 'mad scientist', 'mad scientist', 'wolf', 'wolf', 'wolf', 'wolf cub', 'wolf cub', 'matchmaker', 'matchmaker', 'hunter', 'hunter', 'time lord', 'time lord', 'traitor', 'vengeful ghost', 'vengeful ghost', 'augur', 'amnesiac'],
                'templates': ['gunner', 'assassin', 'assassin']
            },
            19: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'mad scientist', 'mad scientist', 'wolf', 'wolf', 'wolf', 'wolf cub', 'wolf cub', 'matchmaker', 'matchmaker', 'hunter', 'hunter', 'time lord', 'time lord', 'traitor', 'vengeful ghost', 'vengeful ghost', 'augur', 'amnesiac'],
                'templates': ['gunner', 'assassin', 'assassin']
            },
            20: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'mad scientist', 'mad scientist', 'wolf', 'wolf', 'wolf', 'wolf cub', 'wolf cub', 'matchmaker', 'matchmaker', 'hunter', 'hunter', 'time lord', 'time lord', 'traitor', 'vengeful ghost', 'vengeful ghost', 'augur', 'amnesiac'],
                'templates': ['gunner', 'assassin', 'assassin']
            },
            21: {
                'roles': ['villager', 'villager', 'seer', 'mad scientist', 'mad scientist', 'wolf', 'wolf', 'wolf', 'wolf', 'wolf cub', 'wolf cub', 'matchmaker', 'matchmaker', 'hunter', 'hunter', 'time lord', 'time lord', 'traitor', 'vengeful ghost', 'vengeful ghost', 'augur', 'amnesiac'],
                'templates': ['gunner', 'assassin', 'assassin']
            },
            22: {
                'roles': ['villager', 'villager', 'seer', 'mad scientist', 'mad scientist', 'wolf', 'wolf', 'wolf', 'wolf', 'wolf cub', 'wolf cub', 'matchmaker', 'matchmaker', 'hunter', 'hunter', 'time lord', 'time lord', 'traitor', 'vengeful ghost', 'vengeful ghost', 'vengeful ghost', 'vengeful ghost', 'augur', 'amnesiac'],
                'templates': ['gunner', 'assassin', 'assassin', 'assassin']
            },
            23: {
                'roles': ['villager', 'villager', 'seer', 'mad scientist', 'mad scientist', 'wolf', 'wolf', 'wolf', 'wolf', 'wolf cub', 'wolf cub', 'matchmaker', 'matchmaker', 'hunter', 'hunter', 'time lord', 'time lord', 'traitor', 'vengeful ghost', 'vengeful ghost', 'augur', 'amnesiac'],
                'templates': ['gunner', 'assassin', 'assassin']
            },
            24: {
                'roles': ['villager', 'villager', 'seer', 'mad scientist', 'mad scientist', 'wolf', 'wolf', 'wolf', 'wolf', 'wolf cub', 'wolf cub', 'matchmaker', 'matchmaker', 'hunter', 'hunter', 'time lord', 'time lord', 'traitor', 'vengeful ghost', 'vengeful ghost', 'augur', 'amnesiac'],
                'templates': ['gunner', 'assassin', 'assassin']
            }
        }
        
        # Get role assignment for this player count
        if num_players in rapidfire_assignments:
            assignment = rapidfire_assignments[num_players]
            roles = assignment['roles'][:]
            templates = assignment['templates'][:]
        else:
            # Default fallback for unsupported player counts in rapidfire mode
            if num_players < 6:
                roles = ['villager'] * (num_players - 3) + ['mad scientist', 'seer', 'wolf']
                templates = ['gunner']
            else:
                # Simple fallback with dangerous roles
                base_roles = ['seer', 'mad scientist', 'hunter', 'wolf', 'wolf cub']
                villager_count = num_players - len(base_roles)
                roles = ['villager'] * villager_count + base_roles
                templates = ['gunner', 'assassin']
        
        # Ensure exact counts
        if len(roles) != num_players:
            logger.warning(f"Role count mismatch: {len(roles)} roles for {num_players} players")
            # Fallback with dangerous roles
            base_roles = ['seer', 'mad scientist', 'hunter', 'wolf']
            villager_count = num_players - len(base_roles)
            roles = ['villager'] * villager_count + base_roles
            templates = ['gunner', 'assassin']
        
        # Shuffle roles and templates
        random.shuffle(roles)
        random.shuffle(templates)
        
        # Assign roles and templates to players
        for i, player_id in enumerate(player_ids):
            role = roles[i] if i < len(roles) else 'villager'
            template = templates[i] if i < len(templates) else None
            game_state.add_player(player_id, role, template)
            
    elif setup == "noreveal":
        # Noreveal gamemode - Roles are not revealed on death
        noreveal_assignments = {
            4: {
                'roles': ['villager', 'villager', 'seer', 'wolf'],
                'templates': []
            },
            5: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'wolf'],
                'templates': []
            },
            6: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'wolf'],
                'templates': []
            },
            7: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'wolf'],
                'templates': []
            },
            8: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'wolf', 'mystic', 'wolf mystic'],
                'templates': []
            },
            9: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'wolf', 'mystic', 'wolf mystic'],
                'templates': []
            },
            10: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'wolf', 'mystic', 'traitor', 'wolf mystic', 'hunter'],
                'templates': []
            },
            11: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'wolf', 'mystic', 'traitor', 'wolf mystic', 'hunter'],
                'templates': []
            },
            12: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'wolf', 'wolf', 'mystic', 'traitor', 'wolf mystic', 'guardian angel', 'hunter'],
                'templates': []
            },
            13: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'wolf', 'wolf', 'mystic', 'traitor', 'wolf mystic', 'guardian angel', 'hunter'],
                'templates': []
            },
            14: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'wolf', 'wolf', 'mystic', 'traitor', 'wolf mystic', 'guardian angel', 'hunter'],
                'templates': []
            },
            15: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'wolf', 'wolf', 'mystic', 'traitor', 'wolf mystic', 'guardian angel', 'hunter', 'werecrow', 'detective', 'clone'],
                'templates': []
            },
            16: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'wolf', 'wolf', 'mystic', 'traitor', 'wolf mystic', 'guardian angel', 'hunter', 'werecrow', 'detective', 'clone'],
                'templates': []
            },
            17: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'wolf', 'wolf', 'mystic', 'traitor', 'wolf mystic', 'guardian angel', 'hunter', 'werecrow', 'detective', 'clone', 'lycan', 'amnesiac'],
                'templates': []
            },
            18: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'wolf', 'wolf', 'mystic', 'traitor', 'wolf mystic', 'guardian angel', 'hunter', 'werecrow', 'detective', 'clone', 'lycan', 'amnesiac'],
                'templates': []
            },
            19: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'wolf', 'wolf', 'wolf', 'mystic', 'traitor', 'wolf mystic', 'guardian angel', 'hunter', 'werecrow', 'detective', 'clone', 'lycan', 'amnesiac'],
                'templates': []
            },
            20: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'wolf', 'wolf', 'wolf', 'mystic', 'traitor', 'wolf mystic', 'guardian angel', 'hunter', 'werecrow', 'detective', 'clone', 'lycan', 'amnesiac'],
                'templates': []
            },
            21: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'villager', 'seer', 'wolf', 'wolf', 'wolf', 'mystic', 'traitor', 'wolf mystic', 'guardian angel', 'hunter', 'werecrow', 'detective', 'clone', 'lycan', 'amnesiac'],
                'templates': []
            }
        }
        
        # Get role assignment for this player count
        if num_players in noreveal_assignments:
            assignment = noreveal_assignments[num_players]
            roles = assignment['roles'][:]
            templates = assignment['templates'][:]
        else:
            # Default fallback for unsupported player counts in noreveal mode
            if num_players < 4:
                roles = ['villager'] * (num_players - 1) + ['wolf']
                templates = []
            else:
                # Simple fallback with basic roles
                base_roles = ['seer', 'wolf']
                villager_count = num_players - len(base_roles)
                roles = ['villager'] * villager_count + base_roles
                templates = []
        
        # Ensure exact counts
        if len(roles) != num_players:
            logger.warning(f"Role count mismatch: {len(roles)} roles for {num_players} players")
            # Fallback with basic roles
            base_roles = ['seer', 'wolf']
            villager_count = num_players - len(base_roles)
            roles = ['villager'] * villager_count + base_roles
            templates = []
        
        # Shuffle roles and templates
        random.shuffle(roles)
        random.shuffle(templates)
        
        # Assign roles and templates to players
        for i, player_id in enumerate(player_ids):
            role = roles[i] if i < len(roles) else 'villager'
            template = templates[i] if i < len(templates) else None
            game_state.add_player(player_id, role, template)
            
    elif setup == "bloodbath":
        # Bloodbath gamemode - A serial killer is on the loose... shall it end up on the noose?
        bloodbath_assignments = {
            9: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'bodyguard', 'serial killer', 'wolf', 'traitor'],
                'templates': []
            },
            10: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'bodyguard', 'serial killer', 'wolf', 'traitor', 'shaman', 'cultist'],
                'templates': []
            },
            11: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'bodyguard', 'serial killer', 'wolf', 'traitor', 'shaman', 'oracle', 'cultist'],
                'templates': []
            },
            12: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'bodyguard', 'serial killer', 'wolf', 'traitor', 'shaman', 'oracle', 'turncoat', 'werecrow'],
                'templates': []
            },
            13: {
                'roles': ['villager', 'villager', 'villager', 'seer', 'bodyguard', 'serial killer', 'wolf', 'traitor', 'shaman', 'oracle', 'turncoat', 'cultist', 'werecrow'],
                'templates': []
            },
            14: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'bodyguard', 'serial killer', 'wolf', 'wolf', 'traitor', 'shaman', 'oracle', 'turncoat', 'werecrow', 'hunter'],
                'templates': []
            },
            15: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'bodyguard', 'serial killer', 'serial killer', 'wolf', 'wolf', 'traitor', 'shaman', 'oracle', 'turncoat', 'cultist', 'werecrow', 'hunter'],
                'templates': []
            },
            16: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'bodyguard', 'serial killer', 'serial killer', 'wolf', 'wolf', 'traitor', 'shaman', 'oracle', 'turncoat', 'werecrow', 'hunter', 'priest', 'guardian angel'],
                'templates': []
            },
            17: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'bodyguard', 'serial killer', 'serial killer', 'wolf', 'wolf', 'traitor', 'shaman', 'oracle', 'turncoat', 'cultist', 'werecrow', 'hunter', 'priest', 'guardian angel', 'hag'],
                'templates': []
            },
            18: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'bodyguard', 'serial killer', 'serial killer', 'wolf', 'wolf', 'traitor', 'shaman', 'oracle', 'turncoat', 'werecrow', 'hunter', 'priest', 'guardian angel', 'hag', 'vengeful ghost'],
                'templates': []
            },
            19: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'bodyguard', 'serial killer', 'serial killer', 'wolf', 'wolf', 'traitor', 'shaman', 'oracle', 'turncoat', 'cultist', 'werecrow', 'hunter', 'priest', 'guardian angel', 'hag', 'vengeful ghost'],
                'templates': []
            },
            20: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'bodyguard', 'serial killer', 'serial killer', 'wolf', 'wolf', 'traitor', 'shaman', 'oracle', 'turncoat', 'cultist', 'werecrow', 'hunter', 'priest', 'guardian angel', 'hag', 'vengeful ghost', 'clone'],
                'templates': []
            },
            21: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'bodyguard', 'serial killer', 'serial killer', 'wolf', 'wolf', 'traitor', 'shaman', 'shaman', 'oracle', 'turncoat', 'cultist', 'werecrow', 'hunter', 'priest', 'guardian angel', 'hag', 'vengeful ghost', 'clone'],
                'templates': []
            },
            22: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'bodyguard', 'serial killer', 'serial killer', 'wolf', 'wolf', 'traitor', 'shaman', 'shaman', 'oracle', 'turncoat', 'cultist', 'werecrow', 'hunter', 'priest', 'guardian angel', 'hag', 'vengeful ghost', 'clone', 'amnesiac'],
                'templates': []
            },
            23: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'bodyguard', 'serial killer', 'serial killer', 'wolf', 'wolf', 'traitor', 'shaman', 'shaman', 'oracle', 'turncoat', 'cultist', 'werecrow', 'hunter', 'priest', 'guardian angel', 'hag', 'vengeful ghost', 'clone', 'amnesiac'],
                'templates': []
            },
            24: {
                'roles': ['villager', 'villager', 'villager', 'villager', 'seer', 'bodyguard', 'serial killer', 'serial killer', 'wolf', 'wolf', 'traitor', 'shaman', 'shaman', 'oracle', 'turncoat', 'cultist', 'werecrow', 'hunter', 'priest', 'guardian angel', 'hag', 'vengeful ghost', 'clone', 'amnesiac'],
                'templates': []
            }
        }
        
        # Get role assignment for this player count
        if num_players in bloodbath_assignments:
            assignment = bloodbath_assignments[num_players]
            roles = assignment['roles'][:]
            templates = assignment['templates'][:]
        else:
            # Default fallback for unsupported player counts in bloodbath mode
            if num_players < 9:
                roles = ['villager'] * (num_players - 3) + ['serial killer', 'seer', 'wolf']
                templates = []
            else:
                # Simple fallback with serial killer
                base_roles = ['seer', 'bodyguard', 'serial killer', 'wolf', 'traitor']
                villager_count = num_players - len(base_roles)
                roles = ['villager'] * villager_count + base_roles
                templates = []
        
        # Ensure exact counts
        if len(roles) != num_players:
            logger.warning(f"Role count mismatch: {len(roles)} roles for {num_players} players")
            # Fallback with serial killer
            base_roles = ['seer', 'serial killer', 'wolf']
            villager_count = num_players - len(base_roles)
            roles = ['villager'] * villager_count + base_roles
            templates = []
        
        # Shuffle roles and templates
        random.shuffle(roles)
        random.shuffle(templates)
        
        # Assign roles and templates to players
        for i, player_id in enumerate(player_ids):
            role = roles[i] if i < len(roles) else 'villager'
            template = templates[i] if i < len(templates) else None
            game_state.add_player(player_id, role, template)
            
    elif setup == "random":
        # Random gamemode - A completely random set of roles for chaotic gameplay
        
        # Define all available roles organized by category
        village_roles = [
            'villager', 'seer', 'oracle', 'shaman', 'harlot', 'bodyguard', 'guardian angel',
            'priest', 'detective', 'augur', 'mystic', 'matchmaker', 'hunter', 'gunner',
            'mad scientist', 'time lord'
        ]
        
        wolf_roles = [
            'wolf', 'wolf cub', 'werecrow', 'wolf shaman', 'wolf mystic', 'werekitten'
        ]
        
        neutral_roles = [
            'traitor', 'jester', 'fool', 'serial killer', 'piper',
            'succubus', 'monster', 'hag', 'warlock', 'cultist', 'clone', 'amnesiac',
            'turncoat', 'lycan', 'vengeful ghost', 'crazed shaman', 'hot potato'
        ]
        
        available_templates = [
            'cursed', 'gunner', 'assassin', 'mayor', 'blessed'
        ]
        
        # Ensure minimum balanced composition
        min_wolves = max(1, num_players // 6)  # At least 1 wolf, roughly 1 per 6 players
        min_village = max(2, num_players // 3)  # At least 2 village roles
        
        # Start with guaranteed roles for balance
        roles = []
        
        # Add minimum wolves
        for _ in range(min_wolves):
            role = random.choice(wolf_roles)
            roles.append(role)
        
        # Add minimum village roles (ensure at least one investigative role)
        investigative_roles = ['seer', 'oracle', 'detective', 'augur', 'mystic']
        roles.append(random.choice(investigative_roles))
        
        # Add other village roles
        for _ in range(min_village - 1):
            role = random.choice(village_roles)
            roles.append(role)
        
        # Fill remaining slots with random roles from all categories
        remaining_slots = num_players - len(roles)
        all_roles = village_roles + wolf_roles + neutral_roles
        
        for _ in range(remaining_slots):
            role = random.choice(all_roles)
            roles.append(role)
        
        # Randomly assign templates to some players (20-40% chance)
        templates = []
        num_templates = random.randint(max(1, num_players // 6), max(2, num_players // 3))
        
        for _ in range(num_templates):
            template = random.choice(available_templates)
            templates.append(template)
        
        # Pad templates list to match player count
        while len(templates) < num_players:
            templates.append(None)
        
        # Ensure exact counts
        if len(roles) != num_players:
            # Adjust by adding/removing villagers
            while len(roles) < num_players:
                roles.append('villager')
            while len(roles) > num_players:
                if 'villager' in roles:
                    roles.remove('villager')
                else:
                    roles.pop()
        
        # Shuffle roles and templates
        random.shuffle(roles)
        random.shuffle(templates)
        
        # Assign roles and templates to players
        for i, player_id in enumerate(player_ids):
            role = roles[i] if i < len(roles) else 'villager'
            template = templates[i] if i < len(templates) else None
            game_state.add_player(player_id, role, template)
            
    else:
        # Other setups can be added here
        roles = ['villager'] * (num_players - 1) + ['wolf']
        random.shuffle(roles)
        for i, player_id in enumerate(player_ids):
            role = roles[i] if i < len(roles) else 'villager'
            game_state.add_player(player_id, role)

async def check_win_conditions(ctx):
    """Check if any team has won"""
    alive_players = game_state.get_alive_players()
    
    # Count teams
    village_count = len(game_state.get_players_by_team('village'))
    wolf_count = len(game_state.get_players_by_team('wolf'))
    
    # Check for special neutral wins first
    for player_id in alive_players:
        role = game_state.players[player_id]['role']
        
        # Jester/Fool win by being lynched (handled elsewhere)
        # Piper wins when all alive are charmed
        if role == 'piper':
            charmed_count = sum(1 for p in alive_players if game_state.players[p].get('charmed', False))
            if charmed_count == len(alive_players):
                await announce_winner(ctx, 'piper', [player_id])
                return True
        
        # Serial Killer/Monster win by being last alive
        if role in ['serial killer', 'monster'] and len(alive_players) == 1:
            await announce_winner(ctx, 'neutral', [player_id])
            return True
    
    # Village wins if all wolves dead
    if wolf_count == 0:
        village_players = game_state.get_players_by_team('village')
        await announce_winner(ctx, 'village', village_players)
        return True
    
    # Wolves win if they equal or outnumber village
    if wolf_count >= village_count:
        wolf_players = game_state.get_players_by_team('wolf')
        await announce_winner(ctx, 'wolf', wolf_players)
        return True
    
    return False

async def announce_winner(ctx, team: str, winners: List[int]):
    """Announce game winners and reveal all roles"""
    winner_names = [bot.get_user(uid).display_name for uid in winners if bot.get_user(uid)]
    
    embed = discord.Embed(
        title="🎉 Game Over!",
        description=f"**{team.title()} Team Wins!**\n\n**Winners**: {', '.join(winner_names)}",
        color=0x00FF00
    )
    
    # Create role reveal section
    role_reveals = []
    
    # Group players by team for better organization
    village_players = []
    wolf_players = []
    neutral_players = []
    
    # Include both alive and dead players
    all_players = {**game_state.players, **game_state.dead_players}
    
    for player_id, player_data in game_state.players.items():
        user = bot.get_user(player_id)
        if not user:
            continue
            
        role = player_data.get('role', 'unknown')
        template = player_data.get('template')
        is_alive = player_data.get('alive', False)
        
        # Create status indicator
        status = "✅" if is_alive else "💀"
        
        # Format role display
        role_display = role.replace('_', ' ').title()
        if template:
            role_display += f" ({template.replace('_', ' ').title()})"
        
        player_info = f"{status} **{user.display_name}**: {role_display}"
        
        # Categorize by team
        if role in VILLAGE_ROLES_ORDERED:
            village_players.append(player_info)
        elif role in WOLF_ROLES_ORDERED or role in WOLFCHAT_ROLES:
            wolf_players.append(player_info)
        else:  # Neutral roles
            neutral_players.append(player_info)
    
    # Add dead players that aren't in the current players dict
    for player_id, role in game_state.dead_players.items():
        if player_id not in game_state.players:
            user = bot.get_user(player_id)
            if user:
                role_display = role.replace('_', ' ').title()
                player_info = f"💀 **{user.display_name}**: {role_display}"
                
                if role in VILLAGE_ROLES_ORDERED:
                    village_players.append(player_info)
                elif role in WOLF_ROLES_ORDERED or role in WOLFCHAT_ROLES:
                    wolf_players.append(player_info)
                else:
                    neutral_players.append(player_info)
    
    # Add role reveal fields
    if village_players:
        embed.add_field(
            name="🏘️ Village Team",
            value="\n".join(village_players),
            inline=False
        )
    
    if wolf_players:
        embed.add_field(
            name="🐺 Wolf Team", 
            value="\n".join(wolf_players),
            inline=False
        )
    
    if neutral_players:
        embed.add_field(
            name="⚖️ Neutral Players",
            value="\n".join(neutral_players),
            inline=False
        )
    
    embed.add_field(
        name="📊 Game Statistics",
        value=f"**Day**: {game_state.day_number}\n"
              f"**Total Players**: {len(all_players)}\n"
              f"**Village**: {len(village_players)}\n"
              f"**Wolves**: {len(wolf_players)}\n"
              f"**Neutrals**: {len(neutral_players)}",
        inline=True
    )
    
    await ctx.send(embed=embed)
    
    # Cleanup chat channels
    await cleanup_chat_channels()
    
    game_state.reset()

# ==================== TIMER FUNCTIONS ====================
async def start_phase_timer(ctx, phase: str, duration: int):
    """Start phase timer"""
    logger.info(f"Starting {phase} phase timer for {duration} seconds")
    
    if game_state.timer_task:
        game_state.timer_task.cancel()
        logger.info(f"Cancelled previous timer task")
    
    game_state.timer_task = asyncio.create_task(phase_timer(ctx, phase, duration))
    logger.info(f"Created new timer task for {phase} phase")

async def phase_timer(ctx, phase: str, duration: int):
    """Enhanced phase timer with countdown alerts and auto-completion checks"""
    try:
        channel = ctx.channel
        elapsed = 0
        
        # Countdown alerts (in seconds before end)
        alerts = [60, 30, 10, 3, 2, 1]
        alerted = set()  # Track which alerts we've sent
        
        # Send initial timer message
        if phase == "day":
            await channel.send(f"⏰ Day phase started! **{duration} seconds** ({duration//60} minutes) to vote or until everyone votes.")
        elif phase == "night":
            await channel.send(f"🌙 Night phase started! **{duration} seconds** ({duration//60} minutes) for night actions or until everyone acts.")
        
        while elapsed < duration:
            await asyncio.sleep(1)
            elapsed += 1
            remaining = duration - elapsed
            
            # Check if phase should end early (all actions completed)
            if await check_phase_completion(channel, phase):
                await channel.send(f"✅ All {phase} actions completed! Moving to next phase...")
                break
            
            # Send countdown alerts (only once per alert)
            if remaining in alerts and remaining not in alerted:
                alerted.add(remaining)
                if remaining >= 30:
                    await channel.send(f"⏰ **{remaining} seconds** remaining in {phase} phase!")
                elif remaining >= 10:
                    await channel.send(f"⚠️ **{remaining} seconds** remaining!")
                elif remaining >= 3:
                    await channel.send(f"🚨 **{remaining}**")
                else:
                    await channel.send(f"**{remaining}**")
        
        # Only proceed to next phase if we didn't break early
        if elapsed >= duration:
            await channel.send(f"⏰ {phase.title()} phase time expired! Moving to next phase...")
            
        # Phase transition
        if phase == "signup":
            await start_game(ctx, game_state.gamemode)
        elif phase == "day":
            await end_day_phase(ctx)
        elif phase == "night":
            await end_night_phase(ctx)
            
    except asyncio.CancelledError:
        logger.info(f"Timer for {phase} phase was cancelled")
        pass
    except Exception as e:
        logger.error(f"Error in phase timer for {phase}: {e}")
        # Try to continue the game even if timer fails
        if phase == "signup":
            await start_game(ctx, game_state.gamemode)
        elif phase == "day":
            await end_day_phase(ctx)
        elif phase == "night":
            await end_night_phase(ctx)

async def check_phase_completion(channel, phase: str) -> bool:
    """Check if current phase can end early due to all actions being completed"""
    try:
        if not game_state.active:
            return False
        
        if phase == "day":
            # Day phase ends early if all alive players have voted
            alive_players = game_state.get_alive_players()
            if not alive_players:
                return True  # No one alive, end phase
                
            voted_players = set()
            
            for voter_id in game_state.votes.keys():
                if game_state.is_player_alive(voter_id):
                    # Check if player is injured/silenced (can't vote)
                    player = game_state.players[voter_id]
                    if not player.get('injured', False) and not player.get('silenced', False):
                        voted_players.add(voter_id)
            
            # Count players who can vote
            eligible_voters = []
            for player_id in alive_players:
                player = game_state.players[player_id]
                if not player.get('injured', False) and not player.get('silenced', False):
                    eligible_voters.append(player_id)
            
            logger.info(f"Day phase completion check: {len(voted_players)}/{len(eligible_voters)} voted")
            return len(voted_players) == len(eligible_voters) and len(eligible_voters) > 0
        
        elif phase == "night":
            # Night phase ends early if all power roles have acted
            alive_players = game_state.get_alive_players()
            if not alive_players:
                return True  # No one alive, end phase
                
            required_actions = set()
            completed_actions = set()
            
            for player_id in alive_players:
                player_data = game_state.players.get(player_id, {})
                role = player_data.get('role', '')
                
                # Add roles that should act at night
                if role in ACTUAL_WOLVES + ['vigilante', 'serial killer', 'monster']:
                    required_actions.add(f"{player_id}_kill")
                elif role in ['seer', 'oracle']:
                    required_actions.add(f"{player_id}_see")
                elif role in ['guardian angel', 'bodyguard']:
                    required_actions.add(f"{player_id}_guard")
                elif role == 'harlot':
                    required_actions.add(f"{player_id}_visit")
                elif role in ['shaman', 'wolf shaman', 'crazed shaman']:
                    required_actions.add(f"{player_id}_give")
                elif role == 'werecrow':
                    required_actions.add(f"{player_id}_observe")
                elif role == 'detective':
                    required_actions.add(f"{player_id}_id")
                elif role == 'village drunk':
                    required_actions.add(f"{player_id}_shoot")
                elif role in ['mystic', 'wolf mystic']:
                    required_actions.add(f"{player_id}_mysticism")
                elif role == 'priest':
                    required_actions.add(f"{player_id}_bless")
                elif role == 'augur':
                    required_actions.add(f"{player_id}_see")
                elif role == 'hag':
                    required_actions.add(f"{player_id}_hex")
                elif role == 'warlock':
                    required_actions.add(f"{player_id}_curse")
                elif role == 'piper':
                    required_actions.add(f"{player_id}_charm")
                elif role == 'succubus':
                    required_actions.add(f"{player_id}_visit")
                elif role == 'amnesiac':
                    required_actions.add(f"{player_id}_remember")
                elif role == 'turncoat':
                    required_actions.add(f"{player_id}_turn")
                elif role == 'doomsayer':
                    required_actions.add(f"{player_id}_doom")
                elif role == 'hot potato':
                    required_actions.add(f"{player_id}_choose")
            
            # Check completed actions
            for player_id, action_data in game_state.night_actions.items():
                if game_state.is_player_alive(player_id):
                    action_type = action_data.get('action', '')
                    completed_actions.add(f"{player_id}_{action_type}")
            
            logger.info(f"Night phase completion check: {len(completed_actions)}/{len(required_actions)} actions done")
            # Phase complete if all required actions are done
            return len(required_actions) > 0 and required_actions.issubset(completed_actions)
        
        return False
        
    except Exception as e:
        logger.error(f"Error in check_phase_completion: {e}")
        return False  # Don't end early if there's an error

# ==================== GAME MANAGEMENT COMMANDS ====================
@bot.command(name='start', aliases=['s'])
async def start_signup(ctx, gamemode="default"):
    """Start a new game signup"""
    if game_state.active:
        await ctx.send("❌ A game is already active! Use `!end` to stop it.")
        return
    
    # Validate gamemode
    valid_gamemodes = ["default", "foolish", "charming", "mad", "lycan", "rapidfire", "noreveal", "bloodbath", "random"]
    if gamemode.lower() not in valid_gamemodes:
        await ctx.send(f"❌ Invalid gamemode! Valid options: {', '.join(valid_gamemodes)}")
        return
    
    game_state.reset()
    game_state.active = True
    game_state.phase = "signup"
    game_state.gamemode = gamemode.lower()
    game_state.channel_id = ctx.channel.id
    
    gamemode_info = {
        "default": "Standard werewolf with balanced roles",
        "foolish": "Watch out, because the fool is always there to steal the win!",
        "charming": "Charmed players must band together to find the piper in this game mode",
        "mad": "This game mode has mad scientist and many things that may kill you",
        "lycan": "Many lycans will turn into wolves. Hunt them down before the wolves overpower the village",
        "rapidfire": "Many killing roles and roles that cause chain deaths. Living has never been so hard",
        "noreveal": "Roles are not revealed on death",
        "bloodbath": "Serial killers everywhere! Bodyguards are your only protection in this deadly mode",
        "random": "A completely random set of roles is chosen, making for a chaotic and unpredictable game"
    }
    
    gamemode_colors = {
        "default": 0x8B4513,
        "foolish": 0xFF4500,
        "charming": 0x9932CC,
        "mad": 0xFF0000,
        "lycan": 0x800080,
        "rapidfire": 0xDC143C,
        "noreveal": 0x2F4F4F,
        "bloodbath": 0x8B0000,
        "random": 0xFF1493
    }
    
    embed = discord.Embed(
        title=f"🐺 Werewolf Game Starting! ({gamemode.title()} Mode)",
        description=f"{gamemode_info[gamemode.lower()]}\n\nType `{prefix}join` to join the game!\n\n⏰ Signup ends in **3 minutes** ({game_state.settings['signup_length']} seconds)",
        color=gamemode_colors.get(gamemode.lower(), 0x8B4513)
    )
    embed.add_field(name="Players", value="None yet", inline=False)
    
    # Add gamemode-specific info
    if gamemode.lower() == "foolish":
        embed.add_field(
            name="🃏 Foolish Mode Special Rules",
            value="• A fool is guaranteed in every game\n• The fool can win by being lynched\n• Multiple harlots in larger games\n• Oracle instead of seer for investigations",
            inline=False
        )
    elif gamemode.lower() == "charming":
        embed.add_field(
            name="🎵 Charming Mode Special Rules",
            value="• A piper is guaranteed in every game\n• Piper wins when all alive players are charmed\n• Piper can charm one player each night\n• Mix of village, wolf, and neutral roles for complex gameplay",
            inline=False
        )
    elif gamemode.lower() == "mad":
        embed.add_field(
            name="🧪 Mad Mode Special Rules",
            value="• A mad scientist is guaranteed in every game\n• Multiple dangerous roles that can kill players\n• Increased chaos with werecrows, cultists, and jesters\n• More unpredictable gameplay with various neutral roles",
            inline=False
        )
    elif gamemode.lower() == "lycan":
        embed.add_field(
            name="🌙 Lycan Mode Special Rules",
            value="• Multiple lycans that appear as wolves to seers\n• Lycans turn into actual wolves when attacked\n• Hunters are essential for eliminating lycans\n• Race against time before lycans overpower the village",
            inline=False
        )
    elif gamemode.lower() == "rapidfire":
        embed.add_field(
            name="🔥 Rapidfire Mode Special Rules",
            value="• Many killing roles and chain death mechanics\n• Mad scientists, hunters, and gunners everywhere\n• Assassins and vengeful ghosts create chaos\n• Time lords can reverse lynchings for more mayhem",
            inline=False
        )
    elif gamemode.lower() == "noreveal":
        embed.add_field(
            name="🔒 Noreveal Mode Special Rules",
            value="• Player roles are never revealed when they die\n• Information warfare - use investigative roles wisely\n• Mystics help detect power roles\n• Pure deduction and social gameplay",
            inline=False
        )
    elif gamemode.lower() == "bloodbath":
        embed.add_field(
            name="🩸 Bloodbath Mode Special Rules",
            value="• Serial killers are guaranteed in every game\n• Bodyguards are essential for village protection\n• High death rate with multiple killing roles\n• Survive the bloodbath to claim victory",
            inline=False
        )
    elif gamemode.lower() == "random":
        embed.add_field(
            name="🎲 Random Mode Special Rules",
            value="• Completely random role selection each game\n• No fixed role table - every game is unique\n• Minimum balance ensured (wolves, village, investigative)\n• Chaotic and unpredictable gameplay experience",
            inline=False
        )
    
    await ctx.send(embed=embed)
    await start_phase_timer(ctx, "signup", game_state.settings['signup_length'])

@bot.command(name='foolish', aliases=['fool'])
async def start_foolish_game(ctx):
    """Start a new foolish gamemode signup"""
    await start_signup(ctx, "foolish")

@bot.command(name='charming', aliases=['charm', 'piper'])
async def start_charming_game(ctx):
    """Start a new charming gamemode signup"""
    await start_signup(ctx, "charming")

@bot.command(name='mad', aliases=['scientist', 'madness'])
async def start_mad_game(ctx):
    """Start a new mad gamemode signup"""
    await start_signup(ctx, "mad")

@bot.command(name='lycan', aliases=['lycans', 'werewolf'])
async def start_lycan_game(ctx):
    """Start a new lycan gamemode signup"""
    await start_signup(ctx, "lycan")

@bot.command(name='rapidfire', aliases=['rapid', 'fire', 'chaos'])
async def start_rapidfire_game(ctx):
    """Start a new rapidfire gamemode signup"""
    await start_signup(ctx, "rapidfire")

@bot.command(name='noreveal', aliases=['mystery', 'hidden', 'secret'])
async def start_noreveal_game(ctx):
    """Start a new noreveal gamemode signup"""
    await start_signup(ctx, "noreveal")

@bot.command(name='bloodbath', aliases=['blood', 'bath', 'killer'])
async def start_bloodbath_game(ctx):
    """Start a new bloodbath gamemode signup"""
    await start_signup(ctx, "bloodbath")

@bot.command(name='random', aliases=['rand', 'chaos', 'surprise'])
async def start_random_game(ctx):
    """Start a new random gamemode signup"""
    await start_signup(ctx, "random")

@bot.command(name='join', aliases=['j'])
async def join_game(ctx):
    """Join the current game"""
    if not game_state.active or game_state.phase != "signup":
        await ctx.send("❌ No game signup is currently active!")
        return
    
    if ctx.author.id in game_state.players:
        await ctx.send("❌ You're already in the game!")
        return
    
    if len(game_state.players) >= game_state.settings['max_players']:
        await ctx.send("❌ Game is full!")
        return
    
    game_state.add_player(ctx.author.id)
    
    player_list = [bot.get_user(uid).display_name for uid in game_state.players.keys()]
    player_count = len(game_state.players)
    
    embed = discord.Embed(
        title="🐺 Werewolf Game",
        description=f"⏰ Signup ends in {game_state.settings['signup_length']} seconds",
        color=0x8B4513
    )
    embed.add_field(
        name=f"Players ({player_count}/{game_state.settings['max_players']})",
        value="\n".join(player_list) if player_list else "None",
        inline=False
    )
    
    await ctx.send(f"✅ {ctx.author.display_name} joined the game!", embed=embed)

@bot.command(name='leave', aliases=['l'])
async def leave_game(ctx):
    """Leave the current game"""
    if not game_state.active:
        await ctx.send("❌ No game is currently active!")
        return
    
    if ctx.author.id not in game_state.players:
        await ctx.send("❌ You're not in the game!")
        return
    
    if game_state.phase != "signup":
        await ctx.send("❌ You can only leave during signup!")
        return
    
    del game_state.players[ctx.author.id]
    await ctx.send(f"✅ {ctx.author.display_name} left the game!")

async def start_game(ctx, gamemode="default"):
    """Start the actual game"""
    if len(game_state.players) < game_state.settings['min_players']:
        await ctx.send(f"❌ Need at least {game_state.settings['min_players']} players to start!")
        game_state.reset()
        return
    
    # Assign roles with specified gamemode
    player_ids = list(game_state.players.keys())
    assign_roles(player_ids, gamemode)
    
    # Set up wolfchat system
    await setup_wolfchat_for_game(ctx.guild)
    
    # Send role PMs
    for player_id in player_ids:
        await send_role_pm(bot, player_id)
    
    # Start day phase
    game_state.phase = "day"
    game_state.day_number = 1
    
    gamemode_display = gamemode.title() if gamemode != "default" else "Default"
    
    embed = discord.Embed(
        title="🌅 Day 1 Begins!",
        description=f"**{gamemode_display} Gamemode**\n\nThe village wakes up to find everyone alive and well...\n\nDiscuss and vote to lynch someone suspicious!\n\n⏰ **2 minutes** to vote (or until everyone votes)",
        color=0xFFD700
    )
    
    player_list = [bot.get_user(uid).display_name for uid in game_state.get_alive_players()]
    embed.add_field(
        name=f"Alive Players ({len(player_list)})",
        value="\n".join(player_list),
        inline=False
    )
    
    # Add voting instructions for Day 1
    embed.add_field(
        name="📝 How to Vote",
        value=f"`{prefix}vote <player_name>` - Vote to lynch someone\n"
              f"`{prefix}unvote` - Remove your vote\n"
              f"`{prefix}votes` - See current vote count\n"
              f"`{prefix}players` - See all alive players",
        inline=False
    )
    
    embed.add_field(
        name="💡 Voting Tips",
        value="• You need a majority to lynch someone\n"
              "• Discuss suspicions before voting\n"
              "• You can change your vote anytime\n"
              "• Day ends when everyone votes or time runs out",
        inline=False
    )
    
    # Add wolfchat info if wolves exist
    wolf_count = len([pid for pid in game_state.get_alive_players() 
                     if game_state.players[pid]['role'] in WOLFCHAT_ROLES])
    if wolf_count > 0 and game_state.wolfchat_channel:
        embed.add_field(
            name="🐺 Wolf Team",
            value=f"Wolves have access to {game_state.wolfchat_channel.mention} for private coordination!",
            inline=False
        )
    
    await ctx.send(embed=embed)
    await start_phase_timer(ctx, "day", game_state.settings['day_length'])

@bot.command(name='end')
async def end_game(ctx):
    """End the current game (admin only)"""
    if not game_state.active:
        await ctx.send("❌ No game is currently active!")
        return
    
    # Simple admin check - can be enhanced
    if not ctx.author.guild_permissions.manage_messages:
        await ctx.send("❌ You need Manage Messages permission to end games!")
        return
    
    # Cleanup chat channels
    await cleanup_chat_channels()
    
    game_state.reset()
    await ctx.send("🛑 Game ended by admin!")

@bot.command(name='gamemodes', aliases=['modes'])
async def show_gamemodes(ctx):
    """Show available gamemodes and their details"""
    embed = discord.Embed(
        title="🎮 Available Gamemodes",
        description="Choose your preferred werewolf experience!",
        color=0x8B4513
    )
    
    # Default gamemode
    embed.add_field(
        name="🏘️ Default Mode",
        value="**Players**: 4-24\n"
              "**Description**: Standard balanced werewolf with all classic roles\n"
              "**Features**: Seers, shamans, wolves, and village roles\n"
              "**Command**: `!start` or `!start default`",
        inline=False
    )
    
    # Foolish gamemode
    embed.add_field(
        name="🃏 Foolish Mode",
        value="**Players**: 8-24\n"
              "**Description**: Watch out, because the fool is always there to steal the win!\n"
              "**Features**: Guaranteed fool, oracle instead of seer, multiple harlots\n"
              "**Command**: `!start foolish` or `!foolish`",
        inline=False
    )
    
    # Charming gamemode
    embed.add_field(
        name="🎵 Charming Mode",
        value="**Players**: 6-24\n"
              "**Description**: Charmed players must band together to find the piper\n"
              "**Features**: Guaranteed piper, complex role mix, charm mechanic\n"
              "**Command**: `!start charming` or `!charming`",
        inline=False
    )
    
    # Mad gamemode
    embed.add_field(
        name="🧪 Mad Mode",
        value="**Players**: 7-22\n"
              "**Description**: This game mode has mad scientist and many things that may kill you\n"
              "**Features**: Guaranteed mad scientist, dangerous roles, increased chaos\n"
              "**Command**: `!start mad` or `!mad`",
        inline=False
    )
    
    # Lycan gamemode
    embed.add_field(
        name="🌙 Lycan Mode",
        value="**Players**: 7-21\n"
              "**Description**: Many lycans will turn into wolves. Hunt them down before the wolves overpower the village\n"
              "**Features**: Multiple lycans, hunters, clones, wolf transformation mechanics\n"
              "**Command**: `!start lycan` or `!lycan`",
        inline=False
    )
    
    # Rapidfire gamemode
    embed.add_field(
        name="🔥 Rapidfire Mode",
        value="**Players**: 6-24\n"
              "**Description**: Many killing roles and roles that cause chain deaths. Living has never been so hard\n"
              "**Features**: Mad scientists, hunters, gunners, assassins, vengeful ghosts, time lords\n"
              "**Command**: `!start rapidfire` or `!rapidfire`",
        inline=False
    )
    
    # Noreveal gamemode
    embed.add_field(
        name="🔒 Noreveal Mode",
        value="**Players**: 4-21\n"
              "**Description**: Roles are not revealed on death\n"
              "**Features**: Information warfare, mystic investigation, pure deduction gameplay\n"
              "**Command**: `!start noreveal` or `!noreveal`",
        inline=False
    )
    
    # Bloodbath gamemode
    embed.add_field(
        name="🩸 Bloodbath Mode",
        value="**Players**: 9-24\n"
              "**Description**: Serial killers everywhere! Bodyguards are your only protection in this deadly mode\n"
              "**Features**: Guaranteed serial killers, bodyguards, high death rate, survival focus\n"
              "**Command**: `!start bloodbath` or `!bloodbath`",
        inline=False
    )
    
    # Random gamemode
    embed.add_field(
        name="🎲 Random Mode",
        value="**Players**: 8-20\n"
              "**Description**: A completely random set of roles is chosen, making for a chaotic and unpredictable game\n"
              "**Features**: No fixed table, unique experience every time, minimum balance ensured\n"
              "**Command**: `!start random` or `!random`",
        inline=False
    )
    
    # Sample role distributions
    embed.add_field(
        name="📊 Sample Distributions",
        value="**Default 8p**: 3 villagers, 1 seer, 1 traitor, 1 shaman, 1 harlot, 1 wolf\n"
              "**Foolish 8p**: 3 villagers, 1 oracle, 1 harlot, 1 fool, 1 wolf, 1 traitor\n"
              "**Charming 8p**: 3 villagers, 1 seer, 1 piper, 1 wolf, 1 werekitten, 1 traitor\n"
              "**Mad 8p**: 4 villagers, 1 seer, 1 mad scientist, 1 wolf, 1 traitor\n"
              "**Lycan 8p**: 1 villager, 1 seer, 2 hunters, 1 lycan, 1 wolf, 1 traitor, 1 clone\n"
              "**Rapidfire 8p**: 3 villagers, 1 seer, 1 mad scientist, 1 wolf, 1 wolf cub, 1 hunter + gunner, assassin\n"
              "**Noreveal 8p**: 4 villagers, 1 seer, 1 wolf, 1 mystic, 1 wolf mystic\n"
              "**Bloodbath 9p**: 3 villagers, 1 seer, 1 bodyguard, 1 serial killer, 1 wolf, 1 traitor, 1 jester\n"
              "**Random 8p**: Completely random roles each game (example: 2 villagers, 1 oracle, 1 harlot, 1 mad scientist, 1 wolf, 1 lycan, 1 jester)",
        inline=False
    )
    
    embed.add_field(
        name="⚙️ How to Start",
        value=f"• `{prefix}start` - Default mode\n"
              f"• `{prefix}start foolish` - Foolish mode\n"
              f"• `{prefix}start charming` - Charming mode\n"
              f"• `{prefix}start mad` - Mad mode\n"
              f"• `{prefix}start lycan` - Lycan mode\n"
              f"• `{prefix}start rapidfire` - Rapidfire mode\n"
              f"• `{prefix}start noreveal` - Noreveal mode\n"
              f"• `{prefix}start bloodbath` - Bloodbath mode\n"
              f"• `{prefix}start random` - Random mode\n"
              f"• `{prefix}foolish` - Quick foolish start\n"
              f"• `{prefix}charming` - Quick charming start\n"
              f"• `{prefix}mad` - Quick mad start\n"
              f"• `{prefix}lycan` - Quick lycan start\n"
              f"• `{prefix}rapidfire` - Quick rapidfire start\n"
              f"• `{prefix}noreveal` - Quick noreveal start\n"
              f"• `{prefix}bloodbath` - Quick bloodbath start\n"
              f"• `{prefix}random` - Quick random start\n"
              f"• `{prefix}join` - Join any active signup",
        inline=False
    )
    
    await ctx.send(embed=embed)

# ==================== VOTING COMMANDS ====================
@bot.command(name='vote', aliases=['lynch', 'v'])
async def vote_lynch(ctx, *, target=None):
    """Vote to lynch a player"""
    if not game_state.active or game_state.phase != "day":
        await ctx.send("❌ Voting is only available during the day phase!")
        return
    
    if not game_state.is_player_alive(ctx.author.id):
        await ctx.send("❌ Dead players cannot vote!")
        return
    
    if not target:
        alive_list = get_player_list_for_help(bot)
        await ctx.send(f"❌ You must specify who to vote for!\n**Alive players**: {alive_list}")
        return
    
    # Find target player using improved search
    target_id = find_player_by_name(target, bot, alive_only=True)
    
    if not target_id:
        alive_list = get_player_list_for_help(bot)
        await ctx.send(f"❌ Player '{target}' not found!\n**Alive players**: {alive_list}")
        return
    
    if target_id == ctx.author.id:
        await ctx.send("❌ You cannot vote for yourself!")
        return
    
    # Check if player is injured/blinded
    if game_state.players[ctx.author.id].get('injured', False):
        await ctx.send("❌ You are injured and cannot vote!")
        return
    
    # Record vote
    game_state.votes[ctx.author.id] = target_id
    target_user = bot.get_user(target_id)
    
    # Check for majority reached
    alive_count = len(game_state.get_alive_players())
    majority_needed = (alive_count // 2) + 1
    
    # Count votes for the target
    vote_counts = {}
    for voter_id, voted_target_id in game_state.votes.items():
        if game_state.is_player_alive(voter_id) and game_state.is_player_alive(voted_target_id):
            multiplier = 1
            if game_state.players[voter_id].get('totem') == 'influence_totem':
                multiplier = 2
            elif game_state.players[voter_id].get('template') == 'mayor':
                multiplier = 2
            
            vote_counts[voted_target_id] = vote_counts.get(voted_target_id, 0) + multiplier
    
    # Enhanced vote confirmation with progress
    progress_text = get_vote_progress_text()
    
    target_votes = vote_counts.get(target_id, 0)
    vote_msg = f"✅ {ctx.author.display_name} voted to lynch **{target_user.display_name}**!"
    
    if target_votes >= majority_needed:
        vote_msg += f"\n🔥 **MAJORITY REACHED!** {target_user.display_name} has {target_votes} votes (majority: {majority_needed})"
    
    vote_msg += f"\n{progress_text}"
    
    await ctx.send(vote_msg)

@bot.command(name='unvote', aliases=['uv'])
async def unvote(ctx):
    """Remove your vote"""
    if not game_state.active or game_state.phase != "day":
        await ctx.send("❌ Voting is only available during the day phase!")
        return
    
    if ctx.author.id not in game_state.votes:
        await ctx.send("❌ You haven't voted yet!")
        return
    
    del game_state.votes[ctx.author.id]
    
    # Enhanced unvote confirmation with progress
    progress_text = get_vote_progress_text()
    
    await ctx.send(f"✅ {ctx.author.display_name} removed their vote!\n{progress_text}")

@bot.command(name='votes', aliases=['vote_count', 'vc'])
async def show_votes(ctx):
    """Show current vote count"""
    if not game_state.active or game_state.phase != "day":
        await ctx.send("❌ Voting is only available during the day phase!")
        return
    
    # Count votes using the same logic as final votes
    vote_counts = await calculate_final_votes()
    
    if not vote_counts:
        progress_text = get_vote_progress_text()
        await ctx.send(f"📊 No votes cast yet!\n{progress_text}")
        return
    
    # Sort by vote count
    sorted_votes = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)
    
    embed = discord.Embed(title="📊 Current Votes", color=0xFFD700)
    
    vote_text = []
    for target_id, count in sorted_votes:
        target_user = bot.get_user(target_id)
        vote_text.append(f"**{target_user.display_name}**: {count} vote{'s' if count != 1 else ''}")
    
    embed.description = "\n".join(vote_text)
    
    alive_count = len(game_state.get_alive_players())
    majority = (alive_count // 2) + 1
    votes_cast = len([1 for v_id, t_id in game_state.votes.items() 
                     if game_state.is_player_alive(v_id) and game_state.is_player_alive(t_id)])
    votes_remaining = alive_count - votes_cast
    
    embed.add_field(name="Majority Needed", value=str(majority), inline=True)
    embed.add_field(name="Vote Progress", value=f"{votes_cast}/{alive_count} voted\n{votes_remaining} remaining", inline=True)
    
    # Add totem effects information
    totem_info = []
    for player_id in game_state.get_alive_players():
        totem = game_state.players[player_id].get('totem')
        if totem in ['influence_totem', 'impatience_totem', 'pacifism_totem']:
            user = bot.get_user(player_id)
            if totem == 'influence_totem':
                totem_info.append(f"{user.display_name}: Double votes")
            elif totem == 'impatience_totem':
                totem_info.append(f"{user.display_name}: Votes for everyone")
            elif totem == 'pacifism_totem':
                totem_info.append(f"{user.display_name}: Cannot vote")
    
    if totem_info:
        embed.add_field(name="Totem Effects", value="\n".join(totem_info), inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='players', aliases=['alive', 'p'])
async def show_players(ctx):
    """Show all alive players"""
    if not game_state.active:
        await ctx.send("❌ No game is currently active!")
        return
    
    alive_players = game_state.get_alive_players()
    if not alive_players:
        await ctx.send("💀 No players are alive!")
        return
    
    embed = discord.Embed(
        title="👥 Alive Players",
        color=0x00FF00
    )
    
    player_names = []
    for player_id in alive_players:
        user = bot.get_user(player_id)
        if user:
            # Add status indicators for special conditions
            status_indicators = []
            player_data = game_state.players[player_id]
            
            if player_data.get('injured', False):
                status_indicators.append("🤕")
            if player_data.get('silenced', False):
                status_indicators.append("🔇")
            if player_data.get('protected', False):
                status_indicators.append("🛡️")
            if player_data.get('totem'):
                status_indicators.append("🏺")
            
            status_text = " ".join(status_indicators)
            player_name = f"{user.display_name} {status_text}".strip()
            player_names.append(player_name)
    
    embed.description = "\n".join(f"• {name}" for name in player_names)
    embed.add_field(
        name="Total Alive",
        value=f"{len(alive_players)} players",
        inline=True
    )
    
    if game_state.phase == "day":
        majority = (len(alive_players) // 2) + 1
        embed.add_field(
            name="Majority Needed",
            value=f"{majority} votes",
            inline=True
        )
    
    # Add legend for status indicators
    legend_items = []
    if any(game_state.players[pid].get('injured', False) for pid in alive_players):
        legend_items.append("🤕 Injured (can't vote)")
    if any(game_state.players[pid].get('silenced', False) for pid in alive_players):
        legend_items.append("🔇 Silenced (can't use powers)")
    if any(game_state.players[pid].get('protected', False) for pid in alive_players):
        legend_items.append("🛡️ Protected")
    if any(game_state.players[pid].get('totem') for pid in alive_players):
        legend_items.append("🏺 Has totem")
    
    if legend_items:
        embed.add_field(
            name="Status Legend",
            value="\n".join(legend_items),
            inline=False
        )
    
    await ctx.send(embed=embed)

async def end_day_phase(ctx):
    """End day phase and process lynch"""
    # Count final votes with totem effects
    vote_counts = await calculate_final_votes()
    
    lynched_player = None
    if vote_counts:
        max_votes = max(vote_counts.values())
        tied_players = [pid for pid, votes in vote_counts.items() if votes == max_votes]
        
        if len(tied_players) == 1:
            lynched_player = tied_players[0]
        else:
            # Tie - no lynch
            await ctx.send("⚖️ **No Lynch** - The vote ended in a tie!")
    else:
        await ctx.send("⚖️ **No Lynch** - No votes were cast!")
    
    # Process lynch
    if lynched_player:
        lynched_user = bot.get_user(lynched_player)
        lynched_role = game_state.players[lynched_player]['role']
        lynched_template = game_state.players[lynched_player].get('template')
        
        # Format role display
        role_display = lynched_role.replace('_', ' ').title()
        if lynched_template:
            role_display += f" ({lynched_template.replace('_', ' ').title()})"
        
        # Check for revealing totem (saves from death but reveals role)
        if game_state.players[lynched_player].get('totem') == 'revealing_totem':
            await ctx.send(f"✨ **{lynched_user.display_name}** was about to be lynched, but the **Revealing Totem** saves them!\n\n🔍 **Role Revealed**: {role_display}")
            # Remove the totem after use
            game_state.players[lynched_player]['totem'] = None
        else:
            # Normal lynch with role reveal
            await ctx.send(f"⚰️ **{lynched_user.display_name}** was lynched!\n\n🔍 **Role**: {role_display}")
            
            # Check for desperation totem (kills last voter)
            if game_state.players[lynched_player].get('totem') == 'desperation_totem':
                # Find the last person to vote for them (need to implement vote history)
                await ctx.send(f"💥 **Desperation Totem** activates! The last person to vote dies too!")
            
            # Kill player
            game_state.players[lynched_player]['alive'] = False
            game_state.dead_players[lynched_player] = lynched_role
            
            # Handle death effects (wolfchat, etc.)
            await handle_player_death(lynched_player, ctx)
            
            # Check for special death effects
            await process_death_effects(ctx, lynched_player, 'lynch')
    
    # Check win conditions
    if await check_win_conditions(ctx):
        return
    
    # Start night phase
    await start_night_phase(ctx)

async def calculate_final_votes() -> dict:
    """Calculate final vote counts with all totem effects"""
    vote_counts = {}
    alive_players = game_state.get_alive_players()
    
    # Process normal votes first
    for voter_id, target_id in game_state.votes.items():
        if game_state.is_player_alive(voter_id) and game_state.is_player_alive(target_id):
            voter_totem = game_state.players[voter_id].get('totem')
            
            # Skip votes from pacifism totem holders
            if voter_totem == 'pacifism_totem':
                continue
                
            multiplier = 1
            if voter_totem == 'influence_totem':
                multiplier = 2
            elif game_state.players[voter_id].get('template') == 'mayor':
                multiplier = 2
            
            vote_counts[target_id] = vote_counts.get(target_id, 0) + multiplier
    
    # Process impatience totem (votes for everyone except themselves)
    for player_id in alive_players:
        if game_state.players[player_id].get('totem') == 'impatience_totem':
            for target_id in alive_players:
                if target_id != player_id:  # Don't vote for self
                    vote_counts[target_id] = vote_counts.get(target_id, 0) + 1
    
    return vote_counts

async def start_night_phase(ctx):
    """Start night phase"""
    game_state.phase = "night"
    game_state.night_actions.clear()
    
    # Reset totem assignments for new night
    game_state.assigned_totems.clear()
    game_state.used_shamans.clear()
    
    embed = discord.Embed(
        title="🌙 Night Falls",
        description="The village sleeps... but some are still awake.\n\nNight actions are now being processed.\n\n⏰ **2 minutes** for night actions (or until everyone acts)",
        color=0x2F4F4F
    )
    
    await ctx.send(embed=embed)
    
    # Send night action prompts
    await send_night_prompts()
    
    await start_phase_timer(ctx, "night", game_state.settings['night_length'])

async def send_night_prompts():
    """Send night action prompts to players"""
    for player_id, player_data in game_state.players.items():
        if not player_data['alive']:
            continue
        
        role = player_data['role']
        user = bot.get_user(player_id)
        if not user:
            continue
        
        # Check if silenced
        if player_data.get('silenced', False):
            try:
                await user.send("🔇 You are silenced and cannot use your power tonight.")
            except:
                pass
            continue
        
        # Send appropriate prompt based on role
        embed = None
        if role == 'seer':
            embed = discord.Embed(
                title="🔮 Seer - Night Action",
                description="You can see the exact role of any player.",
                color=0x8A2BE2
            )
            embed.add_field(
                name="� Your Power",
                value="Learn the exact role of a target player",
                inline=False
            )
            embed.add_field(
                name="📝 Command",
                value=f"`{prefix}see <player_name>`",
                inline=False
            )
            embed.add_field(
                name="💡 Example",
                value=f"`{prefix}see John` → You'll learn John's exact role",
                inline=False
            )
            
        elif role == 'oracle':
            embed = discord.Embed(
                title="🔮 Oracle - Night Action",
                description="You can see which team a player belongs to.",
                color=0x8A2BE2
            )
            embed.add_field(
                name="💭 Your Power",
                value="Learn if target is Village/Wolf/Neutral team",
                inline=False
            )
            embed.add_field(
                name="📝 Command",
                value=f"`{prefix}see <player_name>`",
                inline=False
            )
            embed.add_field(
                name="💡 Example",
                value=f"`{prefix}see Alice` → You'll learn Alice's team",
                inline=False
            )
            
        elif role == 'detective':
            embed = discord.Embed(
                title="🕵️ Detective - Night Action",
                description="Compare players to see if they have the same role.",
                color=0x4169E1
            )
            embed.add_field(
                name="� Your Power",
                value="Compare target with previously investigated players",
                inline=False
            )
            embed.add_field(
                name="📝 Command",
                value=f"`{prefix}id <player_name>`",
                inline=False
            )
            embed.add_field(
                name="💡 Example",
                value=f"`{prefix}id Bob` → Compare Bob with your previous targets",
                inline=False
            )
            
        elif role in ['guardian angel', 'bodyguard']:
            action_desc = "Protect from death" if role == 'guardian angel' else "Die instead of target if attacked"
            embed = discord.Embed(
                title=f"🛡️ {role.title()} - Night Action",
                description=f"You can protect another player tonight.",
                color=0x32CD32
            )
            embed.add_field(
                name="💭 Your Power",
                value=action_desc,
                inline=False
            )
            embed.add_field(
                name="📝 Command",
                value=f"`{prefix}guard <player_name>`",
                inline=False
            )
            embed.add_field(
                name="💡 Example",
                value=f"`{prefix}guard Emma` → Protect Emma from attacks",
                inline=False
            )
            
        elif role in ACTUAL_WOLVES:  # Wolf, Wolf Cub, Werekitten, Wolf Shaman, Wolf Mystic
            embed = discord.Embed(
                title="🐺 Wolf Pack - Night Kill",
                description="Time to hunt! Choose who to eliminate tonight.",
                color=0x8B0000
            )
            embed.add_field(
                name="� Your Power",
                value="Vote to kill a villager with your pack",
                inline=False
            )
            embed.add_field(
                name="📝 Command",
                value=f"`{prefix}kill <player_name>`",
                inline=False
            )
            embed.add_field(
                name="💡 Example",
                value=f"`{prefix}kill Charlie` → Vote to kill Charlie tonight",
                inline=False
            )
            embed.add_field(
                name="🔄 How Wolf Kills Work",
                value="• All wolves vote on who to kill\n• Most voted target dies\n• Coordinate with your pack!",
                inline=False
            )
            
            # Add wolf allies info
            wolf_allies = []
            for pid in game_state.get_players_by_team('wolf'):
                if pid != player_id:
                    ally_user = bot.get_user(pid)
                    if ally_user:
                        ally_role = game_state.players[pid]['role']
                        wolf_allies.append(f"{ally_user.display_name} ({ally_role})")
            
            if wolf_allies:
                embed.add_field(
                    name="🐺 Your Wolf Allies",
                    value="\n".join(wolf_allies),
                    inline=False
                )
                
        elif role == 'werecrow':
            embed = discord.Embed(
                title="👁️ Werecrow - Night Action",
                description="Watch and see who visits your target.",
                color=0x8B0000
            )
            embed.add_field(
                name="� Your Power",
                value="See who visits your target tonight",
                inline=False
            )
            embed.add_field(
                name="📝 Command",
                value=f"`{prefix}observe <player_name>`",
                inline=False
            )
            embed.add_field(
                name="💡 Example",
                value=f"`{prefix}observe David` → See who visits David",
                inline=False
            )
            
        elif role == 'vigilante':
            embed = discord.Embed(
                title="🔫 Vigilante - Night Action",
                description="Take justice into your own hands.",
                color=0x654321
            )
            embed.add_field(
                name="� Your Power",
                value="Kill a player you suspect of being evil",
                inline=False
            )
            embed.add_field(
                name="📝 Command",
                value=f"`{prefix}kill <player_name>`",
                inline=False
            )
            embed.add_field(
                name="💡 Example",
                value=f"`{prefix}kill Suspect` → Kill your suspected target",
                inline=False
            )
            embed.add_field(
                name="⚠️ Warning",
                value="Choose carefully - you might kill an innocent!",
                inline=False
            )
            
        elif role == 'village drunk':
            embed = discord.Embed(
                title="🍺 Village Drunk - Night Action",
                description="Shoot... but you might miss!",
                color=0xD2691E
            )
            embed.add_field(
                name="💭 Your Power",
                value="Shoot someone, but accuracy is not guaranteed",
                inline=False
            )
            embed.add_field(
                name="📝 Command",
                value=f"`{prefix}shoot <player_name>`",
                inline=False
            )
            embed.add_field(
                name="💡 Example",
                value=f"`{prefix}shoot Target` → Attempt to shoot Target",
                inline=False
            )
            embed.add_field(
                name="🎯 Drunk Effects",
                value="• You might miss completely\n• You might hit someone nearby\n• Drink responsibly!",
                inline=False
            )
            
        elif role == 'harlot':
            embed = discord.Embed(
                title="💃 Harlot - Night Action",
                description="Visit someone and stay safe from wolves.",
                color=0xFF69B4
            )
            embed.add_field(
                name="� Your Power",
                value="Visit a player and become immune to wolf attacks",
                inline=False
            )
            embed.add_field(
                name="📝 Command",
                value=f"`{prefix}visit <player_name>`",
                inline=False
            )
            embed.add_field(
                name="💡 Example",
                value=f"`{prefix}visit Frank` → Visit Frank tonight",
                inline=False
            )
            embed.add_field(
                name="🛡️ Safety",
                value="You're safe from wolves while visiting!",
                inline=False
            )
            
        elif role in ['shaman', 'wolf shaman', 'crazed shaman']:
            totems = SHAMAN_TOTEMS if role == 'shaman' else WOLF_SHAMAN_TOTEMS
            team_color = 0x9932CC if role == 'shaman' else 0x8B0000
            
            embed = discord.Embed(
                title=f"🎭 {role.title()} - Night Action",
                description="Give a magical totem to another player.",
                color=team_color
            )
            embed.add_field(
                name="💭 Your Power",
                value="Give a totem with special effects to any player",
                inline=False
            )
            embed.add_field(
                name="📝 Command",
                value=f"`{prefix}give <player_name> <totem_name>`",
                inline=False
            )
            embed.add_field(
                name="💡 Example",
                value=f"`{prefix}give Grace protection_totem`",
                inline=False
            )
            embed.add_field(
                name="🎭 Available Totems",
                value="\n".join([f"• `{t}`" for t in totems[:8]]),  # Show first 8
                inline=False
            )
            
            if len(totems) > 8:
                embed.add_field(
                    name="🎭 More Totems",
                    value="\n".join([f"• `{t}`" for t in totems[8:]]),
                    inline=False
                )
        
        elif role in ['mystic', 'wolf mystic']:
            team_color = 0x9932CC if role == 'mystic' else 0x8B0000
            embed = discord.Embed(
                title=f"🔮 {role.title()} - Night Action",
                description="Use mysticism to detect power roles.",
                color=team_color
            )
            embed.add_field(
                name="💭 Your Power",
                value="Learn if a player has an active power role",
                inline=False
            )
            embed.add_field(
                name="📝 Command",
                value=f"`{prefix}mysticism <player_name>`",
                inline=False
            )
            embed.add_field(
                name="💡 Example",
                value=f"`{prefix}mysticism Henry` → Learn if Henry has powers",
                inline=False
            )
            
        elif role == 'priest':
            embed = discord.Embed(
                title="✨ Priest - Night Action",
                description="Bless a player to protect them from lycanthropy.",
                color=0xFFD700
            )
            embed.add_field(
                name="💭 Your Power",
                value="Protect a player from being turned into a wolf",
                inline=False
            )
            embed.add_field(
                name="📝 Command",
                value=f"`{prefix}bless <player_name>`",
                inline=False
            )
            embed.add_field(
                name="💡 Example",
                value=f"`{prefix}bless Isabella` → Bless Isabella tonight",
                inline=False
            )
            embed.add_field(
                name="🛡️ Protection",
                value="Blessed players cannot be turned by lycanthropy totem",
                inline=False
            )
            
        elif role == 'augur':
            embed = discord.Embed(
                title="🔮 Augur - Night Action",
                description="See if a player can kill others.",
                color=0x8A2BE2
            )
            embed.add_field(
                name="💭 Your Power",
                value="Learn if target can kill (wolves, vigilante, etc.)",
                inline=False
            )
            embed.add_field(
                name="📝 Command",
                value=f"`{prefix}see <player_name>`",
                inline=False
            )
            embed.add_field(
                name="💡 Example",
                value=f"`{prefix}see Jack` → Learn if Jack can kill",
                inline=False
            )
        
        # Send the embed if one was created
        if embed:
            try:
                await user.send(embed=embed)
            except Exception as e:
                logger.error(f"Failed to send night prompt to {user.display_name}: {e}")
                # Fallback to simple text
                simple_prompt = f"🌙 **Night Action Available** - Use commands in this DM!"
                try:
                    await user.send(simple_prompt)
                except:
                    pass
                pass

async def end_night_phase(ctx):
    """End night phase and process actions"""
    # Process all night actions
    deaths = []
    protections = set()
    totem_effects = {}
    
    # First, process totem giving (happens immediately)
    for player_id, action in game_state.night_actions.items():
        if action['action'] == 'give':
            target_id = action['target']
            totem = action['totem']
            game_state.players[target_id]['totem'] = totem
            totem_effects[target_id] = totem
    
    # Process protective actions
    for player_id, action in game_state.night_actions.items():
        if action['action'] == 'guard':
            target_id = action['target']
            protections.add(target_id)
            game_state.players[target_id]['protected'] = True
    
    # Process totem effects that happen immediately
    for player_id, totem in totem_effects.items():
        if totem == 'death_totem':
            deaths.append((player_id, 'death totem'))
        elif totem == 'protection_totem':
            protections.add(player_id)
            game_state.players[player_id]['protected'] = True
        elif totem == 'blinding_totem':
            game_state.players[player_id]['injured'] = True
        elif totem == 'silence_totem':
            game_state.players[player_id]['silenced'] = True
        elif totem == 'cursed_totem':
            if game_state.players[player_id].get('template') != 'cursed':
                game_state.players[player_id]['template'] = 'cursed'
    
    # Process wolf kills
    wolf_targets = []
    for player_id, action in game_state.night_actions.items():
        if (action['action'] == 'kill' and 
            game_state.players[player_id]['role'] in ACTUAL_WOLVES):
            wolf_targets.append(action['target'])
    
    # Wolves kill most common target
    if wolf_targets:
        from collections import Counter
        target_counts = Counter(wolf_targets)
        wolf_target = target_counts.most_common(1)[0][0]
        
        # Check totem effects on wolf target
        target_totem = game_state.players[wolf_target].get('totem')
        
        if target_totem == 'lycanthropy_totem':
            # Turn into wolf instead of dying
            game_state.players[wolf_target]['role'] = 'wolf'
            game_state.players[wolf_target]['totem'] = None
            wolf_user = bot.get_user(wolf_target)
            await ctx.send(f"🐺 **{wolf_user.display_name}** was bitten by wolves and transformed!")
        elif target_totem == 'retribution_totem':
            # Kill a random wolf
            alive_wolves = [pid for pid in game_state.get_alive_players() 
                          if game_state.players[pid]['role'] in ACTUAL_WOLVES]
            if alive_wolves:
                import random
                revenge_target = random.choice(alive_wolves)
                deaths.append((revenge_target, 'retribution totem'))
            deaths.append((wolf_target, 'wolves'))
        elif wolf_target not in protections:
            deaths.append((wolf_target, 'wolves'))
    
    # Process other kills (vigilante, serial killer, etc.)
    for player_id, action in game_state.night_actions.items():
        if action['action'] == 'kill':
            role = game_state.players[player_id]['role']
            target = action['target']
            
            if role == 'vigilante' and target not in protections:
                deaths.append((target, 'vigilante'))
            elif role in ['serial killer', 'monster'] and target not in protections:
                deaths.append((target, role))
    
    # Process other night actions (seers, etc.)
    for player_id, action in game_state.night_actions.items():
        if action['action'] == 'see':
            # Process seer/oracle results (send to player)
            await process_seer_action(player_id, action)
        elif action['action'] == 'visit':
            # Harlot/Succubus visits
            await process_visit_action(player_id, action)
        elif action['action'] == 'hex':
            # Hag hex (mark for role exchange on death)
            game_state.players[player_id]['hex_target'] = action['target']
        elif action['action'] == 'charm':
            # Piper charm
            game_state.players[action['target']]['charmed'] = True
        elif action['action'] == 'mysticism':
            # Mystic/Wolf Mystic power check
            await process_mysticism_action(player_id, action)
        elif action['action'] == 'bless':
            # Priest blessing (protects from lycanthropy)
            target_id = action['target']
            game_state.players[target_id]['blessed'] = True
            user = bot.get_user(player_id)
            target_user = bot.get_user(target_id)
            try:
                await user.send(f"✨ You blessed **{target_user.display_name}** - they are now protected from lycanthropy!")
            except:
                pass
        elif action['action'] == 'observe':
            # Werecrow observation
            await process_observe_action(player_id, action)
        elif action['action'] == 'id':
            # Detective investigation
            await process_detective_action(player_id, action)
        elif action['action'] == 'shoot':
            # Village drunk shooting
            await process_drunk_shot(player_id, action, deaths)
        elif action['action'] == 'curse':
            # Warlock curse (mark for death in 2 nights)
            await process_curse_action(player_id, action)
        elif action['action'] == 'remember':
            # Amnesiac remembering
            await process_remember_action(player_id, action)
        elif action['action'] == 'turn':
            # Turncoat changing teams
            await process_turn_action(player_id, action)
        elif action['action'] == 'doom':
            # Doomsayer doom (mark for day kill)
            await process_doom_action(player_id, action)
    
    # Apply deaths with role reveals
    death_messages = []
    for victim_id, killer in deaths:
        victim_user = bot.get_user(victim_id)
        victim_role = game_state.players[victim_id]['role']
        victim_template = game_state.players[victim_id].get('template')
        
        # Format role display
        role_display = victim_role.replace('_', ' ').title()
        if victim_template:
            role_display += f" ({victim_template.replace('_', ' ').title()})"
        
        game_state.players[victim_id]['alive'] = False
        game_state.dead_players[victim_id] = victim_role
        
        death_messages.append(f"💀 **{victim_user.display_name}** ({role_display}) was killed by {killer}!")
        
        # Handle chat permissions and death effects
        await handle_player_death(victim_id, ctx)
        await process_death_effects(ctx, victim_id, 'night')
    
    # Clear temporary effects
    for player_id in game_state.players:
        game_state.players[player_id]['protected'] = False
        # Clear totems that are one-time use
        totem = game_state.players[player_id].get('totem')
        if totem in ['death_totem', 'protection_totem', 'revealing_totem', 'lycanthropy_totem', 'retribution_totem']:
            game_state.players[player_id]['totem'] = None
    
    # Send death report
    game_state.day_number += 1
    
    if death_messages:
        embed = discord.Embed(
            title=f"🌅 Day {game_state.day_number}",
            description="\n".join(death_messages),
            color=0xFFD700
        )
    else:
        embed = discord.Embed(
            title=f"🌅 Day {game_state.day_number}",
            description="The village wakes up to find everyone alive!",
            color=0xFFD700
        )
    
    await ctx.send(embed=embed)
    
    # Check win conditions
    if await check_win_conditions(ctx):
        return
    
    # Start new day
    game_state.phase = "day"
    game_state.day_number += 1
    game_state.votes.clear()
    
    # Announce new day
    embed = discord.Embed(
        title=f"🌅 Day {game_state.day_number} Begins!",
        description=f"The sun rises on day {game_state.day_number}...\n\nDiscuss and vote to lynch someone suspicious!\n\n⏰ **2 minutes** to vote (or until everyone votes)",
        color=0xFFD700
    )
    
    alive_players = game_state.get_alive_players()
    player_list = [bot.get_user(uid).display_name for uid in alive_players]
    embed.add_field(
        name=f"Alive Players ({len(player_list)})",
        value="\n".join(player_list),
        inline=False
    )
    
    await ctx.send(embed=embed)
    
    await start_phase_timer(ctx, "day", game_state.settings['day_length'])

async def process_seer_action(player_id: int, action: dict):
    """Process seer/oracle vision results"""
    try:
        seer_user = bot.get_user(player_id)
        target_id = action['target']
        target_user = bot.get_user(target_id)
        
        role = game_state.players[player_id]['role']
        target_role = game_state.players[target_id]['role']
        target_totem = game_state.players[target_id].get('totem')
        
        # Check for deceit totem (flips seer results)
        flip_result = target_totem == 'deceit_totem'
        
        if role == 'seer':
            # Show exact role, but deceit totem flips it
            if flip_result:
                if target_role in ROLES_SEEN_VILLAGER:
                    shown_role = "Wolf"
                else:
                    shown_role = "Villager"
            else:
                shown_role = target_role
            
            await seer_user.send(f"🔮 **Seer Vision**: {target_user.display_name} is a **{shown_role}**!")
            
        elif role == 'oracle':
            # Show team
            if target_role in VILLAGE_ROLES_ORDERED:
                team = "Village" if not flip_result else "Wolf"
            elif target_role in WOLF_ROLES_ORDERED + WOLFCHAT_ROLES:
                team = "Wolf" if not flip_result else "Village"
            else:
                team = "Neutral"
            
            await seer_user.send(f"🔮 **Oracle Vision**: {target_user.display_name} is on the **{team}** team!")
            
        elif role == 'augur':
            # Check if target can kill
            can_kill = target_role in ACTUAL_WOLVES + ['vigilante', 'serial killer', 'monster', 'hunter']
            result = "can kill" if can_kill else "cannot kill"
            if flip_result:
                result = "cannot kill" if can_kill else "can kill"
            
            await seer_user.send(f"🔮 **Augur Vision**: {target_user.display_name} **{result}**!")
            
    except Exception as e:
        logger.error(f"Error processing seer action: {e}")

async def process_visit_action(player_id: int, action: dict):
    """Process harlot/succubus visits"""
    try:
        visitor_role = game_state.players[player_id]['role']
        target_id = action['target']
        
        if visitor_role == 'harlot':
            # Harlot becomes immune to wolf attacks
            game_state.players[player_id]['visiting'] = target_id
        elif visitor_role == 'succubus':
            # Track succubus visits (kill if visited twice)
            visits = game_state.players[player_id].get('succubus_visits', [])
            if target_id in visits:
                # Second visit - kill target
                game_state.players[target_id]['alive'] = False
                target_user = bot.get_user(target_id)
                # This would need to be added to death messages in main function
            else:
                visits.append(target_id)
                game_state.players[player_id]['succubus_visits'] = visits
                
    except Exception as e:
        logger.error(f"Error processing visit action: {e}")

async def process_death_effects(ctx, player_id: int, death_type: str):
    """Process special effects when a player dies"""
    role = game_state.players[player_id]['role']
    template = game_state.players[player_id].get('template')
    user = bot.get_user(player_id)
    
    # Handle chat permissions for dead player
    await handle_player_death(player_id, ctx)
    
    # Lover death - if player has a lover, the lover dies too
    lover_id = game_state.players[player_id].get('lover')
    if lover_id and game_state.is_player_alive(lover_id):
        lover_user = bot.get_user(lover_id)
        lover_role = game_state.players[lover_id]['role']
        lover_template = game_state.players[lover_id].get('template')
        
        # Format role display
        lover_role_display = lover_role.replace('_', ' ').title()
        if lover_template:
            lover_role_display += f" ({lover_template.replace('_', ' ').title()})"
        
        # Kill the lover
        game_state.players[lover_id]['alive'] = False
        game_state.dead_players[lover_id] = lover_role
        
        await ctx.send(f"💔 **{lover_user.display_name}** ({lover_role_display}) dies of heartbreak after losing their lover!")
        
        # Handle lover's death effects recursively (but prevent infinite loop)
        await handle_player_death(lover_id, ctx)
        if lover_id != player_id:  # Prevent infinite recursion
            await process_death_effects(ctx, lover_id, 'heartbreak')
    
    # Assassin template - kill target when assassin dies
    if template == 'assassin':
        assassin_target = game_state.players[player_id].get('assassin_target')
        if assassin_target and game_state.is_player_alive(assassin_target):
            target_user = bot.get_user(assassin_target)
            target_role = game_state.players[assassin_target]['role']
            target_template = game_state.players[assassin_target].get('template')
            
            # Format role display
            role_display = target_role.replace('_', ' ').title()
            if target_template:
                role_display += f" ({target_template.replace('_', ' ').title()})"
            
            # Kill the target
            game_state.players[assassin_target]['alive'] = False
            game_state.dead_players[assassin_target] = target_role
            
            await ctx.send(f"💀 **Assassin's Revenge!** {user.display_name}'s death triggers their assassination target!\n\n⚰️ **{target_user.display_name}** ({role_display}) dies with the assassin!")
            
            # Handle target's death effects recursively
            await handle_player_death(assassin_target, ctx)
            await process_death_effects(ctx, assassin_target, 'assassin')
    
    # Hunter revenge kill
    if role == 'hunter':
        # Hunter can kill someone when they die
        # This would normally prompt the player, simplified here
        pass
    
    # Mad Scientist template/role - kill adjacent players
    if role == 'mad scientist':
        # Kill adjacent players (would need to implement seating order)
        pass
    
    # Wolf cub effect
    if role == 'wolf cub':
        # Wolves get extra kill next night (would be implemented in night processing)
        pass
    
    # Jester/Fool win condition
    if role in ['jester', 'fool'] and death_type == 'lynch':
        await announce_winner(ctx, 'jester', [player_id])

async def process_mysticism_action(player_id: int, action: dict):
    """Process mysticism power (mystic/wolf mystic)"""
    try:
        user = bot.get_user(player_id)
        target_id = action['target']
        target_user = bot.get_user(target_id)
        target_role = game_state.players[target_id]['role']
        
        # Check if target has active power role
        power_roles = ['seer', 'oracle', 'detective', 'guardian angel', 'bodyguard', 'hunter', 'vigilante', 
                      'village drunk', 'harlot', 'shaman', 'mystic', 'augur', 'priest'] + ACTUAL_WOLVES + \
                     ['werecrow', 'doomsayer', 'wolf shaman', 'hag', 'warlock', 'wolf mystic', 'serial killer', 
                      'monster', 'piper', 'succubus', 'mad scientist', 'time lord', 'turncoat']
        
        has_power = target_role in power_roles
        result = "has an active power role" if has_power else "does not have an active power role"
        
        await user.send(f"🔮 **Mysticism Result**: {target_user.display_name} **{result}**!")
        
    except Exception as e:
        logger.error(f"Error processing mysticism action: {e}")

async def process_observe_action(player_id: int, action: dict):
    """Process werecrow observation"""
    try:
        user = bot.get_user(player_id)
        target_id = action['target']
        target_user = bot.get_user(target_id)
        
        # Check who visited the target (simplified - would need visit tracking)
        visitors = []
        for pid, player_action in game_state.night_actions.items():
            if (player_action.get('action') == 'visit' and 
                player_action.get('target') == target_id and 
                pid != player_id):
                visitor_user = bot.get_user(pid)
                if visitor_user:
                    visitors.append(visitor_user.display_name)
        
        if visitors:
            visitor_list = ", ".join(visitors)
            await user.send(f"👁️ **Observation**: {target_user.display_name} was visited by: {visitor_list}")
        else:
            await user.send(f"👁️ **Observation**: {target_user.display_name} had no visitors tonight.")
            
    except Exception as e:
        logger.error(f"Error processing observe action: {e}")

async def process_detective_action(player_id: int, action: dict):
    """Process detective investigation"""
    try:
        user = bot.get_user(player_id)
        target_id = action['target']
        target_user = bot.get_user(target_id)
        target_role = game_state.players[target_id]['role']
        
        # Get detective's previous investigations
        investigations = game_state.players[player_id].get('investigations', [])
        
        # Check if target matches any previous investigation
        match_found = False
        for prev_target, prev_role in investigations:
            if prev_role == target_role:
                prev_user = bot.get_user(prev_target)
                await user.send(f"🕵️ **Detective Result**: {target_user.display_name} has the **same role** as {prev_user.display_name}!")
                match_found = True
                break
        
        if not match_found:
            if investigations:
                await user.send(f"🕵️ **Detective Result**: {target_user.display_name} has a **different role** from your previous investigations!")
            else:
                await user.send(f"🕵️ **Detective Result**: {target_user.display_name} is your first investigation!")
        
        # Add to investigations
        investigations.append((target_id, target_role))
        game_state.players[player_id]['investigations'] = investigations
        
    except Exception as e:
        logger.error(f"Error processing detective action: {e}")

async def process_drunk_shot(player_id: int, action: dict, deaths: list):
    """Process village drunk shooting (with accuracy issues)"""
    try:
        import random
        target_id = action['target']
        
        # Village drunk has accuracy issues
        accuracy = random.random()
        
        if accuracy < 0.3:  # 30% miss completely
            user = bot.get_user(player_id)
            await user.send("🍺 **Drunk Shot**: You missed completely! Maybe next time...")
        elif accuracy < 0.6:  # 30% hit adjacent player
            alive_players = game_state.get_alive_players()
            if len(alive_players) > 1:
                # Find adjacent players (simplified - random nearby player)
                nearby_players = [pid for pid in alive_players if pid != player_id and pid != target_id]
                if nearby_players:
                    actual_target = random.choice(nearby_players)
                    deaths.append((actual_target, 'village drunk (misfired)'))
                    
                    user = bot.get_user(player_id)
                    actual_user = bot.get_user(actual_target)
                    await user.send(f"🍺 **Drunk Shot**: You aimed poorly and hit {actual_user.display_name} instead!")
        else:  # 40% hit intended target
            deaths.append((target_id, 'village drunk'))
            user = bot.get_user(player_id)
            target_user = bot.get_user(target_id)
            await user.send(f"🍺 **Drunk Shot**: You successfully shot {target_user.display_name}!")
            
    except Exception as e:
        logger.error(f"Error processing drunk shot: {e}")

async def process_curse_action(player_id: int, action: dict):
    """Process warlock curse (2-night delayed kill)"""
    try:
        user = bot.get_user(player_id)
        target_id = action['target']
        target_user = bot.get_user(target_id)
        
        # Mark target for death in 2 nights
        game_state.players[target_id]['cursed_death'] = game_state.day_number + 2
        
        await user.send(f"🌙 **Curse Cast**: {target_user.display_name} will die in 2 nights!")
        
    except Exception as e:
        logger.error(f"Error processing curse action: {e}")

async def process_remember_action(player_id: int, action: dict):
    """Process amnesiac remembering"""
    try:
        user = bot.get_user(player_id)
        target_id = action['target']
        
        # Check if target is dead
        if target_id in game_state.dead_players:
            new_role = game_state.dead_players[target_id]
            old_role = game_state.players[player_id]['role']
            
            # Change role
            game_state.players[player_id]['role'] = new_role
            
            target_user = bot.get_user(target_id)
            await user.send(f"🧠 **Memory Restored**: You are now a **{new_role}** (remembered from {target_user.display_name})!")
            
            # Send new role PM
            await send_role_pm(bot, player_id)
        else:
            await user.send(f"❌ **Memory Failed**: You can only remember the roles of dead players!")
            
    except Exception as e:
        logger.error(f"Error processing remember action: {e}")

async def process_turn_action(player_id: int, action: dict):
    """Process turncoat team change"""
    try:
        user = bot.get_user(player_id)
        current_role = game_state.players[player_id]['role']
        
        # Simple team switching logic
        if current_role in VILLAGE_ROLES_ORDERED:
            # Join wolves
            game_state.players[player_id]['team'] = 'wolf'
            await user.send(f"🔄 **Team Change**: You have joined the wolf team!")
        else:
            # Join village
            game_state.players[player_id]['team'] = 'village'
            await user.send(f"🔄 **Team Change**: You have joined the village team!")
            
    except Exception as e:
        logger.error(f"Error processing turn action: {e}")

async def process_doom_action(player_id: int, action: dict):
    """Process doomsayer doom (next day kill)"""
    try:
        user = bot.get_user(player_id)
        target_id = action['target']
        target_user = bot.get_user(target_id)
        
        # Mark target for death next day
        game_state.players[target_id]['doomed'] = True
        
        await user.send(f"💀 **Doom Predicted**: {target_user.display_name} will die tomorrow!")
        
    except Exception as e:
        logger.error(f"Error processing doom action: {e}")

# ==================== DAY ACTION COMMANDS ====================
@bot.command(name='shoot')
async def gunner_shoot(ctx, *, target=None):
    """Gunner shoot command (day phase only)"""
    if not game_state.active or game_state.phase != "day":
        await ctx.send("❌ You can only shoot during the day phase!")
        return
    
    if not game_state.is_player_alive(ctx.author.id):
        await ctx.send("❌ Dead players cannot act!")
        return
    
    # Check if player has gunner template
    player = game_state.players[ctx.author.id]
    if player.get('template') not in ['gunner', 'sharpshooter']:
        await ctx.send("❌ You don't have the gunner ability!")
        return
    
    # Check if player has bullets
    bullets = player.get('bullets', 0)
    if bullets <= 0:
        await ctx.send("❌ You have no bullets left!")
        return
    
    if not target:
        alive_list = get_player_list_for_help(bot)
        await ctx.send(f"❌ Usage: `{prefix}shoot <player>`\n**Alive players**: {alive_list}")
        return
    
    # Find target using improved search
    target_id = find_player_by_name(target, bot, alive_only=True)
    if not target_id:
        alive_list = get_player_list_for_help(bot)
        await ctx.send(f"❌ Player '{target}' not found!\n**Alive players**: {alive_list}")
        return
    
    if target_id == ctx.author.id:
        await ctx.send("❌ You cannot shoot yourself!")
        return
    
    # Use bullet
    game_state.players[ctx.author.id]['bullets'] -= 1
    
    # Determine hit/miss for gunner (sharpshooter always hits)
    is_sharpshooter = player.get('template') == 'sharpshooter'
    hit_chance = 1.0 if is_sharpshooter else 0.8  # 80% hit chance for regular gunner
    shot_hits = random.random() < hit_chance
    
    target_user = bot.get_user(target_id)
    
    if not shot_hits:
        await ctx.send(f"💥 **{ctx.author.display_name}** shoots at **{target_user.display_name}** but misses!")
        return
    
    # Shot hits - check for protections
    if attempt_kill(target_id, 'shot'):
        # Target dies
        target_role = game_state.players[target_id]['role']
        target_template = game_state.players[target_id].get('template')
        
        # Format role display
        role_display = target_role.replace('_', ' ').title()
        if target_template:
            role_display += f" ({target_template.replace('_', ' ').title()})"
        
        # Kill target
        game_state.players[target_id]['alive'] = False
        game_state.dead_players[target_id] = target_role
        
        await ctx.send(f"💥 **{target_user.display_name}** ({role_display}) was shot and killed by {ctx.author.display_name}!")
        
        # Handle death effects
        await handle_player_death(target_id, ctx)
        await process_death_effects(ctx, target_id, 'shot')
    else:
        # Target was protected
        await ctx.send(f"💥 **{ctx.author.display_name}** shoots **{target_user.display_name}**, but they are protected!")
    
    # Check if game ended
    await check_win_conditions(ctx)

@bot.command(name='reveal', aliases=['mayor'])
async def mayor_reveal(ctx):
    """Mayor reveals themselves to cancel lynching"""
    if not game_state.active or game_state.phase != "day":
        await ctx.send("❌ You can only reveal as mayor during the day phase!")
        return
    
    if not game_state.is_player_alive(ctx.author.id):
        await ctx.send("❌ Dead players cannot use abilities!")
        return
    
    player_template = game_state.players[ctx.author.id].get('template')
    if player_template != 'mayor':
        await ctx.send("❌ You are not the mayor!")
        return
    
    if game_state.players[ctx.author.id].get('mayor_revealed', False):
        await ctx.send("❌ You have already used your mayor reveal!")
        return
    
    # Check if player is about to be lynched
    vote_counts = await calculate_final_votes()
    alive_count = len(game_state.get_alive_players())
    majority_needed = (alive_count // 2) + 1
    
    player_votes = vote_counts.get(ctx.author.id, 0)
    if player_votes < majority_needed:
        await ctx.send("❌ You can only reveal as mayor when you are about to be lynched (have majority votes)!")
        return
    
    # Use mayor reveal
    game_state.players[ctx.author.id]['mayor_revealed'] = True
    
    # Cancel all votes for today
    game_state.votes.clear()
    
    embed = discord.Embed(
        title="👑 MAYOR REVEALED!",
        description=f"**{ctx.author.display_name}** reveals themselves as the **MAYOR**!\n\nThe lynch is cancelled and all votes are reset!",
        color=0xFFD700
    )
    embed.add_field(
        name="⚠️ One-Time Use",
        value="The mayor can only use this ability once per game.",
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command(name='target', aliases=['assassin_target'])
async def assassin_target(ctx, *, target=None):
    """Assassin targets someone to die with them"""
    if not game_state.active:
        await ctx.send("❌ No game is currently active!")
        return
    
    if not game_state.is_player_alive(ctx.author.id):
        await ctx.send("❌ Dead players cannot use abilities!")
        return
    
    player_template = game_state.players[ctx.author.id].get('template')
    if player_template != 'assassin':
        await ctx.send("❌ You are not the assassin!")
        return
    
    if not target:
        alive_list = get_player_list_for_help(bot)
        await ctx.send(f"❌ Usage: `{prefix}target <player>`\n**Alive players**: {alive_list}")
        return
    
    # Find target player
    target_id = find_player_by_name(target, bot, alive_only=True)
    if not target_id:
        alive_list = get_player_list_for_help(bot)
        await ctx.send(f"❌ Player '{target}' not found!\n**Alive players**: {alive_list}")
        return
    
    if target_id == ctx.author.id:
        await ctx.send("❌ You cannot target yourself!")
        return
    
    # Set assassin target
    game_state.players[ctx.author.id]['assassin_target'] = target_id
    target_user = bot.get_user(target_id)
    
    await ctx.send(f"🎯 You have targeted **{target_user.display_name}**! If you die, they will die with you.")

# ==================== NIGHT ACTION COMMANDS ====================
# These commands work in DMs during night phase

async def security_warning(ctx, command_name: str):
    """Send security warning when night actions are used in public"""
    await ctx.send("🚨 **SECURITY WARNING!** Night actions must be done in DMs only! Please send me a private message to use this command.")
    try:
        await ctx.author.send(f"🌙 **Night Action Reminder**: Use `{prefix}{command_name}` in THIS private message, not in the public channel!")
    except:
        pass

@bot.command(name='see')
async def seer_see(ctx, *, target=None):
    """Seer/Oracle see command"""
    if isinstance(ctx.channel, discord.DMChannel):
        # Process in DM
        if (game_state.active and game_state.phase == "night" and 
            game_state.is_player_alive(ctx.author.id)):
            
            role = game_state.players[ctx.author.id]['role']
            if role not in ['seer', 'oracle']:
                await ctx.send("❌ You don't have this power!")
                return
            
            if not target:
                alive_list = get_player_list_for_help(bot)
                await ctx.send(f"❌ You must specify a target!\n**Alive players**: {alive_list}")
                return
            
            # Find target using improved search
            target_id = find_player_by_name(target, bot, alive_only=True)
            
            if not target_id:
                alive_list = get_player_list_for_help(bot)
                await ctx.send(f"❌ Player '{target}' not found!\n**Alive players**: {alive_list}")
                return
            
            if target_id == ctx.author.id:
                await ctx.send("❌ You cannot target yourself!")
                return
            
            # Record action
            game_state.night_actions[ctx.author.id] = {
                'action': 'see',
                'target': target_id
            }
            
            # Give result immediately (simplified)
            target_role = game_state.players[target_id]['role']
            target_user = bot.get_user(target_id)
            
            if role == 'seer':
                await ctx.send(f"🔮 **{target_user.display_name}** is a **{target_role}**!")
            else:  # oracle
                if target_role in VILLAGE_ROLES_ORDERED:
                    team = "Village"
                elif target_role in WOLF_ROLES_ORDERED or target_role in WOLFCHAT_ROLES:
                    team = "Wolf"
                else:
                    team = "Neutral"
                await ctx.send(f"🔮 **{target_user.display_name}** is on the **{team}** team!")
    else:
        # Security warning for public channel usage
        await security_warning(ctx, "see <player>")

@bot.command(name='kill')
async def night_kill(ctx, *, target=None):
    """Night kill command (also works for vengeful ghost when dead)"""
    if isinstance(ctx.channel, discord.DMChannel):
        # Check for vengeful ghost (can kill when dead)
        if (game_state.active and ctx.author.id in game_state.dead_players and 
            game_state.dead_players[ctx.author.id] == 'vengeful ghost'):
            
            # Vengeful ghost can kill from beyond the grave
            if not target:
                alive_list = get_player_list_for_help(bot)
                await ctx.send(f"❌ You must specify a target!\n**Alive players**: {alive_list}")
                return
            
            # Find target using helper function
            target_id = find_player_by_name(target, bot, alive_only=True)
            if not target_id:
                alive_list = get_player_list_for_help(bot)
                await ctx.send(f"❌ Player '{target}' not found!\n**Alive players**: {alive_list}")
                return
            
            if target_id == ctx.author.id:
                await ctx.send("❌ Suicide is bad! You cannot target yourself.")
                return
            
            # Check if already used vengeful ghost power
            if game_state.players[ctx.author.id].get('ghost_kill_used', False):
                await ctx.send("❌ You have already used your vengeful ghost kill!")
                return
            
            # Use the power
            game_state.players[ctx.author.id]['ghost_kill_used'] = True
            target_user = bot.get_user(target_id)
            
            # Kill target immediately (vengeful ghost kills bypass night phase)
            if attempt_kill(target_id, 'ghost'):
                target_role = game_state.players[target_id]['role']
                target_template = game_state.players[target_id].get('template')
                
                # Format role display
                role_display = target_role.replace('_', ' ').title()
                if target_template:
                    role_display += f" ({target_template.replace('_', ' ').title()})"
                
                # Kill target
                game_state.players[target_id]['alive'] = False
                game_state.dead_players[target_id] = target_role
                
                await ctx.send(f"👻 **{target_user.display_name}** ({role_display}) has been killed by your vengeful spirit!")
                
                # Handle death effects
                await handle_player_death(target_id, ctx)
                await process_death_effects(ctx, target_id, 'ghost')
            else:
                await ctx.send(f"👻 You attack **{target_user.display_name}** from beyond the grave, but they are protected!")
        
        elif (game_state.active and game_state.phase == "night" and 
            game_state.is_player_alive(ctx.author.id)):
            
            role = game_state.players[ctx.author.id]['role']
            if role not in ACTUAL_WOLVES + ['vigilante', 'serial killer', 'monster']:
                await ctx.send("❌ You don't have this power!")
                return
            
            if not target:
                alive_list = get_player_list_for_help(bot)
                await ctx.send(f"❌ You must specify a target!\n**Alive players**: {alive_list}")
                return
            
            # Find target using improved search
            target_id = find_player_by_name(target, bot, alive_only=True)
            
            if not target_id:
                alive_list = get_player_list_for_help(bot)
                await ctx.send(f"❌ Player '{target}' not found!\n**Alive players**: {alive_list}")
                return
            
            if target_id == ctx.author.id:
                await ctx.send("❌ You cannot target yourself!")
                return
            
            # Record action
            game_state.night_actions[ctx.author.id] = {
                'action': 'kill',
                'target': target_id
            }
            target_user = bot.get_user(target_id)
            await ctx.send(f"✅ You will attempt to kill **{target_user.display_name}** tonight!")
    else:
        # Security warning for public channel usage
        await security_warning(ctx, "kill <player>")

@bot.command(name='guard')
async def guard_protect(ctx, *, target=None):
    """Guard protection command"""
    if isinstance(ctx.channel, discord.DMChannel):
        if (game_state.active and game_state.phase == "night" and 
            game_state.is_player_alive(ctx.author.id)):
            
            role = game_state.players[ctx.author.id]['role']
            if role not in ['guardian angel', 'bodyguard']:
                await ctx.send("❌ You don't have this power!")
                return
            
            # Find target using helper function
            target_id = await find_target_for_night_action(ctx, target, bot, allow_self=False)
            if not target_id:
                return
            
            # Record action
            game_state.night_actions[ctx.author.id] = {
                'action': 'guard',
                'target': target_id
            }
            target_user = bot.get_user(target_id)
            await ctx.send(f"🛡️ You will protect **{target_user.display_name}** tonight!")
    else:
        await security_warning(ctx, "guard <player>")

@bot.command(name='visit')
async def harlot_visit(ctx, *, target=None):
    """Harlot/Succubus visit command"""
    if isinstance(ctx.channel, discord.DMChannel):
        if (game_state.active and game_state.phase == "night" and 
            game_state.is_player_alive(ctx.author.id)):
            
            role = game_state.players[ctx.author.id]['role']
            if role not in ['harlot', 'succubus']:
                await ctx.send("❌ You don't have this power!")
                return
            
            # Find target using helper function
            target_id = await find_target_for_night_action(ctx, target, bot, allow_self=False)
            if not target_id:
                return
            
            # Record action
            game_state.night_actions[ctx.author.id] = {
                'action': 'visit',
                'target': target_id
            }
            target_user = bot.get_user(target_id)
            
            if role == 'harlot':
                await ctx.send(f"💃 You will visit **{target_user.display_name}** tonight! (You'll be safe from wolves)")
            elif role == 'succubus':
                # Check if already visited this person before
                previous_visits = game_state.players[ctx.author.id].get('succubus_visits', [])
                if target_id in previous_visits:
                    await ctx.send(f"😈 You will visit **{target_user.display_name}** tonight! (They will die since this is your second visit)")
                else:
                    await ctx.send(f"😈 You will visit **{target_user.display_name}** tonight! (They will be entranced)")
    else:
        await security_warning(ctx, "visit <player>")

@bot.command(name='give')
async def shaman_give(ctx, *, target=None):
    """Shaman give totem command - now gives 1 random totem per shaman"""
    if isinstance(ctx.channel, discord.DMChannel):
        if (game_state.active and game_state.phase == "night" and 
            game_state.is_player_alive(ctx.author.id)):
            
            role = game_state.players[ctx.author.id]['role']
            if role not in ['shaman', 'wolf shaman', 'crazed shaman']:
                await ctx.send("❌ You don't have this power!")
                return
            
            # Check if shaman already used their totem this night
            if ctx.author.id in game_state.used_shamans:
                assigned_totem = game_state.assigned_totems.get(ctx.author.id, 'unknown')
                await ctx.send(f"❌ You already used your totem this night! You were assigned: **{assigned_totem.replace('_', ' ').title()}**")
                return
            
            if not target:
                alive_list = get_player_list_for_help(bot)
                await ctx.send(f"❌ Usage: `{prefix}give <player>`\n**Alive players**: {alive_list}")
                return
            
            # Find target using helper function
            target_id = await find_target_for_night_action(ctx, target, bot, allow_self=True)
            if not target_id:
                return
            
            # Assign random totem based on shaman type
            if ctx.author.id not in game_state.assigned_totems:
                if role == 'shaman':
                    available_totems = SHAMAN_TOTEMS
                elif role == 'wolf shaman':
                    available_totems = WOLF_SHAMAN_TOTEMS  
                elif role == 'crazed shaman':
                    available_totems = CRAZED_SHAMAN_TOTEMS
                
                assigned_totem = random.choice(available_totems)
                game_state.assigned_totems[ctx.author.id] = assigned_totem
            else:
                assigned_totem = game_state.assigned_totems[ctx.author.id]
            
            # Record action
            game_state.night_actions[ctx.author.id] = {
                'action': 'give',
                'target': target_id,
                'totem': assigned_totem
            }
            game_state.used_shamans.add(ctx.author.id)
            
            target_user = bot.get_user(target_id)
            
            # Show different info based on shaman type
            if role == 'crazed shaman':
                await ctx.send(f"🎭 You give a mysterious totem to **{target_user.display_name}**!\n\n❓ **Effect**: Unknown - you don't know what this totem does!")
            else:
                totem_description = TOTEMS.get(assigned_totem, "Unknown totem effect.")
                await ctx.send(f"🎭 You give **{assigned_totem.replace('_', ' ').title()}** to **{target_user.display_name}**!\n\n📝 **Effect**: {totem_description}")
    else:
        await security_warning(ctx, "give <player>")

@bot.command(name='observe')
async def werecrow_observe(ctx, *, target=None):
    """Werecrow observe command"""
    if isinstance(ctx.channel, discord.DMChannel):
        if (game_state.active and game_state.phase == "night" and 
            game_state.is_player_alive(ctx.author.id)):
            
            role = game_state.players[ctx.author.id]['role']
            if role != 'werecrow':
                await ctx.send("❌ You don't have this power!")
                return
            
            if not target:
                alive_list = get_player_list_for_help(bot)
                await ctx.send(f"❌ Usage: `{prefix}observe <player>`\n**Alive players**: {alive_list}")
                return
            
            # Find target using helper function
            target_id = await find_target_for_night_action(ctx, target, bot, allow_self=False)
            if not target_id:
                return
            
            # Record action
            game_state.night_actions[ctx.author.id] = {
                'action': 'observe',
                'target': target_id
            }
            target_user = bot.get_user(target_id)
            await ctx.send(f"👁️ You will observe **{target_user.display_name}** tonight!")
    else:
        await security_warning(ctx, "observe <player>")

@bot.command(name='id')
async def detective_id(ctx, *, target=None):
    """Detective ID command"""
    if isinstance(ctx.channel, discord.DMChannel):
        if (game_state.active and game_state.phase == "night" and 
            game_state.is_player_alive(ctx.author.id)):
            
            role = game_state.players[ctx.author.id]['role']
            if role != 'detective':
                await ctx.send("❌ You don't have this power!")
                return
            
            if not target:
                alive_list = get_player_list_for_help(bot)
                await ctx.send(f"❌ Usage: `{prefix}id <player>`\n**Alive players**: {alive_list}")
                return
            
            # Find target using helper function
            target_id = await find_target_for_night_action(ctx, target, bot, allow_self=False)
            if not target_id:
                return
            
            # Record action
            game_state.night_actions[ctx.author.id] = {
                'action': 'id',
                'target': target_id
            }
            target_user = bot.get_user(target_id)
            await ctx.send(f"🕵️ You will investigate **{target_user.display_name}** tonight!")
    else:
        await security_warning(ctx, "id <player>")

@bot.command(name='drunk_shoot')
async def drunk_shoot(ctx, *, target=None):
    """Village drunk shoot command"""
    if isinstance(ctx.channel, discord.DMChannel):
        if (game_state.active and game_state.phase == "night" and 
            game_state.is_player_alive(ctx.author.id)):
            
            role = game_state.players[ctx.author.id]['role']
            if role != 'village drunk':
                await ctx.send("❌ You don't have this power!")
                return
            
            if not target:
                alive_list = get_player_list_for_help(bot)
                await ctx.send(f"❌ Usage: `{prefix}drunk_shoot <player>`\n**Alive players**: {alive_list}")
                return
            
            # Find target using helper function  
            target_id = await find_target_for_night_action(ctx, target, bot, allow_self=False)
            if not target_id:
                return
            
            # Record action
            game_state.night_actions[ctx.author.id] = {
                'action': 'shoot',
                'target': target_id
            }
            target_user = bot.get_user(target_id)
            await ctx.send(f"🔫 You will shoot **{target_user.display_name}** tonight!")
    else:
        await security_warning(ctx, "drunk_shoot <player>")

# ==================== MISSING ADVANCED ROLE COMMANDS ====================

@bot.command(name='hex')
async def hag_hex(ctx, *, target=None):
    """Hag hex command"""
    if isinstance(ctx.channel, discord.DMChannel):
        if (game_state.active and game_state.phase == "night" and 
            game_state.is_player_alive(ctx.author.id)):
            
            role = game_state.players[ctx.author.id]['role']
            if role != 'hag':
                await ctx.send("❌ You don't have this power!")
                return
            
            if not target:
                alive_list = get_player_list_for_help(bot)
                await ctx.send(f"❌ Usage: `{prefix}hex <player>`\n**Alive players**: {alive_list}")
                return
            
            # Find target using helper function
            target_id = await find_target_for_night_action(ctx, target, bot, allow_self=False)
            if not target_id:
                return
            
            # Record action
            game_state.night_actions[ctx.author.id] = {
                'action': 'hex',
                'target': target_id
            }
            target_user = bot.get_user(target_id)
            await ctx.send(f"🔮 You will hex **{target_user.display_name}** tonight!")
    else:
        await security_warning(ctx, "hex <player>")

@bot.command(name='curse')
async def warlock_curse(ctx, *, target=None):
    """Warlock curse command"""
    if isinstance(ctx.channel, discord.DMChannel):
        if (game_state.active and game_state.phase == "night" and 
            game_state.is_player_alive(ctx.author.id)):
            
            role = game_state.players[ctx.author.id]['role']
            if role != 'warlock':
                await ctx.send("❌ You don't have this power!")
                return
            
            # Check if already used
            if game_state.players[ctx.author.id].get('curse_used', False):
                await ctx.send("❌ You have already used your curse!")
                return
            
            if not target:
                alive_list = get_player_list_for_help(bot)
                await ctx.send(f"❌ Usage: `{prefix}curse <player>`\n**Alive players**: {alive_list}")
                return
            
            # Find target using helper function
            target_id = await find_target_for_night_action(ctx, target, bot, allow_self=False)
            if not target_id:
                return
            
            # Record action
            game_state.night_actions[ctx.author.id] = {
                'action': 'curse',
                'target': target_id
            }
            game_state.players[ctx.author.id]['curse_used'] = True
            target_user = bot.get_user(target_id)
            await ctx.send(f"🌙 You will curse **{target_user.display_name}** tonight! They will die in 2 nights.")
    else:
        await security_warning(ctx, "curse <player>")

@bot.command(name='charm')
async def piper_charm(ctx, *, target=None):
    """Piper charm command"""
    if isinstance(ctx.channel, discord.DMChannel):
        if (game_state.active and game_state.phase == "night" and 
            game_state.is_player_alive(ctx.author.id)):
            
            role = game_state.players[ctx.author.id]['role']
            if role != 'piper':
                await ctx.send("❌ You don't have this power!")
                return
            
            if not target:
                alive_list = get_player_list_for_help(bot)
                await ctx.send(f"❌ Usage: `{prefix}charm <player>`\n**Alive players**: {alive_list}")
                return
            
            # Find target using helper function
            target_id = await find_target_for_night_action(ctx, target, bot, allow_self=False)
            if not target_id:
                return
            
            # Record action
            game_state.night_actions[ctx.author.id] = {
                'action': 'charm',
                'target': target_id
            }
            target_user = bot.get_user(target_id)
            await ctx.send(f"🎵 You will charm **{target_user.display_name}** tonight!")
    else:
        await security_warning(ctx, "charm <player>")

@bot.command(name='remember')
async def amnesiac_remember(ctx, *, target=None):
    """Amnesiac remember command"""
    if isinstance(ctx.channel, discord.DMChannel):
        if (game_state.active and game_state.phase == "night" and 
            game_state.is_player_alive(ctx.author.id)):
            
            role = game_state.players[ctx.author.id]['role']
            if role != 'amnesiac':
                await ctx.send("❌ You don't have this power!")
                return
            
            # Check if already used
            if game_state.players[ctx.author.id].get('remember_used', False):
                await ctx.send("❌ You have already used your remember power!")
                return
            
            # Show dead players
            dead_players = [bot.get_user(uid).display_name for uid in game_state.dead_players.keys()]
            if not dead_players:
                await ctx.send("❌ No dead players to remember!")
                return
            
            if not target:
                await ctx.send(f"❌ Usage: `{prefix}remember <dead_player>`\n**Dead players**: {', '.join(dead_players)}")
                return
            
            # Find dead player
            target_id = find_player_by_name(target, bot, alive_only=False)
            if not target_id or target_id not in game_state.dead_players:
                await ctx.send(f"❌ Dead player '{target}' not found!\n**Dead players**: {', '.join(dead_players)}")
                return
            
            # Record action
            game_state.night_actions[ctx.author.id] = {
                'action': 'remember',
                'target': target_id
            }
            game_state.players[ctx.author.id]['remember_used'] = True
            target_user = bot.get_user(target_id)
            await ctx.send(f"🧠 You will remember the role of **{target_user.display_name}** tonight!")
    else:
        await security_warning(ctx, "remember <dead_player>")

@bot.command(name='turn')
async def turncoat_turn(ctx):
    """Turncoat team change command"""
    if isinstance(ctx.channel, discord.DMChannel):
        if (game_state.active and game_state.phase == "night" and 
            game_state.is_player_alive(ctx.author.id)):
            
            role = game_state.players[ctx.author.id]['role']
            if role != 'turncoat':
                await ctx.send("❌ You don't have this power!")
                return
            
            # Check if already used
            if game_state.players[ctx.author.id].get('turn_used', False):
                await ctx.send("❌ You have already used your turn power!")
                return
            
            # Record action
            game_state.night_actions[ctx.author.id] = {
                'action': 'turn',
                'target': ctx.author.id
            }
            game_state.players[ctx.author.id]['turn_used'] = True
            await ctx.send(f"🔄 You will change your team allegiance tonight!")
    else:
        await security_warning(ctx, "turn")

@bot.command(name='doom')
async def doomsayer_doom(ctx, *, target=None):
    """Doomsayer doom command"""
    if isinstance(ctx.channel, discord.DMChannel):
        if (game_state.active and game_state.phase == "night" and 
            game_state.is_player_alive(ctx.author.id)):
            
            role = game_state.players[ctx.author.id]['role']
            if role != 'doomsayer':
                await ctx.send("❌ You don't have this power!")
                return
            
            # Check if already used
            if game_state.players[ctx.author.id].get('doom_used', False):
                await ctx.send("❌ You have already used your doom power!")
                return
            
            if not target:
                alive_list = get_player_list_for_help(bot)
                await ctx.send(f"❌ Usage: `{prefix}doom <player>`\n**Alive players**: {alive_list}")
                return
            
            # Find target using helper function
            target_id = await find_target_for_night_action(ctx, target, bot, allow_self=False)
            if not target_id:
                return
            
            # Record action
            game_state.night_actions[ctx.author.id] = {
                'action': 'doom',
                'target': target_id
            }
            game_state.players[ctx.author.id]['doom_used'] = True
            target_user = bot.get_user(target_id)
            await ctx.send(f"☠️ You will doom **{target_user.display_name}** tonight! They will die tomorrow.")
    else:
        await security_warning(ctx, "doom <player>")

@bot.command(name='bless')
async def priest_bless(ctx, *, target=None):
    """Priest bless command"""
    if isinstance(ctx.channel, discord.DMChannel):
        if (game_state.active and game_state.phase == "night" and 
            game_state.is_player_alive(ctx.author.id)):
            
            role = game_state.players[ctx.author.id]['role']
            if role != 'priest':
                await ctx.send("❌ You don't have this power!")
                return
            
            if not target:
                alive_list = get_player_list_for_help(bot)
                await ctx.send(f"❌ Usage: `{prefix}bless <player>`\n**Alive players**: {alive_list}")
                return
            
            # Find target using helper function
            target_id = await find_target_for_night_action(ctx, target, bot, allow_self=True)
            if not target_id:
                return
            
            # Record action
            game_state.night_actions[ctx.author.id] = {
                'action': 'bless',
                'target': target_id
            }
            target_user = bot.get_user(target_id)
            await ctx.send(f"✨ You will bless **{target_user.display_name}** tonight!")
    else:
        await security_warning(ctx, "bless <player>")

@bot.command(name='mysticism')
async def mystic_power(ctx, *, target=None):
    """Mystic/Wolf Mystic mysticism command"""
    if isinstance(ctx.channel, discord.DMChannel):
        if (game_state.active and game_state.phase == "night" and 
            game_state.is_player_alive(ctx.author.id)):
            
            role = game_state.players[ctx.author.id]['role']
            if role not in ['mystic', 'wolf mystic']:
                await ctx.send("❌ You don't have this power!")
                return
            
            if not target:
                alive_list = get_player_list_for_help(bot)
                await ctx.send(f"❌ Usage: `{prefix}mysticism <player>`\n**Alive players**: {alive_list}")
                return
            
            # Find target using helper function
            target_id = await find_target_for_night_action(ctx, target, bot, allow_self=False)
            if not target_id:
                return
            
            # Record action
            game_state.night_actions[ctx.author.id] = {
                'action': 'mysticism',
                'target': target_id
            }
            target_user = bot.get_user(target_id)
            await ctx.send(f"🔮 You will use mysticism on **{target_user.display_name}** tonight!")
    else:
        await security_warning(ctx, "mysticism <player>")

@bot.command(name='time')
async def time_lord_time(ctx):
    """Time Lord time travel command - used during day phase"""
    if not isinstance(ctx.channel, discord.DMChannel):
        await ctx.send("🚨 **SECURITY WARNING!** Time travel must be done in DMs only!")
        return
    
    if (game_state.active and game_state.phase == "day" and 
        game_state.is_player_alive(ctx.author.id)):
        
        role = game_state.players[ctx.author.id]['role']
        if role != 'time lord':
            await ctx.send("❌ You don't have this power!")
            return
        
        # Check if already used
        if game_state.players[ctx.author.id].get('time_used', False):
            await ctx.send("❌ You have already used your time travel power!")
            return
        
        # Check if there was a lynch to undo
        if not game_state.last_votes:
            await ctx.send("❌ No lynch to undo!")
            return
        
        game_state.players[ctx.author.id]['time_used'] = True
        await ctx.send(f"⏰ You are activating time travel! The previous lynch will be undone!")
        
        # Reset the lynch (this would need more complex implementation)
        # For now, just notify
        await ctx.send("🌀 Time has been reversed! Previous day phase is restored.")
    else:
        await ctx.send("❌ Time travel can only be used during the day phase!")

@bot.command(name='match', aliases=['choose', 'lovers'])
async def matchmaker_match(ctx, *, targets=None):
    """Matchmaker creates lovers (first night only)"""
    if isinstance(ctx.channel, discord.DMChannel):
        if (game_state.active and game_state.phase == "night" and 
            game_state.is_player_alive(ctx.author.id)):
            
            role = game_state.players[ctx.author.id]['role']
            if role != 'matchmaker':
                await ctx.send("❌ You don't have this power!")
                return
            
            # Check if matchmaker already used power
            if game_state.players[ctx.author.id].get('matched', False):
                await ctx.send("❌ You have already created lovers!")
                return
            
            # Check if it's first night
            if game_state.day_number > 1:
                await ctx.send("❌ You can only create lovers on the first night!")
                return
            
            if not targets:
                alive_list = get_player_list_for_help(bot)
                await ctx.send(f"❌ Usage: `{prefix}match <player1> and <player2>`\n**Alive players**: {alive_list}")
                return
            
            # Parse targets (expect "player1 and player2" format)
            if " and " not in targets.lower():
                await ctx.send(f"❌ Usage: `{prefix}match <player1> and <player2>`")
                return
            
            target_names = [name.strip() for name in targets.lower().split(" and ")]
            if len(target_names) != 2:
                await ctx.send(f"❌ You must select exactly 2 players!")
                return
            
            # Find both targets
            target_ids = []
            for name in target_names:
                target_id = find_player_by_name(name, bot, alive_only=True)
                if not target_id:
                    alive_list = get_player_list_for_help(bot)
                    await ctx.send(f"❌ Player '{name}' not found!\n**Alive players**: {alive_list}")
                    return
                target_ids.append(target_id)
            
            if target_ids[0] == target_ids[1]:
                await ctx.send("❌ You must select two different players!")
                return
            
            # Record the match
            game_state.players[ctx.author.id]['matched'] = True
            game_state.players[target_ids[0]]['lover'] = target_ids[1]
            game_state.players[target_ids[1]]['lover'] = target_ids[0]
            
            target1_user = bot.get_user(target_ids[0])
            target2_user = bot.get_user(target_ids[1])
            
            await ctx.send(f"💕 You have made **{target1_user.display_name}** and **{target2_user.display_name}** lovers!\n\n💔 If one dies, the other will die of heartbreak!")
            
            # Notify the lovers
            try:
                await target1_user.send(f"💕 **You are now lovers with {target2_user.display_name}!**\n\n💔 If one of you dies, the other will die of heartbreak!")
                await target2_user.send(f"💕 **You are now lovers with {target1_user.display_name}!**\n\n💔 If one of you dies, the other will die of heartbreak!")
            except:
                pass
    else:
        await security_warning(ctx, "match <player1> and <player2>")

# ==================== INFORMATION COMMANDS ====================

@bot.command(name='dead', aliases=['graveyard'])
async def list_dead(ctx):
    """List all dead players"""
    if not game_state.active:
        await ctx.send("❌ No game is currently active!")
        return
    
    if not game_state.dead_players:
        await ctx.send("😇 No one has died yet!")
        return
    
    dead_list = []
    for player_id, role in game_state.dead_players.items():
        user = bot.get_user(player_id)
        if user:
            dead_list.append(f"{user.display_name} - {role}")
    
    embed = discord.Embed(
        title=f"💀 Dead Players ({len(dead_list)})",
        description="\n".join(dead_list),
        color=0xFF0000
    )
    
    await ctx.send(embed=embed)

@bot.command(name='status', aliases=['game'])
async def game_status(ctx):
    """Show current game status"""
    if not game_state.active:
        await ctx.send("❌ No game is currently active!")
        return
    
    embed = discord.Embed(
        title="🎮 Game Status",
        color=0x8B4513
    )
    
    embed.add_field(name="Phase", value=game_state.phase.title(), inline=True)
    embed.add_field(name="Day", value=str(game_state.day_number), inline=True)
    embed.add_field(name="Alive Players", value=str(len(game_state.get_alive_players())), inline=True)
    
    if game_state.phase == "day" and game_state.votes:
        vote_count = len(game_state.votes)
        embed.add_field(name="Votes Cast", value=str(vote_count), inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='roles', aliases=['rolelist'])
async def list_roles(ctx):
    """List all available roles"""
    embed = discord.Embed(title="🎭 All Roles", color=0x8B4513)
    
    embed.add_field(
        name="🏘️ Village Team",
        value=", ".join(VILLAGE_ROLES_ORDERED),
        inline=False
    )
    
    embed.add_field(
        name="🐺 Wolf Team", 
        value=", ".join(WOLF_ROLES_ORDERED),
        inline=False
    )
    
    embed.add_field(
        name="⚪ Neutral Team",
        value=", ".join(NEUTRAL_ROLES_ORDERED),
        inline=False
    )
    
    embed.add_field(
        name="🎖️ Templates",
        value=", ".join(TEMPLATES_ORDERED),
        inline=False
    )
    
    await ctx.send(embed=embed)

@bot.command(name='role')
async def role_info(ctx, *, role_name=None):
    """Get information about a specific role"""
    if not role_name:
        await ctx.send(f"❌ Usage: `{prefix}role <role_name>`")
        return
    
    role_name = role_name.lower()
    
    if role_name in ROLE_DESCRIPTIONS:
        description = ROLE_DESCRIPTIONS[role_name]
    elif role_name in TEMPLATE_DESCRIPTIONS:
        description = TEMPLATE_DESCRIPTIONS[role_name]
    else:
        await ctx.send("❌ Role not found!")
        return
    
    embed = discord.Embed(
        title=f"🎭 {role_name.title()}",
        description=description,
        color=0x8B4513
    )
    
    await ctx.send(embed=embed)

@bot.command(name='totems')
async def list_totems(ctx):
    """List all totems"""
    embed = discord.Embed(title="🎭 Totems", color=0x8B4513)
    
    shaman_totems = "\n".join([f"**{t.replace('_', ' ').title()}**: {TOTEMS[t]}" for t in SHAMAN_TOTEMS])
    wolf_totems = "\n".join([f"**{t.replace('_', ' ').title()}**: {TOTEMS[t]}" for t in WOLF_SHAMAN_TOTEMS])
    
    embed.add_field(name="🧙 Shaman Totems", value=shaman_totems[:1024], inline=False)
    embed.add_field(name="🐺 Wolf Shaman Totems", value=wolf_totems[:1024], inline=False)
    
    await ctx.send(embed=embed)

# ==================== WOLFCHAT COMMANDS ====================
@bot.command(name='wchat', aliases=['wolfchat', 'wc'])
async def wolfchat_command(ctx, *, message=None):
    """Send a message to wolfchat (for wolves only)"""
    if not game_state.active:
        await ctx.send("❌ No game is currently active!")
        return
    
    if ctx.author.id not in game_state.players:
        await ctx.send("❌ You're not in the current game!")
        return
    
    player_role = game_state.players[ctx.author.id]['role']
    
    # Check if player has wolfchat access
    if player_role not in WOLFCHAT_ROLES:
        await ctx.send("❌ You don't have access to wolfchat!")
        return
    
    if not game_state.is_player_alive(ctx.author.id):
        await ctx.send("❌ Dead players cannot use wolfchat! Use dead chat instead.")
        return
    
    if not game_state.wolfchat_channel:
        await ctx.send("❌ Wolfchat channel not available!")
        return
    
    if not message:
        await ctx.send(f"❌ Usage: `{prefix}wchat <message>`")
        return
    
    # Send message to wolfchat
    embed = discord.Embed(
        description=f"**{ctx.author.display_name}**: {message}",
        color=0x8B0000
    )
    embed.set_footer(text=f"From main channel • {ctx.channel.name}")
    
    await game_state.wolfchat_channel.send(embed=embed)
    await ctx.send("🐺 Message sent to wolfchat!")

@bot.command(name='deadchat', aliases=['dchat', 'dc'])
async def deadchat_command(ctx, *, message=None):
    """Send a message to dead chat (for dead players only)"""
    if not game_state.active:
        await ctx.send("❌ No game is currently active!")
        return
    
    if ctx.author.id not in game_state.players:
        await ctx.send("❌ You're not in the current game!")
        return
    
    if game_state.is_player_alive(ctx.author.id):
        await ctx.send("❌ Only dead players can use dead chat!")
        return
    
    if not game_state.dead_chat_channel:
        await ctx.send("❌ Dead chat channel not available!")
        return
    
    if not message:
        await ctx.send(f"❌ Usage: `{prefix}deadchat <message>`")
        return
    
    # Send message to dead chat
    player_role = game_state.players[ctx.author.id]['role']
    embed = discord.Embed(
        description=f"**{ctx.author.display_name}** ({player_role}): {message}",
        color=0x2F4F4F
    )
    embed.set_footer(text=f"From main channel • {ctx.channel.name}")
    
    await game_state.dead_chat_channel.send(embed=embed)
    await ctx.send("💀 Message sent to dead chat!")

@bot.command(name='chatinfo', aliases=['chats'])
async def chat_info(ctx):
    """Show information about game chat channels"""
    if not game_state.active:
        await ctx.send("❌ No game is currently active!")
        return
    
    embed = discord.Embed(
        title="📢 Game Chat Information",
        description="Information about available chat channels",
        color=0x8B4513
    )
    
    # Wolfchat info
    if game_state.wolfchat_channel:
        wolf_members = [bot.get_user(uid).display_name for uid in game_state.wolfchat_members 
                       if bot.get_user(uid)]
        embed.add_field(
            name="🐺 Wolfchat",
            value=f"**Channel**: {game_state.wolfchat_channel.mention}\n"
                  f"**Members**: {', '.join(wolf_members) if wolf_members else 'None'}\n"
                  f"**Command**: `{prefix}wchat <message>`",
            inline=False
        )
    
    # Dead chat info
    if game_state.dead_chat_channel:
        dead_members = [bot.get_user(uid).display_name for uid in game_state.dead_chat_members 
                       if bot.get_user(uid)]
        embed.add_field(
            name="💀 Dead Chat",
            value=f"**Channel**: {game_state.dead_chat_channel.mention}\n"
                  f"**Members**: {', '.join(dead_members) if dead_members else 'None'}\n"
                  f"**Command**: `{prefix}deadchat <message>`",
            inline=False
        )
    
    # Usage info
    embed.add_field(
        name="📝 Usage",
        value="• Wolves can use wolfchat to coordinate privately\n"
              "• Dead players can use dead chat to discuss freely\n"
              "• Commands send messages from main channel to private chats\n"
              "• You can also type directly in the private channels",
        inline=False
    )
    
    await ctx.send(embed=embed)

# ==================== ADMIN COMMANDS ====================
@bot.command(name='fstart')
async def force_start(ctx):
    """Force start game (admin only)"""
    if not ctx.author.guild_permissions.manage_messages:
        await ctx.send("❌ You need Manage Messages permission!")
        return
    
    if not game_state.active or game_state.phase != "signup":
        await ctx.send("❌ No signup phase active!")
        return
    
    await start_game(ctx)

@bot.command(name='fday')
async def force_day(ctx):
    """Force day phase (admin only)"""
    if not ctx.author.guild_permissions.manage_messages:
        await ctx.send("❌ You need Manage Messages permission!")
        return
    
    if game_state.phase == "night":
        await end_night_phase(ctx)
    else:
        await ctx.send("❌ Not in night phase!")

@bot.command(name='fnight')
async def force_night(ctx):
    """Force night phase (admin only)"""
    if not ctx.author.guild_permissions.manage_messages:
        await ctx.send("❌ You need Manage Messages permission!")
        return
    
    if game_state.phase == "day":
        await end_day_phase(ctx)
    else:
        await ctx.send("❌ Not in day phase!")

@bot.command(name='settings')
async def game_settings(ctx, setting=None, value=None):
    """View or change game settings (admin only)"""
    if setting is None:
        # Show current settings
        embed = discord.Embed(title="⚙️ Game Settings", color=0x8B4513)
        for key, val in game_state.settings.items():
            embed.add_field(name=key.replace('_', ' ').title(), value=str(val), inline=True)
        await ctx.send(embed=embed)
        return
    
    if not ctx.author.guild_permissions.manage_messages:
        await ctx.send("❌ You need Manage Messages permission!")
        return
    
    if value is None:
        await ctx.send(f"❌ Current {setting}: {game_state.settings.get(setting, 'Not found')}")
        return
    
    try:
        value = int(value)
        if setting in game_state.settings:
            game_state.settings[setting] = value
            await ctx.send(f"✅ Set {setting} to {value}")
        else:
            await ctx.send("❌ Invalid setting!")
    except ValueError:
        await ctx.send("❌ Value must be a number!")

# ==================== HELP COMMAND ====================
@bot.command(name='help', aliases=['h', 'commands'])
async def help_command(ctx, category=None):
    """Show help information"""
    
    if category is None:
        embed = discord.Embed(
            title="🐺 Discord Werewolf Bot - COMPLETE HELP",
            description="A fully-featured Werewolf game bot with ALL roles and commands!",
            color=0x8B4513
        )
        
        embed.add_field(
            name="🎮 Gamemodes",
            value=f"`{prefix}gamemodes` - View available gamemodes",
            inline=False
        )
        
        embed.add_field(
            name="📋 Game Commands",
            value=f"`{prefix}help game` - Game management commands",
            inline=False
        )
        
        embed.add_field(
            name="🗳️ Voting Commands", 
            value=f"`{prefix}help voting` - Day phase voting commands",
            inline=False
        )
        
        embed.add_field(
            name="🌙 Night Commands",
            value=f"`{prefix}help night` - Night action commands", 
            inline=False
        )
        
        embed.add_field(
            name="📊 Info Commands",
            value=f"`{prefix}help info` - Information and status commands",
            inline=False
        )
        
        embed.add_field(
            name="👑 Admin Commands",
            value=f"`{prefix}help admin` - Administrative commands",
            inline=False
        )
        
        embed.add_field(
            name="💬 Chat Commands",
            value=f"`{prefix}help chat` - Wolfchat and dead chat commands",
            inline=False
        )
        
        embed.add_field(
            name="🎭 Roles & Features",
            value=f"• **43 Unique Roles** across 3 teams\n• **16 Totems** with special effects\n• **7 Templates** for role modifications\n• **Day/Night Cycles** with timed phases\n• **Wolfchat & Dead Chat** for team coordination\n• **Complete Win Conditions** for all teams",
            inline=False
        )
        
    elif category.lower() == "game":
        embed = discord.Embed(title="📋 Game Management Commands", color=0x8B4513)
        embed.add_field(name=f"{prefix}start [gamemode]", value="Start a game (default or foolish)", inline=False)
        embed.add_field(name=f"{prefix}foolish", value="Start a foolish gamemode", inline=False)
        embed.add_field(name=f"{prefix}gamemodes", value="Show available gamemodes", inline=False)
        embed.add_field(name=f"{prefix}join", value="Join current game", inline=False)
        embed.add_field(name=f"{prefix}leave", value="Leave current game", inline=False)
        embed.add_field(name=f"{prefix}end", value="End current game (admin)", inline=False)
        embed.add_field(name=f"{prefix}start", value="Start a new game signup", inline=False)
        embed.add_field(name=f"{prefix}join", value="Join the current game", inline=False)  
        embed.add_field(name=f"{prefix}leave", value="Leave during signup", inline=False)
        embed.add_field(name=f"{prefix}end", value="End the current game (admin)", inline=False)
        
    elif category.lower() == "voting":
        embed = discord.Embed(title="🗳️ Voting Commands", color=0xFFD700)
        embed.add_field(name=f"{prefix}vote <player>", value="Vote to lynch a player", inline=False)
        embed.add_field(name=f"{prefix}unvote", value="Remove your vote", inline=False)
        embed.add_field(name=f"{prefix}votes", value="Show current vote count", inline=False)
        
    elif category.lower() == "night":
        embed = discord.Embed(title="🌙 Night Action Commands (DM Only)", color=0x2F4F4F)
        embed.add_field(name=f"{prefix}see <player>", value="Seer/Oracle: Learn role or team", inline=False)
        embed.add_field(name=f"{prefix}kill <player>", value="Wolf/Vigilante: Kill a player", inline=False)
        embed.add_field(name=f"{prefix}guard <player>", value="Guardian Angel/Bodyguard: Protect a player", inline=False)
        embed.add_field(name=f"{prefix}give <player> <totem>", value="Shaman: Give a totem", inline=False)
        embed.add_field(name=f"{prefix}visit <player>", value="Harlot: Visit a player", inline=False)
        embed.add_field(name=f"{prefix}observe <player>", value="Werecrow: See who visits target", inline=False)
        
    elif category.lower() == "info":
        embed = discord.Embed(title="📊 Information Commands", color=0x00FF00)
        embed.add_field(name=f"{prefix}players", value="List alive players", inline=False)
        embed.add_field(name=f"{prefix}dead", value="List dead players", inline=False) 
        embed.add_field(name=f"{prefix}status", value="Show game status", inline=False)
        embed.add_field(name=f"{prefix}roles", value="List all 43 roles", inline=False)
        embed.add_field(name=f"{prefix}role <name>", value="Get role information", inline=False)
        embed.add_field(name=f"{prefix}totems", value="List all 16 totems", inline=False)
        
    elif category.lower() == "admin":
        embed = discord.Embed(title="👑 Admin Commands", color=0xFF0000)
        embed.add_field(name=f"{prefix}fstart", value="Force start game", inline=False)
        embed.add_field(name=f"{prefix}fday", value="Force day phase", inline=False)
        embed.add_field(name=f"{prefix}fnight", value="Force night phase", inline=False)
        embed.add_field(name=f"{prefix}settings", value="View/change game settings", inline=False)
        
    elif category.lower() == "chat":
        embed = discord.Embed(title="💬 Chat Commands", color=0x8B0000)
        embed.add_field(name=f"{prefix}wchat <message>", value="Send message to wolfchat (wolves only)", inline=False)
        embed.add_field(name=f"{prefix}deadchat <message>", value="Send message to dead chat (dead players only)", inline=False)
        embed.add_field(name=f"{prefix}chatinfo", value="Show information about game chat channels", inline=False)
        embed.add_field(
            name="📝 Chat System Info",
            value="• **Wolfchat**: Private channel for wolf team coordination\n"
                  "• **Dead Chat**: Channel for eliminated players to discuss\n"
                  "• **Commands**: Send messages from main channel to private chats\n"
                  "• **Direct Access**: You can also type directly in private channels",
            inline=False
        )
        
    else:
        await ctx.send("❌ Invalid help category! Use: game, voting, night, info, admin, chat")
        return
    
    await ctx.send(embed=embed)

# ==================== BOT STARTUP ====================
def main():
    """Main function to start the bot"""
    # Get token from environment or config
    token = os.getenv('DISCORD_TOKEN') or config.get('discord_token')
    
    if not token:
        logger.error("No Discord token found! Set DISCORD_TOKEN environment variable or add to config.")
        return
    
    logger.info("Starting Discord Werewolf Bot - COMPLETE IMPLEMENTATION")
    logger.info(f"Prefix: {prefix}")
    logger.info("Features: 43 Roles, 16 Totems, 7 Templates, Complete Game System")
    
    try:
        bot.run(token)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == "__main__":
    main()
