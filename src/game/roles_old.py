"""
Role system for Discord Werewolf Bot
Defines all roles, their abilities, and win conditions
"""

from enum import Enum
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
import random

class Team(Enum):
    """Teams in werewolf"""
    VILLAGE = "village"
    WOLF = "wolf"
    NEUTRAL = "neutral"

class WinCondition(Enum):
    """Win conditions for roles"""
    VILLAGE_WINS = "village_wins"      # Village eliminates all wolves
    WOLF_WINS = "wolf_wins"           # Wolves equal or outnumber village
    SURVIVOR = "survivor"             # Survive to the end
    LOVERS = "lovers"                 # Both lovers survive or die together
    CUSTOM = "custom"                 # Custom win condition

@dataclass
class RoleInfo:
    """Information about a role"""
    name: str
    team: Team
    win_condition: WinCondition
    description: str
    night_action: bool = False
    one_time_action: bool = False
    can_be_seen: bool = True  # Can be seen by seer
    wolf_seen: bool = False   # Appears as wolf to seer
    
class WerewolfRole:
    """Base class for all werewolf roles"""
    
    def __init__(self, name: str, team: Team, win_condition: WinCondition, description: str):
        self.info = RoleInfo(name, team, win_condition, description)
        self.has_acted = False
        self.alive = True
        
    def can_act(self, phase: str) -> bool:
        """Check if role can act in the given phase"""
        if not self.alive:
            return False
        if self.info.one_time_action and self.has_acted:
            return False
        return self.info.night_action and phase == "night"
    
    def get_targets(self, alive_players: List[int], exclude_self: bool = True) -> List[int]:
        """Get valid targets for this role's action"""
        targets = alive_players.copy()
        if exclude_self and hasattr(self, 'player_id'):
            targets = [p for p in targets if p != self.player_id]
        return targets
    
    def act(self, target: Optional[int] = None, **kwargs) -> Dict:
        """Perform the role's action"""
        self.has_acted = True
        return {"success": True, "message": "Action completed"}

# Village Team Roles
class Villager(WerewolfRole):
    """Basic villager role"""
    def __init__(self):
        super().__init__(
            "Villager",
            Team.VILLAGE,
            WinCondition.VILLAGE_WINS,
            "A regular villager with no special abilities. Help the village find and eliminate the wolves!"
        )

class Seer(WerewolfRole):
    """Seer can check one player each night"""
    def __init__(self):
        super().__init__(
            "Seer",
            Team.VILLAGE,
            WinCondition.VILLAGE_WINS,
            "Each night, you may investigate one player to learn their alignment (village or wolf)."
        )
        self.info.night_action = True
    
    def act(self, target: Optional[int] = None, players_dict: Dict = None, **kwargs) -> Dict:
        if not target or not players_dict:
            return {"success": False, "message": "Invalid target"}
        
        if target not in players_dict:
            return {"success": False, "message": "Player not found"}
        
        target_player = players_dict[target]
        target_role = target_player.role
        
        # Check what seer sees
        if hasattr(target_role, 'info') and target_role.info.wolf_seen:
            result = "Wolf"
        elif hasattr(target_role, 'info') and target_role.info.team == Team.WOLF:
            result = "Wolf"
        else:
            result = "Village"
        
        self.has_acted = True
        return {
            "success": True,
            "message": f"Your investigation reveals: **{target_player.name}** is aligned with the **{result}**.",
            "result": result,
            "target": target
        }

class Detective(WerewolfRole):
    """Detective can investigate players for their exact role"""
    def __init__(self):
        super().__init__(
            "Detective",
            Team.VILLAGE,
            WinCondition.VILLAGE_WINS,
            "Each night, you may investigate one player to learn their exact role."
        )
        self.info.night_action = True
    
    def act(self, target: Optional[int] = None, players_dict: Dict = None, **kwargs) -> Dict:
        if not target or not players_dict:
            return {"success": False, "message": "Invalid target"}
        
        if target not in players_dict:
            return {"success": False, "message": "Player not found"}
        
        target_player = players_dict[target]
        role_name = target_player.role.info.name
        
        self.has_acted = True
        return {
            "success": True,
            "message": f"Your investigation reveals: **{target_player.name}** is a **{role_name}**.",
            "result": role_name,
            "target": target
        }

class GuardianAngel(WerewolfRole):
    """Guardian Angel can protect one player each night"""
    def __init__(self):
        super().__init__(
            "Guardian Angel",
            Team.VILLAGE,
            WinCondition.VILLAGE_WINS,
            "Each night, you may protect one player from being killed. You cannot protect the same player on consecutive nights."
        )
        self.info.night_action = True
        self.last_protected = None
    
    def get_targets(self, alive_players: List[int], exclude_self: bool = False) -> List[int]:
        """Guardian Angel can protect anyone including themselves, but not the same person twice"""
        targets = alive_players.copy()
        if self.last_protected and self.last_protected in targets:
            targets.remove(self.last_protected)
        return targets
    
    def act(self, target: Optional[int] = None, **kwargs) -> Dict:
        if not target:
            return {"success": False, "message": "Invalid target"}
        
        self.last_protected = target
        self.has_acted = True
        return {
            "success": True,
            "message": f"You are now protecting your target tonight.",
            "protected": target
        }

# Wolf Team Roles
class Wolf(WerewolfRole):
    """Basic wolf role"""
    def __init__(self):
        super().__init__(
            "Wolf",
            Team.WOLF,
            WinCondition.WOLF_WINS,
            "You are a werewolf! Work with your pack to eliminate the village. You know who the other wolves are."
        )
        self.info.night_action = True
    
    def act(self, target: Optional[int] = None, **kwargs) -> Dict:
        if not target:
            return {"success": False, "message": "Invalid target"}
        
        self.has_acted = True
        return {
            "success": True,
            "message": f"You have chosen your target for tonight.",
            "target": target
        }

class WolfCub(WerewolfRole):
    """Wolf Cub - when killed, wolves get extra kill next night"""
    def __init__(self):
        super().__init__(
            "Wolf Cub",
            Team.WOLF,
            WinCondition.WOLF_WINS,
            "You are a young werewolf. If you die, the remaining wolves will be enraged and get an extra kill the following night."
        )
        self.info.night_action = True

class Traitor(WerewolfRole):
    """Traitor - appears as villager but wins with wolves"""
    def __init__(self):
        super().__init__(
            "Traitor",
            Team.WOLF,
            WinCondition.WOLF_WINS,
            "You appear as a villager to investigations, but you win with the wolves. You will become a wolf if all wolves die."
        )
        self.info.wolf_seen = False  # Appears as village to seer

# Neutral Roles
class Fool(WerewolfRole):
    """Fool wins if lynched"""
    def __init__(self):
        super().__init__(
            "Fool",
            Team.NEUTRAL,
            WinCondition.CUSTOM,
            "You win if you are lynched by the village during the day. Try to act suspicious without being too obvious!"
        )

class Survivor(WerewolfRole):
    """Survivor just needs to survive"""
    def __init__(self):
        super().__init__(
            "Survivor",
            Team.NEUTRAL,
            WinCondition.SURVIVOR,
            "You win if you survive until the end of the game, regardless of which team wins."
        )

class Jester(WerewolfRole):
    """Jester wins if lynched, similar to fool"""
    def __init__(self):
        super().__init__(
            "Jester",
            Team.NEUTRAL,
            WinCondition.CUSTOM,
            "You win if you are lynched by the village. If you win, you may kill one person who voted for you."
        )

# Role Registry
AVAILABLE_ROLES = {
    # Village roles
    "villager": Villager,
    "seer": Seer,
    "detective": Detective,
    "guardian_angel": GuardianAngel,
    
    # Wolf roles
    "wolf": Wolf,
    "wolf_cub": WolfCub,
    "traitor": Traitor,
    
    # Neutral roles
    "fool": Fool,
    "survivor": Survivor,
    "jester": Jester,
}

def create_role(role_name: str) -> Optional[WerewolfRole]:
    """Create a role instance by name"""
    if role_name.lower() in AVAILABLE_ROLES:
        return AVAILABLE_ROLES[role_name.lower()]()
    return None

def get_role_info(role_name: str) -> Optional[RoleInfo]:
    """Get information about a role without creating an instance"""
    role = create_role(role_name)
    return role.info if role else None

def get_all_roles() -> Dict[str, RoleInfo]:
    """Get information about all available roles"""
    return {name: create_role(name).info for name in AVAILABLE_ROLES.keys()}

# Game mode configurations
GAME_MODES = {
    "default": {
        4: {"villager": 2, "seer": 1, "wolf": 1},
        5: {"villager": 2, "seer": 1, "wolf": 2},
        6: {"villager": 3, "seer": 1, "wolf": 2},
        7: {"villager": 3, "seer": 1, "guardian_angel": 1, "wolf": 2},
        8: {"villager": 3, "seer": 1, "guardian_angel": 1, "wolf": 2, "traitor": 1},
        9: {"villager": 4, "seer": 1, "guardian_angel": 1, "wolf": 2, "traitor": 1},
        10: {"villager": 4, "seer": 1, "detective": 1, "guardian_angel": 1, "wolf": 2, "traitor": 1},
    },
    "foolish": {
        6: {"villager": 2, "seer": 1, "fool": 1, "wolf": 2},
        7: {"villager": 3, "seer": 1, "fool": 1, "wolf": 2},
        8: {"villager": 3, "seer": 1, "guardian_angel": 1, "fool": 1, "wolf": 2},
        9: {"villager": 3, "seer": 1, "guardian_angel": 1, "fool": 1, "wolf": 2, "traitor": 1},
        10: {"villager": 4, "seer": 1, "guardian_angel": 1, "fool": 1, "wolf": 2, "traitor": 1},
    },
    "random": {
        # Random mode will be handled separately
    }
}

def get_role_distribution(player_count: int, game_mode: str = "default") -> Optional[Dict[str, int]]:
    """Get role distribution for given player count and game mode"""
    if game_mode not in GAME_MODES:
        return None
    
    mode_config = GAME_MODES[game_mode]
    if player_count in mode_config:
        return mode_config[player_count].copy()
    
    # For default mode, scale up from largest available configuration
    if game_mode == "default" and player_count > max(mode_config.keys()):
        base_config = mode_config[max(mode_config.keys())].copy()
        extra_players = player_count - sum(base_config.values())
        
        # Add extra villagers for additional players
        base_config["villager"] += extra_players
        return base_config
    
    return None

def assign_roles(player_ids: List[int], game_mode: str = "default") -> Dict[int, WerewolfRole]:
    """Assign roles to players"""
    player_count = len(player_ids)
    role_dist = get_role_distribution(player_count, game_mode)
    
    if not role_dist:
        # Fallback: basic setup
        wolf_count = max(1, player_count // 4)
        village_count = player_count - wolf_count
        role_dist = {"villager": village_count - 1, "seer": 1, "wolf": wolf_count}
    
    # Create list of roles to assign
    roles_to_assign = []
    for role_name, count in role_dist.items():
        roles_to_assign.extend([role_name] * count)
    
    # Shuffle and assign
    random.shuffle(roles_to_assign)
    random.shuffle(player_ids)
    
    assignments = {}
    for i, player_id in enumerate(player_ids):
        if i < len(roles_to_assign):
            role = create_role(roles_to_assign[i])
            if role:
                role.player_id = player_id
                assignments[player_id] = role
    
    return assignments
