from fastapi import FastAPI, Depends, HTTPException, Query, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from jwt.exceptions import InvalidTokenError
import os
import requests
import jwt

from models import UserResponse, RecommendationRequest, Recommendation, GameDetail
from steam_api import (
    fetchUserOwnedGames,
    fetchGameDetailsWithRetry,
    transformGameData,
)

from db_helper import (
    saveUser,
    getUser,
    cacheOwnedGames,
    getOwnedGamesIds,
    isOwnedGamesCacheRecent,
    getUserGamingProfile,
    cacheGameDetails,
    getCachedGameDetails,
    saveRecommendation,
    getUserRecommendations,
    getRecommendationsCount,
    getRecommendedGameIds,
    savePreference,
    getPreferenceGameIds,
    deletePreference
)

from game_recommender import generateSmartRecommendation

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="Steam Pal API",
    version="1.0.0",
    description="Steam companion app with OAuth authentication")

# CONFIGURATION

# Security
SECRET_KEY = os.getenv("SECRET_KEY", "your-generated-secret-jwt-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# Steam API
STEAM_API_KEY = os.getenv("STEAM_API_KEY", "your-steam-web-api-key")
STEAM_OPENID_URL = os.getenv("STEAM_OPENID_URL", "https://steamcommunity.com/openid/login")

# Frontend URLs
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
FRONTEND_AUTH_CALLBACK_URL = os.getenv("FRONTEND_AUTH_CALLBACK_URL", "http://localhost:5173/auth-callback.html")

# Backend URLs
BACKEND_URL = "http://localhost:8000"
BACKEND_AUTH_CALLBACK_URL = os.getenv("BACKEND_AUTH_CALLBACK_URL", "http://localhost:8000/api/auth/steam/callback")


# CORS MIDDLEWARE
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Frontend
        "http://127.0.0.1:5173",
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
def createJwtToken(steamId: str, displayName: str, avatarUrl: str = "") -> str:
    """
    Create JWT token for authenticated user
    """
    expiration = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    tokenData = {
        "sub": steamId,
        "displayName": displayName,
        "avatarUrl": avatarUrl,
        "exp": expiration
    }
    
    token = jwt.encode(tokenData, SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token

async def verifyToken(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Verify JWT token and return user data
    """
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        steamId = payload.get("sub")
        if not steamId:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing steam ID"
            )
        
        return payload
        
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
 

# AUTHENTICATION ENDPOINTS
@app.get("/api/auth/steam/login")
def steamLogin():
    """
    Initiate Steam OpenID authentication
    Returns Steam OpenID login URL for frontend redirection
    """
    params = {
        'openid.ns': 'http://specs.openid.net/auth/2.0',
        'openid.mode': 'checkid_setup',
        'openid.return_to': BACKEND_AUTH_CALLBACK_URL,
        'openid.realm': BACKEND_URL,
        'openid.identity': 'http://specs.openid.net/auth/2.0/identifier_select',
        'openid.claimed_id': 'http://specs.openid.net/auth/2.0/identifier_select',
    }
    
    loginUrl = f"{STEAM_OPENID_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    return {"login_url": loginUrl}

@app.get("/api/auth/steam/callback")
async def steamCallback(
    request: Request,
):
    """
    Handle Steam OAuth callback
    """
    params = dict(request.query_params)
    openid_claimed_id = params.get("openid.claimed_id")
    
    print("="*70)
    print("STEAM CALLBACK RECEIVED")
    print(f"All params: {list(params.keys())}")
    print(f"openid.claimed_id: {openid_claimed_id}")
    print("="*70)
    
    if not openid_claimed_id:
        raise HTTPException(status_code=400, detail="Missing openid.claimed_id parameter")
    
    try:
        # Extract Steam ID from claimed_id URL
        steamId = openid_claimed_id.split('/')[-1]
        print(f"Extracted Steam ID: {steamId}")
        
        # Fetch user profile from Steam
        profileUrl = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
        params = {"key": STEAM_API_KEY, "steamids": steamId}
        
        response = requests.get(profileUrl, params=params)
        data = response.json()
        
        if not data.get("response", {}).get("players"):
            raise HTTPException(status_code=400, detail="Failed to fetch Steam profile")
        
        player = data["response"]["players"][0]
        displayName = player.get("personaname", "Unknown")
        avatarUrl = player.get("avatarfull", "")
        steamProfileUrl = player.get("profileurl", "")

        print(f"User: {displayName}")

        # Save user to database
        saveUser(steamId, displayName, avatarUrl, steamProfileUrl)
        
        # Fetch and cache owned games
        try:
            ownedGames = fetchUserOwnedGames(steamId)
            if ownedGames:
                cacheOwnedGames(steamId, ownedGames)
                print(f"Cached {len(ownedGames)} games for user {steamId}")
        except Exception as e:
            print(f"Failed to cache owned games: {e}")
            # Continue login even if caching fails
        
        # Create JWT token
        token = createJwtToken(steamId, displayName, avatarUrl)
        print(f"Token created, redirecting to: {FRONTEND_AUTH_CALLBACK_URL}")
        
        # Redirect to frontend with token
        return RedirectResponse(
            url=f"{FRONTEND_AUTH_CALLBACK_URL}?token={token}"
        )
        
    except Exception as e:
        print(f"Steam callback error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@app.get("/api/auth/me")
async def getCurrentUser(currentUser: dict = Depends(verifyToken)):
    """
    Get current authenticated user
    """
    steamId = currentUser["sub"]
    user = getUser(steamId)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        steamId=user["steamId"],
        displayName=user["displayName"],
        avatarUrl=user["avatarUrl"],
        profileUrl=user.get("profileUrl", ""),
        lastLogin=datetime.fromtimestamp(user["lastLogin"]).isoformat()
    )

@app.post("/api/auth/logout")
async def logout(currentUser: dict = Depends(verifyToken)):
    """Logout endpoint (client should discard token)"""
    return {"status": "success", "message": "Logged out successfully"}


# RECOMMENDATION ENDPOINT
@app.post("/api/recommendations")
async def getRecommendation(
    request: RecommendationRequest,
    currentUser: dict = Depends(verifyToken)
):
    """
    Generate AI-powered game recommendation
    """
    steamId = currentUser["sub"]
    
    try:
        # STEP 1: Check/refresh owned games cache
        if not isOwnedGamesCacheRecent(steamId, maxAgeHours=24):
            print(f"Refreshing owned games cache for {steamId}")
            ownedGames = fetchUserOwnedGames(steamId)
            if ownedGames:
                cacheOwnedGames(steamId, ownedGames)
        
        # STEP 2: Get user's gaming profile
        gamingProfile = getUserGamingProfile(steamId)
        print(f"Gaming Profile: {gamingProfile['gameCount']} games, {gamingProfile['totalPlaytime']}h total")

        # STEP 3: Get exclusion lists
        ownedGameIds = set(getOwnedGamesIds(steamId))
        recommendedGameIds = set(getRecommendedGameIds(steamId))
        dislikedGameIds = set(getPreferenceGameIds(steamId, "disliked"))
        
        # Combine all games to exclude
        excludeGameIds = ownedGameIds | recommendedGameIds | dislikedGameIds
        
        print(f"Excluding {len(excludeGameIds)} games")

        # STEP 4: Generate recommendation
        recommendation = generateSmartRecommendation(
            steamId=steamId,
            gamingProfile=gamingProfile,
            requestedGenres=request.genres,
            excludeGameIds=excludeGameIds,
        )
        
        if not recommendation:
            raise HTTPException(
                status_code=404,
                detail="No suitable games found. Try different genres or check back later."
            )
        
        # STEP 5: Save recommendation to history
        saveRecommendation(
            steamId=steamId,
            game=recommendation["game"],
            reasoning=recommendation["reasoning"],
            matchScore=recommendation["matchScore"],
            requestedGenres=request.genres
        )
        
        # STEP 6: Return to frontend
        return Recommendation(
            game=GameDetail(**recommendation["game"]),
            reasoning=recommendation["reasoning"],
            matchScore=recommendation["matchScore"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Recommendation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate recommendation: {str(e)}"
        )


# RECOMMENDATION HISTORY ENDPOINT
@app.get("/api/recommendations/history")
async def getRecommendationHistory(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    currentUser: dict = Depends(verifyToken)
):
    """
    Get user's recommendation history
    """
    steamId = currentUser["sub"]
    
    offset = (page - 1) * limit
    recommendations = getUserRecommendations(steamId, limit, offset)
    totalCount = getRecommendationsCount(steamId)
    totalPages = (totalCount + limit - 1) // limit
    
    return {
        "recommendations": recommendations,
        "page": page,
        "limit": limit,
        "total": totalCount,
        "pages": totalPages
    }


# PREFERENCE MANAGEMENT ENDPOINT
@app.post("/api/preferences/{gameId}/like")
async def likeGame(gameId: str, currentUser: dict = Depends(verifyToken)):
    """
    Mark a game as liked
    """
    steamId = currentUser["sub"]
    
    try:
        savePreference(steamId, gameId, "liked")
        return {"status": "success", "gameId": gameId, "preference": "liked", "message": f"Game {gameId} liked"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/preferences/{gameId}/dislike")
async def dislikeGame(gameId: str, currentUser: dict = Depends(verifyToken)):
    """
    Mark a game as disliked
    """
    steamId = currentUser["sub"]
    
    try:
        savePreference(steamId, gameId, "disliked")
        return {"status": "success", "gameId": gameId, "preference": "disliked", "message": f"Game {gameId} disliked"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/preferences/{gameId}")
async def removePreference(gameId: str, currentUser: dict = Depends(verifyToken)):
    """
    Remove a preference (undo like/dislike)
    """
    steamId = currentUser["sub"]
    
    try:
        deletePreference(steamId, gameId)
        return {"status": "success", "gameId": gameId, "message": f"Preference removed for game {gameId}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/preferences/liked")
async def getLikedGames(currentUser: dict = Depends(verifyToken)):
    """
    Get all liked games with full details
    """
    steamId = currentUser["sub"]
    
    try:
        likedGameIds = getPreferenceGameIds(steamId, "liked")
        
        # Fetch full game details for each liked game
        likedGames = []
        for gameId in likedGameIds:
            gameData = getCachedGameDetails(gameId)
            
            if not gameData:
                # Fetch from Steam API
                gameData = fetchGameDetailsWithRetry(gameId)
                if gameData:
                    cacheGameDetails(gameId, gameData)
            
            if gameData:
                transformedGame = transformGameData(gameData)
                likedGames.append(transformedGame)
        
        return {
            "games": likedGames,
            "count": len(likedGames)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/preferences/disliked")
async def getDislikedGames(currentUser: dict = Depends(verifyToken)):
    """
    Get all disliked games with full details
    """
    steamId = currentUser["sub"]
    
    try:
        dislikedGameIds = getPreferenceGameIds(steamId, "disliked")
        
        # Fetch full game details for each disliked game
        dislikedGames = []
        for gameId in dislikedGameIds:
            gameData = getCachedGameDetails(gameId)
            
            if not gameData:
                # Fetch from Steam API
                gameData = fetchGameDetailsWithRetry(gameId)
                if gameData:
                    cacheGameDetails(gameId, gameData)
            
            if gameData:
                transformedGame = transformGameData(gameData)
                dislikedGames.append(transformedGame)
        
        return {
            "games": dislikedGames,
            "count": len(dislikedGames)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/preferences/all")
async def getAllPreferences(currentUser: dict = Depends(verifyToken)):
    """
    Get all user preferences (liked and disliked)
    """
    steamId = currentUser["sub"]
    
    try:
        likedGameIds = getPreferenceGameIds(steamId, "liked")
        dislikedGameIds = getPreferenceGameIds(steamId, "disliked")
        
        return {
            "preferences": {
                "liked": [{"gameId": gid} for gid in likedGameIds],
                "disliked": [{"gameId": gid} for gid in dislikedGameIds]
            },
            "totals": {
                "liked": len(likedGameIds),
                "disliked": len(dislikedGameIds)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ROOT ENDPOINTS
@app.get("/")
def readRoot():
    """Root endpoint - API status"""
    return {
        "message": "Steam Pal API is running",
        "status": "healthy",
        "version": "1.0.0",
        "docs": "/docs",
        "steam_login": "/api/auth/steam/login"
    }

@app.get("/health")
def healthCheck():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)