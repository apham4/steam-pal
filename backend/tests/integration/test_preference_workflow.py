"""
Integration tests for user preference workflow
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app, createJwtToken
from db_helper import saveUser, cacheOwnedGames, getPreferenceGameIds

client = TestClient(app)

class TestPreferenceIntegration:
    """Tests for preference system integration"""
    
    def test_like_dislike_crud_operations(self, test_db_connection, sample_user_data):
        """Test like/dislike CRUD operations work correctly"""
        steamId = sample_user_data['steamId']
        token = createJwtToken(
            steamId,
            sample_user_data['displayName'],
            sample_user_data['avatarUrl']
        )
        
        saveUser(
            steamId,
            sample_user_data['displayName'],
            sample_user_data['avatarUrl'],
            sample_user_data['profileUrl']
        )
        
        # Like a game
        response = client.post(
            "/api/preferences/440/like",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        liked_ids = getPreferenceGameIds(steamId, 'liked')
        assert '440' in liked_ids
        
        # Change to dislike
        response = client.post(
            "/api/preferences/440/dislike",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        
        liked_ids = getPreferenceGameIds(steamId, 'liked')
        disliked_ids = getPreferenceGameIds(steamId, 'disliked')
        
        assert '440' not in liked_ids
        assert '440' in disliked_ids
        
        print(f"Test PASSED: Preference CRUD operations")
    
    @patch('main.generateSmartRecommendation')
    def test_liked_games_excluded_via_recommendation_history(
        self,
        mock_generate_recommendation,
        test_db_connection,
        sample_user_data,
        sample_owned_games,
    ):
        """Test liked games are excluded in future recommendations"""
        steamId = sample_user_data['steamId']
        token = createJwtToken(
            steamId,
            sample_user_data['displayName'],
            sample_user_data['avatarUrl']
        )
        
        saveUser(
            steamId,
            sample_user_data['displayName'],
            sample_user_data['avatarUrl'],
            sample_user_data['profileUrl']
        )
        
        cacheOwnedGames(steamId, sample_owned_games)

        # Mock recommendations
        mock_generate_recommendation.side_effect = [
            {
                'game': {
                    'gameId': '440',
                    'title': 'Team Fortress 2',
                    'thumbnail': 'https://cdn.akamai.steamstatic.com/steam/apps/440/header.jpg',
                    'releaseDate': 'Oct 10, 2007',
                    'publisher': 'Valve',
                    'developer': 'Valve',
                    'price': 'Free',
                    'salePrice': '',
                    'description': 'Great multiplayer shooter'
                },
                'reasoning': 'Based on your gaming profile',
                'matchScore': 85,
                'similarTo': ['Counter-Strike']
            },
            {
                'game': {
                    'gameId': '999',
                    'title': 'Other Game',
                    'thumbnail': 'https://cdn.akamai.steamstatic.com/steam/apps/999/header.jpg',
                    'releaseDate': 'Jan 1, 2020',
                    'publisher': 'Test Publisher',
                    'developer': 'Test Developer',
                    'price': '$19.99',
                    'salePrice': '',
                    'description': 'Different recommendation'
                },
                'reasoning': 'Based on your preferences',
                'matchScore': 80,
                'similarTo': ['Action Game']
            }
        ]
        
        # Get first recommendation
        response1 = client.post(
            "/api/recommendations",
            headers={"Authorization": f"Bearer {token}"},
            json={"genres": ["Action"]}
        )
        
        assert response1.status_code == 200, f"First recommendation failed: {response1.json()}"
        data1 = response1.json()
        assert data1['game']['gameId'] == '440'
        
        # User likes the first recommendation
        like_response = client.post(
            "/api/preferences/440/like",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert like_response.status_code == 200
        
        # Get second recommendation
        response2 = client.post(
            "/api/recommendations",
            headers={"Authorization": f"Bearer {token}"},
            json={"genres": ["Action"]}
        )
        
        assert response2.status_code == 200, f"Second recommendation failed: {response2.json()}"
        data2 = response2.json()
        
        # Verify generateSmartRecommendation was called twice
        assert mock_generate_recommendation.call_count == 2, "Recommendation should be called twice"
        
        # Check second call's exclude list
        second_call_kwargs = mock_generate_recommendation.call_args_list[1][1]
        exclude_ids = second_call_kwargs['excludeGameIds']
        
        # Game 440 should be excluded in second call (from recommendation history)
        assert '440' in exclude_ids, "Previously recommended game should be excluded"
        
        # Verify second recommendation is different
        assert data2['game']['gameId'] == '999', "Second recommendation should be different game"

        print(f"Tests PASSED: Liked games excluded in future recommendations")