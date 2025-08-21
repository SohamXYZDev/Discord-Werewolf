"""
Role system for Discord Werewolf Bot
Based on comprehensive role specifications from Werewolf.md
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import random
# Temporarily removed logger import to avoid discord.py compatibility issues

class Team(Enum):
    VILLAGE = "village"
    WEREWOLF = "werewolf" 
    NEUTRAL = "neutral"

class WinCondition(Enum):
    VILLAGE_WINS = "Eliminate all werewolves"
    WEREWOLF_WINS = "Equal or outnumber the village"
    NEUTRAL_SURVIVES = "Survive to the end"
    NEUTRAL_LYNCHED = "Get lynched by the village"
    NEUTRAL_CHARM_ALL = "Charm all living players"
    NEUTRAL_ENTRANCE_ALL = "Entrance all living players"
    NEUTRAL_KILL_TARGET = "Get your target lynched"
    NEUTRAL_LAST_STANDING = "Be among the last players alive"

@dataclass
class RoleInfo:
    """Information about a werewolf role"""
    name: str
    description: str
    team: Team
    win_condition: WinCondition
    night_action: bool = False
    day_action: bool = False
    passive_ability: bool = False
    max_uses: Optional[int] = None
    
class WerewolfRole:
    """Base class for all werewolf roles"""
    
    def __init__(self, info: RoleInfo):
        self.info = info
        self.uses_remaining = info.max_uses
        
    @property
    def name(self) -> str:
        return self.info.name
        
    @property
    def description(self) -> str:
        return self.info.description
        
    @property
    def team(self) -> Team:
        return self.info.team
        
    @property
    def win_condition(self) -> WinCondition:
        return self.info.win_condition
    
    def can_act(self, phase: str) -> bool:
        """Check if role can act during this phase"""
        if phase == "night":
            return self.info.night_action and (self.uses_remaining is None or self.uses_remaining > 0)
        elif phase == "day":
            return self.info.day_action and (self.uses_remaining is None or self.uses_remaining > 0)
        return False
    
    def use_ability(self):
        """Use one charge of the ability"""
        if self.uses_remaining is not None:
            self.uses_remaining = max(0, self.uses_remaining - 1)

# Village Team Roles
class Villager(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Villager",
            description="A regular villager with no special abilities. Your strength is in discussion and voting during the day phase.",
            team=Team.VILLAGE,
            win_condition=WinCondition.VILLAGE_WINS
        ))

class Seer(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Seer",
            description="Each night, you can investigate one player to learn their exact role. Use `see <player>` in DMs.",
            team=Team.VILLAGE,
            win_condition=WinCondition.VILLAGE_WINS,
            night_action=True
        ))

class Oracle(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Oracle",
            description="Each night, you can investigate one player to learn their alignment (wolf or not wolf). Use `see <player>` in DMs.",
            team=Team.VILLAGE,
            win_condition=WinCondition.VILLAGE_WINS,
            night_action=True
        ))

class Detective(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Detective",
            description="Once per day, you can investigate a player to learn their exact role. This may reveal your identity to the wolves. Use `id <player>` during the day.",
            team=Team.VILLAGE,
            win_condition=WinCondition.VILLAGE_WINS,
            day_action=True,
            max_uses=1
        ))

class GuardianAngel(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Guardian Angel",
            description="Each night, you can protect one player from being killed. You cannot protect the same player two nights in a row. Use `guard <player>` in DMs.",
            team=Team.VILLAGE,
            win_condition=WinCondition.VILLAGE_WINS,
            night_action=True
        ))

class Bodyguard(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Bodyguard", 
            description="Each night, you can guard a player. If they are attacked, you die in their place. Use `guard <player>` in DMs.",
            team=Team.VILLAGE,
            win_condition=WinCondition.VILLAGE_WINS,
            night_action=True
        ))

class Hunter(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Hunter",
            description="Once per game at night, you can kill a player. Use `kill <player>` in DMs.",
            team=Team.VILLAGE,
            win_condition=WinCondition.VILLAGE_WINS,
            night_action=True,
            max_uses=1
        ))

class Priest(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Priest",
            description="Once per game during the day, you can bless a player for one-time death protection. You can also consecrate dead bodies. Use `bless <player>` or `consecrate <player>`.",
            team=Team.VILLAGE,
            win_condition=WinCondition.VILLAGE_WINS,
            day_action=True,
            max_uses=1
        ))

class Shaman(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Shaman",
            description="Each night, you receive a random helpful totem and must give it to a player. Use `give <player>` in DMs.",
            team=Team.VILLAGE,
            win_condition=WinCondition.VILLAGE_WINS,
            night_action=True
        ))

class Harlot(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Harlot",
            description="Each night, you can visit a player. If you visit a wolf or the wolves' victim, you die. Use `visit <player>` in DMs.",
            team=Team.VILLAGE,
            win_condition=WinCondition.VILLAGE_WINS,
            night_action=True
        ))

class Mystic(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Mystic",
            description="Each night, you automatically learn the total number of living wolves.",
            team=Team.VILLAGE,
            win_condition=WinCondition.VILLAGE_WINS,
            passive_ability=True
        ))

class Matchmaker(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Matchmaker",
            description="On the first night, you must choose two players to become lovers. Use `choose <player1> and <player2>` in DMs.",
            team=Team.VILLAGE,
            win_condition=WinCondition.VILLAGE_WINS,
            night_action=True,
            max_uses=1
        ))

class Augur(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Augur",
            description="Each night, you can investigate one player to learn their team's aura (Red for Wolf Team, Blue for Village Team, Grey for Neutral). Use `see <player>` in DMs.",
            team=Team.VILLAGE,
            win_condition=WinCondition.VILLAGE_WINS,
            night_action=True
        ))

class VillageDrunk(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Village Drunk",
            description="A regular villager, but some of your actions (if you gain them via templates) are less reliable.",
            team=Team.VILLAGE,
            win_condition=WinCondition.VILLAGE_WINS
        ))

class MadScientist(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Mad Scientist",
            description="A villager who, upon death, kills the players immediately adjacent to them in the player list.",
            team=Team.VILLAGE,
            win_condition=WinCondition.VILLAGE_WINS,
            passive_ability=True
        ))

class TimeLord(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Time Lord",
            description="A villager whose death causes the day and night timers to become much shorter for the rest of the game.",
            team=Team.VILLAGE,
            win_condition=WinCondition.VILLAGE_WINS,
            passive_ability=True
        ))

# Wolf Team Roles
class Werewolf(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Werewolf",
            description="You can communicate with other wolves at night and vote to kill a player. Use `kill <player>` in DMs.",
            team=Team.WEREWOLF,
            win_condition=WinCondition.WEREWOLF_WINS,
            night_action=True
        ))

class Werecrow(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Werecrow",
            description="A wolf who can also observe a player at night to see if they were home or visiting someone. Use `observe <player>` in DMs.",
            team=Team.WEREWOLF,
            win_condition=WinCondition.WEREWOLF_WINS,
            night_action=True
        ))

class WolfCub(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Wolf Cub",
            description="A wolf who cannot kill. If you die, the other wolves become enraged and get to kill two players the following night.",
            team=Team.WEREWOLF,
            win_condition=WinCondition.WEREWOLF_WINS,
            passive_ability=True
        ))

class Werekitten(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Werekitten",
            description="A wolf who appears as a villager to the Seer.",
            team=Team.WEREWOLF,
            win_condition=WinCondition.WEREWOLF_WINS,
            night_action=True,
            passive_ability=True
        ))

class WolfShaman(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Wolf Shaman",
            description="A wolf who receives a random harmful totem each night and must give it to a player. Use `give <player>` in DMs.",
            team=Team.WEREWOLF,
            win_condition=WinCondition.WEREWOLF_WINS,
            night_action=True
        ))

class Traitor(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Traitor",
            description="A villager who secretly wins with the wolves. If all other wolves die, you become a full Wolf.",
            team=Team.WEREWOLF,
            win_condition=WinCondition.WEREWOLF_WINS,
            passive_ability=True
        ))

class Sorcerer(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Sorcerer",
            description="A wolf-aligned Seer. You can observe a player to see if they are the real Seer, Oracle, or Augur. Use `observe <player>` in DMs.",
            team=Team.WEREWOLF,
            win_condition=WinCondition.WEREWOLF_WINS,
            night_action=True
        ))

class Minion(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Minion",
            description="A villager who knows who the wolves are and wins with them. The wolves do not know who you are.",
            team=Team.WEREWOLF,
            win_condition=WinCondition.WEREWOLF_WINS,
            passive_ability=True
        ))

class Hag(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Hag",
            description="A wolf-aligned role that can hex a player, preventing them from using their ability for a day/night cycle. Use `hex <player>` in DMs.",
            team=Team.WEREWOLF,
            win_condition=WinCondition.WEREWOLF_WINS,
            night_action=True
        ))

class Warlock(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Warlock",
            description="A wolf-aligned role that can curse a player, making them permanently appear as a wolf to the Seer. Use `curse <player>` in DMs.",
            team=Team.WEREWOLF,
            win_condition=WinCondition.WEREWOLF_WINS,
            night_action=True
        ))

class WolfMystic(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Wolf Mystic",
            description="A wolf who, each night, learns the number of powerful (non-villager) village roles.",
            team=Team.WEREWOLF,
            win_condition=WinCondition.WEREWOLF_WINS,
            passive_ability=True
        ))

class Doomsayer(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Doomsayer",
            description="A wolf who can see a player to inflict a random doom upon them (sickness, lycanthropy, or death). Use `see <player>` in DMs.",
            team=Team.WEREWOLF,
            win_condition=WinCondition.WEREWOLF_WINS,
            night_action=True
        ))

class Cultist(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Cultist",
            description="A villager who wins with the wolves, but does not know who they are.",
            team=Team.WEREWOLF,
            win_condition=WinCondition.WEREWOLF_WINS,
            passive_ability=True
        ))

# Neutral Roles
class Jester(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Jester",
            description="You win if you are lynched by the village during the day. After being lynched, you kill a random player who voted for you.",
            team=Team.NEUTRAL,
            win_condition=WinCondition.NEUTRAL_LYNCHED
        ))

class Fool(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Fool",
            description="You win if you are lynched by the village during the day. If you win, the game ends immediately.",
            team=Team.NEUTRAL,
            win_condition=WinCondition.NEUTRAL_LYNCHED
        ))

class SerialKiller(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Serial Killer",
            description="A lone killer who can kill one player each night. You win if you are one of the last players alive. Use `kill <player>` in DMs.",
            team=Team.NEUTRAL,
            win_condition=WinCondition.NEUTRAL_LAST_STANDING,
            night_action=True
        ))

class Piper(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Piper",
            description="Each night, you can charm up to two players. You win if every living player is charmed. Use `charm <player1> [and <player2>]` in DMs.",
            team=Team.NEUTRAL,
            win_condition=WinCondition.NEUTRAL_CHARM_ALL,
            night_action=True
        ))

class Succubus(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Succubus",
            description="Each night, you can visit and entrance a player. You win if every living player is entranced. Use `visit <player>` in DMs.",
            team=Team.NEUTRAL,
            win_condition=WinCondition.NEUTRAL_ENTRANCE_ALL,
            night_action=True
        ))

class Executioner(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Executioner",
            description="You are assigned a villager target at the start. You win if your target is lynched. If they die by other means, you become a Jester.",
            team=Team.NEUTRAL,
            win_condition=WinCondition.NEUTRAL_KILL_TARGET
        ))

class CrazedShaman(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Crazed Shaman",
            description="A Shaman who wins if they are alive at the end of the game, regardless of which team wins. Use `give <player>` in DMs.",
            team=Team.NEUTRAL,
            win_condition=WinCondition.NEUTRAL_SURVIVES,
            night_action=True
        ))

class Monster(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Monster",
            description="Cannot be killed by wolves at night. You win if you are alive at the end of the game, stealing the win from the main teams.",
            team=Team.NEUTRAL,
            win_condition=WinCondition.NEUTRAL_SURVIVES,
            passive_ability=True
        ))

class Amnesiac(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Amnesiac",
            description="You start as a villager but will remember a new, random role on the third night.",
            team=Team.NEUTRAL,
            win_condition=WinCondition.NEUTRAL_SURVIVES,
            passive_ability=True
        ))

class VengefulGhost(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Vengeful Ghost",
            description="After dying, you can kill one player each night from the team that killed you. You win if your target team loses. Use `kill <player>` in DMs.",
            team=Team.NEUTRAL,
            win_condition=WinCondition.NEUTRAL_LAST_STANDING,
            night_action=True
        ))

class Clone(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Clone",
            description="On the first night, you must clone a player. If that player dies, you take on their role. Use `clone <player>` in DMs.",
            team=Team.NEUTRAL,
            win_condition=WinCondition.NEUTRAL_SURVIVES,
            night_action=True,
            max_uses=1
        ))

class Lycan(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Lycan",
            description="A villager who becomes a wolf if targeted by wolves at night, instead of dying.",
            team=Team.NEUTRAL,
            win_condition=WinCondition.NEUTRAL_SURVIVES,
            passive_ability=True
        ))

class Turncoat(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Turncoat",
            description="You can side with either the villagers or wolves each night. You win if your chosen team wins. Use `side <villagers/wolves>` in DMs.",
            team=Team.NEUTRAL,
            win_condition=WinCondition.NEUTRAL_SURVIVES,
            night_action=True
        ))

class HotPotato(WerewolfRole):
    def __init__(self):
        super().__init__(RoleInfo(
            name="Hot Potato",
            description="A cursed role that cannot win. At night, you can choose a player to swap roles with. Use `choose <player>` in DMs.",
            team=Team.NEUTRAL,
            win_condition=WinCondition.NEUTRAL_SURVIVES,  # Cannot actually win
            night_action=True
        ))

# Role registry for easy access
ROLE_REGISTRY = {
    # Village Team
    "villager": Villager,
    "seer": Seer,
    "oracle": Oracle,
    "augur": Augur,
    "detective": Detective,
    "guardian_angel": GuardianAngel,
    "bodyguard": Bodyguard,
    "hunter": Hunter,
    "priest": Priest,
    "shaman": Shaman,
    "harlot": Harlot,
    "mystic": Mystic,
    "matchmaker": Matchmaker,
    "village_drunk": VillageDrunk,
    "mad_scientist": MadScientist,
    "time_lord": TimeLord,
    
    # Wolf Team
    "werewolf": Werewolf,
    "werecrow": Werecrow,
    "wolf_cub": WolfCub,
    "werekitten": Werekitten,
    "wolf_shaman": WolfShaman,
    "traitor": Traitor,
    "sorcerer": Sorcerer,
    "minion": Minion,
    "hag": Hag,
    "warlock": Warlock,
    "wolf_mystic": WolfMystic,
    "doomsayer": Doomsayer,
    "cultist": Cultist,
    
    # Neutral
    "jester": Jester,
    "fool": Fool,
    "serial_killer": SerialKiller,
    "piper": Piper,
    "succubus": Succubus,
    "executioner": Executioner,
    "crazed_shaman": CrazedShaman,
    "monster": Monster,
    "amnesiac": Amnesiac,
    "vengeful_ghost": VengefulGhost,
    "clone": Clone,
    "lycan": Lycan,
    "turncoat": Turncoat,
    "hot_potato": HotPotato
}

def get_role_by_name(name: str) -> Optional[WerewolfRole]:
    """Get a role instance by name"""
    role_class = ROLE_REGISTRY.get(name.lower())
    if role_class:
        return role_class()
    return None

def assign_roles(player_ids: List[int], gamemode: str = "default") -> Dict[int, WerewolfRole]:
    """Assign roles to players based on gamemode"""
    num_players = len(player_ids)
    
    # Default gamemode role distribution
    if gamemode == "default" or gamemode not in GAMEMODE_CONFIGS:
        return _assign_default_roles(player_ids, num_players)
    
    config = GAMEMODE_CONFIGS[gamemode]
    return _assign_roles_from_config(player_ids, config)

def _assign_default_roles(player_ids: List[int], num_players: int) -> Dict[int, WerewolfRole]:
    """Assign roles using default distribution"""
    # Calculate wolves: approximately 1/4 to 1/3 of players
    num_wolves = max(1, min(num_players // 3, (num_players + 1) // 4))
    
    roles = []
    
    # Add wolves
    for _ in range(num_wolves):
        roles.append(get_role_by_name("werewolf"))
    
    # Add special village roles based on player count
    if num_players >= 6:
        roles.append(get_role_by_name("seer"))
    if num_players >= 8:
        roles.append(get_role_by_name("guardian_angel"))
    if num_players >= 10:
        roles.append(get_role_by_name("detective"))
    if num_players >= 12:
        roles.append(get_role_by_name("hunter"))
    
    # Add neutral roles occasionally
    if num_players >= 7 and random.random() < 0.3:
        roles.append(get_role_by_name("jester"))
    
    # Fill remaining slots with villagers
    while len(roles) < num_players:
        roles.append(get_role_by_name("villager"))
    
    # Shuffle and assign
    random.shuffle(roles)
    random.shuffle(player_ids)
    
    return dict(zip(player_ids, roles))

def _assign_roles_from_config(player_ids: List[int], config: Dict) -> Dict[int, WerewolfRole]:
    """Assign roles from a specific gamemode configuration"""
    # This would be implemented based on specific gamemode configs
    # For now, fall back to default
    return _assign_default_roles(player_ids, len(player_ids))

# Gamemode configurations (can be expanded)
GAMEMODE_CONFIGS = {
    "default": {
        "min_players": 4,
        "max_players": 20,
        "description": "Standard werewolf game with basic roles"
    },
    "chaos": {
        "min_players": 6,
        "max_players": 15,
        "description": "Chaotic game with many special roles and neutrals"
    },
    "classic": {
        "min_players": 4,
        "max_players": 12,
        "description": "Simple game with just wolves, villagers, and a seer"
    }
}
