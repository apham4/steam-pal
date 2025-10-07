"""
Steam API Integration Module
Handles all interactions with Steam Web API and Store API
"""

import requests
import os
from typing import Optional, Dict, List
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Steam API endpoints
STEAM_API_BASE = "https://api.steampowered.com"
STEAM_STORE_API = "https://store.steampowered.com/api"
STEAM_API_KEY = os.getenv("STEAM_API_KEY")

# Timeouts for API calls (in seconds)
API_TIMEOUT = 10


def fetch_game_details(app_id: str) -> Optional[Dict]:
    """
    Fetch game details from Steam Store API
    Args:
        app_id: Steam application ID (e.g., "292030" for Witcher 3)
    Returns:
        Dictionary with game data in raw Steam format, or None if failed
    """
    print(f"[fetch_game_details] Fetching game ID: {app_id}")

    url = f"{STEAM_STORE_API}/appdetails"
    params = {"appids": app_id}

    try:      
        response = requests.get(url, params=params, timeout=API_TIMEOUT)
        response.raise_for_status()

        data = response.json()

        # Steam API returns: { "app_id": { "success": bool, "data": { ... } } }
        if not data.get(app_id):
            print(f"[fetch_game_details] No data returned for game {app_id}")
            return None
        
        if not data[app_id].get("success"):
            print(f"[fetch_game_details] Steam API returned success=false for game {app_id}")
            return None
        
        game_data = data[app_id].get("data")
        
        if not game_data:
            print(f"[fetch_game_details] No game data in response for {app_id}")
            return None
        
        print(f"[fetch_game_details] Successfully fetched and cached: {game_data.get('name', 'Unknown')}")
        return game_data
        
    except requests.exceptions.Timeout:
        print(f"[fetch_game_details] Timeout fetching game {app_id}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[fetch_game_details] Error fetching game {app_id}: {e}")
        return None
    except Exception as e:
        print(f"[fetch_game_details] Unexpected error fetching game {app_id}: {e}")
        return None


def fetch_user_owned_games(steam_id: str) -> List[Dict]:
    """
    Fetch list of games owned by a Steam user with caching
    Requires STEAM_API_KEY environment variable
    Args:
        steam_id: 64-bit Steam ID (e.g., "76561197960287930")
    Returns:
        List of game dictionaries with appid, name, playtime
    """
    if not STEAM_API_KEY:
        print("[fetch_user_owned_games] ERROR: STEAM_API_KEY not set in environment")
        return []

    try:
        print(f"[fetch_user_owned_games] Fetching from Steam API: {steam_id}")
        
        url = f"{STEAM_API_BASE}/IPlayerService/GetOwnedGames/v0001/"
        params = {
            "key": STEAM_API_KEY,
            "steamid": steam_id,
            "include_appinfo": 1,
            "include_played_free_games": 1,
            "format": "json"
        }
        
        response = requests.get(url, params=params, timeout=API_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        games = data.get("response", {}).get("games", [])
        
        print(f"[fetch_user_owned_games] Successfully fetched and cached {len(games)} games for user {steam_id}")
        return games
        
    except requests.exceptions.Timeout:
        print(f"[fetch_user_owned_games] Timeout fetching library for {steam_id}")
        return []
    except requests.exceptions.RequestException as e:
        print(f"[fetch_user_owned_games] Error fetching library for {steam_id}: {e}")
        return []
    except Exception as e:
        print(f"[fetch_user_owned_games] Unexpected error fetching library for {steam_id}: {e}")
        return []


def fetch_user_profile(steam_id: str) -> Optional[Dict]:
    """
    Fetch Steam user profile information with caching
    Requires STEAM_API_KEY environment variable
    Args:
        steam_id: 64-bit Steam ID
    Returns:
        Dictionary with user profile data
    """
    if not STEAM_API_KEY:
        print("[fetch_user_profile] ERROR: STEAM_API_KEY not set in environment")
        return None
    
    try:
        print(f"[fetch_user_profile] Fetching from Steam API: {steam_id}")
        
        url = f"{STEAM_API_BASE}/ISteamUser/GetPlayerSummaries/v0002/"
        params = {
            "key": STEAM_API_KEY,
            "steamids": steam_id
        }
        
        response = requests.get(url, params=params, timeout=API_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        players = data.get("response", {}).get("players", [])
        
        if not players:
            print(f"[fetch_user_profile] No profile found for {steam_id}")
            return None
        
        profile = players[0]

        print(f"[fetch_user_profile] Found profile: {profile.get('personaname', 'Unknown')}")
        return profile
        
    except requests.exceptions.Timeout:
        print(f"[fetch_user_profile] Timeout fetching profile for {steam_id}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[fetch_user_profile] Error fetching profile for {steam_id}: {e}")
        return None
    except Exception as e:
        print(f"[fetch_user_profile] Unexpected error fetching profile for {steam_id}: {e}")
        return None


def transform_game_data(raw_steam_data: Dict) -> Dict:
    """
    Transform raw Steam API response to frontend-compatible format
    Args:
        raw_steam_data: Raw game data from Steam Store API
    Returns:
        Dictionary matching GameDetail model (all strings, no None values)
    """
    try:
        price_overview = raw_steam_data.get("price_overview", {})
        
        # Get release date
        release_date = raw_steam_data.get("release_date", {})
        release_date_str = release_date.get("date", "") if isinstance(release_date, dict) else ""
        
        # Get developers and publishers
        developers = raw_steam_data.get("developers", [])
        publishers = raw_steam_data.get("publishers", [])
        
        return {
            "id": str(raw_steam_data.get("steam_appid", "0")),
            "title": raw_steam_data.get("name", "Unknown Game"),
            "thumbnail": raw_steam_data.get("header_image", ""),
            "releaseDate": release_date_str,
            "publisher": ", ".join(publishers) if publishers else "",
            "developer": ", ".join(developers) if developers else "",
            "price": format_price(price_overview),
            "salePrice": format_sale_price(price_overview),
            "description": raw_steam_data.get("short_description", "")
        }
    except Exception as e:
        print(f"[transform_game_data] Error transforming data: {e}")
        # Return minimal valid structure with all required fields as strings
        return {
            "id": str(raw_steam_data.get("steam_appid", "0")),
            "title": raw_steam_data.get("name", "Unknown Game"),
            "thumbnail": "",
            "releaseDate": "",
            "publisher": "",
            "developer": "",
            "price": "",
            "salePrice": "",
            "description": ""
        }


def format_price(price_overview: Optional[Dict]) -> str:
    """
    Format price from Steam API response
    Args:
        price_overview: Price data from Steam API
    Returns:
        Formatted price string (e.g., "$39.99" or "Free to Play")
    """
    if not price_overview:
        return "Free to Play"
    
    try:
        # Steam returns price in cents
        final_price = price_overview.get("final", 0) / 100
        currency = price_overview.get("currency", "USD")
        
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
        print(f"[format_price] Error formatting price: {e}")
        return "Price unavailable"


def format_sale_price(price_overview: Optional[Dict]) -> str:
    """
    Format sale price if game is on discount
    Args:
        price_overview: Price data from Steam API
    Returns:
        Formatted sale price or empty string if no discount
    """
    if not price_overview:
        return ""
    
    try:
        discount_percent = price_overview.get("discount_percent", 0)
        
        if discount_percent == 0:
            return ""  # No sale
        
        # Return the discounted price
        return format_price(price_overview)
        
    except Exception as e:
        print(f"[format_sale_price] Error formatting sale price: {e}")
        return ""


def get_game_genres(raw_steam_data: Dict) -> List[str]:
    """
    Extract genre names from Steam game data
    Args:
        raw_steam_data: Raw game data from Steam Store API
    Returns:
        List of genre strings
    """
    try:
        genres = raw_steam_data.get("genres", [])
        return [genre.get("description", "") for genre in genres if genre.get("description")]
    except Exception as e:
        print(f"[get_game_genres] Error extracting genres: {e}")
        return []


def get_popular_game_ids(limit: int = 100) -> List[str]:
    """
    Get list of popular game IDs for recommendations
    Args:
        limit: Maximum number of game IDs to return
    Returns:
        List of Steam app IDs as strings
    """
    popular_games = [
        # RPG
        "292030",   # The Witcher 3: Wild Hunt
        "72850",    # The Elder Scrolls V: Skyrim
        "648800",   # Elden Ring
        "1091500",  # Cyberpunk 2077
        "1174180",  # Red Dead Redemption 2
        "489830",   # The Elder Scrolls Online
        "1328670",  # Mass Effect Legendary Edition
        "1086940",  # Baldur's Gate 3
        
        # Action/Adventure
        "271590",   # Grand Theft Auto V
        "1245620",  # ELDEN RING
        "1942280",  # Starfield
        "1938090",  # Call of Duty®: Modern Warfare® III
        
        # Strategy
        "1097840",  # Sid Meier's Civilization VI
        "1466860",  # Age of Empires IV
        "394360",   # Hearts of Iron IV
        
        # Simulation
        "413150",   # Stardew Valley
        "1220",     # Euro Truck Simulator 2
        "255710",   # Cities: Skylines
        
        # Multiplayer
        "570",      # Dota 2
        "730",      # Counter-Strike 2
        "578080",   # PUBG: BATTLEGROUNDS
        "1172470",  # Apex Legends
        "252490",   # Rust
        "221100",   # DayZ
        
        # Indie
        "105600",   # Terraria
        "367520",   # Hollow Knight
        "548430",   # Deep Rock Galactic
        "322330",   # Don't Starve Together
        
        # Horror
        "418370",   # Phasmophobia
        "1966720",  # Lethal Company
        "736590",   # Resident Evil 2
        
        # Survival
        "346110",   # ARK: Survival Evolved
        "454850",   # Subnautica
        "383870",   # Firewatch
    ]
    
    return popular_games[:limit]


# Test function to verify API connectivity
def test_steam_api_connection() -> bool:
    """
    Test if Steam API is accessible and API key is valid
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        # Test 1: Check Steam Store API (no key needed)
        print("[test_steam_api] Testing Steam Store API...")
        game_data = fetch_game_details("292030")  # Witcher 3
        
        if not game_data:
            print("[test_steam_api] Steam Store API test failed")
            return False
        
        print(f"[test_steam_api] Steam Store API working: {game_data.get('name')}")
        
        # Test 2: Check Steam Web API (requires key)
        if not STEAM_API_KEY:
            print("[test_steam_api] STEAM_API_KEY not set - Web API tests skipped")
            return True  
        
        print("[test_steam_api] Testing Steam Web API...")
        
        # Use a known public Steam ID (Gabe Newell's account)
        test_steam_id = "76561198010565263"
        profile = fetch_user_profile(test_steam_id)
        
        if not profile:
            print("[test_steam_api] Steam Web API test failed")
            return False
        
        print(f"[test_steam_api] Steam Web API working: {profile.get('personaname')}")
        return True
        
    except Exception as e:
        print(f"[test_steam_api] Connection test failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("Steam API Connection Test")
    print("=" * 50)
    
    if test_steam_api_connection():
        print("\nAll Steam API tests passed!")
    else:
        print("\nSome Steam API tests failed. Check your configuration.")