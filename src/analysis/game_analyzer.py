"""
Game Analyzer - Analyze completed games

Provides analysis of finished games to identify errors and improve learning.
"""

import chess
from typing import Dict
from loguru import logger
import chess.engine

class GameAnalyzer:
    """Analyzes completed chess games for performance evaluation."""
    
    def __init__(self, engine):
        self.engine = engine
    
    async def analyze_game(self, game_data: Dict) -> Dict:
        """Analyze a completed game."""
        logger.info("Analyzing completed game...")
        
        mistakes = 0
        blunders = 0
        
        board = chess.Board()
        for move_str in game_data['moves']:
            move = chess.Move.from_uci(move_str)
            board.push(move)
            
            # Evaluate position after each move
            score = await self.engine.evaluate_position(board)
            logger.debug(f"Move: {move}, Score: {score}")
            
            if score < -2.0:  # Arbitrary thresholds for errors
                mistakes += 1
                if score < -5.0:
                    blunders += 1
        
        logger.info("Game analysis complete")
        return {
            'mistakes': mistakes,
            'blunders': blunders
        }

