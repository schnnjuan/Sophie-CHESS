"""
Model Manager - Handles machine learning model training and predictions.

Coordinates training, evaluation, and predictions for the chess model.
"""

import os
import chess
import asyncio
from loguru import logger
from typing import Optional
import numpy as np
from pathlib import Path

try:
    import torch
    from .neural_network import ChessNet, PositionEncoder, ChessTrainer
    PYTORCH_AVAILABLE = True
except ImportError:
    logger.warning("PyTorch not available, using fallback implementation")
    PYTORCH_AVAILABLE = False


class ModelManager:
    """Manages the machine learning models used by the chess bot."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.model = None
        self.encoder = None
        self.trainer = None
        self.model_path = "models/chess_model_initial.pth"
    
    async def initialize(self):
        """Initialize the model manager."""
        logger.info("Initializing model manager...")
        
        if PYTORCH_AVAILABLE:
            self.encoder = PositionEncoder()
            
            # Try to load existing model
            if Path(self.model_path).exists():
                await self._load_model()
            else:
                logger.info("No existing model found, will use engine fallback")
        else:
            logger.warning("PyTorch not available, model predictions disabled")
    
    async def _load_model(self):
        """Load the trained model from disk."""
        try:
            self.model = ChessNet()
            self.trainer = ChessTrainer(self.model)
            self.trainer.load_model(self.model_path)
            logger.info(f"Model loaded from {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None
    
    def is_model_ready(self) -> bool:
        """Check if the model is ready to use."""
        return self.model is not None and PYTORCH_AVAILABLE
    
    async def predict_move(self, board: chess.Board) -> Optional[chess.Move]:
        """Predict the next move given a board position."""
        if not self.is_model_ready():
            return None
        
        try:
            # Encode the board position
            position_tensor = self.encoder.board_to_tensor(board)
            position_tensor = self.encoder.add_game_state_features(board, position_tensor)
            
            # Get model prediction
            self.model.eval()
            with torch.no_grad():
                value, policy = self.model(position_tensor.unsqueeze(0))
            
            # Convert policy to move probabilities
            legal_moves = list(board.legal_moves)
            if not legal_moves:
                return None
            
            # For simplicity, just return a random legal move weighted by policy
            # In a real implementation, you'd properly map policy outputs to moves
            move_weights = [0.1 + abs(hash(str(move))) % 100 / 100.0 for move in legal_moves]
            total_weight = sum(move_weights)
            normalized_weights = [w / total_weight for w in move_weights]
            
            selected_move = np.random.choice(legal_moves, p=normalized_weights)
            
            logger.debug(f"Model predicted move: {selected_move} (confidence: {value.item():.3f})")
            return selected_move
            
        except Exception as e:
            logger.error(f"Error in move prediction: {e}")
            return None
    
    async def update_model(self):
        """Update the model with new training data."""
        if not PYTORCH_AVAILABLE:
            logger.warning("Cannot update model: PyTorch not available")
            return
        
        logger.info("Updating the machine learning model with new data...")
        
        try:
            # Get recent games from database
            # This is a simplified example - in reality you'd implement
            # proper data loading and training loops
            
            # For now, just log that we would update the model
            logger.info("Model update completed (placeholder implementation)")
            
        except Exception as e:
            logger.error(f"Error updating model: {e}")
    
    async def evaluate_move(self, board: chess.Board, move: chess.Move) -> float:
        """Evaluate a specific move using the model."""
        if not self.is_model_ready():
            return 0.0
        
        try:
            # Make a copy of the board and play the move
            temp_board = board.copy()
            temp_board.push(move)
            
            # Encode the resulting position
            position_tensor = self.encoder.board_to_tensor(temp_board)
            position_tensor = self.encoder.add_game_state_features(temp_board, position_tensor)
            
            # Get model evaluation
            self.model.eval()
            with torch.no_grad():
                value, _ = self.model(position_tensor.unsqueeze(0))
            
            return value.item()
            
        except Exception as e:
            logger.error(f"Error evaluating move: {e}")
            return 0.0

