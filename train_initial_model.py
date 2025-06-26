#!/usr/bin/env python3
"""
Initial Model Training Script

Trains the initial chess model using existing game data or random games.
"""

import asyncio
import sys
from pathlib import Path
from loguru import logger
import torch
import chess
import random

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.learning.neural_network import ChessNet, PositionEncoder, ChessTrainer
from src.database.db_manager import DatabaseManager
from src.engine.stockfish_engine import StockfishEngine


class InitialTrainer:
    """Handles initial training of the chess model."""
    
    def __init__(self):
        self.model = ChessNet()
        self.trainer = ChessTrainer(self.model)
        self.encoder = PositionEncoder()
        self.db_manager = None
        self.engine = None
    
    async def initialize(self):
        """Initialize components."""
        logger.info("🚀 Initializing training components...")
        
        # Initialize database
        self.db_manager = DatabaseManager()
        await self.db_manager.initialize()
        
        # Initialize Stockfish for generating training data
        self.engine = StockfishEngine()
        await self.engine.initialize()
        
        logger.info("✅ Training components initialized")
    
    async def generate_training_data(self, num_games=100):
        """Generate training data by playing random games with Stockfish analysis."""
        logger.info(f"🎮 Generating {num_games} training games...")
        
        training_data = []
        
        for game_num in range(num_games):
            logger.info(f"Generating game {game_num + 1}/{num_games}")
            
            board = chess.Board()
            positions = []
            evaluations = []
            
            # Play a random game
            while not board.is_game_over() and len(board.move_stack) < 100:
                # Get random legal move
                legal_moves = list(board.legal_moves)
                if not legal_moves:
                    break
                
                move = random.choice(legal_moves)
                board.push(move)
                
                # Encode position
                position_tensor = self.encoder.board_to_tensor(board)
                position_tensor = self.encoder.add_game_state_features(board, position_tensor)
                
                # Get Stockfish evaluation
                evaluation = await self.engine.evaluate_position(board)
                
                positions.append(position_tensor)
                evaluations.append(evaluation / 10.0)  # Normalize to [-1, 1] range
            
            # Add to training data
            for pos, eval_score in zip(positions, evaluations):
                training_data.append((pos, eval_score))
            
            if (game_num + 1) % 10 == 0:
                logger.info(f"Generated {len(training_data)} training positions so far")
        
        logger.info(f"✅ Generated {len(training_data)} training positions")
        return training_data
    
    async def train_model(self, training_data, epochs=50, batch_size=32):
        """Train the model on the generated data."""
        logger.info(f"🧠 Training model for {epochs} epochs...")
        
        for epoch in range(epochs):
            random.shuffle(training_data)
            
            total_value_loss = 0
            total_policy_loss = 0
            num_batches = 0
            
            # Process in batches
            for i in range(0, len(training_data), batch_size):
                batch = training_data[i:i + batch_size]
                
                positions = [item[0] for item in batch]
                values = [item[1] for item in batch]
                
                # For now, use random move indices (in real implementation, 
                # you'd extract actual moves from the training data)
                moves = [random.randint(0, 4095) for _ in batch]
                
                value_loss, policy_loss = self.trainer.train_step(positions, values, moves)
                
                total_value_loss += value_loss
                total_policy_loss += policy_loss
                num_batches += 1
            
            avg_value_loss = total_value_loss / num_batches
            avg_policy_loss = total_policy_loss / num_batches
            
            if (epoch + 1) % 10 == 0:
                logger.info(f"Epoch {epoch + 1}/{epochs} - "
                           f"Value Loss: {avg_value_loss:.4f}, "
                           f"Policy Loss: {avg_policy_loss:.4f}")
        
        logger.info("✅ Model training completed")
    
    def save_model(self):
        """Save the trained model."""
        model_path = "models/chess_model_initial.pth"
        Path("models").mkdir(exist_ok=True)
        self.trainer.save_model(model_path)
        logger.info(f"💾 Model saved to {model_path}")
    
    async def cleanup(self):
        """Clean up resources."""
        if self.engine:
            await self.engine.shutdown()
        if self.db_manager:
            await self.db_manager.close()


async def main():
    """Main training function."""
    logger.info("🤖 Chess Model Initial Training")
    logger.info("=" * 40)
    
    trainer = InitialTrainer()
    
    try:
        await trainer.initialize()
        
        # Generate training data
        training_data = await trainer.generate_training_data(num_games=50)
        
        # Train the model
        await trainer.train_model(training_data, epochs=30)
        
        # Save the model
        trainer.save_model()
        
        logger.success("🎉 Initial training completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Training failed: {e}")
        raise
    
    finally:
        await trainer.cleanup()


if __name__ == "__main__":
    # Setup logging
    logger.add(
        "data/logs/training.log",
        rotation="10 MB",
        retention="1 week",
        level="INFO"
    )
    
    # Create necessary directories
    Path("data/logs").mkdir(parents=True, exist_ok=True)
    Path("models").mkdir(exist_ok=True)
    
    # Run training
    asyncio.run(main())

