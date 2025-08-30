"""
Game phase management for Discord Werewolf Bot
Handles night/day cycles, voting, and game progression
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
from enum import Enum
import discord

from src.core import get_config, get_logger
from src.game.roles import Team, WinCondition
from src.utils.helpers import send_to_game_channel, send_dm, create_embed, create_success_embed, create_error_embed

config = get_config()
logger = get_logger()

class GamePhase(Enum):
    """Game phases"""
    LOBBY = "lobby"
    DAY = "day"
    NIGHT = "night"
    ENDED = "ended"

class VoteType(Enum):
    """Types of votes"""
    LYNCH = "lynch"
    GAMEMODE = "gamemode"

class GameManager:
    """Manages game phases, voting, and progression"""
    
    def __init__(self, bot):
        self.bot = bot
        self.phase = GamePhase.LOBBY
        self.phase_start_time = datetime.now()
        self.phase_timer_task = None
        
        # Voting system
        self.votes: Dict[int, int] = {}  # voter_id -> target_id
        self.vote_counts: Dict[int, int] = {}  # target_id -> vote_count
        self.abstain_votes: Set[int] = set()  # players who abstained
        
        # Night actions
        self.night_actions: Dict[int, Dict] = {}  # player_id -> action_data
        self.night_results: List[str] = []
        
        # Game state
        self.day_count = 0
        self.night_count = 0
        
        # Timers (in seconds)
        self.day_duration = 600  # 10 minutes
        self.night_duration = 120  # 2 minutes
        self.day_warning_time = 60  # 1 minute warning
        self.night_warning_time = 30  # 30 second warning
    
    def start_day_phase(self) -> None:
        """Start the day phase"""
        self.phase = GamePhase.DAY
        self.phase_start_time = datetime.now()
        self.day_count += 1
        
        # Clear voting data
        self.votes.clear()
        self.vote_counts.clear()
        self.abstain_votes.clear()
        
        # Start timer
        if self.phase_timer_task:
            self.phase_timer_task.cancel()
        self.phase_timer_task = asyncio.create_task(self._day_timer())
        
        logger.info(f"Day {self.day_count} started")
    
    def start_night_phase(self) -> None:
        """Start the night phase"""
        self.phase = GamePhase.NIGHT
        self.phase_start_time = datetime.now()
        self.night_count += 1
        
        # Clear night action data
        self.night_actions.clear()
        self.night_results.clear()
        
        # Start timer
        if self.phase_timer_task:
            self.phase_timer_task.cancel()
        self.phase_timer_task = asyncio.create_task(self._night_timer())
        
        logger.info(f"Night {self.night_count} started")
    
    def end_game(self, winners: List[int], win_reason: str) -> None:
        """End the game"""
        self.phase = GamePhase.ENDED
        
        if self.phase_timer_task:
            self.phase_timer_task.cancel()
        
        logger.info(f"Game ended: {win_reason}")
    
    async def _day_timer(self):
        """Day phase timer"""
        try:
            # Wait for warning time
            warning_time = self.day_duration - self.day_warning_time
            await asyncio.sleep(warning_time)
            
            # Send warning
            embed = create_embed(
                "⏰ Day Phase Warning",
                f"Day ends in **{self.day_warning_time}** seconds!\n"
                f"Make sure to cast your vote or use `{config.prefix}abstain`."
            )
            await send_to_game_channel("", embed=embed)
            
            # Wait for remaining time
            await asyncio.sleep(self.day_warning_time)
            
            # End day phase
            await self.end_day_phase()
            
        except asyncio.CancelledError:
            pass  # Timer was cancelled
    
    async def _night_timer(self):
        """Night phase timer"""
        try:
            # Wait for warning time
            warning_time = self.night_duration - self.night_warning_time
            await asyncio.sleep(warning_time)
            
            # Send warning
            embed = create_embed(
                "🌙 Night Phase Warning",
                f"Night ends in **{self.night_warning_time}** seconds!\n"
                f"Submit your night actions quickly!"
            )
            await send_to_game_channel("", embed=embed)
            
            # Wait for remaining time
            await asyncio.sleep(self.night_warning_time)
            
            # End night phase
            await self.end_night_phase()
            
        except asyncio.CancelledError:
            pass  # Timer was cancelled
    
    async def process_vote(self, voter_id: int, target_id: Optional[int], session) -> Tuple[bool, str]:
        """Process a lynch vote"""
        if self.phase != GamePhase.DAY:
            return False, "Voting is only allowed during the day phase."
        
        if voter_id not in session.players:
            return False, "You are not in the game."
        
        voter = session.players[voter_id]
        if not voter.alive:
            return False, "Dead players cannot vote."
        
        # Handle explicit abstain
        if target_id is None:
            # Remove previous vote mapping if present
            if voter_id in self.votes:
                try:
                    del self.votes[voter_id]
                except KeyError:
                    pass

            self.abstain_votes.add(voter_id)
            return True, "You have abstained from voting."
        
        # Validate target
        if target_id not in session.players:
            return False, "Invalid target."
        
        target = session.players[target_id]
        if not target.alive:
            return False, "You cannot vote for a dead player."
        
        # Remove from abstain if they were abstaining
        self.abstain_votes.discard(voter_id)

        # If player has pacifism totem/template, force abstain
        try:
            templates = getattr(voter, 'templates', set())
        except Exception:
            templates = set()

        if 'pacifism' in templates:
            # Ensure they are in abstain list and remove any vote mapping
            if voter_id in self.votes:
                try:
                    del self.votes[voter_id]
                except KeyError:
                    pass
            self.abstain_votes.add(voter_id)
            return True, "Your totem forces you to abstain from voting."

        # Record the vote (we calculate weighted counts in get_vote_status)
        self.votes[voter_id] = target_id

        # If impatience totem holder voted, attempt immediate end of day
        if 'impatience' in templates:
            try:
                asyncio.get_event_loop().create_task(self.end_day_phase())
            except Exception:
                logger.exception('Failed to trigger immediate end_day_phase from impatience totem')

        return True, f"You voted to lynch **{target.name}**."
    
    async def process_night_action(self, player_id: int, action_data: Dict, session) -> Tuple[bool, str]:
        """Process a night action"""
        if self.phase != GamePhase.NIGHT:
            return False, "Night actions can only be submitted during the night phase."
        
        if player_id not in session.players:
            return False, "You are not in the game."
        
        player = session.players[player_id]
        if not player.alive:
            return False, "Dead players cannot perform actions."
        
        role = player.role
        if not role.can_act("night"):
            return False, "Your role cannot act tonight."
        
        # Store the action
        self.night_actions[player_id] = action_data
        
        return True, "Your action has been submitted."
    
    def get_vote_status(self, session) -> Dict:
        """Get current voting status"""
        alive_players = session.get_alive_players()
        total_alive = len(alive_players)

        # Recompute weighted vote counts from self.votes taking totems into account
        weighted_counts: Dict[int, int] = {}
        explicit_voters = set()

        for voter_id, target_id in list(self.votes.items()):
            if voter_id not in session.players:
                continue
            if target_id not in session.players:
                continue

            voter = session.players[voter_id]
            templates = getattr(voter, 'templates', set())

            # Pacifism forces abstain
            if 'pacifism' in templates:
                self.abstain_votes.add(voter_id)
                continue

            weight = 2 if 'influence' in templates else 1
            weighted_counts[target_id] = weighted_counts.get(target_id, 0) + weight
            explicit_voters.add(voter_id)

        voted_count = len(explicit_voters) + len(self.abstain_votes)

        # Votes needed for majority
        majority_needed = (total_alive // 2) + 1

        sorted_votes = sorted(weighted_counts.items(), key=lambda x: x[1], reverse=True)

        return {
            "total_alive": total_alive,
            "voted_count": voted_count,
            "majority_needed": majority_needed,
            "vote_counts": weighted_counts,
            "abstain_count": len(self.abstain_votes),
            "top_voted": sorted_votes[:3] if sorted_votes else [],
            "has_majority": sorted_votes and sorted_votes[0][1] >= majority_needed
        }
    
    async def end_day_phase(self):
        """End the day phase and process lynch"""
        from src.game.state import get_session
        session = get_session()
        
        # Calculate lynch result
        vote_status = self.get_vote_status(session)
        
        embed = create_embed("☀️ Day Phase Ended", f"Day {self.day_count} has ended.")
        
        if vote_status["vote_counts"]:
            # Find player(s) with most votes
            max_votes = max(vote_status["vote_counts"].values())
            most_voted = [pid for pid, votes in vote_status["vote_counts"].items() if votes == max_votes]
            
            if len(most_voted) == 1 and max_votes >= vote_status["majority_needed"]:
                # Lynch the player
                lynched_id = most_voted[0]
                lynched_player = session.players[lynched_id]
                
                session.kill_player(lynched_id, "lynch")
                
                embed.add_field(
                    name="Lynch Result",
                    value=f"**{lynched_player.name}** was lynched by the village!\n"
                          f"They were a **{lynched_player.role.info.name}**.",
                    inline=False
                )
                
                # Check for special lynch effects (Fool, Jester, etc.)
                await self._handle_lynch_effects(lynched_player, session)
                
            elif len(most_voted) > 1:
                # Tie vote - no lynch
                tied_players = [session.players[pid].name for pid in most_voted]
                embed.add_field(
                    name="Lynch Result",
                    value=f"The vote was tied between: {', '.join(tied_players)}.\n"
                          f"No one was lynched today.",
                    inline=False
                )
            else:
                # No majority reached
                embed.add_field(
                    name="Lynch Result",
                    value="No majority was reached. No one was lynched today.",
                    inline=False
                )
        else:
            # No votes cast
            embed.add_field(
                name="Lynch Result",
                value="No votes were cast. No one was lynched today.",
                inline=False
            )
        
        # Show vote summary
        if vote_status["vote_counts"]:
            vote_summary = []
            for player_id, vote_count in sorted(vote_status["vote_counts"].items(), key=lambda x: x[1], reverse=True):
                player_name = session.players[player_id].name
                vote_summary.append(f"**{player_name}**: {vote_count} votes")
            
            if vote_status["abstain_count"] > 0:
                vote_summary.append(f"**Abstain**: {vote_status['abstain_count']} votes")
            
                embed.add_field(name="Vote Summary", value="\n".join(vote_summary), inline=False)

            await send_to_game_channel("", embed=embed)
        
        # Check win conditions
        winner_info = await self._check_win_conditions(session)
        if winner_info:
            await self._end_game_with_winners(winner_info, session)
            return
        
        # If we lynched someone in this resolution, proceed immediately to night
        if 'lynched_id' in locals():
            if self.phase_timer_task:
                self.phase_timer_task.cancel()
            await asyncio.sleep(1)
            await self._start_night_phase_messages(session)
            return

        # Desperation totem: holders who did not vote or abstain die now
        try:
            deserters = []
            for p in session.get_living_players():
                templates = getattr(p, 'templates', set())
                if 'desperation' in templates:
                    if p.user_id not in self.votes and p.user_id not in self.abstain_votes:
                        deserters.append(p)

            if deserters:
                for dp in deserters:
                    session.kill_player(dp.user_id, 'desperation_totem')
                names = ", ".join(f"**{d.name}**" for d in deserters)
                embed = create_embed("💀 Desperation Totem Activated", f"The following players failed to vote and have died: {names}")
                await send_to_game_channel("", embed=embed)
                # Proceed immediately to night after forced deaths
                if self.phase_timer_task:
                    self.phase_timer_task.cancel()
                await asyncio.sleep(1)
                await self._start_night_phase_messages(session)
                return
        except Exception:
            logger.exception('Error processing desperation totem deaths')

        # Otherwise start night phase after a brief pause
        await asyncio.sleep(3)
        await self._start_night_phase_messages(session)
    
    async def end_night_phase(self):
        """End the night phase and process actions"""
        from src.game.state import get_session
        session = get_session()
        
        # Process night actions
        results = await self._process_night_actions(session)
        
        embed = create_embed("🌙 Night Phase Ended", f"Night {self.night_count} has ended.")
        
        if results["deaths"]:
            death_messages = []
            for player_id, reason in results["deaths"].items():
                player = session.players[player_id]
                death_messages.append(f"**{player.name}** ({player.role.info.name}) {reason}")
            
            embed.add_field(name="Night Deaths", value="\n".join(death_messages), inline=False)
        else:
            embed.add_field(name="Night Result", value="No one died last night.", inline=False)
        
        if results["other_effects"]:
            embed.add_field(name="Other Effects", value="\n".join(results["other_effects"]), inline=False)

        await send_to_game_channel("", embed=embed)
        
        # Check win conditions
        winner_info = await self._check_win_conditions(session)
        if winner_info:
            await self._end_game_with_winners(winner_info, session)
            return
        
        # Start day phase immediately if anyone died or if night actions indicate immediate day
        if results["deaths"] or getattr(session, 'force_day', False):
            if self.phase_timer_task:
                self.phase_timer_task.cancel()
            await asyncio.sleep(1)
            await self._start_day_phase_messages(session)
            return

        await asyncio.sleep(3)
        await self._start_day_phase_messages(session)
    
    async def _handle_lynch_effects(self, lynched_player, session):
        """Handle special effects when certain roles are lynched"""
        role = lynched_player.role
        
        if role.info.name in ["Fool", "Jester"]:
            # Fool/Jester wins if lynched
            embed = create_success_embed(
                "🃏 Fool Victory!",
                f"**{lynched_player.name}** was a **{role.info.name}** and wins the game by being lynched!"
            )
            await send_to_game_channel(self.bot, "", embed=embed)
            
            # End game with fool victory
            await self._end_game_with_winners({
                "winners": [lynched_player.user_id],
                "reason": f"{role.info.name} lynched",
                "team": "fool"
            }, session)
    
    async def _process_night_actions(self, session) -> Dict:
        """Process all night actions and return results"""
        results = {
            "deaths": {},
            "protections": [],
            "other_effects": []
        }
        
        # Get all wolves and their targets
        wolf_targets = {}
        wolves = [p for p in session.players.values() if p.alive and p.role.info.team == Team.WOLF]
        
        for wolf in wolves:
            if wolf.user_id in self.night_actions:
                action = self.night_actions[wolf.user_id]
                if "target" in action:
                    target_id = action["target"]
                    wolf_targets[target_id] = wolf_targets.get(target_id, 0) + 1
        
        # Process protections first
        protections = {}
        for player_id, action in self.night_actions.items():
            player = session.players[player_id]
            if player.role.info.name == "Guardian Angel" and "target" in action:
                target_id = action["target"]
                protections[target_id] = player_id
        
        # Process wolf kills
        for target_id, wolf_count in wolf_targets.items():
            if target_id in protections:
                # Player was protected
                protector_id = protections[target_id]
                protector = session.players[protector_id]
                results["other_effects"].append(
                    f"**{session.players[target_id].name}** was protected by a Guardian Angel!"
                )
            else:
                # Player dies
                session.kill_player(target_id, "wolf")
                results["deaths"][target_id] = "was killed by wolves"
        
        # Process other actions (seer, detective, etc.)
        for player_id, action in self.night_actions.items():
            player = session.players[player_id]
            role = player.role
            
            if role.info.name in ["Seer", "Detective"] and "target" in action:
                # Send investigation result to player
                target_id = action["target"]
                result = role.act(target=target_id, players_dict=session.players)
                if result["success"]:
                    await send_dm(player.user, result["message"])
        
        return results
    
    async def _check_win_conditions(self, session) -> Optional[Dict]:
        """Check if any team has won"""
        alive_players = session.get_alive_players()
        
        if not alive_players:
            return {"winners": [], "reason": "No survivors", "team": "none"}
        
        # Count alive players by team
        alive_wolves = [p for p in alive_players if p.role.info.team == Team.WOLF]
        alive_village = [p for p in alive_players if p.role.info.team == Team.VILLAGE]
        alive_neutral = [p for p in alive_players if p.role.info.team == Team.NEUTRAL]
        
        # Wolf victory: wolves >= village
        if len(alive_wolves) >= len(alive_village):
            wolf_ids = [p.user_id for p in alive_wolves]
            # Add traitors to winners
            traitor_ids = [p.user_id for p in session.players.values() 
                          if p.alive and p.role.info.name == "Traitor"]
            return {
                "winners": wolf_ids + traitor_ids,
                "reason": "Wolves equal or outnumber the village",
                "team": "wolf"
            }
        
        # Village victory: no wolves left
        if not alive_wolves:
            village_ids = [p.user_id for p in alive_village]
            return {
                "winners": village_ids,
                "reason": "All wolves have been eliminated",
                "team": "village"
            }
        
        return None
    
    async def _end_game_with_winners(self, winner_info: Dict, session):
        """End the game and announce winners"""
        self.end_game(winner_info["winners"], winner_info["reason"])
        
        embed = create_success_embed("🎉 Game Over!", winner_info["reason"])
        
        if winner_info["winners"]:
            winner_names = []
            for winner_id in winner_info["winners"]:
                if winner_id in session.players:
                    player = session.players[winner_id]
                    winner_names.append(f"**{player.name}** ({player.role.info.name})")
            
            embed.add_field(name="Winners", value="\n".join(winner_names), inline=False)
        
        # Show all players and their roles
        all_players = []
        for player in session.players.values():
            status = "💀" if not player.alive else "✅"
            all_players.append(f"{status} **{player.name}** - {player.role.info.name}")
        
        embed.add_field(name="All Players", value="\n".join(all_players), inline=False)
        
        await send_to_game_channel(self.bot, "", embed=embed)
        
        # Reset game state
        session.end_game()
        
        # Update bot status
        activity = discord.Game(name=config.playing_message)
        await self.bot.change_presence(status=discord.Status.online, activity=activity)
    
    async def _start_day_phase_messages(self, session):
        """Send messages for start of day phase"""
        self.start_day_phase()
        
        alive_players = session.get_alive_players()
        
        # Ping all living players in the game channel to notify them
        mentions = " ".join(p.user.mention for p in alive_players)
        embed = create_embed(
            f"☀️ Day {self.day_count}",
            f"The sun rises on a new day. **{len(alive_players)}** players remain.\n\n"
            f"{mentions}\n\n"
            f"Discuss and vote to lynch someone you suspect of being a wolf.\n"
            f"Use `{config.prefix}vote <player>` to cast your vote.\n"
            f"Use `{config.prefix}abstain` to abstain from voting."
        )
        
        embed.add_field(
            name="Alive Players",
            value="\n".join(f"• {p.name}" for p in alive_players),
            inline=False
        )
        
        embed.add_field(
            name="Phase Timer",
            value=f"Day phase lasts **{self.day_duration // 60}** minutes.",
            inline=True
        )

        await send_to_game_channel(mentions, embed=embed)
    
    async def _start_night_phase_messages(self, session):
        """Send messages for start of night phase"""
        self.start_night_phase()
        # Ping living players in the game channel to notify them of night
        alive_players = session.get_alive_players()
        mentions = " ".join(p.user.mention for p in alive_players)

        embed = create_embed(
            f"🌙 Night {self.night_count}",
            f"Night falls and the village sleeps...\n\n"
            f"{mentions}\n\n"
            f"Players with night actions should check their DMs and submit their actions.\n"
            f"Night phase lasts **{self.night_duration // 60}** minutes."
        )

        await send_to_game_channel(mentions, embed=embed)

        # Send night action prompts to relevant players via DM
        await self._send_night_action_prompts(session)
    
    async def _send_night_action_prompts(self, session):
        """Send night action prompts to players who can act"""
        for player in session.get_alive_players():
            role = player.role
            if role.can_act("night"):
                # DM the player their prompt and ping in DM
                try:
                    await send_dm(player.user, content=f"Night {self.night_count}: you have a night action. Check below for details.")
                except Exception:
                    pass
                await self._send_role_prompt(player, session)

    async def _send_role_prompt(self, player, session):
        """Send night action prompt to a player based on their role"""
        try:
            user = session.bot.get_user(player.user_id)
            if not user:
                logger.warning(f"Could not find user {player.user_id} for role prompt")
                return
            
            role_name = player.role.name
            
            # Different prompts based on role
            if role_name == "Werewolf":
                # Send wolves a DM with their teammates and targets — no public wolfchat
                wolves = session.get_wolf_players()
                wolf_names = ", ".join(w.name for w in wolves if w.user_id != player.user_id)
                alive_nonwolves = [p for p in session.get_alive_players() if p.role.team.value != "werewolf" and p.user_id != player.user_id]
                if alive_nonwolves:
                    targets = ", ".join([p.name for p in alive_nonwolves])
                else:
                    targets = "No valid targets"

                embed = create_embed("🌙 Night Phase - Werewolf Action")
                embed.add_field(
                    name="Wolf Teammates",
                    value=wolf_names or "(You are the only known wolf)",
                    inline=False
                )
                embed.add_field(
                    name="Your Action",
                    value=f"Choose a player to eliminate:\n{targets}\n\nUse: `kill <player name>`",
                    inline=False
                )
                await user.send(embed=embed)
            
            elif role_name == "Seer":
                alive_others = [p for p in session.get_alive_players() if p.user_id != player.user_id]
                if alive_others:
                    targets = ", ".join([p.name for p in alive_others])
                    embed = create_embed("🌙 Night Phase - Seer Vision")
                    embed.add_field(
                        name="Your Action",
                        value=f"Choose a player to investigate:\n{targets}\n\nUse: `see <player name>`",
                        inline=False
                    )
                    await user.send(embed=embed)
            
            elif role_name == "Detective":
                alive_others = [p for p in session.get_alive_players() if p.user_id != player.user_id]
                if alive_others:
                    targets = ", ".join([p.name for p in alive_others])
                    embed = create_embed("🌙 Night Phase - Detective Investigation")
                    embed.add_field(
                        name="Your Action",
                        value=f"Choose a player to investigate:\n{targets}\n\nUse: `detect <player name>`",
                        inline=False
                    )
                    await user.send(embed=embed)
            
            elif role_name == "Guardian Angel":
                alive_others = [p for p in session.get_alive_players() if p.user_id != player.user_id]
                if alive_others:
                    targets = ", ".join([p.name for p in alive_others])
                    embed = create_embed("🌙 Night Phase - Guardian Protection")
                    embed.add_field(
                        name="Your Action",
                        value=f"Choose a player to protect:\n{targets}\n\nUse: `protect <player name>`",
                        inline=False
                    )
                    await user.send(embed=embed)
            
            else:
                # Roles with no night action
                embed = create_embed("🌙 Night Phase")
                embed.add_field(
                    name="No Action Required",
                    value="Your role has no night action. Wait for day phase to begin.",
                    inline=False
                )
                await user.send(embed=embed)
        
        except Exception as e:
            logger.error(f"Error sending role prompt to {player.name}: {e}")

    async def _process_night_actions(self, session):
        """Process all night actions and determine results"""
        try:
            # Get all werewolf kills
            werewolf_targets = set()
            for player_id, action in self.night_actions.items():
                if action.get("action") == "kill":
                    werewolf_targets.add(action["target_id"])
            
            # Get protections
            protected_players = set()
            for player_id, action in self.night_actions.items():
                if action.get("action") == "protect":
                    protected_players.add(action["target_id"])
            
            # Calculate actual kills (targets not protected)
            actual_kills = werewolf_targets - protected_players
            
            # Process kills
            killed_players = []
            for player_id in actual_kills:
                if player_id in session.players:
                    player = session.players[player_id]
                    if player.alive:
                        player.alive = False
                        killed_players.append(player)
            
            # Store investigation results for day phase
            self.investigation_results = []
            for player_id, action in self.night_actions.items():
                if action.get("action") in ["see", "detect"]:
                    investigator = session.players[player_id]
                    target = session.players[action["target_id"]]
                    
                    if action["action"] == "see":
                        # Seer sees role alignment
                        is_evil = target.role.team.value == "werewolf"
                        result = "evil" if is_evil else "good"
                    else:  # detect
                        # Detective sees exact role
                        result = target.role.name
                    
                    self.investigation_results.append({
                        "investigator_id": investigator.user_id,
                        "target_name": target.name,
                        "result": result,
                        "action_type": action["action"]
                    })
            
            return killed_players
        
        except Exception as e:
            logger.error(f"Error processing night actions: {e}")
            return []

    async def _handle_lynch_effects(self, lynched_player, session):
        """Handle special effects when certain roles are lynched"""
        role_name = lynched_player.role.name
        
        # Fool effect - ends game with fool win
        if role_name == "Fool":
            await session.end_game(f"💀 {lynched_player.name} was lynched! The **Fool** wins by being eliminated!")
            return
        
        # Jester effect - kills a random voter
        if role_name == "Jester":
            # Get players who voted for the jester
            voters = [pid for pid, target in self.votes.items() if target == lynched_player.user_id]
            if voters:
                import random
                victim_id = random.choice(voters)
                victim = session.players[victim_id]
                session.kill_player(victim_id, "jester_revenge")
                
                embed = create_embed("💀 Jester's Revenge!")
                embed.add_field(
                    name="Supernatural Vengeance",
                    value=f"The **Jester** {lynched_player.name} has taken revenge!\n"
                          f"**{victim.name}** has been killed by supernatural forces!",
                    inline=False
                )
                await session.channel.send(embed=embed)

    def check_win_conditions(self, session) -> Tuple[bool, str, str]:
        """Check if any team has won the game"""
        alive_players = session.get_alive_players()
        
        if not alive_players:
            return True, "draw", "No players remain alive. The game ends in a draw."
        
        # Count alive players by team
        team_counts = {"village": 0, "werewolf": 0, "independent": 0}
        
        for player in alive_players:
            team = player.role.team.value
            if team in team_counts:
                team_counts[team] += 1
        
        # Check werewolf win condition
        if team_counts["werewolf"] >= team_counts["village"]:
            return True, "werewolf", "🐺 **Werewolves Win!** They have eliminated enough villagers to take control."
        
        # Check village win condition
        if team_counts["werewolf"] == 0:
            return True, "village", "👥 **Village Wins!** All werewolves have been eliminated."
        
        # Check independent win conditions (if any special roles won)
        for player in alive_players:
            role_name = player.role.name
            if role_name == "Survivor" and team_counts["village"] + team_counts["werewolf"] <= 3:
                return True, "survivor", f"🏃 **Survivor Wins!** {player.name} has survived to the final few players."
        
        return False, "", ""
