"""
Database Manager - Manages the persistence layer

Handles storing and retrieving game data from the database.
"""

import aiosqlite
from typing import Dict, Any
from loguru import logger
import os

class DatabaseManager:
    """Manages the storage and retrieval of game data."""
    
    def __init__(self):
        self.db_path = os.getenv('DB_PATH', 'data/chess_bot.db')
        self.connection = None
    
    async def initialize(self):
        """Initialize database connection and tables."""
        logger.info("Initializing database...")
        self.connection = await aiosqlite.connect(self.db_path)
        await self._create_tables()
    
    async def _create_tables(self):
        """Create necessary tables in the database."""
        async with self.connection.cursor() as cursor:
            await cursor.execute('''
                CREATE TABLE IF NOT EXISTS games (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_id TEXT UNIQUE,
                    opponent TEXT,
                    color TEXT,
                    result TEXT,
                    moves TEXT,
                    move_times TEXT,
                    evaluations TEXT,
                    pgn TEXT,
                    duration REAL
                )
            ''')
            await self.connection.commit()
            logger.info("✅ Database tables ready")
    
    async def save_game(self, game_data: Dict[str, Any]):
        """Save a completed game to the database."""
        async with self.connection.cursor() as cursor:
            await cursor.execute('''
                INSERT INTO games (game_id, opponent, color, result, moves, move_times, evaluations, pgn, duration)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                game_data['game_id'],
                game_data['opponent'],
                game_data['color'],
                game_data['result'],
                ','.join(game_data['moves']),
                ','.join(map(str, game_data['move_times'])),
                ','.join(map(str, game_data['evaluations'])),
                game_data['pgn'],
                game_data['duration']
            ))
            await self.connection.commit()
            logger.info(f"Game {game_data['game_id']} saved to database")
    
    async def get_bot_statistics(self) -> Dict[str, int]:
        """Retrieve aggregate statistics for the bot."""
        async with self.connection.cursor() as cursor:
            await cursor.execute('''
                SELECT COUNT(*) as games_played,
                       SUM(case when result = "win" then 1 else 0 end) as wins,
                       SUM(case when result = "loss" then 1 else 0 end) as losses,
                       SUM(case when result = "draw" then 1 else 0 end) as draws
                FROM games
            ''')
            row = await cursor.fetchone()
            return {
                'games_played': row['games_played'],
                'wins': row['wins'],
                'losses': row['losses'],
                'draws': row['draws'],
            }
    
    async def close(self):
        """Close the database connection."""
        if self.connection:
            await self.connection.close()
            logger.info("Database connection closed")

