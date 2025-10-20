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