"""
Integration tests for database operations
"""

import sys
import pytest
import time
import db_helper
from pathlib import Path

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BACKEND_DIR))

class TestDatabaseInitialization:
    """Test database initialization"""
    
    def test_init_database_creates_tables(self, test_db_connection):
        """Test that all required tables are created"""
        import sqlite3
        conn = sqlite3.connect(test_db_connection)
        cursor = conn.cursor()
        
        # Check all tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        expected_tables = ['gameCache', 'ownedGames', 'preferences', 'recommendations', 'users', 'userEvents', 'filterGenres']
        for table in expected_tables:
            assert table in tables, f"Table {table} not created"
    
    def test_init_database_creates_indexes(self, test_db_connection):
        """Test that indexes are created"""
        import sqlite3
        conn = sqlite3.connect(test_db_connection)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name NOT LIKE 'sqlite_%'
        """)
        
        indexes = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # Should have at least these indexes
        assert 'idx_recommendations_user' in indexes
        assert 'idx_preferences_user' in indexes
        assert 'idx_ownedGames_user' in indexes
        assert 'idx_ownedGames_playtime' in indexes
        assert 'idx_filter_genres_user' in indexes


class TestUserManagement:
    """Test user management functions"""
    
    def test_save_user_new(self, test_db_connection, sample_user_data):
        """Test saving a new user"""
        result = db_helper.saveUser(
            sample_user_data['steamId'],
            sample_user_data['displayName'],
            sample_user_data['avatarUrl'],
            sample_user_data['profileUrl']
        )
        
        assert result is True
        
        # Verify user was saved
        user = db_helper.getUser(sample_user_data['steamId'])
        assert user is not None
        assert user['steamId'] == sample_user_data['steamId']
        assert user['displayName'] == sample_user_data['displayName']
    
    def test_save_user_update_existing(self, test_db_connection, sample_user_data):
        """Test updating an existing user"""
        # Save initial user
        db_helper.saveUser(
            sample_user_data['steamId'],
            sample_user_data['displayName'],
            sample_user_data['avatarUrl'],
            sample_user_data['profileUrl']
        )

        # Update with new display name
        new_name = 'Updated Name'
        db_helper.saveUser(
            sample_user_data['steamId'],
            new_name,
            sample_user_data['avatarUrl'],
            sample_user_data['profileUrl']
        )
        
        # Verify update
        user = db_helper.getUser(sample_user_data['steamId'])
        assert user['displayName'] == new_name
    
    def test_get_user_not_found(self, test_db_connection):
        """Test getting a non-existent user"""
        user = db_helper.getUser('nonexistent_steam_id')
        assert user is None


class TestOwnedGamesCache:
    """Test owned games caching functionality"""
    
    def test_cache_owned_games(self, test_db_connection, sample_user_data, mock_steam_api):
        """Test caching owned games"""
        db_helper.cacheOwnedGames(
            sample_user_data['steamId'],
            mock_steam_api['owned_games']
        )
        
        game_ids = db_helper.getOwnedGamesIds(sample_user_data['steamId'])
        
        assert len(game_ids) == 3
        assert '292030' in game_ids # The Witcher 3
        assert '72850' in game_ids # Skyrim
        assert '1091500' in game_ids #Cyberpunk 2077
    
    def test_is_owned_games_cache_recent_fresh(self, test_db_connection, sample_user_data, mock_steam_api):
        """Test cache freshness check with fresh cache"""
        db_helper.cacheOwnedGames(
            sample_user_data['steamId'],
            mock_steam_api['owned_games']
        )
        
        is_recent = db_helper.isOwnedGamesCacheRecent(sample_user_data['steamId'], maxAgeHours=24)
        assert is_recent is True


class TestGamingProfile:
    """Test gaming profile analysis"""
    
    def test_get_user_gaming_profile(self, test_db_connection, sample_user_data, mock_steam_api):
        """Test getting user gaming profile"""
        db_helper.cacheOwnedGames(
            sample_user_data['steamId'],
            mock_steam_api['owned_games']
        )
        
        profile = db_helper.getUserGamingProfile(sample_user_data['steamId'])

        assert profile['gameCount'] == 3
        assert profile['totalPlaytime'] == 545.0
        assert len(profile['topGames']) == 3
        assert profile['topGames'][0][1] == 'The Elder Scrolls V: Skyrim' # Most played
        assert profile['topGames'][0][2] == 245.0
    
    def test_get_user_gaming_profile_empty(self, test_db_connection, sample_user_data):
        """Test gaming profile with no cached games"""
        profile = db_helper.getUserGamingProfile(sample_user_data['steamId'])
        
        assert profile['gameCount'] == 0
        assert profile['totalPlaytime'] == 0
        assert len(profile['topGames']) == 0


class TestRecommendationHistory:
    """Test recommendation history management"""
    
    def test_save_recommendation(self, test_db_connection, sample_user_data, sample_game_data):
        """Test saving a recommendation"""
        rec_id = db_helper.saveRecommendation(
            sample_user_data['steamId'],
            sample_game_data,
            'This game is perfect for you!',
            95,
            ['RPG', 'Action']
        )
        
        assert rec_id is not None
        assert isinstance(rec_id, int)
    
    def test_save_recommendation_prevents_duplicates(self, test_db_connection, sample_user_data, sample_game_data):
        """Test that duplicate recommendations are prevented"""
        # Save first recommendation
        rec_id_1 = db_helper.saveRecommendation(
            sample_user_data['steamId'],
            sample_game_data,
            'First recommendation',
            95,
            ['RPG']
        )
        
        # Try to save duplicate
        rec_id_2 = db_helper.saveRecommendation(
            sample_user_data['steamId'],
            sample_game_data,
            'Second recommendation',
            95,
            ['Action']
        )
        
        assert rec_id_1 is not None
        assert rec_id_2 is None, f"Expected None for duplicate, got {rec_id_2}"  # Should return None for duplicate

        # Verify only one recommendation exists
        recs = db_helper.getUserRecommendations(sample_user_data['steamId'], limit=10)
        assert len(recs) == 1
        assert recs[0]['reasoning'] == 'First recommendation'
    
    def test_get_user_recommendations_pagination(self, test_db_connection, sample_user_data):
        """Test recommendation pagination"""
        # Save multiple recommendations
        for i in range(5):
            game_data = {
                'gameId': str(100 + i),
                'title': f'Game {i}',
                'thumbnail': '',
                'releaseDate': '',
                'publisher': '',
                'developer': '',
                'price': '',
                'salePrice': '',
                'description': ''
            }
            db_helper.saveRecommendation(
                sample_user_data['steamId'],
                game_data,
                f'Recommendation {i}',
                80 + i
            )
        
        # Test pagination
        page1 = db_helper.getUserRecommendations(sample_user_data['steamId'], limit=2, offset=0)
        page2 = db_helper.getUserRecommendations(sample_user_data['steamId'], limit=2, offset=2)
        
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0]['gameId'] != page2[0]['gameId']
    
    
class TestPreferences:
    """Test user preference management"""
    
    def test_save_preference_liked(self, test_db_connection, sample_user_data):
        """Test saving a liked preference"""
        result = db_helper.savePreference(
            sample_user_data['steamId'],
            '570',
            'liked'
        )
        
        assert result is True
        
        liked_ids = db_helper.getPreferenceGameIds(sample_user_data['steamId'], 'liked')
        assert '570' in liked_ids
    
    def test_save_preference_update(self, test_db_connection, sample_user_data):
        """Test updating a preference (change from liked to disliked)"""
        # First like
        db_helper.savePreference(sample_user_data['steamId'], '570', 'liked')
        
        # Then dislike
        db_helper.savePreference(sample_user_data['steamId'], '570', 'disliked')
        
        liked_ids = db_helper.getPreferenceGameIds(sample_user_data['steamId'], 'liked')
        disliked_ids = db_helper.getPreferenceGameIds(sample_user_data['steamId'], 'disliked')
        
        assert '570' not in liked_ids
        assert '570' in disliked_ids


class TestUserEvents:
    """Test user events logging and retrieval"""
    
    def test_save_user_event_complete(self, test_db_connection, sample_user_data):
        """Test saving user event with all fields"""
        result = db_helper.saveUserEvent(
            steamId=sample_user_data['steamId'],
            eventType='recommendation_request',
            gameId='570',
            timestamp=1735689600
        )
        
        assert result is True
        
        # Verify saved
        events = db_helper.getUserEvents(
            steamId=sample_user_data['steamId'],
            from_ts=1735689600,
            to_ts=1735776000
        )
        
        assert len(events) == 1
        assert events[0]['eventType'] == 'recommendation_request'
        assert events[0]['gameId'] == '570'
    
    def test_save_multiple_events_same_user(self, test_db_connection, sample_user_data):
        """Test saving multiple events for same user"""
        for i in range(5):
            result = db_helper.saveUserEvent(
                steamId=sample_user_data['steamId'],
                eventType=f'event_{i}',
                timestamp=1735689600 + i * 100
            )
            assert result is True
        
        events = db_helper.getUserEvents(
            steamId=sample_user_data['steamId'],
            from_ts=1735689600,
            to_ts=1735776000
        )
        
        assert len(events) == 5


class TestFilterGenres:
    """Test filter genres management (Feature 6)"""
    
    def test_save_filter_genres_new(self, test_db_connection, sample_user_data):
        """Test saving new filter genres"""
        genres = ['RPG', 'Action', 'Open World']
        
        result = db_helper.saveFilterGenres(
            sample_user_data['steamId'],
            genres
        )
        
        assert result is True
        
        # Verify saved
        saved_genres = db_helper.getFilterGenres(sample_user_data['steamId'])
        assert saved_genres == genres

    def test_save_filter_genres_update_existing(self, test_db_connection, sample_user_data):
        """Test updating existing filter genres"""
        # Save initial genres
        db_helper.saveFilterGenres(sample_user_data['steamId'], ['RPG', 'Action'])
    
        # Update with new genres
        db_helper.saveFilterGenres(sample_user_data['steamId'], ['Horror', 'Survival'])
    
        # Verify update (should replace, not append)
        saved_genres = db_helper.getFilterGenres(sample_user_data['steamId'])
        assert saved_genres == ['Horror', 'Survival']
        assert 'RPG' not in saved_genres
    

class TestDatabaseErrorHandling:
    """Test error handling in database operations"""
    
    def test_save_user_invalid_data(self, test_db_connection):
        """Test saving user with invalid data"""
        with pytest.raises(Exception):
            db_helper.saveUser(None, None, None, None)