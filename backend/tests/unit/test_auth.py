"""
Unit tests for JWT authentication functions
"""

import pytest
import jwt
from datetime import datetime, timedelta, timezone
from main import createJwtToken, SECRET_KEY, JWT_ALGORITHM


class TestJWTTokenGeneration:
    """Test JWT token generation"""
    
    def test_create_jwt_token_valid_inputs(self):
        """Test createJwtToken() with valid inputs"""
        token = createJwtToken(
            "76561197960287930",
            "Test User",
            "https://example.com/avatar.jpg"
        )
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode to verify structure
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        assert payload["sub"] == "76561197960287930"
        assert payload["displayName"] == "Test User"
        assert payload["avatarUrl"] == "https://example.com/avatar.jpg"
        assert "exp" in payload
    
    def test_create_jwt_token_expiration_time(self):
        """Test JWT token has correct expiration (24 hours)"""
        token = createJwtToken(
            "76561197960287930",
            "Test User",
            "https://example.com/avatar.jpg"
        )
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = datetime.now(timezone.utc)
        
        duration = exp_time - now
        expected_duration = timedelta(hours=24)
        
        # Allow 5 second tolerance for test execution time
        assert abs((duration - expected_duration).total_seconds()) < 5
    
    def test_create_jwt_token_with_special_characters(self):
        """Test JWT creation with special characters in name"""
        token = createJwtToken(
            "76561197960287930",
            "Test User [Pro]",
            "https://example.com/avatar.jpg"
        )
        
        assert token is not None
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        assert payload["displayName"] == "Test User [Pro]"


class TestJWTTokenDecoding:
    """Test JWT token validation and decoding"""
    
    def test_decode_valid_token(self):
        """Test decoding valid token"""
        token = createJwtToken(
            "76561197960287930",
            "Test User",
            "https://example.com/avatar.jpg"
        )
        
        # Decode using jwt library
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        assert payload is not None
        assert payload["sub"] == "76561197960287930"
        assert payload["displayName"] == "Test User"
        assert payload["avatarUrl"] == "https://example.com/avatar.jpg"
    
    def test_decode_invalid_token_format(self):
        """Test decoding malformed token raises error"""
        with pytest.raises(jwt.DecodeError):
            jwt.decode("not_a_valid_jwt_token", SECRET_KEY, algorithms=[JWT_ALGORITHM])
    
    def test_decode_token_wrong_signature(self):
        """Test decoding token with wrong signature raises error"""
        # Create token with different secret
        fake_token = jwt.encode(
            {
                "sub": "123",
                "displayName": "Fake User",
                "exp": datetime.now(timezone.utc) + timedelta(hours=1)
            },
            "wrong_secret_key_12345",
            algorithm=JWT_ALGORITHM
        )
        
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(fake_token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    
    def test_decode_expired_token(self):
        """Test decoding expired token raises error"""
        # Create token that expired 1 hour ago
        expired_token = jwt.encode(
            {
                "sub": "76561197960287930",
                "displayName": "Test User",
                "avatarUrl": "https://example.com/avatar.jpg",
                "exp": datetime.now(timezone.utc) - timedelta(hours=1)
            },
            SECRET_KEY,
            algorithm=JWT_ALGORITHM
        )
        
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(expired_token, SECRET_KEY, algorithms=[JWT_ALGORITHM])


class TestJWTTokenEdgeCases:
    """Test edge cases and error conditions"""

    def test_decode_none_token(self):
        """Test decoding None raises error"""
        with pytest.raises((jwt.DecodeError, TypeError)):
            jwt.decode(None, SECRET_KEY, algorithms=[JWT_ALGORITHM])
    
    def test_create_token_empty_steam_id(self):
        """Test creating token with empty steam ID"""
        token = createJwtToken("", "Test User", "")
        
        # Token is created but payload has empty sub
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        assert payload["sub"] == ""