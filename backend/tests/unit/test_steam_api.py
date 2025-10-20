import sys
import pytest
from unittest.mock import patch, Mock
import steam_api
from pathlib import Path

# Add backend to path
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BACKEND_DIR))

class TestGameDetailsFetching:
    """Test fetching game details from Steam API"""
    
    @patch('steam_api.requests.get')
    def test_fetch_game_details_success(self, mock_get, mock_steam_api):
        """Test successfully fetching game details"""
        mock_response = Mock()
        mock_response.json.return_value = {
            '292030': {
                'success': True,
                'data': mock_steam_api['game_details']
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = steam_api.fetchGameDetails('292030')
        
        assert result is not None
        assert result['name'] == 'The Witcher 3: Wild Hunt'
        assert result['steam_appid'] == 292030
    
    @patch('steam_api.requests.get')
    def test_fetch_game_details_not_found(self, mock_get):
        """Test fetching non-existent game"""
        mock_response = Mock()
        mock_response.json.return_value = {
            '99999': {
                'success': False
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = steam_api.fetchGameDetails('99999')
        assert result is None
    
    @patch('steam_api.requests.get')
    def test_fetch_game_details_timeout(self, mock_get):
        """Test timeout handling"""
        mock_get.side_effect = steam_api.requests.exceptions.Timeout
        
        result = steam_api.fetchGameDetails('292030')
        assert result is None
    
    @patch('steam_api.requests.get')
    def test_fetch_game_details_with_retry_success_on_first_attempt(self, mock_get, mock_steam_api):
        """Test retry logic succeeds on first attempt"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            '292030': {
                'success': True,
                'data': mock_steam_api['game_details']
            }
        }
        mock_get.return_value = mock_response
        
        result = steam_api.fetchGameDetailsWithRetry('292030')
        
        assert result is not None
        assert mock_get.call_count == 1
    
    @patch('steam_api.requests.get')
    @patch('steam_api.time.sleep')  # Mock sleep to speed up test
    def test_fetch_game_details_with_retry_success_on_second_attempt(self, mock_sleep, mock_get, mock_steam_api):
        """Test retry logic succeeds on second attempt"""
        # First call fails with 500, second succeeds
        fail_response = Mock()
        fail_response.status_code = 500
        
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {
            '292030': {
                'success': True,
                'data': mock_steam_api['game_details']
            }
        }
        
        mock_get.side_effect = [fail_response, success_response]
        
        result = steam_api.fetchGameDetailsWithRetry('292030', maxRetries=3)
        
        assert result is not None
        assert mock_get.call_count == 2
    
    @patch('steam_api.requests.get')
    @patch('steam_api.time.sleep')
    def test_fetch_game_details_with_retry_all_fail(self, mock_sleep, mock_get):
        """Test retry logic when all attempts fail"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        result = steam_api.fetchGameDetailsWithRetry('292030', maxRetries=3)
        
        assert result is None
        assert mock_get.call_count == 3


class TestUserDataFetching:
    """Test fetching user data from Steam API"""
    
    @patch('steam_api.requests.get')
    def test_fetch_user_owned_games_success(self, mock_get, mock_steam_api):
        """Test fetching user's owned games"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'response': {
                'games': mock_steam_api['owned_games']
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = steam_api.fetchUserOwnedGames('76561197960287930')
        
        assert len(result) == 3
        assert result[0]['appid'] == 292030
        assert result[0]['name'] == 'The Witcher 3: Wild Hunt'
    
    @patch('steam_api.requests.get')
    def test_fetch_user_owned_games_no_games(self, mock_get):
        """Test fetching owned games for user with no games"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'response': {
                'games': []
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = steam_api.fetchUserOwnedGames('76561197960287930')
        assert len(result) == 0
    
    @patch('steam_api.STEAM_API_KEY', None)
    def test_fetch_user_owned_games_no_api_key(self):
        """Test fetching owned games without API key"""
        result = steam_api.fetchUserOwnedGames('76561197960287930')
        assert len(result) == 0
    
    @patch('steam_api.requests.get')
    def test_fetch_user_profile_success(self, mock_get, mock_steam_api):
        """Test fetching user profile"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'response': {
                'players': [mock_steam_api['user_profile']]
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = steam_api.fetchUserProfile('76561197960287930')
        
        assert result is not None
        assert result['steamid'] == '76561197960287930'
        assert result['personaname'] == 'Test User'
    
    @patch('steam_api.requests.get')
    def test_fetch_user_profile_not_found(self, mock_get):
        """Test fetching non-existent user profile"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'response': {
                'players': []
            }
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        result = steam_api.fetchUserProfile('99999999999999999')
        assert result is None


class TestDataTransformation:
    """Test data transformation functions"""
    
    def test_transform_game_data_complete(self, mock_steam_api):
        """Test transforming complete game data"""
        result = steam_api.transformGameData(mock_steam_api['game_details'])
        
        assert result['gameId'] == '292030'
        assert result['title'] == 'The Witcher 3: Wild Hunt'
        assert result['releaseDate'] == 'May 18, 2015'
        assert result['publisher'] == 'CD PROJEKT RED'
        assert result['developer'] == 'CD PROJEKT RED'
        assert result['price'] == '$9.99'
        assert result['salePrice'] == '$9.99'
    
    def test_transform_game_data_minimal(self):
        """Test transforming minimal game data"""
        minimal_data = {
            'steam_appid': '12345',
            'name': 'Test Game'
        }
        
        result = steam_api.transformGameData(minimal_data)
        
        assert result['gameId'] == '12345'
        assert result['title'] == 'Test Game'
        assert result['thumbnail'] == ''
        assert result['releaseDate'] == ''
    
    def test_transform_game_data_with_error(self):
        """Test transforming invalid game data"""
        invalid_data = None
        
        # Should not raise error, return minimal structure
        result = steam_api.transformGameData(invalid_data or {})
        
        assert 'gameId' in result
        assert 'title' in result


class TestPriceFormatting:
    """Test price formatting functions"""
    
    def test_format_price_usd(self):
        """Test formatting USD price"""
        price_data = {
            'final': 3999,  # $39.99
            'currency': 'USD'
        }
        
        result = steam_api.formatPrice(price_data)
        assert result == '$39.99'
    
    def test_format_price_eur(self):
        """Test formatting EUR price"""
        price_data = {
            'final': 2999,
            'currency': 'EUR'
        }
        
        result = steam_api.formatPrice(price_data)
        assert result == '€29.99'
    
    def test_format_price_gbp(self):
        """Test formatting GBP price"""
        price_data = {
            'final': 1999,
            'currency': 'GBP'
        }
        
        result = steam_api.formatPrice(price_data)
        assert result == '£19.99'
    
    def test_format_price_free(self):
        """Test formatting free game"""
        result = steam_api.formatPrice(None)
        assert result == 'Free to Play'
    
    def test_format_sale_price_on_sale(self):
        """Test formatting sale price when on sale"""
        price_data = {
            'final': 999,
            'discount_percent': 75,
            'currency': 'USD'
        }
        
        result = steam_api.formatSalePrice(price_data)
        assert result == '$9.99'
    
    def test_format_sale_price_no_sale(self):
        """Test formatting sale price when not on sale"""
        price_data = {
            'final': 3999,
            'discount_percent': 0,
            'currency': 'USD'
        }
        
        result = steam_api.formatSalePrice(price_data)
        assert result == ''
    
    def test_format_sale_price_none(self):
        """Test formatting sale price when price data is None"""
        result = steam_api.formatSalePrice(None)
        assert result == ''