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
    
    def test_cache_owned_games_replaces_old_cache(self, test_db_connection, sample_user_data, mock_steam_api):
        """Test that caching replaces old data"""
        # Cache initial games
        db_helper.cacheOwnedGames(
            sample_user_data['steamId'],
            mock_steam_api['owned_games']
        )
        
        # Cache new games
        new_games = [
            {
                'appid': 440,
                'name': 'Team Fortress 2',
                'playtimeForever': 3000,
                'playtime2Weeks': 100
            }
        ]
        
        db_helper.cacheOwnedGames(sample_user_data['steamId'], new_games)
        
        game_ids = db_helper.getOwnedGamesIds(sample_user_data['steamId'])
        
        assert len(game_ids) == 1
        assert '440' in game_ids
        assert '570' not in game_ids
    
    def test_is_owned_games_cache_recent_fresh(self, test_db_connection, sample_user_data, mock_steam_api):
        """Test cache freshness check with fresh cache"""
        db_helper.cacheOwnedGames(
            sample_user_data['steamId'],
            mock_steam_api['owned_games']
        )
        
        is_recent = db_helper.isOwnedGamesCacheRecent(sample_user_data['steamId'], maxAgeHours=24)
        assert is_recent is True
    
    def test_is_owned_games_cache_recent_stale(self, test_db_connection, sample_user_data, mock_steam_api):
        """Test cache freshness check with stale cache"""
        db_helper.cacheOwnedGames(
            sample_user_data['steamId'],
            mock_steam_api['owned_games']
        )
        
        # Check with very short max age
        is_recent = db_helper.isOwnedGamesCacheRecent(sample_user_data['steamId'], maxAgeHours=0.0001)
        
        time.sleep(1.0)
        
        is_recent_after = db_helper.isOwnedGamesCacheRecent(sample_user_data['steamId'], maxAgeHours=0.0001)
        assert is_recent_after is False
    
    def test_is_owned_games_cache_recent_no_cache(self, test_db_connection, sample_user_data):
        """Test cache freshness check with no cache"""
        is_recent = db_helper.isOwnedGamesCacheRecent(sample_user_data['steamId'])
        assert is_recent is False


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
    
    def test_get_user_gaming_profile_recently_active(self, test_db_connection, sample_user_data, mock_steam_api):
        """Test recently active games in profile"""
        db_helper.cacheOwnedGames(
            sample_user_data['steamId'],
            mock_steam_api['owned_games']
        )
        
        profile = db_helper.getUserGamingProfile(sample_user_data['steamId'])
        
        assert len(profile['recentlyActiveGames']) == 2
        assert profile['recentlyActiveGames'][0][1] == 'The Witcher 3: Wild Hunt'  # Most recent
        assert profile['recentlyActiveGames'][0][2] == 15.0  # 900 minutes = 15 hours
    
    def test_get_user_gaming_profile_most_played(self, test_db_connection, sample_user_data, mock_steam_api):
        """Test most played games (50+ hours) in profile"""
        db_helper.cacheOwnedGames(
            sample_user_data['steamId'],
            mock_steam_api['owned_games']
        )
        
        profile = db_helper.getUserGamingProfile(sample_user_data['steamId'])
        
        assert len(profile['mostPlayedGames']) == 3
        assert profile['mostPlayedGames'][0][2] >= 50  # First game has 50+ hours
    
    def test_get_user_gaming_profile_empty(self, test_db_connection, sample_user_data):
        """Test gaming profile with no cached games"""
        profile = db_helper.getUserGamingProfile(sample_user_data['steamId'])
        
        assert profile['gameCount'] == 0
        assert profile['totalPlaytime'] == 0
        assert len(profile['topGames']) == 0


class TestGameDetailsCache:
    """Test game details caching"""
    
    def test_cache_game_details(self, test_db_connection, mock_steam_api):
        """Test caching game details"""
        result = db_helper.cacheGameDetails(
            '292030',
            mock_steam_api['game_details']
        )
        
        assert result is True
        
        cached = db_helper.getCachedGameDetails('292030')
        assert cached is not None
        assert cached['name'] == 'The Witcher 3: Wild Hunt'
    
    def test_get_cached_game_details_fresh(self, test_db_connection, mock_steam_api):
        """Test getting fresh cached game details"""
        db_helper.cacheGameDetails('292030', mock_steam_api['game_details'])
        
        cached = db_helper.getCachedGameDetails('292030', maxAgeHours=24)
        assert cached is not None
    
    def test_get_cached_game_details_expired(self, test_db_connection, mock_steam_api):
        """Test getting expired cached game details"""
        db_helper.cacheGameDetails('292030', mock_steam_api['game_details'])
        
        # Check with very short max age
        time.sleep(1.0)
        cached = db_helper.getCachedGameDetails('292030', maxAgeHours=0.0001)
        
        assert cached is None
    
    def test_get_cached_game_details_not_found(self, test_db_connection):
        """Test getting non-existent cached game"""
        cached = db_helper.getCachedGameDetails('99999')
        assert cached is None


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
    
    def test_get_user_recommendations(self, test_db_connection, sample_user_data, sample_game_data):
        """Test getting user recommendations"""
        db_helper.saveRecommendation(
            sample_user_data['steamId'],
            sample_game_data,
            'Great game!',
            92,
            ['RPG']
        )
        
        recommendations = db_helper.getUserRecommendations(sample_user_data['steamId'])
        
        assert len(recommendations) == 1
        assert recommendations[0]['title'] == sample_game_data['title']
        assert recommendations[0]['reasoning'] == 'Great game!'
    
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
    
    def test_get_recommendations_count(self, test_db_connection, sample_user_data, sample_game_data):
        """Test getting recommendation count"""
        initial_count = db_helper.getRecommendationsCount(sample_user_data['steamId'])
        assert initial_count == 0, f"Expected 0 recommendations initially, got {initial_count}"
        
        # Save one recommendation
        db_helper.saveRecommendation(
            sample_user_data['steamId'],
            sample_game_data,
            'Test',
            88
        )
        
        # Count should be 1
        count = db_helper.getRecommendationsCount(sample_user_data['steamId'])
        assert count == 1
    
    def test_get_recommended_game_ids(self, test_db_connection, sample_user_data, sample_game_data):
        """Test getting recommended game IDs"""
        db_helper.saveRecommendation(
            sample_user_data['steamId'],
            sample_game_data,
            'Test',
            88
        )
        
        game_ids = db_helper.getRecommendedGameIds(sample_user_data['steamId'])
        assert sample_game_data['gameId'] in game_ids


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
    
    def test_save_preference_disliked(self, test_db_connection, sample_user_data):
        """Test saving a disliked preference"""
        result = db_helper.savePreference(
            sample_user_data['steamId'],
            '730',
            'disliked'
        )
        
        assert result is True
        
        disliked_ids = db_helper.getPreferenceGameIds(sample_user_data['steamId'], 'disliked')
        assert '730' in disliked_ids
    
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
    
    def test_delete_preference(self, test_db_connection, sample_user_data):
        """Test deleting a preference"""
        db_helper.savePreference(sample_user_data['steamId'], '570', 'liked')
        
        result = db_helper.deletePreference(sample_user_data['steamId'], '570')
        assert result is True
        
        liked_ids = db_helper.getPreferenceGameIds(sample_user_data['steamId'], 'liked')
        assert '570' not in liked_ids
    
    def test_get_preference_game_ids_empty(self, test_db_connection, sample_user_data):
        """Test getting preferences when none exist"""
        liked_ids = db_helper.getPreferenceGameIds(sample_user_data['steamId'], 'liked')
        assert len(liked_ids) == 0


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
        # First save
        db_helper.saveFilterGenres(
            sample_user_data['steamId'],
            ['RPG', 'Action']
        )
        
        # Update with new genres
        new_genres = ['Horror', 'Survival']
        result = db_helper.saveFilterGenres(
            sample_user_data['steamId'],
            new_genres
        )
        
        assert result is True
        
        # Verify updated
        saved_genres = db_helper.getFilterGenres(sample_user_data['steamId'])
        assert saved_genres == new_genres
        assert 'RPG' not in saved_genres
    
    def test_save_filter_genres_empty_list(self, test_db_connection, sample_user_data):
        """Test saving empty genres list"""
        result = db_helper.saveFilterGenres(
            sample_user_data['steamId'],
            []
        )
        
        assert result is True
        
        saved_genres = db_helper.getFilterGenres(sample_user_data['steamId'])
        assert saved_genres == []
    
    def test_get_filter_genres_not_exists(self, test_db_connection, sample_user_data):
        """Test getting filter genres when none exist"""
        genres = db_helper.getFilterGenres(sample_user_data['steamId'])
        assert genres is None
    
    def test_get_filter_genres_invalid_steam_id(self, test_db_connection):
        """Test getting filter genres with invalid Steam ID"""
        genres = db_helper.getFilterGenres('invalid_steam_id')
        assert genres is None
    
    def test_delete_filter_genres(self, test_db_connection, sample_user_data):
        """Test deleting filter genres"""
        # First save
        db_helper.saveFilterGenres(
            sample_user_data['steamId'],
            ['RPG', 'Action']
        )
        
        # Delete
        result = db_helper.deleteFilterGenres(sample_user_data['steamId'])
        assert result is True
        
        # Verify deleted
        genres = db_helper.getFilterGenres(sample_user_data['steamId'])
        assert genres is None
    
    def test_delete_filter_genres_not_exists(self, test_db_connection, sample_user_data):
        """Test deleting filter genres when none exist"""
        result = db_helper.deleteFilterGenres(sample_user_data['steamId'])
        assert result is True  # Should succeed even if nothing to delete
    
    def test_filter_genres_multiple_users(self, test_db_connection, sample_user_data):
        """Test filter genres isolation between users"""
        steam_id_1 = sample_user_data['steamId']
        steam_id_2 = '76561197960287931'
        
        # Save user 2 first
        db_helper.saveUser(steam_id_2, 'User 2', '', '')
        
        # Save for user 1
        db_helper.saveFilterGenres(steam_id_1, ['RPG', 'Action'])
        
        # Save for user 2
        db_helper.saveFilterGenres(steam_id_2, ['Horror', 'Survival'])
        
        # Verify isolation
        genres_1 = db_helper.getFilterGenres(steam_id_1)
        genres_2 = db_helper.getFilterGenres(steam_id_2)
        
        assert genres_1 == ['RPG', 'Action']
        assert genres_2 == ['Horror', 'Survival']
    
    def test_filter_genres_special_characters(self, test_db_connection, sample_user_data):
        """Test filter genres with special characters"""
        genres = ['Action & Adventure', 'Sci-Fi', 'Story-Rich']
        
        result = db_helper.saveFilterGenres(
            sample_user_data['steamId'],
            genres
        )
        
        assert result is True
        
        saved_genres = db_helper.getFilterGenres(sample_user_data['steamId'])
        assert saved_genres == genres
    
    def test_filter_genres_unicode(self, test_db_connection, sample_user_data):
        """Test filter genres with unicode characters"""
        genres = ['アクション', '冒険', 'РПГ']
        
        result = db_helper.saveFilterGenres(
            sample_user_data['steamId'],
            genres
        )
        
        assert result is True
        
        saved_genres = db_helper.getFilterGenres(sample_user_data['steamId'])
        assert saved_genres == genres
    
    def test_filter_genres_very_long_list(self, test_db_connection, sample_user_data):
        """Test saving very long list of genres"""
        genres = [f"Genre{i}" for i in range(100)]
        
        result = db_helper.saveFilterGenres(
            sample_user_data['steamId'],
            genres
        )
        
        assert result is True
        
        saved = db_helper.getFilterGenres(sample_user_data['steamId'])
        assert len(saved) == 100
    
    def test_filter_genres_persistence(self, test_db_connection, sample_user_data):
        """Test that filter genres persist across connections"""
        genres = ['RPG', 'Action']
        
        # Save
        db_helper.saveFilterGenres(
            sample_user_data['steamId'],
            genres
        )
        
        # Simulate new connection by querying again
        saved = db_helper.getFilterGenres(sample_user_data['steamId'])
        
        assert saved == genres
    
    def test_filter_genres_duplicate_values(self, test_db_connection, sample_user_data):
        """Test saving genres with duplicates"""
        genres = ['RPG', 'Action', 'RPG', 'Action', 'RPG']
        
        result = db_helper.saveFilterGenres(
            sample_user_data['steamId'],
            genres
        )
        
        assert result is True
        
        # Should preserve duplicates
        saved = db_helper.getFilterGenres(sample_user_data['steamId'])
        assert saved == genres


class TestDatabaseErrorHandling:
    """Test error handling in database operations"""
    
    def test_save_user_invalid_data(self, test_db_connection):
        """Test saving user with invalid data"""
        with pytest.raises(Exception):
            db_helper.saveUser(None, None, None, None)
    
    def test_cache_owned_games_empty_list(self, test_db_connection, sample_user_data):
        """Test caching empty game list"""
        db_helper.cacheOwnedGames(sample_user_data['steamId'], [])
        
        game_ids = db_helper.getOwnedGamesIds(sample_user_data['steamId'])
        assert len(game_ids) == 0