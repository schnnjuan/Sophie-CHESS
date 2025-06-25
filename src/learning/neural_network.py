"""
Neural Network - Chess position evaluation and move prediction

Implements neural networks for chess position evaluation and move selection.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import chess
from typing import List, Tuple
from loguru import logger


class ChessNet(nn.Module):
    """Neural network for chess position evaluation and move prediction."""
    
    def __init__(self, input_size=768, hidden_size=512):
        super(ChessNet, self).__init__()
        
        # Position encoder layers
        self.position_encoder = nn.Sequential(
            nn.Linear(input_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_size, hidden_size),
            nn.ReLU(),
            nn.Dropout(0.3)
        )
        
        # Value head (position evaluation)
        self.value_head = nn.Sequential(
            nn.Linear(hidden_size, 256),
            nn.ReLU(),
            nn.Linear(256, 1),
            nn.Tanh()  # Output between -1 and 1
        )
        
        # Policy head (move probabilities)
        self.policy_head = nn.Sequential(
            nn.Linear(hidden_size, 256),
            nn.ReLU(),
            nn.Linear(256, 4096),  # Max possible moves in chess
            nn.Softmax(dim=1)
        )
    
    def forward(self, x):
        """Forward pass through the network."""
        encoded = self.position_encoder(x)
        value = self.value_head(encoded)
        policy = self.policy_head(encoded)
        return value, policy


class PositionEncoder:
    """Encodes chess positions into numerical features for the neural network."""
    
    @staticmethod
    def board_to_tensor(board: chess.Board) -> torch.Tensor:
        """Convert a chess board to a tensor representation."""
        # Create a 12x8x8 tensor (12 piece types, 8x8 board)
        tensor = np.zeros((12, 8, 8), dtype=np.float32)
        
        piece_map = {
            chess.PAWN: 0, chess.ROOK: 1, chess.KNIGHT: 2,
            chess.BISHOP: 3, chess.QUEEN: 4, chess.KING: 5
        }
        
        for square, piece in board.piece_map().items():
            row, col = divmod(square, 8)
            piece_idx = piece_map[piece.piece_type]
            if piece.color == chess.BLACK:
                piece_idx += 6
            tensor[piece_idx, row, col] = 1.0
        
        # Flatten for neural network input
        return torch.from_numpy(tensor.flatten())
    
    @staticmethod
    def add_game_state_features(board: chess.Board, tensor: torch.Tensor) -> torch.Tensor:
        """Add additional game state features to the position encoding."""
        features = []
        
        # Castling rights
        features.append(float(board.has_kingside_castling_rights(chess.WHITE)))
        features.append(float(board.has_queenside_castling_rights(chess.WHITE)))
        features.append(float(board.has_kingside_castling_rights(chess.BLACK)))
        features.append(float(board.has_queenside_castling_rights(chess.BLACK)))
        
        # En passant
        features.append(float(board.ep_square is not None))
        
        # Turn
        features.append(float(board.turn == chess.WHITE))
        
        # Halfmove clock
        features.append(board.halfmove_clock / 50.0)  # Normalize
        
        # Fullmove number
        features.append(min(board.fullmove_number / 50.0, 1.0))  # Normalize and cap
        
        additional_features = torch.tensor(features, dtype=torch.float32)
        return torch.cat([tensor, additional_features])


class ChessTrainer:
    """Handles training of the chess neural network."""
    
    def __init__(self, model: ChessNet, learning_rate=0.001):
        self.model = model
        self.optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        self.value_criterion = nn.MSELoss()
        self.policy_criterion = nn.CrossEntropyLoss()
        
    def train_step(self, positions: List[torch.Tensor], 
                  values: List[float], 
                  moves: List[int]) -> Tuple[float, float]:
        """Perform one training step."""
        self.optimizer.zero_grad()
        
        # Prepare batch
        batch_positions = torch.stack(positions)
        batch_values = torch.tensor(values, dtype=torch.float32).unsqueeze(1)
        batch_moves = torch.tensor(moves, dtype=torch.long)
        
        # Forward pass
        predicted_values, predicted_policies = self.model(batch_positions)
        
        # Calculate losses
        value_loss = self.value_criterion(predicted_values, batch_values)
        policy_loss = self.policy_criterion(predicted_policies, batch_moves)
        
        total_loss = value_loss + policy_loss
        
        # Backward pass
        total_loss.backward()
        self.optimizer.step()
        
        return value_loss.item(), policy_loss.item()
    
    def save_model(self, filepath: str):
        """Save the trained model."""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict()
        }, filepath)
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load a trained model."""
        checkpoint = torch.load(filepath)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        logger.info(f"Model loaded from {filepath}")

