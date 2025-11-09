"""
Unit tests for recommendation logic
"""

import sys
import pytest
from unittest.mock import Mock, patch, MagicMock
from game_recommender import GameRecommender, generateSmartRecommendation
from pathlib import Path

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BACKEND_DIR))

class TestGameRecommenderInitialization:
    """Test GameRecommender initialization"""
    
    @patch('game_recommender.getLLMHandler')
    def test_init_default_provider(self, mock_get_llm):
        """Test initializing with default provider"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        recommender = GameRecommender()
        
        assert recommender.llm == mock_llm
        mock_get_llm.assert_called_once_with('gemini')


class TestGameDetailsRetrieval:
    """Test game details retrieval with caching"""
    
    @patch('game_recommender.getLLMHandler')
    @patch('game_recommender.getCachedGameDetails')
    def test_get_game_details_from_cache(self, mock_get_cached, mock_get_llm):
        """Test retrieving game details from cache"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        mock_get_cached.return_value = {
            'steam_appid': '292030',
            'name': 'The Witcher 3'
        }
        
        recommender = GameRecommender()
        result = recommender._getGameDetails('292030')
        
        assert result is not None
        assert result['name'] == 'The Witcher 3'
        mock_get_cached.assert_called_once_with('292030')


class TestRecommendationGeneration:
    """Test recommendation generation workflow"""
    
    @patch('game_recommender.getLLMHandler')
    @patch('game_recommender.fetchGameDetailsWithRetry')
    @patch('game_recommender.transformGameData')
    def test_generate_recommendation_success(
        self, 
        mock_transform,
        mock_fetch,
        mock_get_llm,
        sample_gaming_profile,          
        sample_game_data
    ):
        """Test successful recommendation generation"""
        # Setup LLM mock
        mock_llm = Mock()
        mock_llm.discoverGame.return_value = {
            'gameId': '570',
            'title': 'Dota 2',
            'reasoning': 'Great MOBA game',
            'matchScore': 90
        }
        mock_get_llm.return_value = mock_llm
        
        # Setup Steam API mock
        mock_fetch.return_value = {'name': 'Dota 2'}
        mock_transform.return_value = sample_game_data
        
        recommender = GameRecommender()
        result = recommender.generateRecommendation(
            gamingProfile=sample_gaming_profile,
            requestedGenres=['Action'],
            excludeGameIds=set(),
            logPrefix='Test'
        )
        
        assert result is not None
        assert result['game'] == sample_game_data
        assert result['reasoning'] == 'Great MOBA game'
        assert result['matchScore'] == 90
    
    @patch('game_recommender.getLLMHandler')
    def test_generate_recommendation_llm_fails(self, mock_get_llm, sample_gaming_profile):
        """Test handling when LLM fails to generate recommendation"""
        mock_llm = Mock()
        mock_llm.discoverGame.return_value = None
        mock_get_llm.return_value = mock_llm
        
        recommender = GameRecommender()
        result = recommender.generateRecommendation(
            gamingProfile=sample_gaming_profile,
            requestedGenres=[],
            excludeGameIds=set(),
            logPrefix='Test',
            maxRetries=2
        )
        
        assert result is None
    

class TestAIValidationAndRetryLogic:
    """Test AI validation and retry mechanisms"""
    
    @patch('game_recommender.transformGameData')
    @patch('game_recommender.getCachedGameDetails')
    @patch('game_recommender.fetchGameDetailsWithRetry')
    @patch('game_recommender.cacheGameDetails')
    @patch('game_recommender.getLLMHandler')
    def test_title_mismatch_triggers_retry(
        self,
        mock_get_llm,
        mock_cache,
        mock_fetch,
        mock_get_cached,
        mock_transform,
        sample_gaming_profile,
        sample_game_data
    ):
        """Test that title mismatch between AI and Steam triggers retry"""
        mock_llm = Mock()
        
        # First attempt: AI suggests title that won't match Steam's normalized title
        wrong_response = {
            'gameId': '292030',
            'title': 'Completely Different Game',  # Won't match "The Witcher 3"
            'reasoning': 'Great RPG',
            'matchScore': 90
        }
        
        # Second attempt: Correct title
        correct_response = {
            'gameId': '570',
            'title': 'Dota 2',
            'reasoning': 'Great MOBA',
            'matchScore': 85
        }
        
        mock_llm.discoverGame.side_effect = [wrong_response, correct_response]
        mock_get_llm.return_value = mock_llm
        
        # Mock cache misses
        mock_get_cached.return_value = None
        
        # Mock Steam API responses
        mock_fetch.side_effect = [
            {'name': 'The Witcher 3: Wild Hunt'},  # Doesn't match "Completely Different Game"
            {'name': 'Dota 2'}  # Matches
        ]
        mock_transform.return_value = sample_game_data
        
        recommender = GameRecommender()
        result = recommender.generateRecommendation(
            gamingProfile=sample_gaming_profile,
            requestedGenres=['RPG'],
            excludeGameIds=set(),
            logPrefix='Test'
        )
        
        # Should succeed on second attempt
        assert result is not None
        assert mock_llm.discoverGame.call_count == 2
        assert mock_fetch.call_count == 2