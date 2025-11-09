"""
Integration tests for the recommendation workflow
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app, createJwtToken
from db_helper import *

client = TestClient(app)

class TestRecommendationGeneration:
    """Test for recommendation generation workflow"""

    @patch('main.generateSmartRecommendation')
    def test_new_user_receives_personalized_recommendation(
        self,
        mock_generate_recommendation,
        test_db_connection,
        sample_user_data,
        sample_owned_games
    ):
        """
        Test new user receives recommendation based on their gaming profile
        """

        steamId = sample_user_data['steamId']

        # Setup: User logs in
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
        
        print(f"\nUser setup: {steamId} with {len(sample_owned_games)} owned games")

        ## Mock recommendation response 
        mock_generate_recommendation.return_value = {
            'game': {
                'gameId': '440',
                'title': 'Team Fortress 2',
                'thumbnail': 'https://cdn.akamai.steamstatic.com/steam/apps/440/header.jpg',
                'releaseDate': 'Oct 10, 2007',
                'publisher': 'Valve',
                'developer': 'Valve',
                'price': 'Free to Play',
                'salePrice': '',
                'description': 'Team-based multiplayer FPS game'
            },
            'reasoning': 'Based on your CS:GO experience, this team-based FPS is perfect.',
            'matchScore': 92,
            'similarTo': ['Counter-Strike: Global Offensive', 'Overwatch']
        }

        # User requests recommendation
        response = client.post(
            "/api/recommendations",
            headers={"Authorization": f"Bearer {token}"},
            json={"genres": ["Action", "Multiplayer"]}
        )

        # Verify API response
        assert response.status_code == 200, f"Request failed: {response.json()}"
        data = response.json()
        assert data["game"]["gameId"] == "440"
        assert data["game"]["title"] == "Team Fortress 2"
        assert "reasoning" in data
        print(f"Recommendation received: {data['game']['title']}")

        # Verify generateSmartRecommendation was called
        assert mock_generate_recommendation.called
        call_kwargs = mock_generate_recommendation.call_args[1]
        
        # Verify LLM received gaming profile
        assert 'gamingProfile' in call_kwargs
        profile = call_kwargs['gamingProfile']
        assert profile['gameCount'] == 3
        assert profile['totalPlaytime'] > 0
        print(f"LLM received gaming profile: {profile['gameCount']} games, {profile['totalPlaytime']}h")
        
        # Verify owned games excluded
        assert 'excludeGameIds' in call_kwargs
        exclude_ids = call_kwargs['excludeGameIds']
        assert '292030' in exclude_ids  # Witcher 3
        assert '730' in exclude_ids     # CS:GO
        assert '570' in exclude_ids     # Dota 2
        print(f"LLM excluded {len(exclude_ids)} owned games")
        
        # Verify LLM received requested genres
        assert 'requestedGenres' in call_kwargs
        assert call_kwargs['requestedGenres'] == ["Action", "Multiplayer"]
        print(f"LLM received genres: {call_kwargs['requestedGenres']}")

        # Verify recommendation saved in history
        history = getUserRecommendations(steamId, limit=10, offset=0)
        assert len(history) == 1
        assert history[0]["gameId"] == "440"
        print(f"Recommendation saved to history")
        
        saved_genres = getFilterGenres(steamId)
        assert saved_genres == ["Action", "Multiplayer"]
        print(f"Genres auto-saved")

        print(f"\nTest PASSED: New user recommendation workflow")

class TestExclusionLogic:
    """Test for exclusion list accumulation across user actions"""
    
    @patch('main.generateSmartRecommendation')
    def test_exclusion_list_accumulates_across_actions(
        self,
        mock_generate_recommendation,
        test_db_connection,
        sample_user_data,
        sample_owned_games
    ):
        """
        Test exclusion list grows as user interacts with system
        """

        steamId = sample_user_data['steamId']
        
        # Setup
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
        
        print(f"\nUser setup: {steamId}")

        # Mock return different games for each call
        mock_generate_recommendation.side_effect = [
            {
                'game': {
                    'gameId': '440',
                    'title': 'Team Fortress 2',
                    'thumbnail': 'https://cdn.akamai.steamstatic.com/steam/apps/440/header.jpg',
                    'releaseDate': 'Oct 10, 2007',
                    'publisher': 'Valve',
                    'developer': 'Valve',
                    'price': 'Free to Play',
                    'salePrice': '',
                    'description': 'Team-based FPS'
                },
                'reasoning': 'Great multiplayer game',
                'matchScore': 85,
                'similarTo': ['Counter-Strike']
            },
            {
                'game': {
                    'gameId': '999',
                    'title': 'Strategy Game',
                    'thumbnail': 'https://cdn.akamai.steamstatic.com/steam/apps/999/header.jpg',
                    'releaseDate': 'Jan 1, 2020',
                    'publisher': 'Publisher',
                    'developer': 'Developer',
                    'price': '$29.99',
                    'salePrice': '',
                    'description': 'Strategy game'
                },
                'reasoning': 'Strategic gameplay',
                'matchScore': 80,
                'similarTo': ['Civilization']
            },
            {
                'game': {
                    'gameId': '777',
                    'title': 'RPG Game',
                    'thumbnail': 'https://cdn.akamai.steamstatic.com/steam/apps/777/header.jpg',
                    'releaseDate': 'Mar 15, 2021',
                    'publisher': 'RPG Publisher',
                    'developer': 'RPG Dev',
                    'price': '$39.99',
                    'salePrice': '$19.99',
                    'description': 'Epic RPG'
                },
                'reasoning': 'Story-driven RPG',
                'matchScore': 88,
                'similarTo': ['Skyrim']
            }
        ]

        # Phase 1: Initial exclusion (owned games only)
        print(f"\nPhase 1: Initial recommendation")
        response1 = client.post(
            "/api/recommendations",
            headers={"Authorization": f"Bearer {token}"},
            json={"genres": ["Action"]}
        )
        assert response1.status_code == 200, f"Phase 1 failed: {response1.json()}"

        call1_kwargs = mock_generate_recommendation.call_args_list[0][1]
        exclude1 = set(call1_kwargs['excludeGameIds'])
        
        assert '292030' in exclude1  # Witcher 3 (owned)
        assert '730' in exclude1     # CS:GO (owned)
        assert '570' in exclude1     # Dota 2 (owned)
        assert len(exclude1) == 3
        print(f"Excluded {len(exclude1)} owned games")

        # PHASE 2: After recommendation (owned + past)
        print(f"\nPhase 2: Second recommendation")

        response2 = client.post(
            "/api/recommendations",
            headers={"Authorization": f"Bearer {token}"},
            json={"genres": ["Strategy"]}
        )
        assert response2.status_code == 200, f"Phase 2 failed: {response2.json()}"
        
        call2_kwargs = mock_generate_recommendation.call_args_list[1][1]
        exclude2 = set(call2_kwargs['excludeGameIds'])

        assert '292030' in exclude2  # Owned
        assert '730' in exclude2     # Owned
        assert '570' in exclude2     # Owned
        assert '440' in exclude2     # Past recommendation
        assert len(exclude2) == 4
        print(f"Excluded {len(exclude2)} games (owned + past)")

        # PHASE 3: After dislike (owned + past + disliked)
        print(f"\nPhase 3: After dislike")
        
        client.post(
            f"/api/preferences/888/dislike",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        response3 = client.post(
            "/api/recommendations",
            headers={"Authorization": f"Bearer {token}"},
            json={"genres": ["RPG"]}
        )
        assert response3.status_code == 200, f"Phase 3 failed: {response3.json()}"

        call3_kwargs = mock_generate_recommendation.call_args_list[2][1]
        exclude3 = set(call3_kwargs['excludeGameIds'])
        
        assert '292030' in exclude3  # Owned
        assert '730' in exclude3     # Owned
        assert '570' in exclude3     # Owned
        assert '440' in exclude3     # Past rec 1
        assert '999' in exclude3     # Past rec 2
        assert '888' in exclude3     # Disliked
        assert len(exclude3) == 6
        print(f"Excluded {len(exclude3)} games (owned + past + disliked)")

        print(f"\nTest PASSED: Exclusion accumulation workflow")