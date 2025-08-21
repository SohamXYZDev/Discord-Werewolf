"""
Command loader for Discord Werewolf Bot
Automatically imports and registers all commands
"""

import importlib
import os
from pathlib import Path
from src.core import get_logger

# Initialize logger
try:
    logger = get_logger()
except RuntimeError:
    # Configuration not initialized yet, will be handled by importing modules
    logger = None

def load_all_commands():
    """Load all command modules"""
    commands_dir = Path(__file__).parent
    
    # List of command modules to load
    command_modules = [
        'src.commands.basic',
        'src.commands.game', 
        'src.commands.admin',
        'src.commands.night_actions',
        'src.commands.voting',
        'src.commands.roles_info'
    ]
    
    loaded_count = 0
    
    for module_name in command_modules:
        try:
            importlib.import_module(module_name)
            logger.info(f"Loaded command module: {module_name}")
            loaded_count += 1
        except Exception as e:
            logger.error(f"Failed to load command module {module_name}: {e}")
    
    logger.info(f"Loaded {loaded_count} command modules")
    return loaded_count

def get_all_commands():
    """Get list of all registered commands"""
    from src.commands.base import get_registry
    registry = get_registry()
    return registry.get_all_commands()
