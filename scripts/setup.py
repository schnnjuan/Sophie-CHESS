#!/usr/bin/env python3
"""
Setup Script - Initial setup and configuration

Sets up the chess bot environment and performs initial configuration.
"""

import os
import sys
from pathlib import Path
from loguru import logger


def create_directories():
    """Create necessary directories."""
    directories = [
        'data',
        'data/logs',
        'models',
        'static',
        'templates'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"✅ Created directory: {directory}")


def create_env_file():
    """Create .env file if it doesn't exist."""
    env_path = Path('.env')
    
    if env_path.exists():
        logger.info("ℹ️ .env file already exists")
        return
    
    # Copy from .env.example
    example_path = Path('.env.example')
    if example_path.exists():
        with open(example_path, 'r') as src, open(env_path, 'w') as dst:
            dst.write(src.read())
        logger.info("✅ Created .env file from .env.example")
        logger.warning("⚠️ Please edit .env file with your actual credentials")
    else:
        logger.error("❌ .env.example file not found")


def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        'chess',
        'torch',
        'numpy',
        'loguru',
        'aiohttp',
        'aiosqlite',
        'matplotlib',
        'seaborn',
        'pandas',
        'flask'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            logger.warning(f"⚠️ {package} is not installed")
    
    if missing_packages:
        logger.error(f"❌ Missing packages: {', '.join(missing_packages)}")
        logger.info("Run: pip install -r requirements.txt")
        return False
    
    logger.info("✅ All dependencies are installed")
    return True


def check_stockfish():
    """Check if Stockfish is available."""
    import subprocess
    
    try:
        result = subprocess.run(['stockfish'], 
                              input='quit\n', 
                              text=True, 
                              capture_output=True, 
                              timeout=5)
        if result.returncode == 0:
            logger.info("✅ Stockfish is installed and accessible")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    
    logger.warning("⚠️ Stockfish not found or not accessible")
    logger.info("Please install Stockfish:")
    logger.info("  Windows: choco install stockfish")
    logger.info("  Linux: sudo apt install stockfish")
    logger.info("  macOS: brew install stockfish")
    return False


def main():
    """Main setup function."""
    logger.info("🚀 Setting up Chess Learning Bot...")
    logger.info("=" * 50)
    
    # Create directories
    create_directories()
    
    # Create .env file
    create_env_file()
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    # Check Stockfish
    stockfish_ok = check_stockfish()
    
    logger.info("=" * 50)
    
    if deps_ok and stockfish_ok:
        logger.success("🎉 Setup completed successfully!")
        logger.info("Next steps:")
        logger.info("1. Edit .env file with your Chess.com credentials")
        logger.info("2. Run: python train_initial_model.py")
        logger.info("3. Run: python main.py")
    else:
        logger.error("❌ Setup incomplete. Please resolve the issues above.")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

