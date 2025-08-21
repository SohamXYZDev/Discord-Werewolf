"""
Enhanced Game Phase Management for Discord Werewolf Bot
Comprehensive phase system with role integration and action processing
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Any
import discord
import random

from src.core import get_config, get_logger
from src.game.roles import Team, WinCondition
from src.utils.helpers import send_to_game_channel, send_dm, create_embed, create_success_embed, create_error_embed
from src.game.state import GamePhase

# Initialize configuration if not already done
try:
    config = get_config()
    logger = get_logger()
except RuntimeError:
    # Configuration not initialized yet, import the initializer
    from src.core import initialize_config, initialize_logger
    config = initialize_config()
    logger = initialize_logger()

class PhaseManager:
    """Enhanced phase manager with comprehensive game flow"""
    
    def __init__(self, bot, game_session):
        self.bot = bot
        self.game_session = game_session
        self.phase_timer_task = None
        
        # Phase durations (in seconds)
        self.day_duration = 600  # 10 minutes
        self.night_duration = 120  # 2 minutes
        self.day_warning_time = 60  # 1 minute warning
        self.night_warning_time = 30  # 30 second warning
        
        # Modified durations for Time Lord effect
        self.fast_day_duration = 300  # 5 minutes
        self.fast_night_duration = 60  # 1 minute
        
        self.time_lord_active = False
        self.action_processor = ActionProcessor(game_session)
    
    async def start_game_flow(self) -> None:
        """Start the initial game flow (first night)."""
        await self.start_night_phase()
    
    async def start_night_phase(self) -> None:
        """Start the night phase."""
        self.game_session.advance_to_night()
        
        # Send night messages to players
        await self._send_night_messages()
        
        # Start night timer
        duration = self._get_night_duration()
        if self.phase_timer_task:
            self.phase_timer_task.cancel()
        self.phase_timer_task = asyncio.create_task(self._night_timer(duration))
        
        # Announce night start
        embed = create_embed(
            title=f"🌙 Night {self.game_session.night_count}",
            description="The village sleeps as darkness falls. Those with night actions should send their commands via DM.",
            color=discord.Color.dark_blue()
        )
        await send_to_game_channel(self.bot, embed)
        
        logger.info(f"Night {self.game_session.night_count} started")
    
    async def start_day_phase(self) -> None:
        """Start the day phase."""
        # Process night actions first
        await self._process_night_actions()
        
        self.game_session.advance_to_day()
        
        # Check for game end
        game_over, winners, reason = self.game_session.check_win_conditions()
        if game_over:
            await self._end_game(winners, reason)
            return
        
        # Send day start message
        await self._send_day_start_message()
        
        # Start day timer
        duration = self._get_day_duration()
        if self.phase_timer_task:
            self.phase_timer_task.cancel()
        self.phase_timer_task = asyncio.create_task(self._day_timer(duration))
        
        logger.info(f"Day {self.game_session.day_count} started")
    
    async def end_day_phase(self) -> None:
        """End the day phase and process lynching."""
        target_id = self.game_session.get_lynch_target()
        
        if target_id:
            target = self.game_session.players[target_id]
            self.game_session.kill_player(target_id, "lynched")
            
            embed = create_embed(
                title="⚖️ Lynch Result",
                description=f"{target.mention} has been lynched by the village!",
                color=discord.Color.red()
            )
            
            # Role reveal logic
            if self._should_reveal_role():
                embed.add_field(
                    name="Role Revealed",
                    value=f"{target.name} was a **{target.role.name}**",
                    inline=False
                )
        else:
            embed = create_embed(
                title="⚖️ Lynch Result", 
                description="No one was lynched today (no majority or tie vote).",
                color=discord.Color.orange()
            )
        
        await send_to_game_channel(self.bot, embed)
        
        # Check for game end
        game_over, winners, reason = self.game_session.check_win_conditions()
        if game_over:
            await self._end_game(winners, reason)
            return
        
        # Proceed to night
        await self.start_night_phase()
    
    async def _send_night_messages(self) -> None:
        """Send role-specific messages to players for night actions."""
        for player in self.game_session.get_living_players():
            if player.role and player.can_act("night"):
                await self._send_night_action_prompt(player)
        
        # Send wolf chat coordination
        await self._send_wolf_chat()
    
    async def _send_night_action_prompt(self, player) -> None:
        """Send night action prompt to a specific player."""
        role = player.role
        embed = create_embed(
            title=f"🌙 Night {self.game_session.night_count} - Your Action",
            description=f"**Your Role:** {role.name}\\n\\n{role.description}",
            color=discord.Color.dark_blue()
        )
        
        # Add available targets
        living_players = self.game_session.get_living_players()
        targets = [f"{i+1}. {p.name}" for i, p in enumerate(living_players) if p.user_id != player.user_id]
        
        if targets:
            embed.add_field(
                name="Available Targets",
                value="\\n".join(targets),
                inline=False
            )
        
        # Add action instructions based on role
        instructions = self._get_action_instructions(role.name)
        if instructions:
            embed.add_field(
                name="Commands",
                value=instructions,
                inline=False
            )
        
        await send_dm(self.bot, player.user, embed)
    
    async def _send_wolf_chat(self) -> None:
        """Send wolf team coordination messages."""
        wolves = self.game_session.get_wolf_players()
        if len(wolves) <= 1:
            return
        
        # Create wolf list
        wolf_list = "\\n".join([f"🐺 {wolf.name}" for wolf in wolves])
        living_players = self.game_session.get_living_players()
        target_list = "\\n".join([f"{i+1}. {p.name}" for i, p in enumerate(living_players) 
                                if p.role.team != Team.WEREWOLF])
        
        embed = create_embed(
            title="🐺 Wolf Team - Night Coordination",
            description="Coordinate your kill for tonight. All wolves must agree on a target.",
            color=discord.Color.red()
        )
        
        embed.add_field(name="Wolf Team", value=wolf_list, inline=True)
        if target_list:
            embed.add_field(name="Available Targets", value=target_list, inline=True)
        
        embed.add_field(
            name="Commands",
            value="`kill <player>` - Vote to kill a player\\n`pass` - Skip the kill",
            inline=False
        )
        
        for wolf in wolves:
            await send_dm(self.bot, wolf.user, embed)
    
    async def _process_night_actions(self) -> None:
        """Process all night actions and determine results."""
        results = []
        
        # Process wolf kill first
        if self.game_session.wolf_kill_target:
            target_id = self.game_session.wolf_kill_target
            target = self.game_session.players[target_id]
            
            # Check for protection
            if target_id not in self.game_session.protections_tonight:
                self.game_session.kill_player(target_id, "killed by werewolves")
                results.append(f"💀 {target.name} was killed by werewolves.")
            else:
                results.append(f"🛡️ {target.name} was attacked but survived!")
        
        # Process investigations and other actions
        for player_id, action_data in self.game_session.night_actions.items():
            player = self.game_session.players[player_id]
            action = action_data["action"]
            target_id = action_data.get("target")
            
            if action == "protect" and target_id:
                self.game_session.protections_tonight.add(target_id)
            elif action == "see" and target_id:
                # Send investigation result to player
                result = await self.action_processor.process_investigation(player, target_id)
                await send_dm(self.bot, player.user, create_embed(
                    title="🔍 Investigation Result",
                    description=result,
                    color=discord.Color.blue()
                ))
        
        # Store results for day announcement
        self.game_session.night_results = results
    
    async def _send_day_start_message(self) -> None:
        """Send the day start message with night results."""
        embed = create_embed(
            title=f"☀️ Day {self.game_session.day_count}",
            description="The village wakes to see what transpired in the night.",
            color=discord.Color.gold()
        )
        
        if self.game_session.night_results:
            embed.add_field(
                name="Night Results",
                value="\\n".join(self.game_session.night_results),
                inline=False
            )
        else:
            embed.add_field(
                name="Night Results",
                value="It was a quiet night. No one died.",
                inline=False
            )
        
        # Add living players
        living = self.game_session.get_living_players()
        player_list = ", ".join([p.name for p in living])
        embed.add_field(
            name=f"Living Players ({len(living)})",
            value=player_list,
            inline=False
        )
        
        embed.add_field(
            name="Day Phase",
            value="Discuss and vote to lynch someone. Use `!vote <player>` to cast your vote.",
            inline=False
        )
        
        await send_to_game_channel(self.bot, embed)
    
    async def _night_timer(self, duration: int) -> None:
        """Handle night phase timing."""
        try:
            # Wait for warning time
            warning_time = duration - self.night_warning_time
            if warning_time > 0:
                await asyncio.sleep(warning_time)
                
                embed = create_embed(
                    title="⏰ Night Phase Warning",
                    description=f"{self.night_warning_time} seconds remaining in night phase!",
                    color=discord.Color.orange()
                )
                await send_to_game_channel(self.bot, embed)
                
                await asyncio.sleep(self.night_warning_time)
            else:
                await asyncio.sleep(duration)
            
            # End night phase
            await self.start_day_phase()
            
        except asyncio.CancelledError:
            pass
    
    async def _day_timer(self, duration: int) -> None:
        """Handle day phase timing."""
        try:
            # Wait for warning time
            warning_time = duration - self.day_warning_time
            if warning_time > 0:
                await asyncio.sleep(warning_time)
                
                embed = create_embed(
                    title="⏰ Day Phase Warning",
                    description=f"{self.day_warning_time} seconds remaining in day phase!",
                    color=discord.Color.orange()
                )
                await send_to_game_channel(self.bot, embed)
                
                await asyncio.sleep(self.day_warning_time)
            else:
                await asyncio.sleep(duration)
            
            # End day phase
            await self.end_day_phase()
            
        except asyncio.CancelledError:
            pass
    
    async def _end_game(self, winners: List[int], reason: str) -> None:
        """End the game and announce results."""
        self.game_session.end_game(winners, reason)
        
        if self.phase_timer_task:
            self.phase_timer_task.cancel()
        
        embed = create_embed(
            title="🎉 Game Over",
            description=reason,
            color=discord.Color.green()
        )
        
        if winners:
            winner_names = [self.game_session.players[w].name for w in winners if w in self.game_session.players]
            embed.add_field(
                name="Winners",
                value="\\n".join([f"🏆 {name}" for name in winner_names]),
                inline=False
            )
        
        # Add role reveal
        role_list = []
        for player in self.game_session.players.values():
            status = "💀" if not player.alive else "❤️"
            role_list.append(f"{status} {player.name} - **{player.role.name}**")
        
        embed.add_field(
            name="Final Roles",
            value="\\n".join(role_list),
            inline=False
        )
        
        await send_to_game_channel(self.bot, embed)
        
        # Reset game session
        self.game_session.reset()
    
    def _get_night_duration(self) -> int:
        """Get night duration considering Time Lord effect."""
        return self.fast_night_duration if self.time_lord_active else self.night_duration
    
    def _get_day_duration(self) -> int:
        """Get day duration considering Time Lord effect."""
        return self.fast_day_duration if self.time_lord_active else self.day_duration
    
    def _should_reveal_role(self) -> bool:
        """Check if roles should be revealed on death."""
        return True  # Simplified for now
    
    def _get_action_instructions(self, role_name: str) -> str:
        """Get command instructions for specific roles."""
        instructions = {
            "Seer": "`see <player>` - Learn their exact role",
            "Oracle": "`see <player>` - Learn if they are a wolf",
            "Augur": "`see <player>` - Learn their team aura",
            "Detective": "`id <player>` - Learn their exact role (during day)",
            "Guardian Angel": "`guard <player>` - Protect from death",
            "Bodyguard": "`guard <player>` - Die in their place if attacked",
            "Hunter": "`kill <player>` - Kill a player (once per game)",
            "Harlot": "`visit <player>` - Visit them for the night",
            "Shaman": "`give <player>` - Give your totem to them",
            "Matchmaker": "`choose <player1> and <player2>` - Make them lovers",
            "Werewolf": "`kill <player>` - Vote to kill as wolf team",
            "Werecrow": "`observe <player>` - See if they stayed home",
            "Wolf Shaman": "`give <player>` - Give harmful totem",
            "Sorcerer": "`observe <player>` - Detect if they are Seer/Oracle/Augur",
            "Hag": "`hex <player>` - Prevent them from acting",
            "Warlock": "`curse <player>` - Make them appear as wolf to Seer",
            "Doomsayer": "`see <player>` - Inflict random doom",
            "Serial Killer": "`kill <player>` - Kill a player",
            "Piper": "`charm <player>` - Charm up to 2 players",
            "Succubus": "`visit <player>` - Entrance them",
            "Clone": "`clone <player>` - Take their role if they die",
            "Turncoat": "`side <villagers/wolves>` - Choose your team",
            "Hot Potato": "`choose <player>` - Swap roles with them",
        }
        
        return instructions.get(role_name, "`pass` - Skip your action")

class ActionProcessor:
    """Processes role-specific actions and returns results"""
    
    def __init__(self, game_session):
        self.game_session = game_session
    
    async def process_investigation(self, investigator, target_id: int) -> str:
        """Process investigation actions (Seer, Oracle, Augur)."""
        target = self.game_session.players[target_id]
        role_name = investigator.role.name
        
        if role_name == "Seer":
            return f"You see that {target.name} is a **{target.role.name}**."
        elif role_name == "Oracle":
            is_wolf = target.role.team == Team.WEREWOLF
            return f"{target.name} is {'**a werewolf**' if is_wolf else '**not a werewolf**'}."
        elif role_name == "Augur":
            aura_colors = {
                Team.WEREWOLF: "Red",
                Team.VILLAGE: "Blue", 
                Team.NEUTRAL: "Grey"
            }
            color = aura_colors.get(target.role.team, "Unknown")
            return f"{target.name} has a **{color}** aura."
        
        return "Investigation failed."
    
    async def process_protection(self, protector, target_id: int) -> str:
        """Process protection actions (Guardian Angel, Bodyguard)."""
        target = self.game_session.players[target_id]
        self.game_session.protections_tonight.add(target_id)
        return f"You are protecting {target.name} tonight."
    
    async def process_visit(self, visitor, target_id: int) -> str:
        """Process visit actions (Harlot, Succubus)."""
        target = self.game_session.players[target_id]
        return f"You visit {target.name} tonight."
