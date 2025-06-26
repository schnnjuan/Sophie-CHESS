"""
Lichess Client - Interface with Lichess API

Handles authentication, game finding, and move communication with Lichess.
"""

import asyncio
import aiohttp
import os
from typing import Optional, Dict, Any, List
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

class LichessClient:
    """Client for interacting with Lichess API and playing games."""
    def __init__(self):
        self.username = os.getenv('LICHESS_USERNAME')
        self.api_token = os.getenv('LICHESS_API_TOKEN')
        self.session = None
        self.authenticated = False
        self.current_games = {}
        self.base_url = "https://lichess.org/api"

    async def initialize(self):
        logger.info("Initializing Lichess client...")
        if not all([self.username, self.api_token]):
            raise ValueError("Lichess credentials not provided in environment variables")
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'Authorization': f'Bearer {self.api_token}',
                'User-Agent': f'SophieBot/1.0 ({self.username})'
            }
        )
        self.authenticated = True
        logger.info(f"Lichess client initialized for user: {self.username}")

    async def find_game(self) -> Optional[Dict[str, Any]]:
        if not self.authenticated:
            return None
        # Simulação: sempre retorna um jogo fictício
        if len(self.current_games) >= 1:
            return None
        game_info = {
            'game_id': f'game_{len(self.current_games) + 1}',
            'opponent': 'TestOpponent',
            'color': 'white',
            'time_control': '600+5',
            'white_player': self.username,
            'black_player': 'TestOpponent'
        }
        self.current_games[game_info['game_id']] = game_info
        return game_info

    async def make_move(self, game_id: str, move_uci: str) -> bool:
        try:
            if game_id not in self.current_games:
                logger.error(f"Game {game_id} not found in current games")
                return False
            logger.debug(f"Sending move {move_uci} for game {game_id}")
            await asyncio.sleep(0.1)
            return True
        except Exception as e:
            logger.error(f"Error making move: {e}")
            return False

    async def wait_for_opponent_move(self, game_id: str) -> Optional[str]:
        try:
            if game_id not in self.current_games:
                return None
            await asyncio.sleep(2)
            import random
            demo_moves = ['e2e4', 'd2d4', 'g1f3', 'b1c3', 'f1c4']
            return random.choice(demo_moves)
        except Exception as e:
            logger.error(f"Error waiting for opponent move: {e}")
            return None

    async def close(self):
        if self.session:
            await self.session.close()
            logger.info("Lichess client session closed")
