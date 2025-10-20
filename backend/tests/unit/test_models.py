import sys
import pytest
from pydantic import ValidationError
from models import RecommendationRequest, GameDetail, Recommendation
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
    
    def test_recommendation_request_invalid_type(self):
        """Test creating request with invalid genres type"""
        with pytest.raises(ValidationError):
            RecommendationRequest(genres="RPG")  # Should be list


class TestGameDetail:
    """Test GameDetail model validation"""
    
    def test_game_detail_with_defaults(self):
        """Test that GameDetail uses default values for missing fields"""
        game = GameDetail()
    
        # Verify all fields have default empty string values
        assert game.gameId == ""
        assert game.title == ""
        assert game.thumbnail == ""
        assert game.releaseDate == ""
        assert game.publisher == ""
        assert game.developer == ""
        assert game.price == ""
        assert game.salePrice == ""
        assert game.description == ""
        assert game.id == ""

        # Verify it can be created with partial data
        partial_game = GameDetail(gameId="12345", title="Test Game")
        assert partial_game.gameId == "12345"
        assert partial_game.title == "Test Game"
        assert partial_game.price == "" 
        assert partial_game.id == "12345"

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
    
    def test_game_detail_type_coercion(self):
        """Test type coercion for numeric gameId"""
        game = GameDetail(
            gameId=292030,  # Integer instead of string
            title='The Witcher 3'
        )
        
        assert game.gameId == '292030'  # Should be coerced to string


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
    
    def test_recommendation_missing_fields(self, sample_game_data):
        """Test creating recommendation without required fields"""
        game = GameDetail(**sample_game_data)
        
        with pytest.raises(ValidationError):
            Recommendation(game=game)  # Missing reasoning
        
        with pytest.raises(ValidationError):
            Recommendation(reasoning='Great game!')  # Missing game
    
    def test_recommendation_json_serialization(self, sample_game_data):
        """Test JSON serialization"""
        game = GameDetail(**sample_game_data)
        recommendation = Recommendation(
            game=game,
            reasoning='Test reasoning'
        )
        
        json_data = recommendation.model_dump()
        
        assert 'game' in json_data
        assert 'reasoning' in json_data
        assert json_data['game']['title'] == sample_game_data['title']


class TestModelEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_empty_string_fields(self):
        """Test models with empty string fields"""
        game = GameDetail(
            gameId='',
            title=''
        )
        
        assert game.gameId == ''
        assert game.title == ''
    
    def test_special_characters_in_strings(self):
        """Test models with special characters"""
        game = GameDetail(
            gameId='12345',
            title='Test™ Game® with <special> "characters"',
            description='Line 1\nLine 2\tTabbed'
        )
        
        assert '™' in game.title
        assert '\n' in game.description
    
    def test_very_long_strings(self):
        """Test models with very long strings"""
        long_description = 'A' * 10000
        
        game = GameDetail(
            gameId='12345',
            title='Test Game',
            description=long_description
        )
        
        assert len(game.description) == 10000