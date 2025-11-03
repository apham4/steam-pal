import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from main import app, createJwtToken

client = TestClient(app)

class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    @patch('main.getUser')
    def test_get_current_user_authenticated(self, mock_get_user):
        """Test GET /api/auth/me with valid token"""
        token = createJwtToken(
            steamId="76561197960287930",
            displayName="Test User",
            avatarUrl="https://example.com/avatar.jpg"
        )
        
        mock_get_user.return_value = {
            "steamId": "76561197960287930",
            "displayName": "Test User",
            "avatarUrl": "https://example.com/avatar.jpg",
            "profileUrl": "https://steamcommunity.com/id/testuser/",
            "lastLogin": 1735689600
        }
        
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["steam_id"] == "76561197960287930"
        assert data["display_name"] == "Test User"
        assert data["avatar_url"] == "https://example.com/avatar.jpg"
        assert data["profile_url"] == "https://steamcommunity.com/id/testuser/"
        assert "last_login" in data



class TestRecommendationEndpoints:
    """Test recommendation endpoints"""

    @patch('main.saveRecommendation')
    @patch('main.generateSmartRecommendation')
    @patch('main.getPreferenceGameIds')
    @patch('main.getRecommendedGameIds')
    @patch('main.getOwnedGamesIds')
    @patch('main.getUserGamingProfile')
    @patch('main.isOwnedGamesCacheRecent')
    def test_get_recommendation_success(
        self,
        mock_cache_check,
        mock_get_profile,
        mock_owned_ids,
        mock_rec_ids,
        mock_pref_ids,
        mock_generate,
        mock_save
    ):
        """Test POST /api/recommendations"""
        # Create real token
        from main import createJwtToken
        token = createJwtToken(
            steamId="76561197960287930",
            displayName="Test User",
            avatarUrl=""
        )
        
        # Setup mocks
        mock_cache_check.return_value = True
        mock_get_profile.return_value = {
            "gameCount": 150,
            "totalPlaytime": 545,
            "topGames": [],
            "recentlyActiveGames": [],
            "mostPlayedGames": [],
            "favoriteGenres": ["RPG"]
        }
        mock_owned_ids.return_value = []
        mock_rec_ids.return_value = []
        mock_pref_ids.return_value = []
        
        mock_generate.return_value = {
            "game": {
                "gameId": "570",
                "title": "Dota 2",
                "thumbnail": "",
                "releaseDate": "",
                "publisher": "",
                "developer": "",
                "price": "",
                "salePrice": "",
                "description": ""
            },
            "reasoning": "Great MOBA game",
            "matchScore": 90
        }
        
        response = client.post(
            "/api/recommendations",
            json={"genres": ["Action"]},
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "game" in data
        assert "reasoning" in data
        assert data["game"]["gameId"] == "570"


class TestPreferenceEndpoints:
    """Test Preference Endpoints"""

    @patch('main.savePreference')
    def test_like_game(self, mock_save):
        """Test POST /api/preferences/{gameId}/like"""
        from main import createJwtToken
        token = createJwtToken(
            steamId="76561197960287930",
            displayName="Test User",
            avatarUrl=""
        )
        
        mock_save.return_value = True
        
        response = client.post(
            "/api/preferences/570/like",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["gameId"] == "570"
    
    @patch('main.getCachedGameDetails')
    @patch('main.getPreferenceGameIds')
    def test_get_liked_games(self, mock_get_pref_ids, mock_get_details):
        """Test GET /api/preferences/liked"""
        from main import createJwtToken
        token = createJwtToken(
            steamId="76561197960287930",
            displayName="Test User",
            avatarUrl=""
        )
        
        mock_get_pref_ids.return_value = ["570"]
        mock_get_details.return_value = {
            "steam_appid": 570,
            "name": "Dota 2",
            "header_image": "",
            "release_date": {"date": ""},
            "publishers": [],
            "developers": [],
            "price_overview": None,
            "short_description": ""
        }
        
        response = client.get(
            "/api/preferences/liked",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "games" in data
        assert "count" in data


class TestRecommendationHistoryEndpoints:
    """Test Recommendation History Endpoints"""

    @patch('main.getRecommendationsCount')
    @patch('main.getUserRecommendations')
    def test_get_history(self, mock_get_recs, mock_count):
        """Test GET /api/recommendations/history"""
        from main import createJwtToken
        token = createJwtToken(
            steamId="76561197960287930",
            displayName="Test User",
            avatarUrl=""
        )
        
        mock_get_recs.return_value = [
            {
                "id": 1,
                "steamId": "76561197960287930",
                "gameId": "570",
                "title": "Dota 2",
                "thumbnail": "",
                "releaseDate": "",
                "publisher": "",
                "developer": "",
                "price": "",
                "salePrice": "",
                "description": "",
                "reasoning": "Great game",
                "createdAt": 1234567890,
                "createdAtIso": "2009-02-13T23:31:30"
            }
        ]
        mock_count.return_value = 1
        
        response = client.get(
            "/api/recommendations/history?page=1&limit=20",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert len(data["recommendations"]) == 1
        assert data["total"] == 1


class TestAdvancedFilteringEndpoints:
    """Test Advanced Filtering Endpoints"""

    @patch('main.getFilterGenres')
    def test_get_filter_genres_exists(self, mock_get):
        """Test GET /api/filters/genres when preferences exist"""
        token = createJwtToken("76561197960287930", "Test User", "")
        
        mock_get.return_value = ["Horror", "Survival", "Co-op"]
        
        response = client.get(
            "/api/filters/genres",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["steam_id"] == "76561197960287930"
        assert data["saved_genres"] == ["Horror", "Survival", "Co-op"]

    @patch('main.getFilterGenres')
    def test_get_filter_genres_not_exists(self, mock_get):
        """Test GET /api/filters/genres when no preferences exist"""
        token = createJwtToken("76561197960287930", "Test User", "")
        
        mock_get.return_value = None
        
        response = client.get(
            "/api/filters/genres",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["saved_genres"] == []
    
    def test_get_filter_genres_unauthorized(self):
        """Test GET /api/filters/genres without authentication"""
        response = client.get("/api/filters/genres")
        assert response.status_code == 403

    @patch('main.getFilterGenres')
    def test_get_filter_genres_error_handling(self, mock_get):
        """Test GET /api/filters/genres handles database errors"""
        token = createJwtToken("76561197960287930", "Test User", "")
        
        mock_get.side_effect = Exception("Database error")
        
        response = client.get(
            "/api/filters/genres",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 500

    def test_get_available_genres_success(self):
        """Test GET /api/filters/available-genres returns all categories"""
        response = client.get("/api/filters/available-genres")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "genres" in data
        assert "tags" in data
        assert "modes" in data
        
        # Verify types
        assert isinstance(data["genres"], list)
        assert isinstance(data["tags"], list)
        assert isinstance(data["modes"], list)
        
        # Verify content
        assert "Action" in data["genres"]
        assert "Horror" in data["tags"]
        assert "Single-player" in data["modes"]

    def test_get_available_genres_no_auth_required(self):
        """Test GET /api/filters/available-genres doesn't require authentication"""
        response = client.get("/api/filters/available-genres")
        
        # Should succeed without Authorization header
        assert response.status_code == 200
    
    def test_get_available_genres_no_duplicates(self):
        """Test GET /api/filters/available-genres has no duplicate values"""
        response = client.get("/api/filters/available-genres")
        data = response.json()
        
        # Check no duplicates in each category
        assert len(data["genres"]) == len(set(data["genres"]))
        assert len(data["tags"]) == len(set(data["tags"]))
        assert len(data["modes"]) == len(set(data["modes"]))
    
    def test_get_available_genres_complete_lists(self):
        """Test GET /api/filters/available-genres returns expected values"""
        response = client.get("/api/filters/available-genres")
        data = response.json()
        
        # Check specific expected values
        expected_genres = ["Action", "Adventure", "Strategy"]
        expected_tags = ["Horror", "Sci-Fi", "Survival"]
        expected_modes = ["Single-player", "Multiplayer", "Co-op"]
        
        for genre in expected_genres:
            assert genre in data["genres"], f"Missing genre: {genre}"
        
        for tag in expected_tags:
            assert tag in data["tags"], f"Missing tag: {tag}"
        
        for mode in expected_modes:
            assert mode in data["modes"], f"Missing mode: {mode}"