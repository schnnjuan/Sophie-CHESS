"""
Stockfish Engine - Integration with Stockfish

Controls interactions with the Stockfish engine for move generation and evaluation.
"""

import chess
import asyncio
from loguru import logger
from typing import Optional
import chess.engine
import os


class StockfishEngine:
    """Handles interaction with the Stockfish chess engine."""
    
    def __init__(self):
        self.engine_path = os.getenv('STOCKFISH_PATH', 'stockfish')
        self.engine = None
    
    async def initialize(self):
        """Initialize the Stockfish engine."""
        try:
            logger.info(f"Initializing Stockfish at path: {self.engine_path}")
            
            self.engine = await chess.engine.popen_uci(self.engine_path)
            logger.info("Stockfish engine initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Stockfish engine: {e}")
            raise
    
    async def get_best_move(self, board: chess.Board, time_limit: float = 1.0) -> Optional[chess.Move]:
        """Get the best move for a given chess position."""
        try:
            result = await self.engine.play(board, chess.engine.Limit(time=time_limit))
            return result.move
        except Exception as e:
            logger.error(f"Error getting best move: {e}")
            return None
    
    async def evaluate_position(self, board: chess.Board) -> float:
        """Evaluate the given board position."""
        try:
            info = await self.engine.analyse(board, chess.engine.Limit(depth=20))
            return info['score'].relative.score(mate_score=10000) / 100.0
        except Exception as e:
            logger.error(f"Error evaluating position: {e}")
            return 0.0
    
    async def shutdown(self):
        """Shut down the Stockfish engine."""
        if self.engine:
            await self.engine.quit()
            logger.info("Stockfish engine shut down")

