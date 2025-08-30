"""
Core system initialization for Discord Werewolf Bot
"""

import os
import logging
import json
from typing import Dict, Any, List
from dataclasses import dataclass

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, will use system environment variables
    pass

@dataclass
class BotConfig:
    """Bot configuration class loaded from environment variables"""
    # Core bot settings
    token: str
    prefix: str
    owner_id: int
    
    # Server and channel settings
    werewolf_server: int
    game_channel: int
    debug_channel: int
    
    # Role names
    players_role_name: str
    admins_role_name: str
    werewolf_notify_role_name: str
    
    # Admin user IDs
    admins: List[str]
    
    # Game settings
    tokens_given: int
    token_reset: int
    ignore_threshold: int
    backup_interval: int
    
    # File paths
    notify_file: str
    stasis_file: str
    log_file: str
    
    # Other settings
    min_log_level: int
    message_language: str
    playing_message: str
    ignore_list: List[str]
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.token:
            raise ValueError("DISCORD_TOKEN is required in environment variables or .env file")
        if not self.owner_id:
            raise ValueError("OWNER_ID is required in environment variables or .env file")
        if not self.werewolf_server:
            raise ValueError("WEREWOLF_SERVER is required in environment variables or .env file")

# Global configuration instance
_config: BotConfig = None
_logger: logging.Logger = None

def initialize_config() -> BotConfig:
    """Initialize bot configuration from environment variables and .env file"""
    global _config
    
    if _config is not None:
        return _config
    
    # Helper function to parse comma-separated lists
    def parse_list(value: str) -> List[str]:
        if not value:
            return []
        return [item.strip() for item in value.split(',') if item.strip()]
    
    # Helper function to get int with fallback to config.py
    def get_int_env(env_key: str, config_key: str = None, default: int = 0) -> int:
        value = os.getenv(env_key)
        if value:
            try:
                return int(value)
            except ValueError:
                pass
        
        # Fallback to config.py if available
        if config_key:
            try:
                import config
                return int(getattr(config, config_key, default))
            except (ImportError, AttributeError, ValueError):
                pass
        
        return default
    
    # Helper function to get string with fallback to config.py
    def get_str_env(env_key: str, config_key: str = None, default: str = "") -> str:
        value = os.getenv(env_key)
        if value:
            return value
        
        # Fallback to config.py if available
        if config_key:
            try:
                import config
                return str(getattr(config, config_key, default))
            except (ImportError, AttributeError):
                pass
        
        return default
    
    # Load configuration from environment variables with config.py fallback
    token = get_str_env('DISCORD_TOKEN', 'TOKEN')
    prefix = get_str_env('BOT_PREFIX', 'BOT_PREFIX', '!')
    owner_id = get_int_env('OWNER_ID', 'OWNER_ID')
    
    werewolf_server = get_int_env('WEREWOLF_SERVER', 'WEREWOLF_SERVER')
    game_channel = get_int_env('GAME_CHANNEL', 'GAME_CHANNEL')
    debug_channel = get_int_env('DEBUG_CHANNEL', 'DEBUG_CHANNEL')
    
    players_role_name = get_str_env('PLAYERS_ROLE_NAME', 'PLAYERS_ROLE_NAME', 'Players')
    admins_role_name = get_str_env('ADMINS_ROLE_NAME', 'ADMINS_ROLE_NAME', 'Admins')
    werewolf_notify_role_name = get_str_env('WEREWOLF_NOTIFY_ROLE_NAME', 'WEREWOLF_NOTIFY_ROLE_NAME', 'Werewolf Notify')
    
    # Parse admin list from environment or config.py
    admins_env = os.getenv('ADMINS', '')
    admins = parse_list(admins_env)
    if not admins:
        try:
            import config
            config_admins = getattr(config, 'ADMINS', [])
            admins = [str(admin) for admin in config_admins]
        except (ImportError, AttributeError):
            admins = []
    
    # Parse ignore list
    ignore_list_env = os.getenv('IGNORE_LIST', '')
    ignore_list = parse_list(ignore_list_env)
    if not ignore_list:
        try:
            import config
            config_ignore = getattr(config, 'IGNORE_LIST', [])
            ignore_list = [str(user) for user in config_ignore]
        except (ImportError, AttributeError):
            ignore_list = []
    
    # Game settings
    tokens_given = get_int_env('TOKENS_GIVEN', 'TOKENS_GIVEN', 5)
    token_reset = get_int_env('TOKEN_RESET', 'TOKEN_RESET', 10)
    ignore_threshold = get_int_env('IGNORE_THRESHOLD', 'IGNORE_THRESHOLD', 7)
    backup_interval = get_int_env('BACKUP_INTERVAL', 'BACKUP_INTERVAL', 300)
    min_log_level = get_int_env('MIN_LOG_LEVEL', 'MIN_LOG_LEVEL', 1)
    
    # File paths
    notify_file = get_str_env('NOTIFY_FILE', 'NOTIFY_FILE', 'notify.txt')
    stasis_file = get_str_env('STASIS_FILE', 'STASIS_FILE', 'stasis.json')
    log_file = get_str_env('LOG_FILE', 'LOG_FILE', 'debug.txt')
    
    # Other settings
    message_language = get_str_env('MESSAGE_LANGUAGE', 'MESSAGE_LANGUAGE', 'en')
    playing_message = get_str_env('PLAYING_MESSAGE', 'PLAYING_MESSAGE', f'{prefix}info | {prefix}help | {prefix}join')
    
    # Replace {prefix} placeholder in playing message
    playing_message = playing_message.format(prefix=prefix)
    
    _config = BotConfig(
        token=token,
        prefix=prefix,
        owner_id=owner_id,
        werewolf_server=werewolf_server,
        game_channel=game_channel,
        debug_channel=debug_channel,
        players_role_name=players_role_name,
        admins_role_name=admins_role_name,
        werewolf_notify_role_name=werewolf_notify_role_name,
        admins=admins,
        tokens_given=tokens_given,
        token_reset=token_reset,
        ignore_threshold=ignore_threshold,
        backup_interval=backup_interval,
        notify_file=notify_file,
        stasis_file=stasis_file,
        log_file=log_file,
        min_log_level=min_log_level,
        message_language=message_language,
        playing_message=playing_message,
        ignore_list=ignore_list
    )
    
    return _config

def initialize_logger() -> logging.Logger:
    """Initialize logging system"""
    global _logger
    
    if _config is None:
        raise RuntimeError("Configuration must be initialized before logger")
    
    # Create logger
    _logger = logging.getLogger('werewolf_bot')
    
    # Map min_log_level to proper logging level
    log_level_map = {
        0: logging.DEBUG,
        1: logging.INFO,
        2: logging.WARNING,
        3: logging.ERROR
    }
    log_level = log_level_map.get(_config.min_log_level, logging.INFO)
    _logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in _logger.handlers[:]:
        _logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)
    
    # File handler
    file_handler = logging.FileHandler('werewolf_bot.log')
    file_handler.setFormatter(formatter)
    _logger.addHandler(file_handler)

    # If helpers.AsyncRelayHandler is available, attach it to forward logs to Discord
    try:
        from src.utils.helpers import AsyncRelayHandler
        relay_handler = AsyncRelayHandler()
        relay_handler.setFormatter(formatter)
        _logger.addHandler(relay_handler)
    except Exception:
        # Helpers may not be ready; skip relay handler
        pass
    
    # Prevent propagation to root logger
    _logger.propagate = False
    
    return _logger

def get_config() -> BotConfig:
    """Get the current bot configuration"""
    if _config is None:
        raise RuntimeError("Configuration not initialized. Call initialize_config() first.")
    return _config

def get_logger() -> logging.Logger:
    """Get the current logger instance"""
    if _logger is None:
        raise RuntimeError("Logger not initialized. Call initialize_logger() first.")
    return _logger

# Note: Don't create convenience aliases that can cause confusion
# Always use get_logger() function to get the logger instance
