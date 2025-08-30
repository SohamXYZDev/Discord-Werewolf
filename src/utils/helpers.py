"""
Utility helpers for Discord Werewolf Bot
Handles Discord-specific operations like role management, embeds, and rate limiting
Enhanced version with comprehensive bot integration
"""

import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from src.core import get_config, get_logger

# Global references set during initialization
_bot: commands.Bot = None
_guild: discord.Guild = None
_config = None
_logger = None

# Rate limiting
_rate_limiters: Dict[int, datetime] = {}

# Simple recent-send dedupe to avoid accidental duplicate messages
_recent_sends: Dict[tuple, datetime] = {}
_DUPE_WINDOW_SECONDS = 2

class PermissionLevel:
    """Permission levels for commands"""
    EVERYONE = 0
    PLAYING = 1
    MODERATOR = 2
    ADMIN = 3
    OWNER = 4

async def setup_helpers(bot: commands.Bot):
    """Initialize helper system with bot reference"""
    global _bot, _guild, _config, _logger
    
    _bot = bot
    _config = get_config()
    _logger = get_logger()
    
    # Get guild reference
    if _config.guild_id:
        _guild = bot.get_guild(_config.guild_id)
        if not _guild:
            _logger.warning(f"Could not find guild with ID {_config.guild_id}")
    
    _logger.info("Helper system initialized")

def create_embed(title: str, description: str = "", color: discord.Color = discord.Color.blue()) -> discord.Embed:
    """Create a standard embed with consistent formatting"""
    embed = discord.Embed(
        title=title,
        description=description,
        color=color,
        timestamp=datetime.utcnow()
    )
    embed.set_footer(text="Discord Werewolf Bot")
    return embed

def create_error_embed(title: str, description: str = "") -> discord.Embed:
    """Create an error embed"""
    return create_embed(title, description, discord.Color.red())

def create_success_embed(title: str, description: str = "") -> discord.Embed:
    """Create a success embed"""
    return create_embed(title, description, discord.Color.green())

def create_warning_embed(title: str, description: str = "") -> discord.Embed:
    """Create a warning embed"""
    return create_embed(title, description, discord.Color.orange())

def format_player_list(players: List[Any], show_status: bool = True) -> str:
    """Format a list of players for display"""
    if not players:
        return "None"
    
    formatted = []
    for player in players:
        if hasattr(player, 'alive') and show_status:
            status = "❤️" if player.alive else "💀"
            formatted.append(f"{status} {player.name}")
        else:
            formatted.append(f"• {player.name if hasattr(player, 'name') else str(player)}")
    
    return "\\n".join(formatted)

async def get_guild() -> Optional[discord.Guild]:
    """Get the configured guild"""
    return _guild

async def get_member_by_id(user_id: int) -> Optional[discord.Member]:
    """Get a member by their user ID"""
    if not _guild:
        return None
    return _guild.get_member(user_id)

async def get_channel_by_id(channel_id: int) -> Optional[discord.TextChannel]:
    """Get a channel by its ID"""
    if not _bot:
        return None
    return _bot.get_channel(channel_id)

async def add_player_role(user: discord.Member) -> bool:
    """Add the player role to a user"""
    if not _guild or not _config.player_role_id:
        return True  # Skip if not configured
    
    try:
        role = _guild.get_role(_config.player_role_id)
        if role and role not in user.roles:
            await user.add_roles(role, reason="Joined werewolf game")
            _logger.debug(f"Added player role to {user.display_name}")
        return True
    except discord.Forbidden:
        _logger.error(f"Missing permissions to add role to {user.display_name}")
        return False
    except Exception as e:
        _logger.error(f"Error adding role to {user.display_name}: {e}")
        return False

async def remove_player_role(user: discord.Member) -> bool:
    """Remove the player role from a user"""
    if not _guild or not _config.player_role_id:
        return True  # Skip if not configured
    
    try:
        role = _guild.get_role(_config.player_role_id)
        if role and role in user.roles:
            await user.remove_roles(role, reason="Left werewolf game")
            _logger.debug(f"Removed player role from {user.display_name}")
        return True
    except discord.Forbidden:
        _logger.error(f"Missing permissions to remove role from {user.display_name}")
        return False
    except Exception as e:
        _logger.error(f"Error removing role from {user.display_name}: {e}")
        return False

async def send_to_game_channel(content: str = "", embed: discord.Embed = None) -> bool:
    """Send a message to the configured game channel"""
    if not _config.game_channel_id:
        return False
    
    try:
        channel = await get_channel_by_id(_config.game_channel_id)
        if channel:
            # Dedupe identical messages sent very recently to avoid double-posts
            key = (channel.id, (content or "")[:200], embed.to_dict() if embed else None)
            now = datetime.utcnow()
            last = _recent_sends.get(key)
            if last and (now - last).total_seconds() < _DUPE_WINDOW_SECONDS:
                _logger.debug("Suppressed duplicate message to game channel")
                return True
            _recent_sends[key] = now
            await channel.send(content=content, embed=embed)
            return True
    except Exception as e:
        _logger.error(f"Error sending to game channel: {e}")
    
    return False


async def relay_log_message(content: str = "") -> bool:
    """Relay a log message to the configured logging channel (if set)."""
    if not _config or not getattr(_config, 'logging_channel_id', None):
        return False
    try:
        channel = await get_channel_by_id(_config.logging_channel_id)
        if channel:
            await channel.send(content)
            return True
    except Exception as e:
        _logger.error(f"Error relaying log message: {e}")
    return False


import logging

class AsyncRelayHandler(logging.Handler):
    """Logging handler that relays log messages to the configured logging channel asynchronously."""
    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            # Schedule the relay on the event loop
            try:
                asyncio.get_event_loop().create_task(relay_log_message(msg))
            except RuntimeError:
                # If no running loop, skip
                pass
        except Exception:
            try:
                self.handleError(record)
            except Exception:
                pass

async def send_to_werewolf_channel(content: str = "", embed: discord.Embed = None) -> bool:
    """Send a message to the werewolf channel"""
    if not _config.werewolf_channel_id:
        return False
    
    try:
        channel = await get_channel_by_id(_config.werewolf_channel_id)
        if channel:
            await channel.send(content=content, embed=embed)
            return True
    except Exception as e:
        _logger.error(f"Error sending to werewolf channel: {e}")
    
    return False

async def send_to_village_channel(content: str = "", embed: discord.Embed = None) -> bool:
    """Send a message to the village channel"""
    if not _config.village_channel_id:
        return False
    
    try:
        channel = await get_channel_by_id(_config.village_channel_id)
        if channel:
            await channel.send(content=content, embed=embed)
            return True
    except Exception as e:
        _logger.error(f"Error sending to village channel: {e}")
    
    return False

async def send_dm(user: discord.User, content: str = "", embed: discord.Embed = None) -> bool:
    """Send a direct message to a user"""
    try:
        await user.send(content=content, embed=embed)
        return True
    except discord.Forbidden:
        _logger.warning(f"Cannot send DM to {user.display_name} - DMs disabled")
        return False
    except Exception as e:
        _logger.error(f"Error sending DM to {user.display_name}: {e}")
        return False

def get_rate_limiter(user_id: int, cooldown_seconds: int = 5) -> bool:
    """Check if user is rate limited"""
    now = datetime.now()
    
    if user_id in _rate_limiters:
        last_use = _rate_limiters[user_id]
        if now - last_use < timedelta(seconds=cooldown_seconds):
            return False  # Rate limited
    
    _rate_limiters[user_id] = now
    return True  # Not rate limited

def cleanup_rate_limiters():
    """Clean up old rate limit entries"""
    cutoff = datetime.now() - timedelta(minutes=10)
    to_remove = [user_id for user_id, timestamp in _rate_limiters.items() if timestamp < cutoff]
    
    for user_id in to_remove:
        del _rate_limiters[user_id]

async def parse_duration(duration_str: str) -> Optional[int]:
    """Parse a duration string like '5m', '1h', '30s' into seconds"""
    duration_str = duration_str.lower().strip()
    
    if duration_str.endswith('s'):
        return int(duration_str[:-1])
    elif duration_str.endswith('m'):
        return int(duration_str[:-1]) * 60
    elif duration_str.endswith('h'):
        return int(duration_str[:-1]) * 3600
    elif duration_str.endswith('d'):
        return int(duration_str[:-1]) * 86400
    else:
        # Assume seconds if no unit
        return int(duration_str)

def format_time_remaining(seconds: int) -> str:
    """Format seconds into human readable time remaining"""
    if seconds <= 0:
        return "Time's up!"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    
    return " ".join(parts)

def chunk_message(message: str, max_length: int = 2000) -> List[str]:
    """Split a long message into chunks that fit Discord's limits"""
    if len(message) <= max_length:
        return [message]
    
    chunks = []
    current_chunk = ""
    
    for line in message.split('\\n'):
        if len(current_chunk) + len(line) + 1 > max_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
        
        if len(line) > max_length:
            # Split very long lines
            words = line.split(' ')
            for word in words:
                if len(current_chunk) + len(word) + 1 > max_length:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                        current_chunk = ""
                current_chunk += word + " "
        else:
            current_chunk += line + "\\n"
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks

async def safe_send(ctx, content: str = "", embed: discord.Embed = None):
    """Safely send a message, handling rate limits and long messages"""
    try:
        if content and len(content) > 2000:
            chunks = chunk_message(content)
            for chunk in chunks:
                await ctx.send(chunk)
        else:
            await ctx.send(content=content, embed=embed)
    except discord.HTTPException as e:
        _logger.error(f"Error sending message: {e}")
        await ctx.send("❌ An error occurred while sending the message.")

# Cleanup task
async def periodic_cleanup():
    """Periodic cleanup task"""
    while True:
        await asyncio.sleep(600)  # Run every 10 minutes
        cleanup_rate_limiters()

# Start cleanup task when bot is ready
def start_cleanup_task():
    """Start the periodic cleanup task"""
    asyncio.create_task(periodic_cleanup())

def is_owner(user_id: Union[int, str]) -> bool:
    """Check if user is the bot owner"""
    # For now, return False since we don't have owner_id in config
    # This can be configured later through environment variables
    return False

def is_admin(user_id: Union[int, str]) -> bool:
    """Check if user has admin permissions"""
    if not _guild or not _config.admin_role_id:
        return False
    
    member = _guild.get_member(int(user_id))
    if not member:
        return False
    
    admin_role = _guild.get_role(_config.admin_role_id)
    return admin_role in member.roles if admin_role else False

def has_permission(user_id: Union[int, str], level: int) -> bool:
    """Check if user has required permission level"""
    user_id = int(user_id)
    
    if level == PermissionLevel.EVERYONE:
        return True
    elif level == PermissionLevel.PLAYING:
        from src.game.state import game_session
        return user_id in game_session.players
    elif level == PermissionLevel.MODERATOR:
        return is_admin(user_id)
    elif level == PermissionLevel.ADMIN:
        return is_admin(user_id)
    elif level == PermissionLevel.OWNER:
        return is_owner(user_id)
    
    return False

# Legacy function compatibility - these are replaced by our new implementations above
# Keeping minimal versions for any remaining references

def format_player_list(players: List, show_roles: bool = False) -> str:
    """Format a list of players for display"""
    if not players:
        return "No players"
    
    lines = []
    for i, player in enumerate(players, 1):
        line = f"{i}. {player.name}"
        if show_roles and player.role:
            line += f" ({player.role})"
        if not player.alive:
            line += " 💀"
        lines.append(line)
    
    return "\n".join(lines)

def format_time_delta(delta: timedelta) -> str:
    """Format a timedelta for display"""
    total_seconds = int(delta.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def create_embed(title: str, description: str = "", color: int = 0x7289DA) -> discord.Embed:
    """Create a standard embed"""
    embed = discord.Embed(title=title, description=description, color=color)
    embed.timestamp = datetime.utcnow()
    return embed

def create_error_embed(title: str, description: str = "") -> discord.Embed:
    """Create an error embed"""
    return create_embed(title, description, color=0xFF0000)

def create_success_embed(title: str, description: str = "") -> discord.Embed:
    """Create a success embed"""
    return create_embed(title, description, color=0x00FF00)

def create_warning_embed(title: str, description: str = "") -> discord.Embed:
    """Create a warning embed"""
    return create_embed(title, description, color=0xFFFF00)

class RateLimiter:
    """Simple rate limiter for commands"""
    
    def __init__(self):
        self.cooldowns = {}
    
    def is_on_cooldown(self, user_id: int, command: str, cooldown_seconds: int) -> bool:
        """Check if user is on cooldown for a command"""
        key = f"{user_id}:{command}"
        now = datetime.now()
        
        if key in self.cooldowns:
            if now - self.cooldowns[key] < timedelta(seconds=cooldown_seconds):
                return True
        
        self.cooldowns[key] = now
        return False
    
    def get_remaining_cooldown(self, user_id: int, command: str, cooldown_seconds: int) -> float:
        """Get remaining cooldown time in seconds"""
        key = f"{user_id}:{command}"
        now = datetime.now()
        
        if key in self.cooldowns:
            elapsed = now - self.cooldowns[key]
            remaining = cooldown_seconds - elapsed.total_seconds()
            return max(0, remaining)
        
        return 0

# Global rate limiter instance
rate_limiter = RateLimiter()

def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter"""
    return rate_limiter
