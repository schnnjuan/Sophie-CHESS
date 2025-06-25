"""
Chess.com Client - Interface with Chess.com API

Handles authentication, game finding, and move communication with Chess.com.
"""

import asyncio
import aiohttp
import json
from typing import Optional, Dict, Any, List
from loguru import logger
import os
from dotenv import load_dotenv

load_dotenv()


class ChessComClient:
    """Client for interacting with Chess.com API and playing games."""
    
    def __init__(self):
        self.username = os.getenv('CHESS_COM_USERNAME')
        self.password = os.getenv('CHESS_COM_PASSWORD')
        self.api_key = os.getenv('CHESS_COM_API_KEY')
        
        self.session = None
        self.authenticated = False
        self.current_games = {}
        
        # Chess.com API endpoints
        self.base_url = "https://api.chess.com/pub"
        self.bot_url = "https://lichess.org/api"  # Using Lichess as example
        
    async def initialize(self):
        """Initialize the Chess.com client."""
        logger.info("Initializing Chess.com client...")
        
        if not all([self.username, self.password]):
            raise ValueError("Chess.com credentials not provided in environment variables")
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': f'ChessLearningBot/1.0 ({self.username})'
            }
        )
        
        # Authenticate
        await self._authenticate()
        
        logger.info(f"Chess.com client initialized for user: {self.username}")
    
    async def _authenticate(self):
        """Authenticate with Chess.com."""
        # Note: This is a simplified authentication example
        # In reality, you'd need to implement OAuth2 or API key authentication
        # depending on Chess.com's actual bot API requirements
        
        try:
            # For demo purposes, we'll simulate authentication
            # In real implementation, you would:
            # 1. Use the Chess.com bot API endpoints
            # 2. Handle OAuth2 flow if required
            # 3. Store authentication tokens
            
            self.authenticated = True
            logger.info("✅ Authenticated with Chess.com")
            
        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")
            raise
    
    async def find_game(self) -> Optional[Dict[str, Any]]:
        """Look for available games to join."""
        if not self.authenticated:
            return None
        
        try:
            # In a real implementation, this would:
            # 1. Check for incoming challenges
            # 2. Look for open games to join
            # 3. Create challenges if allowed
            
            # For demo, we'll simulate finding a game
            # This would be replaced with actual API calls
            
            # Check if we already have ongoing games
            if len(self.current_games) >= 1:  # Limit concurrent games
                return None
            
            # Simulate finding a game (replace with real API call)
            game_info = {
                'game_id': f'game_{len(self.current_games) + 1}',
                'opponent': 'TestOpponent',
                'color': 'white',  # or 'black'
                'time_control': '600+5',
                'white_player': self.username if 'white' else 'TestOpponent',
                'black_player': 'TestOpponent' if 'white' else self.username
            }
            
            self.current_games[game_info['game_id']] = game_info
            return game_info
            
        except Exception as e:
            logger.error(f"Error finding game: {e}")
            return None
    
    async def make_move(self, game_id: str, move_uci: str) -> bool:
        """Send a move to Chess.com for the specified game."""
        try:
            if game_id not in self.current_games:
                logger.error(f"Game {game_id} not found in current games")
                return False
            
            # In real implementation, this would be an API call to Chess.com
            # For demo purposes, we'll simulate the move being sent
            
            logger.debug(f"Sending move {move_uci} for game {game_id}")
            
            # Simulate API call
            await asyncio.sleep(0.1)  # Simulate network delay
            
            return True
            
        except Exception as e:
            logger.error(f"Error making move: {e}")
            return False
    
    async def wait_for_opponent_move(self, game_id: str) -> Optional[str]:
        """Wait for opponent's move in the specified game."""
        try:
            if game_id not in self.current_games:
                return None
            
            # In real implementation, this would:
            # 1. Poll the game state API
            # 2. Use websockets for real-time updates
            # 3. Return the opponent's move when available
            
            # For demo, simulate opponent moves
            await asyncio.sleep(2)  # Simulate opponent thinking time
            
            # Generate a random legal move (in real implementation, get from API)
            import chess
            import random
            
            # This is just for demo - in reality you'd get the move from the API
            demo_moves = ['e2e4', 'd2d4', 'g1f3', 'b1c3', 'f1c4']
            return random.choice(demo_moves)
            
        except Exception as e:
            logger.error(f"Error waiting for opponent move: {e}")
            return None
    
    async def get_game_state(self, game_id: str) -> Optional[Dict[str, Any]]:
        """Get current state of a game."""
        try:
            if game_id not in self.current_games:
                return None
            
            # In real implementation, make API call to get game state
            # This would include current position, clock times, etc.
            
            return {
                'game_id': game_id,
                'status': 'playing',  # playing, finished, aborted
                'moves': [],  # List of moves in the game
                'white_time': 600,  # Remaining time in seconds
                'black_time': 600,
                'last_move': None
            }
            
        except Exception as e:
            logger.error(f"Error getting game state: {e}")
            return None
    
    async def resign_game(self, game_id: str) -> bool:
        """Resign from a game."""
        try:
            if game_id not in self.current_games:
                return False
            
            # Make API call to resign
            logger.info(f"Resigning game {game_id}")
            
            # Remove from current games
            del self.current_games[game_id]
            
            return True
            
        except Exception as e:
            logger.error(f"Error resigning game: {e}")
            return False
    
    async def get_player_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """Get player profile information."""
        try:
            # Use public Chess.com API
            url = f"{self.base_url}/player/{username}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    logger.warning(f"Failed to get profile for {username}: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting player profile: {e}")
            return None
    
    async def get_player_games(self, username: str, year: int, month: int) -> List[Dict[str, Any]]:
        """Get player's games for a specific month."""
        try:
            url = f"{self.base_url}/player/{username}/games/{year}/{month:02d}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('games', [])
                else:
                    logger.warning(f"Failed to get games for {username}: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting player games: {e}")
            return []
    
    async def close(self):
        """Close the client session."""
        if self.session:
            await self.session.close()
            logger.info("Chess.com client session closed")

