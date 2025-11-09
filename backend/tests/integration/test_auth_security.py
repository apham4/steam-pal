"""
Integration tests for endpoints authentication and authorization security
"""

import pytest
import jwt
from fastapi.testclient import TestClient
from main import app, createJwtToken, SECRET_KEY, JWT_ALGORITHM
from db_helper import saveUser
from datetime import datetime, timedelta, timezone

client = TestClient(app)

class TestProtectedEndpoints:
    """Test that protected endpoints require valid JWT"""
    
    def test_auth_me_requires_auth(self):
        """Test /api/auth/me requires authentication"""
        response = client.get("/api/auth/me")
        
        assert response.status_code == 403

    def test_get_recommendations_requires_auth(self):
        """Test /api/recommendations requires authentication"""
        response = client.post(
            "/api/recommendations",
            json={"genres": []}
        )
        
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
    
    def test_get_recommendation_history_requires_auth(self):
        """Test /api/recommendations/history requires authentication"""
        response = client.get("/api/recommendations/history")
        
        assert response.status_code == 403

    def test_create_user_event_requires_auth(self):
        """Test /api/events/new requires authentication"""
        response = client.post(
            "/api/events/new",
            json={"eventType": "login"}
        )
        
        assert response.status_code == 403
        
    def test_filter_genres_endpoint_requires_auth(self):
        """Test /api/filters/genres requires authentication"""
        response = client.get("/api/filters/genres")
        
        assert response.status_code == 403


class TestUnprotectedEndpoints:
    """Test that public endpoints don't require authentication"""
    
    def test_health_check_no_auth(self):
        """Test /health endpoint doesn't require auth"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_steam_login_url_no_auth(self):
        """Test /api/auth/steam/login doesn't require auth"""
        response = client.get("/api/auth/steam/login")
        
        assert response.status_code == 200
        data = response.json()
        assert "login_url" in data
        assert data["login_url"].startswith("https://steamcommunity.com/openid/login")
    
    def test_available_genres_no_auth(self):
        """Test /api/filters/available-genres doesn't require auth"""
        response = client.get("/api/filters/available-genres")
        
        assert response.status_code == 200
        data = response.json()
        assert "genres" in data
        assert "tags" in data
        assert "modes" in data


class TestAuthenticatedEndpointAccess:
    """Test authentication flow through FastAPI endpoints"""
    
    def test_auth_me_with_valid_token(self, test_db_connection, sample_user_data):
        """Test /api/auth/me returns user data with valid token"""
        token = createJwtToken(
            sample_user_data['steamId'],
            sample_user_data['displayName'],
            sample_user_data['avatarUrl']
        )
        
        saveUser(
            sample_user_data['steamId'],
            sample_user_data['displayName'],
            sample_user_data['avatarUrl'],
            sample_user_data['profileUrl']
        )
        
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()

        assert data["steam_id"] == sample_user_data['steamId']
        assert data["display_name"] == sample_user_data['displayName']
        assert data["avatar_url"] == sample_user_data['avatarUrl']
    
    def test_malformed_token_rejected(self):
        """Test malformed JWT is rejected by FastAPI middleware"""
        response = client.post(
            "/api/recommendations",
            headers={"Authorization": "Bearer not_a_valid_jwt"},
            json={"genres": ["Action"]}
        )
        
        assert response.status_code == 401
    
    def test_expired_token_rejected(self, test_db_connection, sample_user_data):
        """Test expired JWT is rejected by FastAPI middleware"""
        
        # Create expired token
        expired_token = jwt.encode(
            {
                "sub": sample_user_data['steamId'],
                "displayName": sample_user_data['displayName'],
                "avatarUrl": sample_user_data['avatarUrl'],
                "exp": datetime.now(timezone.utc) - timedelta(hours=1),
            },
            SECRET_KEY,
            algorithm=JWT_ALGORITHM
        )
        
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401