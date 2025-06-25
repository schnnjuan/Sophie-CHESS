"""
Chess Bot - Core implementation

Main chess bot that handles game logic, move generation, and learning.
"""

import asyncio
import chess
import chess.pgn
from typing import Optional, Dict, Any
from loguru import logger
from datetime import datetime

from ..engine.stockfish_engine import StockfishEngine
from ..learning.model_manager import ModelManager
from ..database.db_manager import DatabaseManager
from ..analysis.game_analyzer import GameAnalyzer
from .chess_com_client import ChessComClient


class ChessBot:
    """Main chess bot class that handles gameplay and learning."""
    
    def __init__(self, db_manager: DatabaseManager, model_manager: ModelManager, 
                 engine: StockfishEngine, analyzer: GameAnalyzer):
        self.db_manager = db_manager
        self.model_manager = model_manager
        self.engine = engine
        self.analyzer = analyzer
        self.client = None
        
        self.current_game = None
        self.games_played = 0
        self.wins = 0
        self.losses = 0
        self.draws = 0
        
    async def initialize(self):
        """Initialize the chess bot."""
        logger.info("Initializing Chess Bot...")
        
        # Initialize Chess.com client
        self.client = ChessComClient()
        await self.client.initialize()
        
        # Load bot statistics
        await self._load_statistics()
        
        logger.info(f"Bot initialized - Games: {self.games_played}, Win rate: {self.get_win_rate():.1%}")
    
    async def start_playing(self):
        """Start the main game loop."""
        logger.info("🎯 Starting to play chess...")
        
        while True:
            try:
                # Look for a game
                game_info = await self.client.find_game()
                if game_info:
                    await self.play_game(game_info)
                else:
                    # Wait before looking for another game
                    await asyncio.sleep(10)
                    
            except Exception as e:
                logger.error(f"Error in main game loop: {e}")
                await asyncio.sleep(30)
    
    async def play_game(self, game_info: Dict[str, Any]):
        """Play a single game."""
        game_id = game_info['game_id']
        opponent = game_info['opponent']
        color = game_info['color']  # 'white' or 'black'
        
        logger.info(f"🎮 Starting game {game_id} vs {opponent} as {color}")
        
        board = chess.Board()
        moves_history = []
        move_times = []
        evaluations = []
        
        game_start_time = datetime.now()
        
        try:
            while not board.is_game_over():
                # Get current position
                fen = board.fen()
                
                if (color == 'white' and board.turn == chess.WHITE) or \
                   (color == 'black' and board.turn == chess.BLACK):
                    # Our turn
                    move_start_time = datetime.now()
                    
                    # Get move from our model
                    move = await self._get_best_move(board)
                    
                    move_time = (datetime.now() - move_start_time).total_seconds()
                    move_times.append(move_time)
                    
                    # Make the move
                    board.push(move)
                    moves_history.append(move.uci())
                    
                    # Get evaluation for learning
                    evaluation = await self.engine.evaluate_position(board)
                    evaluations.append(evaluation)
                    
                    # Send move to Chess.com
                    await self.client.make_move(game_id, move.uci())
                    
                    logger.info(f"Made move: {move} (eval: {evaluation}) in {move_time:.2f}s")
                    
                else:
                    # Opponent's turn - wait for their move
                    opponent_move = await self.client.wait_for_opponent_move(game_id)
                    if opponent_move:
                        try:
                            move = chess.Move.from_uci(opponent_move)
                            board.push(move)
                            moves_history.append(opponent_move)
                            
                            # Evaluate opponent's move for learning
                            evaluation = await self.engine.evaluate_position(board)
                            evaluations.append(evaluation)
                            
                            logger.info(f"Opponent played: {move} (eval: {evaluation})")
                        except ValueError:
                            logger.error(f"Invalid move from opponent: {opponent_move}")
                            break
            
            # Game finished - analyze and learn
            result = self._get_game_result(board, color)
            await self._process_finished_game({
                'game_id': game_id,
                'opponent': opponent,
                'color': color,
                'result': result,
                'moves': moves_history,
                'move_times': move_times,
                'evaluations': evaluations,
                'pgn': self._create_pgn(board, game_info, result),
                'duration': (datetime.now() - game_start_time).total_seconds()
            })
            
        except Exception as e:
            logger.error(f"Error during game {game_id}: {e}")
    
    async def _get_best_move(self, board: chess.Board) -> chess.Move:
        """Get the best move for the current position."""
        try:
            # First, try to get move from our trained model
            if self.model_manager.is_model_ready():
                model_move = await self.model_manager.predict_move(board)
                if model_move and model_move in board.legal_moves:
                    # Validate move with engine
                    model_eval = await self.engine.evaluate_move(board, model_move)
                    engine_move = await self.engine.get_best_move(board, time_limit=0.5)
                    engine_eval = await self.engine.evaluate_move(board, engine_move)
                    
                    # Use model move if it's not too much worse than engine
                    if model_eval - engine_eval > -100:  # within 1 pawn
                        logger.debug(f"Using model move: {model_move}")
                        return model_move
            
            # Fallback to engine move
            engine_move = await self.engine.get_best_move(board, time_limit=1.0)
            logger.debug(f"Using engine move: {engine_move}")
            return engine_move
            
        except Exception as e:
            logger.error(f"Error getting best move: {e}")
            # Last resort - random legal move
            import random
            return random.choice(list(board.legal_moves))
    
    async def _process_finished_game(self, game_data: Dict[str, Any]):
        """Process a finished game for learning and statistics."""
        logger.info(f"🏁 Game finished: {game_data['result']}")
        
        # Update statistics
        self.games_played += 1
        if game_data['result'] == 'win':
            self.wins += 1
        elif game_data['result'] == 'loss':
            self.losses += 1
        else:
            self.draws += 1
        
        # Save game to database
        await self.db_manager.save_game(game_data)
        
        # Analyze game for mistakes
        analysis = await self.analyzer.analyze_game(game_data)
        
        # Update model with new data
        if self.games_played % 10 == 0:  # Retrain every 10 games
            logger.info("🧠 Updating model with recent games...")
            await self.model_manager.update_model()
        
        # Log statistics
        win_rate = self.get_win_rate()
        logger.info(f"📊 Games: {self.games_played}, Win rate: {win_rate:.1%}, "
                   f"Mistakes this game: {analysis.get('mistakes', 0)}")
    
    def _get_game_result(self, board: chess.Board, our_color: str) -> str:
        """Determine the game result from our perspective."""
        if board.is_checkmate():
            if (board.turn == chess.WHITE and our_color == 'black') or \
               (board.turn == chess.BLACK and our_color == 'white'):
                return 'win'
            else:
                return 'loss'
        elif board.is_stalemate() or board.is_insufficient_material() or \
             board.is_seventyfive_moves() or board.is_fivefold_repetition():
            return 'draw'
        else:
            return 'unknown'
    
    def _create_pgn(self, board: chess.Board, game_info: Dict, result: str) -> str:
        """Create PGN string for the game."""
        game = chess.pgn.Game()
        
        # Set headers
        game.headers["White"] = game_info.get('white_player', 'Unknown')
        game.headers["Black"] = game_info.get('black_player', 'Unknown') 
        game.headers["Result"] = self._result_to_pgn(result, game_info['color'])
        game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
        game.headers["Site"] = "Chess.com"
        
        # Add moves
        node = game
        for move in board.move_stack:
            node = node.add_variation(move)
        
        return str(game)
    
    def _result_to_pgn(self, result: str, our_color: str) -> str:
        """Convert result to PGN format."""
        if result == 'draw':
            return '1/2-1/2'
        elif result == 'win':
            return '1-0' if our_color == 'white' else '0-1'
        elif result == 'loss':
            return '0-1' if our_color == 'white' else '1-0'
        else:
            return '*'
    
    async def _load_statistics(self):
        """Load bot statistics from database."""
        stats = await self.db_manager.get_bot_statistics()
        if stats:
            self.games_played = stats['games_played']
            self.wins = stats['wins']
            self.losses = stats['losses']
            self.draws = stats['draws']
    
    def get_win_rate(self) -> float:
        """Calculate current win rate."""
        if self.games_played == 0:
            return 0.0
        return self.wins / self.games_played
    
    async def shutdown(self):
        """Shutdown the chess bot."""
        logger.info("Shutting down Chess Bot...")
        if self.client:
            await self.client.close()

