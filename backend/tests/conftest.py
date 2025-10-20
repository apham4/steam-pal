import pytest
import sqlite3
import tempfile
import os
import sys
from pathlib import Path

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

import db_helper

@pytest.fixture
def test_db_connection():
    """Create a temporary test database"""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    # Override the database path in db_helper
    original_db = db_helper.DB_FILE
    db_helper.DB_FILE = db_path
    
    # Initialize database
    db_helper.initDatabase()
    
    yield db_path
    
    # Cleanup
    db_helper.DB_FILE = original_db
    
    # Close file descriptor
    try:
        os.close(db_fd)
    except:
        pass
    
    # Close any open connections
    try:
        conn = sqlite3.connect(db_path)
        conn.close()
    except:
        pass
    
    # Remove database file
    try:
        os.unlink(db_path)
    except PermissionError:
        # File is still locked, try again after a short delay
        import time
        time.sleep(0.1)
        try:
            os.unlink(db_path)
        except:
            pass

@pytest.fixture
def sample_user_data():
    """Sample user data for tests"""
    return {
        'steamId': '76561197960287930',
        'displayName': 'Test User',
        'avatarUrl': 'https://example.com/avatar.jpg',
        'profileUrl': 'https://steamcommunity.com/id/testuser/'
    }

@pytest.fixture
def sample_game_data():
    """Sample game data for tests"""
    return {
        'gameId': '292030',
        'title': 'The Witcher 3: Wild Hunt',
        'thumbnail': 'https://cdn.akamai.steamstatic.com/steam/apps/292030/header.jpg',
        'releaseDate': 'May 18, 2015',
        'publisher': 'CD PROJEKT RED',
        'developer': 'CD PROJEKT RED',
        'price': '$39.99',
        'salePrice': '$9.99',
        'description': 'As war rages on throughout the Northern Realms...'
    }

@pytest.fixture
def sample_gaming_profile():
    """Sample gaming profile for LLM tests"""
    return {
        'topGames': [
            ('72850', 'The Elder Scrolls V: Skyrim', 245.0),
            ('292030', 'The Witcher 3: Wild Hunt', 180.0),
            ('1091500', 'Cyberpunk 2077', 120.0),
        ],
        'totalPlaytime': 545.0,
        'recentlyActiveGames': [
            ('292030', 'The Witcher 3: Wild Hunt', 15.0),
            ('1091500', 'Cyberpunk 2077', 8.0),
        ],
        'mostPlayedGames': [
            ('72850', 'The Elder Scrolls V: Skyrim', 245.0),
            ('292030', 'The Witcher 3: Wild Hunt', 180.0),
            ('1091500', 'Cyberpunk 2077', 120.0),
        ],
        'favoriteGenres': ['RPG', 'Action', 'Open World'],
        'gameCount': 150
    }

@pytest.fixture
def mock_llm_response():
    """Mock LLM API response for game recommendations"""
    return {
        'gameId': '435150',
        'title': 'Divinity: Original Sin 2',
        'reasoning': 'Based on your love for The Witcher 3 and Skyrim, this tactical RPG offers deep storytelling, meaningful choices, and over 100 hours of content.',
        'matchScore': 92,
        'similarTo': ['The Witcher 3: Wild Hunt', 'The Elder Scrolls V: Skyrim']
    }

@pytest.fixture
def mock_steam_api():
    """Mock Steam API responses"""
    return {
        'game_details': {
            'steam_appid': 292030,
            'name': 'The Witcher 3: Wild Hunt',
            'header_image': 'https://cdn.akamai.steamstatic.com/steam/apps/292030/header.jpg',
            'short_description': 'As war rages on throughout the Northern Realms...',
            'developers': ['CD PROJEKT RED'],
            'publishers': ['CD PROJEKT RED'],
            'release_date': {'date': 'May 18, 2015'},
            'price_overview': {
                'currency': 'USD',
                'initial': 3999,
                'final': 999,
                'discount_percent': 75
            },
            'genres': [
                {'description': 'RPG'},
                {'description': 'Action'}
            ]
        },
        'owned_games': [
            {
                'appid': 292030,
                'name': 'The Witcher 3: Wild Hunt',
                'playtime_forever': 10800,
                'playtime_2weeks': 900
            },
            {
                'appid': 72850,
                'name': 'The Elder Scrolls V: Skyrim',
                'playtime_forever': 14700,
                'playtime_2weeks': 0
            },
            {
                'appid': 1091500,
                'name': 'Cyberpunk 2077',
                'playtime_forever': 7200,
                'playtime_2weeks': 480
            }
        ],
        'user_profile': {
            'steamid': '76561197960287930',
            'personaname': 'Test User',
            'profileurl': 'https://steamcommunity.com/id/testuser/',
            'avatar': 'https://example.com/avatar_small.jpg',
            'avatarmedium': 'https://example.com/avatar_medium.jpg',
            'avatarfull': 'https://example.com/avatar.jpg'
        }
    }