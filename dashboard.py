#!/usr/bin/env python3
"""
Chess Bot Dashboard - Monitoring and visualization

Provides a web dashboard to monitor the bot's performance and statistics.
"""

import asyncio
import sys
from pathlib import Path
import json
from datetime import datetime, timedelta
from loguru import logger
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from flask import Flask, render_template, jsonify
from threading import Thread

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from database.db_manager import DatabaseManager

app = Flask(__name__)
db_manager = None


class DashboardData:
    """Handles data collection and processing for the dashboard."""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    async def get_performance_stats(self):
        """Get overall performance statistics."""
        stats = await self.db_manager.get_bot_statistics()
        
        return {
            'total_games': stats['games_played'],
            'wins': stats['wins'],
            'losses': stats['losses'],
            'draws': stats['draws'],
            'win_rate': stats['wins'] / max(stats['games_played'], 1) * 100,
            'loss_rate': stats['losses'] / max(stats['games_played'], 1) * 100,
            'draw_rate': stats['draws'] / max(stats['games_played'], 1) * 100
        }
    
    async def get_recent_games(self, limit=10):
        """Get recent games data."""
        # This would be implemented with proper SQL queries
        # For demo purposes, returning mock data
        return [
            {
                'game_id': f'game_{i}',
                'opponent': f'Player{i}',
                'result': ['win', 'loss', 'draw'][i % 3],
                'color': ['white', 'black'][i % 2],
                'duration': 300 + i * 30,
                'date': (datetime.now() - timedelta(days=i)).isoformat()
            }
            for i in range(limit)
        ]
    
    def generate_performance_chart(self):
        """Generate performance chart over time."""
        # Mock data for demonstration
        dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
        win_rates = [50 + i * 0.5 + (i % 3) * 2 for i in range(30)]
        
        plt.figure(figsize=(12, 6))
        plt.plot(dates, win_rates, marker='o', linewidth=2, markersize=4)
        plt.title('Win Rate Over Time', fontsize=16, fontweight='bold')
        plt.xlabel('Date')
        plt.ylabel('Win Rate (%)')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        chart_path = 'static/performance_chart.png'
        Path('static').mkdir(exist_ok=True)
        plt.savefig(chart_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return chart_path


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('dashboard.html')


@app.route('/api/stats')
def api_stats():
    """API endpoint for performance statistics."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        dashboard_data = DashboardData(db_manager)
        stats = loop.run_until_complete(dashboard_data.get_performance_stats())
        return jsonify(stats)
    finally:
        loop.close()


@app.route('/api/recent-games')
def api_recent_games():
    """API endpoint for recent games."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        dashboard_data = DashboardData(db_manager)
        games = loop.run_until_complete(dashboard_data.get_recent_games())
        return jsonify(games)
    finally:
        loop.close()


async def init_dashboard():
    """Initialize dashboard components."""
    global db_manager
    
    logger.info("Initializing dashboard...")
    
    # Initialize database connection
    db_manager = DatabaseManager()
    await db_manager.initialize()
    
    logger.info("Dashboard initialized")


def run_flask_app():
    """Run the Flask application in a separate thread."""
    app.run(host='0.0.0.0', port=5000, debug=False)


async def main():
    """Main dashboard function."""
    logger.info("📈 Starting Chess Bot Dashboard")
    logger.info("=" * 40)
    
    await init_dashboard()
    
    # Create templates directory and basic template
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)
    
    dashboard_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chess Bot Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 30px; }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stat-value { font-size: 2em; font-weight: bold; color: #333; }
        .stat-label { color: #666; margin-top: 5px; }
        .chart-container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 30px; }
        .games-table { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; }
        .win { color: #28a745; }
        .loss { color: #dc3545; }
        .draw { color: #ffc107; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Chess Learning Bot Dashboard</h1>
            <p>Real-time monitoring and performance analytics</p>
        </div>
        
        <div class="stats-grid" id="stats-container">
            <!-- Stats will be loaded here -->
        </div>
        
        <div class="chart-container">
            <h3>Performance Over Time</h3>
            <canvas id="performanceChart" width="400" height="200"></canvas>
        </div>
        
        <div class="games-table">
            <h3>Recent Games</h3>
            <table id="recent-games-table">
                <thead>
                    <tr>
                        <th>Game ID</th>
                        <th>Opponent</th>
                        <th>Color</th>
                        <th>Result</th>
                        <th>Duration</th>
                        <th>Date</th>
                    </tr>
                </thead>
                <tbody id="recent-games-body">
                    <!-- Recent games will be loaded here -->
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        // Load statistics
        fetch('/api/stats')
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('stats-container');
                container.innerHTML = `
                    <div class="stat-card">
                        <div class="stat-value">${data.total_games}</div>
                        <div class="stat-label">Total Games</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${data.win_rate.toFixed(1)}%</div>
                        <div class="stat-label">Win Rate</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${data.wins}</div>
                        <div class="stat-label">Wins</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${data.losses}</div>
                        <div class="stat-label">Losses</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${data.draws}</div>
                        <div class="stat-label">Draws</div>
                    </div>
                `;
            });
        
        // Load recent games
        fetch('/api/recent-games')
            .then(response => response.json())
            .then(games => {
                const tbody = document.getElementById('recent-games-body');
                tbody.innerHTML = games.map(game => `
                    <tr>
                        <td>${game.game_id}</td>
                        <td>${game.opponent}</td>
                        <td>${game.color}</td>
                        <td class="${game.result}">${game.result.toUpperCase()}</td>
                        <td>${Math.floor(game.duration / 60)}m ${game.duration % 60}s</td>
                        <td>${new Date(game.date).toLocaleDateString()}</td>
                    </tr>
                `).join('');
            });
        
        // Create performance chart
        const ctx = document.getElementById('performanceChart').getContext('2d');
        new Chart(ctx, {
            type: 'line',
            data: {
                labels: Array.from({length: 30}, (_, i) => `Day ${i + 1}`),
                datasets: [{
                    label: 'Win Rate (%)',
                    data: Array.from({length: 30}, (_, i) => 50 + i * 0.5 + (i % 3) * 2),
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
        
        // Auto-refresh every 30 seconds
        setInterval(() => {
            location.reload();
        }, 30000);
    </script>
</body>
</html>
    '''
    
    with open(templates_dir / 'dashboard.html', 'w', encoding='utf-8') as f:
        f.write(dashboard_template)
    
    # Start Flask app in a separate thread
    flask_thread = Thread(target=run_flask_app, daemon=True)
    flask_thread.start()
    
    logger.info("🌐 Dashboard available at http://localhost:5000")
    logger.info("Press Ctrl+C to stop")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("🛑 Dashboard stopping...")
        if db_manager:
            await db_manager.close()


if __name__ == "__main__":
    # Setup logging
    logger.add(
        "data/logs/dashboard.log",
        rotation="10 MB",
        retention="1 week",
        level="INFO"
    )
    
    # Create necessary directories
    Path("data/logs").mkdir(parents=True, exist_ok=True)
    Path("static").mkdir(exist_ok=True)
    
    # Run dashboard
    asyncio.run(main())

