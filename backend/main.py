from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
import models
import requests
import urllib.parse
from jose import JWTError, jwt
from datetime import datetime, timedelta
import re
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Steam Pal API", description="Steam companion app with OAuth authentication")

# Root Endpoints
@app.get("/")
def read_root():
    """Root endpoint - API status"""
    return {
        "message": "Steam Pal API is running",
        "status": "healthy",
        "version": "1.0.0",
        "docs": "/docs",
        "steam_login": "/api/auth/steam/login"
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
STEAM_API_KEY = os.getenv("STEAM_API_KEY", "your-steam-api-key")  # Get from https://steamcommunity.com/dev/apikey
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
FRONTEND_AUTH_CALLBACK_URL = os.getenv("FRONTEND_AUTH_CALLBACK_URL", "http://localhost:5173/auth-callback")
TEST_SERVER_URL = os.getenv("TEST_SERVER_URL", "http://localhost:3000")
REDIRECT_URI = "http://localhost:8000/api/auth/steam/callback"

# Steam OpenID URLs
STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"
STEAM_API_BASE = "https://api.steampowered.com"

# CORS middleware
origins = [
    "http://localhost:5173",  # Vue dev server
    "http://127.0.0.1:5173",
    "http://localhost:3000",  # Test server
    "http://127.0.0.1:3000",
    "http://localhost:8000",  # Backend server
    "http://127.0.0.1:8000",
    FRONTEND_URL,
    FRONTEND_AUTH_CALLBACK_URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# In-memory user storage (replace with database in production)
users_db = {}

# JWT Token Functions
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        steam_id: str = payload.get("sub")
        if steam_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"steam_id": steam_id}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Steam API Functions
def get_steam_user_info(steam_id: str) -> dict:
    """Fetch user info from Steam API"""
    url = f"{STEAM_API_BASE}/ISteamUser/GetPlayerSummaries/v0002/"
    params = {
        "key": STEAM_API_KEY,
        "steamids": steam_id
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data["response"]["players"]:
            player = data["response"]["players"][0]
            return {
                "steam_id": steam_id,
                "display_name": player.get("personaname", "Unknown"),
                "avatar_url": player.get("avatarfull", ""),
                "profile_url": player.get("profileurl", ""),
                "last_login": datetime.utcnow()
            }
    except Exception as e:
        print(f"Error fetching Steam user info: {e}")
    
    # Fallback if API fails
    return {
        "steam_id": steam_id,
        "display_name": f"Steam User {steam_id[-4:]}",
        "avatar_url": "",
        "profile_url": f"https://steamcommunity.com/profiles/{steam_id}",
        "last_login": datetime.utcnow()
    }

def extract_steam_id_from_url(identity_url: str) -> str:
    """Extract Steam ID from OpenID identity URL"""
    # Handle the standard OpenID response format
    # Steam returns: https://steamcommunity.com/openid/id/<steamid>
    
    # Try OpenID format first
    match = re.search(r'/openid/id/(\d+)', identity_url)
    if match:
        return match.group(1)
    
    # Try profiles format
    match = re.search(r'/profiles/(\d+)', identity_url)
    if match:
        return match.group(1)
    
    # Try to extract any 17-digit Steam ID from the URL
    match = re.search(r'(\d{17})', identity_url)
    if match:
        return match.group(1)
    
    print(f"Could not extract Steam ID from URL: {identity_url}")
    raise ValueError(f"Could not extract Steam ID from identity URL: {identity_url}")

# Authentication Endpoints

@app.get("/api/auth/steam/login")
def steam_login_redirect():
    """Redirect user to Steam OpenID login"""
    # Use localhost consistently for better compatibility
    callback_url = 'http://localhost:8000/api/auth/steam/callback'
    realm_url = 'http://localhost:8000'
    
    params = {
        'openid.ns': 'http://specs.openid.net/auth/2.0',
        'openid.mode': 'checkid_setup',
        'openid.return_to': callback_url,
        'openid.realm': realm_url,
        'openid.identity': 'http://specs.openid.net/auth/2.0/identifier_select',
        'openid.claimed_id': 'http://specs.openid.net/auth/2.0/identifier_select',
    }
    
    query_string = urllib.parse.urlencode(params)
    steam_login_url = f"{STEAM_OPENID_URL}?{query_string}"
    
    return {"login_url": steam_login_url}

@app.get("/api/auth/steam/callback")
def steam_auth_callback(request: Request):
    """Handle Steam OpenID callback and create JWT token"""
    params = dict(request.query_params)
    # Verify the OpenID response
    validation_params = params.copy()
    validation_params['openid.mode'] = 'check_authentication'

    try:
        # Debug: log incoming params (avoid logging secrets in production)
        print("[steam_auth_callback] incoming params:", params)

        # Verify with Steam
        validation_response = requests.post(STEAM_OPENID_URL, data=validation_params, timeout=10)
        print(f"[steam_auth_callback] validation status: {validation_response.status_code}")
        print("[steam_auth_callback] validation body:", validation_response.text)

        # Accept variants like 'is_valid:true' or 'is_valid: true'
        if not re.search(r'is_valid\s*:\s*true', validation_response.text, re.IGNORECASE):
            # include validation response text to help debugging (trim length) 
            detail_text = validation_response.text.strip()[:500]
            print(f"[steam_auth_callback] validation failed (body starts): {detail_text}")
            raise HTTPException(status_code=400, detail=f"Steam authentication failed: validation failed")

        # Extract Steam ID (try claimed_id then identity)
        identity_url = params.get('openid.claimed_id') or params.get('openid.identity')
        if not identity_url:
            print("[steam_auth_callback] No identity URL found in params")
            raise HTTPException(status_code=400, detail="No Steam ID found in callback parameters")

        try:
            steam_id = extract_steam_id_from_url(identity_url)
        except ValueError as ve:
            print(f"[steam_auth_callback] Steam ID extraction error: {ve}")
            raise HTTPException(status_code=400, detail=str(ve))

        # Get user info from Steam API
        user_info = get_steam_user_info(steam_id)

        # Store/update user in database
        users_db[steam_id] = user_info

        # Create JWT token
        access_token = create_access_token({"sub": steam_id})

        # Check if request came from test server via Referer header or environment
        referer = request.headers.get('referer', '')
        is_test_mode = os.getenv("STEAM_TEST_MODE", "false").lower() == "true"
        
        if is_test_mode or ':3000' in referer or 'localhost:3000' in referer:
            # Redirect to test server
            redirect_url = f"{TEST_SERVER_URL}/test_steam_oauth.html?token={access_token}"
        else:
            # Redirect to frontend
            redirect_url = f"{FRONTEND_AUTH_CALLBACK_URL}?token={access_token}"
        
        print(f"[steam_auth_callback] successful login for steam_id={steam_id}, redirecting to {redirect_url}")
        return RedirectResponse(url=redirect_url)

    except HTTPException:
        # Re-raise HTTPExceptions to preserve status and detail
        raise
    except Exception as e:
        print(f"[steam_auth_callback] unexpected error: {e}")
        raise HTTPException(status_code=400, detail="Steam authentication failed")

@app.get("/api/auth/me", response_model=models.User)
def get_current_user(token_data: dict = Depends(verify_token)):
    """Get current authenticated user"""
    steam_id = token_data["steam_id"]
    
    if steam_id not in users_db:
        # Try to fetch from Steam API if not in cache
        user_info = get_steam_user_info(steam_id)
        users_db[steam_id] = user_info
    
    return users_db[steam_id]

@app.post("/api/auth/logout")
def logout():
    """Logout endpoint (client should discard token)"""
    return {"message": "Logged out successfully"}

# Game Recommendation Endpoints (mock data for now)
@app.post("/api/recommendations", response_model=models.Recommendation)
def get_recommendation(filters: models.RecommendationFilters, token_data: dict = Depends(verify_token)):
    """Returns a mock game recommendation (now requires authentication)"""
    steam_id = token_data["steam_id"]
    print(f"Getting recommendation for user {steam_id} with filters: {filters.genres}, {filters.tags}")
    
    return {
        "game_id": "292030",
        "game_name": "The Witcher 3: Wild Hunt",
        "reasoning": "Based on your interest in RPG and Story Rich games, this is a perfect match."
    }