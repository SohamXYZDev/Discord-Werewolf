"""
Game state management for Discord Werewolf Bot
"""

import discord
from datetime import datetime, timedelta
from collections import OrderedDict
from typing import Dict, List, Optional, Tuple, Any, Set
import json
import asyncio
import random
from enum import Enum

from src.core import get_config, get_logger
from src.utils.helpers import create_embed
from src.game.roles import ROLE_REGISTRY, get_role_by_name, Team, WinCondition

# Note: config and logger will be imported when needed to avoid circular imports
try:
    config = get_config()
    logger = get_logger()
except RuntimeError:
    config = None
    logger = None
class GamePhase(Enum):
    """Game phases"""
    LOBBY = "lobby"
    DAY = "day" 
    NIGHT = "night"
    ENDED = "ended"

class Player:
    """Represents a player in the game"""
    
    def __init__(self, user_id: int, user: discord.Member):
        self.user_id = user_id
        self.user = user
        self.alive = True
        self.role = None  # Will be set to a WerewolfRole instance
        self.vote_target = None  # Current lynch vote target
        self.night_action = None  # Current night action
        self.night_action_target = None  # Target of night action
        self.protected = False  # Protected from death this night
        self.templates = set()  # Applied templates (cursed, blessed, etc.)
        self.stasis_count = 0  # Penalty for leaving games
        
    def __repr__(self):
        role_name = self.role.info.name if self.role else "No Role"
        return f"Player({self.user.display_name}, {role_name}, alive={self.alive})"
    
    @property
    def name(self) -> str:
        return self.user.display_name
    
    @property
    def mention(self) -> str:
        return self.user.mention
    
    def can_vote(self) -> bool:
        """Check if player can vote (alive and not restricted)"""
        # 'blinding' totem makes the player unable to vote; some code uses 'injured' alias
        blocked = False
        try:
            blocked = ('injured' in self.templates) or ('blinding' in self.templates)
        except Exception:
            blocked = False
        return self.alive and not blocked
    
    def can_act(self, phase: str) -> bool:
        """Check if player can perform their role action"""
        if not self.alive or not self.role:
            return False
        # If the player is silenced by a totem/template, they cannot act
        try:
            if 'silence' in self.templates:
                return False
        except Exception:
            pass
        return self.role.can_act(phase)

class GameSession:
    """Manages the current game session state"""
    
    def __init__(self):
        # Game state
        self.playing = False
        self.phase = GamePhase.LOBBY
        self.players: Dict[int, Player] = OrderedDict()
        self.spectators: Set[int] = set()
        
        # Phase timing
        self.phase_start_time = None
        self.night_start = None
        self.day_start = None
        self.night_elapsed = timedelta(0)
        self.day_elapsed = timedelta(0)
        self.first_join = None
        
        # Game progression
        self.day_count = 0
        self.night_count = 0
        
        # Voting system
        self.votes: Dict[int, int] = {}  # voter_id -> target_id
        self.vote_counts: Dict[int, int] = {}  # target_id -> vote_count
        self.abstain_votes: Set[int] = set()  # players who abstained
        
    # Night actions
    self.night_actions: Dict[int, Dict[str, Any]] = {}  # player_id -> action_data
    self.night_results: List[str] = []

    # Game configuration
    self.gamemode = "default"
    self.gamemode_votes: Dict[str, Set[int]] = {}  # gamemode -> voter_ids

    # Lobby start votes
    self.start_votes: Set[int] = set()

    # Kill queue and protection
    self.kills_tonight: Set[int] = set()  # Players to be killed
    self.protections_tonight: Set[int] = set()  # Players protected

    # Wolf team coordination
    self.wolf_kill_votes: Dict[int, int] = {}  # wolf_id -> target_id
    self.wolf_kill_target = None

    # Win tracking
    self.winners: List[int] = []
    self.win_reason = ""
    # Totem / global flags
    self.wolves_sick = False  # set by pestilence totem to block wolf kills next night
    
    # Player Management Methods
    
    def add_player(self, user: discord.Member) -> bool:
        """Add a player to the game. Returns True if successful."""
        if self.playing:
            return False
        
        if user.id in self.players:
            return False
        
        player = Player(user.id, user)
        self.players[user.id] = player
        
        if self.first_join is None:
            self.first_join = datetime.now()
        
        if logger:
            logger.info(f"Player {user.display_name} ({user.id}) joined the game")
        return True
    
    def remove_player(self, user_id: int) -> bool:
        """Remove a player from the game. Returns True if successful."""
        if user_id not in self.players:
            return False
        
        player = self.players[user_id]
        
        if self.playing:
            # If game is active, kill the player instead of removing
            self.kill_player(user_id, "quit")
            player.stasis_count += 1  # Penalty for leaving during game
        else:
            # Remove from lobby
            del self.players[user_id]
        
        logger.info(f"Player {player.name} ({user_id}) left the game")
        return True
    
    def kill_player(self, user_id: int, reason: str = "killed") -> bool:
        """Kill a player in the game."""
        if user_id not in self.players:
            return False
        
        player = self.players[user_id]
        if not player.alive:
            return False
        
        player.alive = False
        self.spectators.add(user_id)
        
        logger.info(f"Player {player.name} was {reason}")
        return True
    
    def get_living_players(self) -> List[Player]:
        """Get all living players."""
        return [p for p in self.players.values() if p.alive]
    
    def get_dead_players(self) -> List[Player]:
        """Get all dead players."""
        return [p for p in self.players.values() if not p.alive]
    
    def get_players_by_team(self, team: Team) -> List[Player]:
        """Get all living players of a specific team."""
        return [p for p in self.get_living_players() 
                if p.role and p.role.team == team]
    
    def get_wolf_players(self) -> List[Player]:
        """Get all living werewolf team players."""
        return self.get_players_by_team(Team.WEREWOLF)
    
    def get_village_players(self) -> List[Player]:
        """Get all living village team players."""
        return self.get_players_by_team(Team.VILLAGE)
    
    def get_neutral_players(self) -> List[Player]:
        """Get all living neutral players."""
        return self.get_players_by_team(Team.NEUTRAL)
    
    # Game State Methods
    
    def can_start_game(self) -> Tuple[bool, str]:
        """Check if the game can be started. Returns (can_start, reason)."""
        if self.playing:
            return False, "Game is already in progress"
        
        if len(self.players) < 4:
            return False, f"Need at least 4 players to start (have {len(self.players)})"
        
        if len(self.players) > 24:
            return False, f"Too many players (maximum 24, have {len(self.players)})"
        
        return True, "Game can be started"
    
    def start_game(self, gamemode: str = None) -> bool:
        """Start the game with role assignment."""
        can_start, reason = self.can_start_game()
        if not can_start:
            logger.warning(f"Cannot start game: {reason}")
            return False
        
        # Set gamemode
        if gamemode:
            self.gamemode = gamemode
        
        # Assign roles
        self.assign_roles()
        
        # Initialize game state
        self.playing = True
        self.phase = GamePhase.NIGHT
        self.phase_start_time = datetime.now()
        self.night_count = 1
        
        logger.info(f"Game started with {len(self.players)} players using {self.gamemode} gamemode")
        return True
    
    def end_game(self, winners: List[int], reason: str) -> None:
        """End the game."""
        self.playing = False
        self.phase = GamePhase.ENDED
        self.winners = winners
        self.win_reason = reason
        
        logger.info(f"Game ended: {reason}")
    
    def assign_roles(self) -> None:
        """Assign roles to all players based on gamemode."""
        from src.game.roles import assign_roles
        
        player_ids = list(self.players.keys())
        role_assignments = assign_roles(player_ids, self.gamemode)
        
        for player_id, role in role_assignments.items():
            if player_id in self.players:
                self.players[player_id].role = role
        
        logger.info(f"Roles assigned to {len(role_assignments)} players")
    
    # Phase Management
    
    def advance_to_day(self) -> None:
        """Advance the game to day phase."""
        self.phase = GamePhase.DAY
        self.phase_start_time = datetime.now()
        self.day_count += 1
        
        # Clear voting data
        self.votes.clear()
        self.vote_counts.clear()
        self.abstain_votes.clear()
        
        logger.info(f"Advanced to Day {self.day_count}")
    
    def advance_to_night(self) -> None:
        """Advance the game to night phase."""
        self.phase = GamePhase.NIGHT
        self.phase_start_time = datetime.now()
        self.night_count += 1
        
        # Clear night action data
        self.night_actions.clear()
        self.night_results.clear()
        self.kills_tonight.clear()
        self.protections_tonight.clear()
        self.wolf_kill_votes.clear()
        self.wolf_kill_target = None
        
        logger.info(f"Advanced to Night {self.night_count}")
    
    # Voting System
    
    def cast_vote(self, voter_id: int, target_id: int) -> bool:
        """Cast a lynch vote. Returns True if successful."""
        if self.phase != GamePhase.DAY:
            return False
        
        if voter_id not in self.players or target_id not in self.players:
            return False
        
        voter = self.players[voter_id]
        target = self.players[target_id]
        
        if not voter.can_vote() or not target.alive:
            return False
        
        # Remove previous vote if exists
        if voter_id in self.votes:
            old_target = self.votes[voter_id]
            self.vote_counts[old_target] -= 1
            if self.vote_counts[old_target] <= 0:
                del self.vote_counts[old_target]
        
        # Add new vote
        self.votes[voter_id] = target_id
        self.vote_counts[target_id] = self.vote_counts.get(target_id, 0) + 1
        voter.vote_target = target_id
        
        # Remove from abstain if was abstaining
        self.abstain_votes.discard(voter_id)
        
        logger.info(f"{voter.name} voted for {target.name}")
        return True
    
    def retract_vote(self, voter_id: int) -> bool:
        """Retract a vote. Returns True if successful."""
        if voter_id not in self.votes:
            return False
        
        target_id = self.votes[voter_id]
        del self.votes[voter_id]
        
        self.vote_counts[target_id] -= 1
        if self.vote_counts[target_id] <= 0:
            del self.vote_counts[target_id]
        
        self.players[voter_id].vote_target = None
        self.abstain_votes.discard(voter_id)
        
        logger.info(f"{self.players[voter_id].name} retracted their vote")
        return True
    
    def abstain_vote(self, voter_id: int) -> bool:
        """Abstain from voting. Returns True if successful."""
        if self.phase != GamePhase.DAY or self.day_count <= 1:  # Can't abstain on day 1
            return False
        
        if voter_id not in self.players:
            return False
        
        voter = self.players[voter_id]
        if not voter.can_vote():
            return False
        
        # Remove any existing vote
        if voter_id in self.votes:
            self.retract_vote(voter_id)
        
        # Add to abstain votes
        self.abstain_votes.add(voter_id)
        
        logger.info(f"{voter.name} abstained from voting")
        return True
    
    def get_lynch_target(self) -> Optional[int]:
        """Get the player with the most votes for lynching."""
        if not self.vote_counts:
            return None
        
        max_votes = max(self.vote_counts.values())
        candidates = [player_id for player_id, votes in self.vote_counts.items() 
                     if votes == max_votes]
        
        if len(candidates) == 1:
            return candidates[0]
        
        # Tie - no lynch
        return None
    
    # Night Action System
    
    def submit_night_action(self, player_id: int, action_type: str, 
                          target_id: Optional[int] = None, **kwargs) -> bool:
        """Submit a night action. Returns True if successful."""
        if self.phase != GamePhase.NIGHT:
            return False
        
        if player_id not in self.players:
            return False
        
        player = self.players[player_id]
        if not player.can_act("night"):
            return False
        
        # Store the action
        self.night_actions[player_id] = {
            "action": action_type,
            "target": target_id,
            "timestamp": datetime.now(),
            **kwargs
        }
        
        player.night_action = action_type
        player.night_action_target = target_id
        
        logger.info(f"{player.name} submitted night action: {action_type}")
        # If all players who can act have submitted their actions, signal to advance to day
        remaining = [p for p in self.get_living_players() if p.role and p.role.can_act("night") and p.user_id not in self.night_actions]
        if not remaining:
            # Attempt to cancel any running night timer and trigger immediate day via game manager if present
            try:
                if hasattr(self, 'game_manager') and getattr(self.game_manager, 'phase_timer_task', None):
                    self.game_manager.phase_timer_task.cancel()
                    # Schedule the end of night on the loop
                    asyncio.get_event_loop().create_task(self.game_manager.end_night_phase())
            except Exception:
                logger.exception("Failed to trigger immediate day after all night actions submitted")

        return True
    
    def wolf_vote_kill(self, wolf_id: int, target_id: int) -> bool:
        """Wolf votes to kill a target. Returns True if successful."""
        if wolf_id not in self.players or target_id not in self.players:
            return False
        
        wolf = self.players[wolf_id]
        target = self.players[target_id]
        
        if not wolf.role or wolf.role.team != Team.WEREWOLF:
            return False
        
        if not target.alive:
            return False
        
        self.wolf_kill_votes[wolf_id] = target_id
        
        # Check if wolves have consensus
        wolves = self.get_wolf_players()
        if len(self.wolf_kill_votes) == len(wolves):
            # All wolves voted, determine target
            vote_counts = {}
            for target in self.wolf_kill_votes.values():
                vote_counts[target] = vote_counts.get(target, 0) + 1
            
            if vote_counts:
                max_votes = max(vote_counts.values())
                candidates = [t for t, v in vote_counts.items() if v == max_votes]
                
                if len(candidates) == 1:
                    self.wolf_kill_target = candidates[0]
                else:
                    # Tie - random choice
                    self.wolf_kill_target = random.choice(candidates)
        
        logger.info(f"Wolf {wolf.name} voted to kill {target.name}")
        return True
    
    # Win Condition Checking
    
    def check_win_conditions(self) -> Tuple[bool, List[int], str]:
        """Check if any team has won. Returns (game_over, winners, reason)."""
        living_players = self.get_living_players()
        
        if not living_players:
            return True, [], "No players left alive"
        
        wolves = self.get_wolf_players()
        village = self.get_village_players()
        
        # Village wins if no wolves left
        if not wolves:
            village_ids = [p.user_id for p in village]
            return True, village_ids, "Village eliminated all werewolves"
        
        # Wolves win if they equal or outnumber non-wolves
        non_wolves = [p for p in living_players if p.role.team != Team.WEREWOLF]
        if len(wolves) >= len(non_wolves):
            wolf_ids = [p.user_id for p in wolves]
            return True, wolf_ids, "Werewolves achieved parity"
        
        # Check neutral individual wins (simplified for now)
        # This would be expanded for specific neutral roles
        
        return False, [], ""
    
    # Utility Methods
    
    def get_player_by_name(self, name: str) -> Optional[Player]:
        """Get a player by their display name or partial name match."""
        name_lower = name.lower()
        
        # Exact match first
        for player in self.players.values():
            if player.name.lower() == name_lower:
                return player
        
        # Partial match
        matches = []
        for player in self.players.values():
            if name_lower in player.name.lower():
                matches.append(player)
        
        if len(matches) == 1:
            return matches[0]
        
        return None

    def get_player_by_id(self, user_id: int) -> Optional[Player]:
        """Get a player object by their user ID."""
        return self.players.get(int(user_id))

    def get_player_by_nick(self, nick: str) -> Optional[Player]:
        """Alias for get_player_by_name - some command code uses 'nick' terminology."""
        return self.get_player_by_name(nick)
    
    def reset(self) -> None:
        """Reset the game session to initial state."""
        self.__init__()
        logger.info("Game session reset")

# Global game session instance
game_session = GameSession()

class PersistentData:
    """Manages persistent data like stasis and notifications"""
    
    def __init__(self):
        self.stasis: Dict[int, int] = {}
        self.notify_list: List[int] = []
        self.load_data()
    
    def load_data(self):
        """Load persistent data from files"""
        # Load stasis data
        try:
            with open(config.stasis_file, 'r') as f:
                data = json.load(f)
                self.stasis = {int(k): v for k, v in data.items()}
        except (FileNotFoundError, json.JSONDecodeError):
            self.stasis = {}
            
        # Load notify list
        try:
            with open(config.notify_file, 'r') as f:
                content = f.read().strip()
                if content:
                    self.notify_list = [int(user_id) for user_id in content.split(',') if user_id.strip()]
                else:
                    self.notify_list = []
        except FileNotFoundError:
            self.notify_list = []
            # Create empty file
            with open(config.notify_file, 'w') as f:
                pass
    
    def save_stasis(self):
        """Save stasis data to file"""
        try:
            with open(config.stasis_file, 'w') as f:
                json.dump(self.stasis, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save stasis data: {e}")
    
    def save_notify_list(self):
        """Save notify list to file"""
        try:
            with open(config.notify_file, 'w') as f:
                f.write(','.join(str(user_id) for user_id in self.notify_list))
        except Exception as e:
            logger.error(f"Failed to save notify list: {e}")
    
    def add_stasis(self, user_id: int, amount: int = 1):
        """Add stasis to a user"""
        if user_id in self.stasis:
            self.stasis[user_id] += amount
        else:
            self.stasis[user_id] = amount
        self.save_stasis()
    
    def remove_stasis(self, user_id: int, amount: int = 1) -> int:
        """Remove stasis from a user. Returns remaining stasis."""
        if user_id not in self.stasis:
            return 0
            
        self.stasis[user_id] = max(0, self.stasis[user_id] - amount)
        if self.stasis[user_id] == 0:
            del self.stasis[user_id]
        
        self.save_stasis()
        return self.stasis.get(user_id, 0)
    
    def get_stasis(self, user_id: int) -> int:
        """Get stasis count for a user"""
        return self.stasis.get(user_id, 0)
    
    def add_to_notify(self, user_id: int) -> bool:
        """Add user to notify list. Returns True if added, False if already in list."""
        if user_id not in self.notify_list:
            self.notify_list.append(user_id)
            self.save_notify_list()
            return True
        return False
    
    def remove_from_notify(self, user_id: int) -> bool:
        """Remove user from notify list. Returns True if removed, False if not in list."""
        if user_id in self.notify_list:
            self.notify_list.remove(user_id)
            self.save_notify_list()
            return True
        return False

# Global instances
session = GameSession()
persistent_data = PersistentData()

def get_session() -> GameSession:
    """Get the global game session"""
    return session

def get_persistent_data() -> PersistentData:
    """Get the global persistent data manager"""
    return persistent_data
