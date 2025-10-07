from fastapi import FastAPI, Depends, HTTPException, Query, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
import re
import os
from dotenv import load_dotenv
import random
import httpx
from typing import Optional

from models import User, Token, RecommendationRequest, GameDetail,Recommendation
from steam_api import (
    fetch_game_details,
    fetch_user_owned_games,
    fetch_user_profile,
    get_popular_game_ids,
    transform_game_data,
    get_game_genres
)

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="Steam Pal API",
    version="1.0.0",
    description="Steam companion app with OAuth authentication")

# CONFIGURATION
SECRET_KEY = os.getenv("SECRET_KEY", "your-generated-secret-jwt-key")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
API_TIMEOUT = int(os.getenv("API_TIMEOUT_SECONDS", "10"))
STEAM_API_KEY = os.getenv("STEAM_API_KEY", "your-steam-web-api-key")  
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
FRONTEND_AUTH_CALLBACK_URL = os.getenv("FRONTEND_AUTH_CALLBACK_URL", "http://localhost:5173/auth-callback")
STEAM_OPENID_URL = os.getenv("STEAM_OPENID_URL", "https://steamcommunity.com/openid/login")

# CORS MIDDLEWARE
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Frontend
        "http://127.0.0.1:5173",
        "http://localhost:8000",  # Backend
        "http://127.0.0.1:8000",
        FRONTEND_URL,
        FRONTEND_AUTH_CALLBACK_URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SECURITY
security = HTTPBearer()

# JWT Token Functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT token
    Args:
        data: Data to encode in the token (e.g. user info)
        expires_delta: Optional custom expiration time
    Returns:
        Encoded JWT token as a string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)

    to_encode.update({"exp": expire})
    encode_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encode_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verify JWT token from Authorization header and return user data
    Args:
        credentials: HTTP Bearer token from request header
    Returns:
        Decoded token payload (user data)
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        steam_id: str = payload.get("sub")
        if steam_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return payload
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

# ROOT ENDPOINTS
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
    return {
        "status": "healthy", 
        "timestamp": datetime.utcnow().isoformat()
        }

# AUTHENTICATION ENDPOINTS
@app.get("/api/auth/steam/login")
def steam_login():
    """
    Initiate Steam OpenID authentication
    Returns:
        Steam OpenID authentication URL
    """
    params = {
        'openid.ns': 'http://specs.openid.net/auth/2.0',
        'openid.mode': 'checkid_setup',
        'openid.return_to': f"{FRONTEND_URL}/auth/callback",
        'openid.realm': FRONTEND_URL,
        'openid.identity': 'http://specs.openid.net/auth/2.0/identifier_select',
        'openid.claimed_id': 'http://specs.openid.net/auth/2.0/identifier_select',
    }
    
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    auth_url = f"{STEAM_OPENID_URL}?{query_string}"

    print(f"[steam_login] Generated auth URL for frontend: {auth_url}")
    return {"auth_url": auth_url}

@app.get("/api/auth/steam/callback")
async def steam_auth_callback(
    openid_ns: str = Query(..., alias="openid.ns"),
    openid_mode: str = Query(..., alias="openid.mode"),
    openid_op_endpoint: str = Query(..., alias="openid.op_endpoint"),
    openid_claimed_id: str = Query(..., alias="openid.claimed_id"),
    openid_identity: str = Query(..., alias="openid.identity"),
    openid_return_to: str = Query(..., alias="openid.return_to"),
    openid_response_nonce: str = Query(..., alias="openid.response_nonce"),
    openid_assoc_handle: str = Query(..., alias="openid.assoc_handle"),
    openid_signed: str = Query(..., alias="openid.signed"),
    openid_sig: str = Query(..., alias="openid.sig"),
):
    """
    Handle Steam OpenID callback and create JWT token
    Args:
        openid_*: OpenID parameters from Steam authentication
    Returns:
        JWT token and user info
    Raises:
        HTTPException: If authentication fails
    """
    print("[steam_auth_callback] Received Steam callback")
    # Verify the OpenID response
    if openid_mode != "id_res":
        raise HTTPException(status_code=400, detail="Invalid OpenID response")
    # Verify response with Steam
    params = {
        "openid.ns": openid_ns,
        "openid.mode": "check_authentication",
        "openid.op_endpoint": openid_op_endpoint,
        "openid.claimed_id": openid_claimed_id,
        "openid.identity": openid_identity,
        "openid.return_to": openid_return_to,
        "openid.response_nonce": openid_response_nonce,
        "openid.assoc_handle": openid_assoc_handle,
        "openid.signed": openid_signed,
        "openid.sig": openid_sig
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(STEAM_OPENID_URL, data=params)

    if "is_valid:true" not in response.text:
        print("[steam_auth_callback] Steam verification failed")
        raise HTTPException(status_code=400, detail="Invalid Steam OpenID verification")
    
    # Extract Steam ID from claimed_id
    match = re.search(r"http://steamcommunity\.com/openid/id/(\d+)", openid_claimed_id)
    if not match:
        raise HTTPException(status_code=400, detail="Could not extract Steam ID")
    steam_id = match.group(1)
    print(f"[steam_auth_callback] Authenticated Steam ID: {steam_id}")

    # Fetch user profile from Steam API
    profile = fetch_user_profile(steam_id)

    if not profile:
        # Fallback if Steam API fails
        print(f"[steam_auth_callback] Could not fetch profile, using fallback")
        profile = {
            "steam_id": steam_id,
            "personaname": f"User_{steam_id[-4:]}",
            "avatarfull": "",
            "profileurl": f"https://steamcommunity.com/profiles/{steam_id}"
        }

    # Create user object
    user = User(
        steam_id=steam_id,
        display_name=profile.get("personaname", f"User_{steam_id[-4:]}"),
        avatar_url=profile.get("avatarfull", ""),
        profile_url=profile.get("profileurl", f"https://steamcommunity.com/profiles/{steam_id}"),
        last_login=datetime.utcnow()
    )

    # Create JWT token
    access_token = create_access_token(
        data={
            "steam_id": user.steam_id,
            "display_name": user.display_name,
            "avatar_url": user.avatar_url,
            "profile_url": user.profile_url,
        }
    )

    # Return token response
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=JWT_EXPIRATION_HOURS * 3600,
        user=user
    )

@app.get("/api/auth/me", response_model=User)
def get_current_user(current_user: dict = Depends(verify_token)):
    """
    Get current authenticated user
    Args:
        current_user: Decoded JWT token payload
    Returns:
        User information from token
    """
    return User(
        steam_id=current_user["steam_id"],
        display_name=current_user["display_name"],
        avatar_url=current_user.get("avatar_url", ""),
        profile_url=current_user.get("profile_url", ""),
        last_login=datetime.utcnow()    
    )

# LOGOUT ENDPOINT
@app.post("/api/auth/logout")
def logout():
    """Logout endpoint (client should discard token)"""
    return {"message": "Logged out successfully"}

# GAME RECOMMENDATION ENDPOINT
@app.post("/api/recommendations", response_model=Recommendation)
async def get_recommendation(
    request: RecommendationRequest,
    current_user: dict = Depends(verify_token)
):
    """
    Get AI-powered game recommendation
    Args:
        request: Game recommendation request
        current_user: Authenticated user from JWT token
    Request format:
    {
        "steamId": "76561197960287930",
        "genre": "RPG",
        "useWishlist": false
    }
    Response format:
    {
        "game": {
            "id": "292030",
            "title": "The Witcher 3: Wild Hunt",
            "thumbnail": "https://...",
            "releaseDate": "May 18, 2015",
            "publisher": "CD PROJEKT RED",
            "developer": "CD PROJEKT RED",
            "price": "$39.99",
            "salePrice": "$9.99",
            "description": "..."
        },
        "reasoning": "Based on your preference..."
    }
    """
    print(f"\n{'='*70}")
    print(f"[get_recommendation] New request from: {current_user.get('display_name', 'Unknown')}")
    print(f"[get_recommendation] Request: steamId={request.steamId}, genre={request.genre}")
    print(f"{'='*70}\n")
    
    try:
        # Step 1: Fetch user's owned games from Steam
        print("Step 1: Fetching user's game library...")
        user_games = fetch_user_owned_games(request.steamId)
        
        if not user_games:
            print("[get_recommendation] Could not fetch user library (may be private or API error)")
        
        user_game_ids = {str(game["appid"]) for game in user_games}
        print(f"User owns {len(user_game_ids)} games")
        
        # Step 2: Get popular game candidates
        print("Step 2: Getting popular game candidates...")
        candidate_game_ids = get_popular_game_ids(limit=50)
        print(f"Found {len(candidate_game_ids)} candidate games")
        
        # Step 3: Filter out games user already owns
        print("Step 3: Filtering out owned games...")
        new_games = [gid for gid in candidate_game_ids if gid not in user_game_ids]
        
        if not new_games:
            print(" User owns all candidate games! Using all candidates.")
            new_games = candidate_game_ids

        print(f"[Step 3] {len(new_games)} games available for recommendation")

        # Step 4: Filter by genre if specified
        if request.genre:
            print(f"[Step 4] Filtering by genre: {request.genre}")
            genre_filtered_games = []
            
            # Check first 20 games to save API calls
            for game_id in new_games[:20]:
                game_data = fetch_game_details(game_id)
                if game_data:
                    genres = get_game_genres(game_data)
                    # Check if requested genre matches any game genre
                    if any(request.genre.lower() in genre.lower() for genre in genres):
                        genre_filtered_games.append(game_id)
                        print(f"[Step 4] {game_data.get('name')} matches {request.genre}")
            
            if genre_filtered_games:
                new_games = genre_filtered_games
                print(f"[Step 4] Found {len(new_games)} {request.genre} games")
            else:
                print(f"[Step 4] No {request.genre} games found, using all candidates instead")

        # Step 5: Select a random game
        print("[Step 5] Selecting recommendation...")
        recommended_game_id = random.choice(new_games)
        print(f"[Step 5] Selected game ID: {recommended_game_id}")

        # Step 6: Fetch full game details from Steam
        print("[Step 6] Fetching game details...")
        raw_game_data = fetch_game_details(recommended_game_id)

        if not raw_game_data:
            raise HTTPException(
                status_code=500,
                detail=f"Could not fetch game details from Steam API"
            )
        
        print(f"[Step 6] Fetched: {raw_game_data.get('name', 'Unknown')}")
        
        # Step 7: Transform to frontend-compatible format
        print("[Step 7] Transforming data...")
        game_data = transform_game_data(raw_game_data)
        
        # Step 8: Generate reasoning
        print("[Step 8] Generating recommendation reasoning...")
        reasoning = generate_reasoning(
            game_data=game_data,
            raw_game_data=raw_game_data,
            user_game_count=len(user_games),
            preferred_genre=request.genre,
            use_wishlist=request.useWishlist
        )
        
        print(f"Success! Recommended: {game_data['title']}, {game_data['price']}")
        print(f"{'='*70}\n")
        
        # Step 9: Return recommendation
        return Recommendation(
            game=GameDetail(**game_data),
            reasoning=reasoning
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        print(f"[get_recommendation] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error while generating recommendation: {str(e)}"
        )


def generate_reasoning(
    game_data: dict,
    raw_game_data: dict,
    user_game_count: int,
    preferred_genre: str = "",
    use_wishlist: bool = False
) -> str:
    """
    Generate personalized reasoning for recommendation
    Args:
        game_data: Transformed game data (frontend format)
        raw_game_data: Raw Steam API response
        user_game_count: Number of games user owns
        preferred_genre: User's preferred genre filter
        use_wishlist: Whether wishlist was considered
    Returns:
        Reasoning text explaining the recommendation
    """
    try:
        reasoning_parts = []
        
        # User context
        if user_game_count > 0:
            reasoning_parts.append(f"Based on your Steam library of {user_game_count} games")
        else:
            reasoning_parts.append("Based on popular games on Steam")
        
        # Genre preference
        if preferred_genre:
            reasoning_parts.append(f"and your interest in {preferred_genre} games")
        
        # Main recommendation
        reasoning = ", ".join(reasoning_parts) + f", we recommend **{game_data['title']}**.\n\n"
        
        # Game description
        if game_data.get('description'):
            description = game_data['description']
            # Truncate if too long
            if len(description) > 250:
                description = description[:250].rsplit(' ', 1)[0] + "..."
            reasoning += description + "\n\n"
        
        # Game details
        genres = get_game_genres(raw_game_data)
        if genres:
            reasoning += f"**Genres:** {', '.join(genres[:3])}\n"
        
        if game_data.get('releaseDate'):
            reasoning += f"**Released:** {game_data['releaseDate']}\n"
        
        if game_data.get('developer'):
            reasoning += f"**Developer:** {game_data['developer']}\n"
        
        # Pricing
        if game_data.get('salePrice'):
            reasoning += f"\n**On Sale!** ~~{game_data['price']}~~ → {game_data['salePrice']}"
        elif game_data.get('price'):
            reasoning += f"\n**Price:** {game_data['price']}"
        
        return reasoning
        
    except Exception as e:
        print(f"[generate_reasoning] Error generating reasoning: {e}")
        return f"We recommend **{game_data.get('title', 'this game')}** based on its popularity and high ratings on Steam."