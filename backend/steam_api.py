# Steam API Integration Module

import requests
import os
import time
from typing import Optional, Dict, List
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Steam API Configuration
STEAM_API_BASE = "https://api.steampowered.com"
STEAM_STORE_API = "https://store.steampowered.com/api"
STEAM_API_KEY = os.getenv("STEAM_API_KEY", "your-steam-web-api-key")

# API Configuration
API_TIMEOUT_SECONDS = int(os.getenv("API_TIMEOUT_SECONDS", "10"))


# GAME DETAILS
def fetchGameDetails(gameId: str) -> Optional[dict]:
    """
    Fetch game details from Steam API 
    """
    print(f"[fetchGameDetails] Fetching game {gameId} from Steam API")

    try:
        url = f"{STEAM_STORE_API}/appdetails"
        params = {"appids": gameId, "cc": "US"}
        
        response = requests.get(url, params=params, timeout=API_TIMEOUT_SECONDS)
        response.raise_for_status()
        
        data = response.json()

        if not data.get(gameId):
            print(f"[fetchGameDetails] No data found for game {gameId}")
            return None

        if not data[gameId].get("success"):
            print(f"[fetchGameDetails] Steam API returned success=false for {gameId}")
            return None

        gameData = data[gameId].get("data")

        if not gameData:
            print(f"[fetchGameDetails] No game data for {gameId}")
            return None
        
        print(f"[fetchGameDetails] Fetched: {gameData.get('name', 'Unknown')}")
        return gameData
        
    except requests.exceptions.Timeout:
        print(f"[fetchGameDetails] Timeout for game {gameId}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[fetchGameDetails] Request error for {gameId}: {e}")
        return None
    except Exception as e:
        print(f"[fetchGameDetails] Unexpected error for {gameId}: {e}")
        return None    


def fetchGameDetailsWithRetry(gameId: str, maxRetries: int = 3) -> Optional[dict]:
    """
    Fetch game details with retry logic for transient failures
    """
    for attempt in range(maxRetries):
        shouldRetry = False
        try:
            url = f"{STEAM_STORE_API}/appdetails"
            params = {"appids": gameId, "cc": "US"}

            response = requests.get(url, params=params, timeout=API_TIMEOUT_SECONDS)

            # Success
            if response.status_code == 200:
                data = response.json()
                
                if data.get(gameId, {}).get("success"):
                    gameData = data[gameId]["data"]
                    print(f"[Attempt {attempt + 1}] Success: {gameData.get('name')}")
                    return gameData
                else:
                    # Game doesn't exist or is region-locked
                    print(f"[Attempt {attempt + 1}] Game {gameId} not available")
                    return None
            
            # Rate limited
            elif response.status_code == 429:
                print(f"[Attempt {attempt + 1}] Rate limited (429)")
                shouldRetry = True

            # Server error    
            elif response.status_code >= 500:
                print(f"[Attempt {attempt + 1}] Steam server error ({response.status_code})")
                shouldRetry = True

             # Client error (404, 403, etc.)
            else:
                print(f"[Attempt {attempt + 1}] HTTP {response.status_code}")
                return None
        
        except requests.Timeout:
            print(f"[Attempt {attempt + 1}] Request timeout")
            shouldRetry = True
        
        except requests.RequestException as e:
            print(f"[Attempt {attempt + 1}] Request error: {e}")
            shouldRetry = True
        
        except Exception as e:
            print(f"[Attempt {attempt + 1}] Unexpected error: {e}")
            shouldRetry = False # Unknown error - don't retry

        # Retry logic with exponential backoff
        if shouldRetry and attempt < maxRetries - 1:
            waitTime = 2 ** attempt  # 1s, 2s, 4s
            print(f"Retrying in {waitTime}s")
            time.sleep(waitTime)
        elif not shouldRetry:
            break     
         
    # All retries failed
    print(f"Failed to fetch {gameId} after {maxRetries} attempts")
    return None


# USER DATA
def fetchUserOwnedGames(steamId: str) -> List[Dict]:
    """
    Fetch user's game library
    """
    if not STEAM_API_KEY:
        print("[fetchUserOwnedGames] ERROR: STEAM_API_KEY not set in environment")
        return []

    try:
        print(f"[fetchUserOwnedGames] Fetching from Steam API: {steamId}")

        url = f"{STEAM_API_BASE}/IPlayerService/GetOwnedGames/v0001/"
        params = {
            "key": STEAM_API_KEY,
            "steamid": steamId,
            "include_appinfo": 1, # Include game names
            "include_played_free_games": 1,
            "format": "json"
        }

        response = requests.get(url, params=params, timeout=API_TIMEOUT_SECONDS)
        response.raise_for_status()
        
        data = response.json()
        games = data.get("response", {}).get("games", [])

        print(f"[fetchUserOwnedGames] Fetched {len(games)} games for user {steamId}")
        return games
        
    except requests.exceptions.Timeout:
        print(f"[fetchUserOwnedGames] Timeout for {steamId}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"[fetchUserOwnedGames] Request error: {e}")
        return []
    except Exception as e:
        print(f"[fetchUserOwnedGames] Unexpected error: {e}")
        return []


def fetchUserProfile(steamId: str) -> Optional[Dict]:
    """
    Fetch user profile
    """
    if not STEAM_API_KEY:
        print("[fetchUserProfile] ERROR: STEAM_API_KEY not set in environment")
        return None
    
    try:
        print(f"[fetchUserProfile] Fetching profile for {steamId}...")
        
        url = f"{STEAM_API_BASE}/ISteamUser/GetPlayerSummaries/v0002/"
        params = {
            "key": STEAM_API_KEY,
            "steamids": steamId
        }
        
        response = requests.get(url, params=params, timeout=API_TIMEOUT_SECONDS)
        response.raise_for_status()
        
        data = response.json()
        players = data.get("response", {}).get("players", [])
        
        if not players:
            print(f"[fetchUserProfile] No profile found")
            return None
        
        profile = players[0]
        print(f"[fetchUserProfile] Found: {profile.get('personaname')}")
        return profile
        
    except requests.exceptions.Timeout:
        print(f"[fetchUserProfile] Timeout for {steamId}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[fetchUserProfile] Request error: {e}")
        return None
    except Exception as e:
        print(f"[fetchUserProfile] Unexpected error: {e}")
        return None

# DATA TRANSFORMATION
def transformGameData(gameData: Dict) -> Dict:
    """
    Transform raw Steam API response to frontend-compatible format
    """
    try:
        priceOverview = gameData.get("price_overview", {})
        
        # Get release date
        releaseDate = gameData.get("release_date", {}).get("date", "")
        
        # Get developers and publishers
        developers = gameData.get("developers", [])
        publishers = gameData.get("publishers", [])
        
        return {
            "gameId": str(gameData.get("steam_appid", "0")),
            "title": gameData.get("name", "Unknown Game"),
            "thumbnail": gameData.get("header_image", ""),
            "releaseDate": releaseDate,
            "publisher": ", ".join(publishers) if publishers else "",
            "developer": ", ".join(developers) if developers else "",
            "price": formatPrice(priceOverview),
            "salePrice": formatSalePrice(priceOverview),
            "description": gameData.get("short_description", "")
        }
    except Exception as e:
        print(f"[transformGameData] Error transforming data: {e}")
        # Return minimal valid structure with all required fields as strings
        return {
            "gameId": str(gameData.get("steam_appid", "0")),
            "title": gameData.get("name", "Unknown Game"),
            "thumbnail": "",
            "releaseDate": "",
            "publisher": "",
            "developer": "",
            "price": "",
            "salePrice": "",
            "description": ""
        }
    

# PRICE FORMATTING
def formatPrice(priceOverview: Optional[Dict]) -> str:
    """
    Format price from Steam API response
    """
    if not priceOverview:
        return "Free to Play"
    
    try:
        # Steam returns price in cents
        final_price = priceOverview.get("final", 0) / 100
        currency = priceOverview.get("currency", "USD")

        # Format based on currency
        if currency == "USD":
            return f"${final_price:.2f}"
        elif currency == "EUR":
            return f"€{final_price:.2f}"
        elif currency == "GBP":
            return f"£{final_price:.2f}"
        else:
            return f"{final_price:.2f} {currency}"
            
    except Exception as e:
        print(f"[formatPrice] Error formatting price: {e}")
        return "Price unavailable"


def formatSalePrice(priceOverview: Optional[Dict]) -> str:
    """
    Format sale price if game is on discount
    """
    if not priceOverview:
        return ""
    
    try:
        discountPercent = priceOverview.get("discount_percent", 0)

        if discountPercent == 0:
            return ""  # No sale
        
        # Return the discounted price
        return formatPrice(priceOverview)

    except Exception as e:
        print(f"[formatSalePrice] Error formatting sale price: {e}")
        return ""




        
