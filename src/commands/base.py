"""
Base command system for Discord Werewolf Bot
"""

import discord
from discord.ext import commands
from typing import Optional, Callable, Any, List
import asyncio
from src.core import get_logger

# Initialize logger
try:
    logger = get_logger()
except RuntimeError:
    # Configuration not initialized yet, will be handled by importing modules
    logger = None
from src.utils.helpers import has_permission, PermissionLevel

class WerewolfCommand:
    """Represents a werewolf game command"""
    
    def __init__(self, name: str, permission_level: int, description: str, 
                 aliases: Optional[List[str]] = None, 
                 game_only: bool = False,
                 pm_only: bool = False):
        self.name = name
        self.permission_level = permission_level
        self.description = description
        self.aliases = aliases or []
        self.game_only = game_only  # Command only works during a game
        self.pm_only = pm_only     # Command only works in PMs
        self.func: Optional[Callable] = None
    
    def __call__(self, func: Callable) -> Callable:
        """Decorator to set the command function"""
        self.func = func
        return func
    
    async def execute(self, ctx: commands.Context, *args, **kwargs) -> Any:
        """Execute the command"""
        if not self.func:
            raise ValueError(f"Command {self.name} has no function set")
        
        return await self.func(ctx, *args, **kwargs)
    
    def can_execute(self, user_id: int, in_game: bool = False, is_pm: bool = False) -> tuple[bool, str]:
        """Check if user can execute this command"""
        # Check permissions
        if not has_permission(user_id, self.permission_level):
            return False, "You don't have permission to use this command."
        
        # Check game-only restriction
        if self.game_only and not in_game:
            return False, "This command can only be used during a game."
        
        # Check PM-only restriction
        if self.pm_only and not is_pm:
            return False, "This command can only be used in private messages."
        
        return True, ""

class CommandRegistry:
    """Registry for all werewolf commands"""
    
    def __init__(self):
        self.commands: dict[str, WerewolfCommand] = {}
        self.aliases: dict[str, str] = {}  # alias -> command_name
    
    def register(self, name: str, permission_level: int, description: str,
                 aliases: Optional[List[str]] = None,
                 game_only: bool = False,
                 pm_only: bool = False) -> Callable:
        """Register a new command"""
        command = WerewolfCommand(name, permission_level, description, aliases, game_only, pm_only)
        
        def decorator(func: Callable) -> Callable:
            command.func = func
            self.commands[name] = command
            
            # Register aliases
            if aliases:
                for alias in aliases:
                    self.aliases[alias] = name
            
            if logger:
                logger.debug(f"Registered command: {name}")
            return func
        
        return decorator
    
    def get_command(self, name: str) -> Optional[WerewolfCommand]:
        """Get a command by name or alias"""
        # Direct lookup
        if name in self.commands:
            return self.commands[name]
        
        # Alias lookup
        if name in self.aliases:
            return self.commands[self.aliases[name]]
        
        return None
    
    def get_all_commands(self) -> List[WerewolfCommand]:
        """Get all registered commands"""
        return list(self.commands.values())
    
    def get_commands_for_user(self, user_id: int, in_game: bool = False) -> List[WerewolfCommand]:
        """Get commands available to a specific user"""
        available = []
        for command in self.commands.values():
            can_execute, _ = command.can_execute(user_id, in_game)
            if can_execute:
                available.append(command)
        return available

# Global command registry
registry = CommandRegistry()

def command(name: str, permission_level: int = PermissionLevel.EVERYONE, 
           description: str = "", aliases: Optional[List[str]] = None,
           game_only: bool = False, pm_only: bool = False) -> Callable:
    """Decorator to register a werewolf command"""
    return registry.register(name, permission_level, description, aliases, game_only, pm_only)

def get_registry() -> CommandRegistry:
    """Get the global command registry"""
    return registry
