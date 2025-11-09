"""
Unit tests for Pydantic validation
"""

import sys
import pytest
import json
from pydantic import ValidationError
from models import RecommendationRequest, GameDetail, Recommendation, FilterGenresResponse
from pathlib import Path

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BACKEND_DIR))

class TestRecommendationRequest:
    """Test RecommendationRequest model validation"""
    
    def test_recommendation_request_with_genres(self):
        """Test creating request with genres"""
        request = RecommendationRequest(
            genres=['RPG', 'Action']
        )
        
        assert request.genres == ['RPG', 'Action']
    
    def test_recommendation_request_empty_genres(self):
        """Test creating request with empty genres"""
        request = RecommendationRequest(genres=[])
        assert request.genres == []
    
    def test_recommendation_request_default(self):
        """Test creating request with defaults"""
        request = RecommendationRequest()
        assert request.genres == []


class TestGameDetail:
    """Test GameDetail model validation"""

    def test_game_detail_complete(self):
        """Test creating complete game detail"""
        game = GameDetail(
            gameId='292030',
            title='The Witcher 3: Wild Hunt',
            thumbnail='https://example.com/image.jpg',
            releaseDate='May 18, 2015',
            publisher='CD PROJEKT RED',
            developer='CD PROJEKT RED',
            price='$39.99',
            salePrice='$9.99',
            description='As war rages on...'
        )
        
        assert game.gameId == '292030'
        assert game.title == 'The Witcher 3: Wild Hunt'
        assert game.salePrice == '$9.99'
    
    def test_game_detail_minimal(self):
        """Test creating minimal game detail"""
        game = GameDetail(
            gameId='12345',
            title='Test Game'
        )
        
        assert game.gameId == '12345'
        assert game.title == 'Test Game'
        assert game.thumbnail == ''
        assert game.price == ''


class TestRecommendation:
    """Test Recommendation model validation"""
    
    def test_recommendation_complete(self, sample_game_data):
        """Test creating complete recommendation"""
        game = GameDetail(**sample_game_data)
        
        recommendation = Recommendation(
            game=game,
            reasoning='This game is perfect for you based on your playtime in similar games.'
        )
        
        assert recommendation.game.title == sample_game_data['title']
        assert recommendation.reasoning.startswith('This game is perfect')


class TestFilterGenresModel:
    """Test FilterGenres response model"""
    
    def test_filter_genres_response_complete(self):
        """Test creating complete filter genres response"""
        
        response = FilterGenresResponse(
            steamId='76561197960287930',
            savedGenres=['Horror', 'Survival', 'Co-op']
        )
        
        assert response.steamId == '76561197960287930'
        assert response.savedGenres == ['Horror', 'Survival', 'Co-op']
    
    def test_filter_genres_response_serialization(self):
        """Test response serialization with aliases"""
        
        response = FilterGenresResponse(
            steamId='76561197960287930',
            savedGenres=['RPG']
        )
        
        serialized = response.model_dump(by_alias=True)
        
        assert 'steam_id' in serialized
        assert 'saved_genres' in serialized
        assert serialized['steam_id'] == '76561197960287930'
        assert serialized['saved_genres'] == ['RPG']
        

class TestModelEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_recommendation_request_invalid_type(self):
        """Test creating request with invalid genres type"""
        with pytest.raises(ValidationError):
            RecommendationRequest(genres="RPG")  # Should be list
