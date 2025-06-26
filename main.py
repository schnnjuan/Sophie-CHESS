import asyncio
import sys
import signal
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

# Load environment variables from .env.local
load_dotenv(dotenv_path=".env.local")

from src.bot.chess_bot import SophieBot
from src.database.db_manager import DatabaseManager
from src.learning.model_manager import ModelManager
from src.engine.stockfish_engine import StockfishEngine
from src.analysis.game_analyzer import GameAnalyzer


class ChessLearningBot:
    """Main class that orchestrates the chess learning bot."""
    
    def __init__(self):
        self.bot = None
        self.db_manager = None
        self.model_manager = None
        self.engine = None
        self.analyzer = None
        self.running = False
        
    async def initialize(self):
        """Initialize all components of the bot."""
        from loguru import logger
        logger.info("🚀 Initializing SophieBot...")
        
        try:
            # Initialize database
            self.db_manager = DatabaseManager()
            await self.db_manager.initialize()
            logger.info("✅ Database initialized")
            
            # Initialize Stockfish engine
            self.engine = StockfishEngine()
            await self.engine.initialize()
            logger.info("✅ Stockfish engine initialized")
            
            # Initialize game analyzer
            self.analyzer = GameAnalyzer(self.engine)
            logger.info("✅ Game analyzer initialized")
            
            # Initialize model manager
            self.model_manager = ModelManager(self.db_manager)
            await self.model_manager.initialize()
            logger.info("✅ Model manager initialized")
            
            # Initialize chess bot
            self.bot = SophieBot(
                db_manager=self.db_manager,
                model_manager=self.model_manager,
                engine=self.engine,
                analyzer=self.analyzer
            )
            await self.bot.initialize()
            logger.info("✅ SophieBot initialized")
            
            logger.success("🎯 All components initialized successfully!")
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            raise
    
    async def start(self):
        """Start the bot's main loop."""
        self.running = True
        logger.info("🎮 Starting Chess Learning Bot...")
        
        try:
            await self.bot.start_playing()
        except KeyboardInterrupt:
            logger.info("🛑 Received interrupt signal, shutting down...")
        except Exception as e:
            logger.error(f"❌ Error during execution: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Gracefully shutdown all components."""
        logger.info("🛑 Shutting down Chess Learning Bot...")
        self.running = False
        
        if self.bot:
            await self.bot.shutdown()
        if self.engine:
            await self.engine.shutdown()
        if self.db_manager:
            await self.db_manager.close()
            
        logger.info("👋 Chess Learning Bot shutdown complete")


def setup_signal_handlers(bot_instance):
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        asyncio.create_task(bot_instance.shutdown())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main entry point."""
    # Setup logging
    logger.add(
        "data/logs/bot.log",
        rotation="10 MB",
        retention="1 week",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    )
    
    logger.info("🤖 Chess Learning Bot v1.0.0")
    logger.info("=" * 50)
    
    # Create and initialize bot
    chess_bot = ChessLearningBot()
    setup_signal_handlers(chess_bot)
    
    try:
        await chess_bot.initialize()
        await chess_bot.start()
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Create necessary directories
    Path("data/logs").mkdir(parents=True, exist_ok=True)
    Path("models").mkdir(exist_ok=True)
    
    # Run the bot
    asyncio.run(main())

