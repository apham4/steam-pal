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
    
    @patch('game_recommender.getLLMHandler')
    def test_init_custom_provider(self, mock_get_llm):
        """Test initializing with custom provider"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        recommender = GameRecommender(llmProvider='custom')
        
        mock_get_llm.assert_called_once_with('custom')


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
    
    @patch('game_recommender.getLLMHandler')
    @patch('game_recommender.getCachedGameDetails')
    @patch('game_recommender.fetchGameDetailsWithRetry')
    @patch('game_recommender.cacheGameDetails')
    def test_get_game_details_cache_miss(self, mock_cache, mock_fetch, mock_get_cached, mock_get_llm):
        """Test fetching and caching when cache miss"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        # Cache miss
        mock_get_cached.return_value = None
        
        # Fetch from API
        game_data = {
            'steam_appid': '292030',
            'name': 'The Witcher 3'
        }
        mock_fetch.return_value = game_data
        
        recommender = GameRecommender()
        result = recommender._getGameDetails('292030')
        
        assert result is not None
        mock_fetch.assert_called_once_with('292030')
        mock_cache.assert_called_once_with('292030', game_data)
    
    @patch('game_recommender.getLLMHandler')
    @patch('game_recommender.getCachedGameDetails')
    @patch('game_recommender.fetchGameDetailsWithRetry')
    def test_get_game_details_fetch_fails(self, mock_fetch, mock_get_cached, mock_get_llm):
        """Test handling when API fetch fails"""
        mock_llm = Mock()
        mock_get_llm.return_value = mock_llm
        
        mock_get_cached.return_value = None
        mock_fetch.return_value = None
        
        recommender = GameRecommender()
        result = recommender._getGameDetails('99999')
        
        assert result is None


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
        mock_llm_response,
        mock_steam_api,        
        sample_game_data
    ):
        """Test successful recommendation generation"""
        # Setup LLM mock
        mock_llm = Mock()
        mock_llm.discoverGame.return_value = mock_llm_response
        mock_get_llm.return_value = mock_llm
        
        # Setup Steam API mock
        mock_fetch.return_value = mock_steam_api['game_details']
        mock_transform.return_value = sample_game_data
        
        recommender = GameRecommender()
        result = recommender.generateRecommendation(
            steamId='76561197960287930',
            gamingProfile=sample_gaming_profile,
            requestedGenres=['RPG'],
            excludeGameIds={'570', '730'}
        )
        
        assert result is not None
        assert 'game' in result
        assert 'reasoning' in result
        assert result['game']['title'] == sample_game_data['title']
        assert result['reasoning'] == mock_llm_response['reasoning']
    
    @patch('game_recommender.getLLMHandler')
    def test_generate_recommendation_llm_fails(self, mock_get_llm, sample_gaming_profile):
        """Test handling when LLM fails to generate recommendation"""
        mock_llm = Mock()
        mock_llm.discoverGame.return_value = None
        mock_get_llm.return_value = mock_llm
        
        recommender = GameRecommender()
        result = recommender.generateRecommendation(
            steamId='76561197960287930',
            gamingProfile=sample_gaming_profile,
            requestedGenres=[],
            excludeGameIds=set()
        )
        
        assert result is None
    
    @patch('game_recommender.getLLMHandler')
    @patch('game_recommender.fetchGameDetailsWithRetry')
    def test_generate_recommendation_game_fetch_fails(
        self,
        mock_fetch,
        mock_get_llm,
        sample_gaming_profile,
        mock_llm_response
    ):
        """Test handling when game details fetch fails"""
        mock_llm = Mock()
        mock_llm.discoverGame.return_value = mock_llm_response
        mock_get_llm.return_value = mock_llm
        
        # Game fetch fails
        mock_fetch.return_value = None
        
        recommender = GameRecommender()
        result = recommender.generateRecommendation(
            steamId='76561197960287930',
            gamingProfile=sample_gaming_profile,
            requestedGenres=['RPG'],
            excludeGameIds=set()
        )

        assert result is not None


class TestPublicAPI:
    """Test public API function"""
    
    @patch('game_recommender.GameRecommender')
    def test_generate_smart_recommendation_calls_recommender(
        self,
        mock_recommender_class,
        sample_gaming_profile
    ):
        """Test that public API correctly calls GameRecommender"""
        mock_recommender = Mock()
        mock_recommender.generateRecommendation.return_value = {
            'game': {'title': 'Test Game'},
            'reasoning': 'Great game!'
        }
        mock_recommender_class.return_value = mock_recommender
        
        result = generateSmartRecommendation(
            steamId='76561197960287930',
            gamingProfile=sample_gaming_profile,
            requestedGenres=['RPG'],
            excludeGameIds={'570'}
        )
        
        assert result is not None
        mock_recommender.generateRecommendation.assert_called_once_with(
            steamId='76561197960287930',
            gamingProfile=sample_gaming_profile,
            requestedGenres=['RPG'],
            excludeGameIds={'570'}
        )


class TestRecommenderEdgeCases:
    """Test edge cases and error conditions"""
    
    @patch('game_recommender.getLLMHandler')
    def test_generate_recommendation_empty_profile(self, mock_get_llm):
        """Test recommendation with empty gaming profile"""
        mock_llm = Mock()
        mock_llm.discoverGame.return_value = None
        mock_get_llm.return_value = mock_llm
        
        empty_profile = {
            'topGames': [],
            'totalPlaytime': 0,
            'recentlyActiveGames': [],
            'mostPlayedGames': [],
            'favoriteGenres': [],
            'gameCount': 0
        }
        
        recommender = GameRecommender()
        result = recommender.generateRecommendation(
            steamId='76561197960287930',
            gamingProfile=empty_profile,
            requestedGenres=[],
            excludeGameIds=set()
        )
        
        # Should still attempt to generate
        assert result is None
        mock_llm.discoverGame.assert_called_once()
    
    @patch('game_recommender.getLLMHandler')
    def test_generate_recommendation_large_exclude_set(self, mock_get_llm, sample_gaming_profile):
        """Test recommendation with large exclude set"""
        mock_llm = Mock()
        mock_llm.discoverGame.return_value = None
        mock_get_llm.return_value = mock_llm
        
        large_exclude_set = {str(i) for i in range(1000)}
        
        recommender = GameRecommender()
        result = recommender.generateRecommendation(
            steamId='76561197960287930',
            gamingProfile=sample_gaming_profile,
            requestedGenres=[],
            excludeGameIds=large_exclude_set
        )
        
        # Should handle large sets without error
        mock_llm.discoverGame.assert_called_once()