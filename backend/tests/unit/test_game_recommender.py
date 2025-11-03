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
    
    @patch('game_recommender.fetchGameDetailsWithRetry')
    @patch('game_recommender.getLLMHandler')
    def test_generate_recommendation_game_fetch_fails(
        self,
        mock_get_llm,
        mock_fetch,
        sample_gaming_profile
    ):
        """Test handling when game details cannot be fetched"""
        mock_llm = Mock()
        mock_llm.discoverGame.return_value = {
            'gameId': '999',
            'title': 'Unknown Game',
            'reasoning': 'Test',
            'matchScore': 85
        }
        mock_get_llm.return_value = mock_llm
        
        mock_fetch.return_value = None
        
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
    
    @patch('game_recommender.transformGameData')
    @patch('game_recommender.getCachedGameDetails')
    @patch('game_recommender.fetchGameDetailsWithRetry')
    @patch('game_recommender.cacheGameDetails')
    @patch('game_recommender.getLLMHandler')
    def test_steam_api_failure_triggers_retry(
        self,
        mock_get_llm,
        mock_cache,
        mock_fetch,
        mock_get_cached,
        mock_transform,
        sample_gaming_profile,
        sample_game_data
    ):
        """Test that Steam API failure triggers retry"""
        mock_llm = Mock()
        
        # AI suggests valid games
        mock_llm.discoverGame.side_effect = [
            {'gameId': '999', 'title': 'Game 1', 'reasoning': 'Test', 'matchScore': 90},
            {'gameId': '570', 'title': 'Dota 2', 'reasoning': 'Test', 'matchScore': 85}
        ]
        mock_get_llm.return_value = mock_llm
        
        # Mock cache misses
        mock_get_cached.return_value = None
        
        # First fetch fails, second succeeds
        mock_fetch.side_effect = [
            None,  # API failure
            {'name': 'Dota 2'}  # Success
        ]
        mock_transform.return_value = sample_game_data
        
        recommender = GameRecommender()
        result = recommender.generateRecommendation(
            gamingProfile=sample_gaming_profile,
            requestedGenres=[],
            excludeGameIds=set(),
            logPrefix='Test',
            maxRetries=3
        )
        
        assert result is not None
        assert mock_fetch.call_count == 2
        assert mock_llm.discoverGame.call_count == 2
    
    @patch('game_recommender.getLLMHandler')
    def test_max_retries_exhausted(self, mock_get_llm, sample_gaming_profile):
        """Test that function returns None after max retries"""
        mock_llm = Mock()
        mock_llm.discoverGame.return_value = None  # Always fails
        mock_get_llm.return_value = mock_llm
        
        recommender = GameRecommender()
        result = recommender.generateRecommendation(
            gamingProfile=sample_gaming_profile,
            requestedGenres=[],
            excludeGameIds=set(),
            logPrefix='Test',
            maxRetries=3
        )
        
        assert result is None
        assert mock_llm.discoverGame.call_count == 3
    
    @patch('game_recommender.transformGameData')
    @patch('game_recommender.getCachedGameDetails')
    @patch('game_recommender.fetchGameDetailsWithRetry')
    @patch('game_recommender.cacheGameDetails')
    @patch('game_recommender.getLLMHandler')
    def test_excluded_game_added_after_failure(
        self,
        mock_get_llm,
        mock_cache,
        mock_fetch,
        mock_get_cached,
        mock_transform,
        sample_gaming_profile,
        sample_game_data
    ):
        """Test that failed game IDs are added to exclusion set"""
        mock_llm = Mock()
        
        initial_exclude = {'123'}
        
        # First: Suggest game with mismatched title
        # Second: Suggest valid game
        mock_llm.discoverGame.side_effect = [
            {'gameId': '999', 'title': 'Bad Game', 'reasoning': 'Test', 'matchScore': 90},
            {'gameId': '570', 'title': 'Dota 2', 'reasoning': 'Test', 'matchScore': 85}
        ]
        mock_get_llm.return_value = mock_llm
        
        # Mock cache misses
        mock_get_cached.return_value = None
        
        mock_fetch.side_effect = [
            {'name': 'Completely Different Name'},  # Mismatch
            {'name': 'Dota 2'}  # Match
        ]
        mock_transform.return_value = sample_game_data
        
        recommender = GameRecommender()
        result = recommender.generateRecommendation(
            gamingProfile=sample_gaming_profile,
            requestedGenres=[],
            excludeGameIds=initial_exclude,
            logPrefix='Test'
        )
        
        # Verify second call includes excluded game from first attempt
        second_call_excludes = mock_llm.discoverGame.call_args_list[1][1]['excludeGameIds']
        assert '999' in second_call_excludes
        assert '123' in second_call_excludes
    
    def test_normalize_title_removes_special_chars(self):
        """Test title normalization removes special characters"""
        recommender = GameRecommender()
        
        assert recommender.normalizeTitle("The Witcher 3: Wild Hunt") == "thewitcher3wildhunt"
        assert recommender.normalizeTitle("Portal 2") == "portal2"
        assert recommender.normalizeTitle("Half-Life: Alyx") == "halflifealyx"
    
    def test_normalize_title_case_insensitive(self):
        """Test title normalization is case insensitive"""
        recommender = GameRecommender()
        
        assert recommender.normalizeTitle("DOOM") == "doom"
        assert recommender.normalizeTitle("dOoM") == "doom"
        assert recommender.normalizeTitle("Doom") == "doom"


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
            gamingProfile=sample_gaming_profile,
            requestedGenres=['RPG'],
            excludeGameIds={'570'},
            logPrefix='Test'
        )
        
        assert result is not None
        mock_recommender.generateRecommendation.assert_called_once_with(
            gamingProfile=sample_gaming_profile,
            requestedGenres=['RPG'],
            excludeGameIds={'570'},
            logPrefix='Test'
        )


class TestRecommenderEdgeCases:
    """Test edge cases and error conditions"""
    
    @patch('game_recommender.transformGameData')
    @patch('game_recommender.fetchGameDetailsWithRetry')
    @patch('game_recommender.getLLMHandler')
    def test_generate_recommendation_empty_profile(
        self,
        mock_get_llm,
        mock_fetch,
        mock_transform,
        sample_game_data
    ):
        """Test recommendation with empty gaming profile"""
        mock_llm = Mock()
        mock_llm.discoverGame.return_value = {
            'gameId': '570',
            'title': 'Dota 2',
            'reasoning': 'Great game',
            'matchScore': 85
        }
        mock_get_llm.return_value = mock_llm
        
        mock_fetch.return_value = {'name': 'Dota 2'}
        mock_transform.return_value = sample_game_data
        
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
            gamingProfile=empty_profile,
            requestedGenres=[],
            excludeGameIds=set(),
            logPrefix='Test'
        )

        assert result is not None
    
    @patch('game_recommender.transformGameData')
    @patch('game_recommender.fetchGameDetailsWithRetry')
    @patch('game_recommender.getLLMHandler')
    def test_generate_recommendation_large_exclude_set(
        self,
        mock_get_llm,
        mock_fetch,
        mock_transform,
        sample_gaming_profile,
        sample_game_data
    ):
        """Test recommendation with large exclude set"""
        mock_llm = Mock()
        mock_llm.discoverGame.return_value = {
            'gameId': '570',
            'title': 'Dota 2',
            'reasoning': 'Great game',
            'matchScore': 85
        }
        mock_get_llm.return_value = mock_llm
        
        mock_fetch.return_value = {'name': 'Dota 2'}
        mock_transform.return_value = sample_game_data
        
        large_exclude_set = {str(i) for i in range(1000)}
        
        recommender = GameRecommender()
        result = recommender.generateRecommendation(
            gamingProfile=sample_gaming_profile,
            requestedGenres=[],
            excludeGameIds=large_exclude_set,
            logPrefix='Test'
        )
        
        assert result is not None