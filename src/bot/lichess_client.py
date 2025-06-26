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
                data = await resp.json()
                # Corrigido: pega os campos diretamente do root da resposta
                game_id = data.get('id')
                color = data.get('color', color)
                url = data.get('url', f'https://lichess.org/{game_id}' if game_id else None)
                if not game_id:
                    logger.error(f"Resposta completa da API ao desafiar Stockfish: {data}")
                    logger.error(f"Desafio criado, mas não foi possível obter o id do desafio!")
                    return None
                return {
                    'game_id': game_id,
                    'opponent': 'stockfish',
                    'color': color,
                    'time_control': data.get('timeControl', {}).get('show', f"{time_limit//60}+{increment}"),
                    'white_player': self.username if color == 'white' else 'stockfish',
                    'black_player': 'stockfish' if color == 'white' else self.username,
                    'url': url
                }
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
                        challenger = challenge.get('challenger', {})
                        if challenger.get('name', '').lower().startswith('stockfish') and challenger.get('rating', 0) >= 3000:
                            challenge_id = challenge['id']
                            accept_url = f"https://lichess.org/api/challenge/{challenge_id}/accept"
                            async with self.session.post(accept_url) as accept_resp:
                                if accept_resp.status == 200:
                                    return await self._wait_for_game_start(challenge_id)
            # Se não encontrou desafios, desafia um bot aleatório
            logger.info("Nenhum desafio pendente encontrado. Desafiando um bot aleatório...")
            challenge = await self.challenge_random_bot()
            if challenge and 'game_id' in challenge:
                return await self._wait_for_game_start(challenge['game_id'])
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar/aceitar desafios no Lichess: {e}")
            return None

    async def _wait_for_game_start(self, challenge_id: str, max_wait: int = 60) -> Optional[Dict[str, Any]]:
        """
        Aguarda o desafio ser aceito e retorna os dados da partida real (game_id).
        """
        import time
        url = f"{self.base_url}/challenge/{challenge_id}"
        start = time.time()
        while time.time() - start < max_wait:
            async with self.session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get('status') == 'created':
                        await asyncio.sleep(2)
                        continue
                    if data.get('status') == 'accepted' and 'game' in data:
                        game = data['game']
                        logger.info(f"Desafio aceito! Partida iniciada: {game.get('id')}")
                        return {
                            'game_id': game.get('id'),
                            'opponent': game.get('opponent', {}).get('username', 'unknown'),
                            'color': game.get('color'),
                            'time_control': game.get('timeControl', {}).get('show', ''),
                            'white_player': game.get('white', {}).get('username', ''),
                            'black_player': game.get('black', {}).get('username', ''),
                            'url': f"https://lichess.org/{game.get('id')}"
                        }
            await asyncio.sleep(2)
        logger.error(f"Timeout esperando início da partida para o desafio {challenge_id}")
        return None

    async def make_move(self, game_id: str, move_uci: str) -> bool:
        """
        Envia um lance real para a API do Lichess.
        """
        try:
            url = f"{self.base_url}/board/game/{game_id}/move/{move_uci}"
            async with self.session.post(url) as resp:
                if resp.status == 200:
                    logger.info(f"Lance {move_uci} enviado com sucesso para o jogo {game_id}")
                    return True
                else:
                    logger.error(f"Erro ao enviar lance {move_uci} para o jogo {game_id}: status {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"Error making move: {e}")
            return False

    async def wait_for_opponent_move(self, game_id: str, last_move: Optional[str] = None, max_wait: int = 60) -> Optional[str]:
        """
        Aguarda o próximo lance do oponente consultando o estado do jogo via API.
        Retorna o novo lance do oponente (UCI) ou None se não houver novo lance após max_wait segundos.
        """
        try:
            url = f"{self.base_url}/board/game/stream/{game_id}"
            timeout = 0
            while timeout < max_wait:
                async with self.session.get(url) as resp:
                    if resp.status == 200:
                        async for line in resp.content:
                            if not line:
                                continue
                            try:
                                event = line.decode().strip()
                                if not event or not event.startswith('{'):
                                    continue
                                import json
                                data = json.loads(event)
                                moves = data.get('state', {}).get('moves', '')
                                moves_list = moves.split() if moves else []
                                if moves_list:
                                    if not last_move or (last_move and moves_list[-1] != last_move):
                                        return moves_list[-1]
                            except Exception:
                                continue
                await asyncio.sleep(2)
                timeout += 2
            logger.warning(f"Timeout esperando lance do oponente no jogo {game_id}")
            return None
        except Exception as e:
            logger.error(f"Error waiting for opponent move: {e}")
            return None

    async def close(self):
        if self.session:
            await self.session.close()
            logger.info("Lichess client session closed")

    async def challenge_bot(self, bot_username: str, time_limit: int = 300, increment: int = 0, color: str = 'random') -> Optional[Dict[str, Any]]:
        """
        Envia um desafio para qualquer bot do Lichess.
        """
        if not self.authenticated:
            return None
        try:
            url = f"{self.base_url}/challenge/{bot_username}"
            payload = {
                "clock.limit": time_limit,
                "clock.increment": increment,
                "color": color,
                "rated": False
            }
            async with self.session.post(url, json=payload) as resp:
                data = await resp.json()
                game_id = data.get('id')
                color = data.get('color', color)
                if not game_id:
                    logger.error(f"Resposta completa da API ao desafiar {bot_username}: {data}")
                    logger.error(f"Desafio criado, mas não foi possível obter o id do desafio!")
                    return None
                return {
                    'game_id': game_id,
                    'opponent': bot_username,
                    'color': color,
                    'time_control': data.get('timeControl', {}).get('show', f"{time_limit//60}+{increment}"),
                    'white_player': self.username if color == 'white' else bot_username,
                    'black_player': bot_username if color == 'white' else self.username
                }
        except Exception as e:
            logger.error(f"Erro ao desafiar {bot_username}: {e}")
            return None

    async def challenge_random_bot(self, bot_list=None, time_limit: int = 300, increment: int = 0, color: str = 'random') -> Optional[Dict[str, Any]]:
        """
        Desafia automaticamente um bot aleatório de uma lista.
        """
        import random
        if bot_list is None:
            bot_list = [
                'FairyStockfish', 'LeelaChess', 'Maia1', 'Maia5', 'Maia9',
                'chessbot', 'ArasanBot', 'KomodoBot', 'Shredderbot', 'LaserBot'
            ]
        bot_username = random.choice(bot_list)
        logger.info(f"Desafiando o bot aleatório: {bot_username}")
        return await self.challenge_bot(bot_username, time_limit, increment, color)
