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

load_dotenv('.env.local')

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

    async def challenge_stockfish(self, time_limit: int = 300, increment: int = 0, color: str = 'random') -> Optional[Dict[str, Any]]:
        """
        Envia um desafio para o bot Stockfish no Lichess (nível máximo).
        Args:
            time_limit: Tempo total em segundos (ex: 300 para 5 minutos).
            increment: Incremento em segundos por lance.
            color: 'white', 'black' ou 'random'.
        Returns:
            Dados do desafio criado ou None em caso de erro.
        """
        if not self.authenticated:
            return None
        try:
            url = f"{self.base_url}/challenge/stockfish"
            payload = {
                "level": 8,  # nível máximo do Stockfish
                "clock.limit": time_limit,
                "clock.increment": increment,
                "color": color,
                "rated": False  # bots não podem desafiar bots para partidas ranqueadas
            }
            async with self.session.post(url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    challenge = data.get('challenge', {})
                    # O campo 'color' pode não estar presente imediatamente
                    color = challenge.get('color', color)
                    game_id = challenge.get('id')
                    if not game_id:
                        logger.error(f"Desafio criado, mas não foi possível obter o id do desafio: {challenge}")
                        return None
                    return {
                        'game_id': game_id,
                        'opponent': 'stockfish',
                        'color': color,
                        'time_control': f"{time_limit//60}+{increment}",
                        'white_player': self.username if color == 'white' else 'stockfish',
                        'black_player': 'stockfish' if color == 'white' else self.username
                    }
                else:
                    logger.error(f"Erro ao desafiar Stockfish: status {resp.status}")
            return None
        except Exception as e:
            logger.error(f"Erro ao desafiar Stockfish: {e}")
            return None

    async def find_game(self) -> Optional[Dict[str, Any]]:
        if not self.authenticated:
            return None
        try:
            # Buscar desafios pendentes
            url = f"https://lichess.org/api/challenge"
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # Procura por desafios pendentes
                    for challenge in data.get('incoming', []):
                        # Aceita apenas desafios para Stockfish nível 8
                        challenger = challenge.get('challenger', {})
                        if challenger.get('name', '').lower().startswith('stockfish') and challenger.get('rating', 0) >= 3000:
                            challenge_id = challenge['id']
                            accept_url = f"https://lichess.org/api/challenge/{challenge_id}/accept"
                            async with self.session.post(accept_url) as accept_resp:
                                if accept_resp.status == 200:
                                    return {
                                        'game_id': challenge_id,
                                        'opponent': challenger['name'],
                                        'color': challenge['color'],
                                        'time_control': challenge['timeControl']['show'],
                                        'white_player': challenger['name'] if challenge['color'] == 'white' else self.username,
                                        'black_player': self.username if challenge['color'] == 'white' else challenger['name']
                                    }
            # Se não encontrou desafios, desafia o Stockfish
            logger.info("Nenhum desafio pendente encontrado. Desafiando Stockfish nível máximo...")
            return await self.challenge_stockfish()
        except Exception as e:
            logger.error(f"Erro ao buscar/aceitar desafios no Lichess: {e}")
            return None

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
