import pytest
import asyncio
from main import ChessLearningBot

@pytest.mark.asyncio
async def test_bot_initialization():
    bot = ChessLearningBot()
    await bot.initialize()
    assert bot.db_manager is not None
    assert bot.engine is not None
    assert bot.model_manager is not None
    assert bot.analyzer is not None
    assert bot.bot is not None
