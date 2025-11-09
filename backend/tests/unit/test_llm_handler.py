"""
Unit tests for LLM prompt generation and response parsing
"""

import sys
import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from llm_handler import LLMHandler
from pathlib import Path

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BACKEND_DIR))

class TestLLMHandlerInitialization:
    """Test LLM handler initialization"""
    
    @patch('llm_handler.genai.configure')
    @patch('llm_handler.genai.GenerativeModel')
    @patch('llm_handler.os.getenv')
    def test_init_with_gemini(self, mock_getenv, mock_model, mock_configure):
        """Test initializing with Gemini provider"""
        mock_getenv.return_value = 'test_api_key'
        
        handler = LLMHandler(provider='gemini')
        
        assert handler.provider == 'gemini'
        mock_configure.assert_called_once_with(api_key='test_api_key')
    
    @patch('llm_handler.os.getenv')
    def test_init_without_api_key(self, mock_getenv):
        """Test initializing without API key"""
        mock_getenv.return_value = None
        
        with pytest.raises(ValueError, match='GEMINI_API_KEY not found'):
            LLMHandler(provider='gemini')


class TestPromptBuilding:
    """Test prompt engineering"""
    
    @patch('llm_handler.genai.configure')
    @patch('llm_handler.genai.GenerativeModel')
    @patch('llm_handler.os.getenv')
    def test_build_prompt_complete_profile(self, mock_getenv, mock_model, mock_configure, sample_gaming_profile):
        """Test building prompt with complete gaming profile"""
        mock_getenv.return_value = 'test_key'
        handler = LLMHandler()
        
        prompt = handler.buildPrompt(
            gamingProfile=sample_gaming_profile,
            requestedGenres=['RPG', 'Action'],
            excludeGameIds={'570', '730'}
        )
        
        assert 'LIBRARY STATS' in prompt
        assert 'The Elder Scrolls V: Skyrim' in prompt
        assert 'The Witcher 3' in prompt
        assert 'RPG' in prompt
        assert 'Action' in prompt
        assert '570' in prompt  # Excluded game ID
        assert '730' in prompt  # Excluded game ID
        assert '150' in prompt  # Game count
        assert '545' in prompt  # Total playtime
    
        # Verify structure
        assert 'TOP 10 MOST-PLAYED GAMES' in prompt
        assert 'RECENTLY ACTIVE GAMES' in prompt
        assert 'FAVORITE GENRES' in prompt
        assert 'JSON' in prompt
    
   
class TestResponseParsing:
    """Test AI response parsing"""
    
    @patch('llm_handler.genai.configure')
    @patch('llm_handler.genai.GenerativeModel')
    @patch('llm_handler.os.getenv')
    def test_parse_response_valid_json(self, mock_getenv, mock_model, mock_configure):
        """Test parsing valid JSON response"""
        mock_getenv.return_value = 'test_key'
        handler = LLMHandler()
        
        response_text = json.dumps({
            'gameId': '292030',
            'title': 'The Witcher 3',
            'reasoning': 'Great game!',
            'matchScore': 95,
            'similarTo': ['Skyrim']
        })
        
        result = handler.parseResponse(response_text)
        
        assert result is not None
        assert result['gameId'] == '292030'
        assert result['title'] == 'The Witcher 3'
        assert result['matchScore'] == 95


class TestGameDiscovery:
    """Test AI game discovery"""
    
    @patch('llm_handler.genai.configure')
    @patch('llm_handler.genai.GenerativeModel')
    @patch('llm_handler.os.getenv')
    def test_discover_game_success(self, mock_getenv, mock_model_class, mock_configure, sample_gaming_profile):
        """Test successful game discovery"""
        mock_getenv.return_value = 'test_key'
        
        # Mock the model's generate_content method
        mock_model = MagicMock()
        mock_response = Mock()
        mock_response.text = json.dumps({
            'gameId': '292030',
            'title': 'The Witcher 3',
            'reasoning': 'Perfect match!',
            'matchScore': 95,
            'similarTo': ['Skyrim']
        })
        mock_model.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_model
        
        handler = LLMHandler()
        
        result = handler.discoverGame(
            gamingProfile=sample_gaming_profile,
            requestedGenres=['RPG'],
            excludeGameIds={'570'}
        )
        
        assert result is not None
        assert result['gameId'] == '292030'
        assert result['title'] == 'The Witcher 3'