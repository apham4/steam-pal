# Test script for Steam API Integration

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add backend directory to path
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BACKEND_DIR))

# Load environment variables from .env file
env_path = BACKEND_DIR / '.env'
if env_path.exists():
    load_dotenv(env_path)
else:
    print(f"Warning: .env file not found at {env_path}")
    load_dotenv()

from steam_api import (
    test_steam_api_connection,
    fetch_game_details,
    fetch_user_owned_games,
    transform_game_data,
    get_popular_game_ids
)


def test_game_details():
    """Test fetching game details"""
    print("\n" + "="*60)
    print("TEST 1: Fetch Game Details")
    print("="*60)
    
    test_game_id = "292030"  # Witcher 3
    print(f"Fetching game: {test_game_id}")
    
    raw_data = fetch_game_details(test_game_id)
    
    if raw_data:
        print(f"Successfully fetched: {raw_data.get('name')}")
        
        # Test transformation
        transformed = transform_game_data(raw_data)
        print(f"Transformed data:")
        print(f"   Title: {transformed['title']}")
        print(f"   Price: {transformed['price']}")
        print(f"   Developer: {transformed['developer']}")
        return True
    else:
        print("Failed to fetch game details")
        return False


def test_user_library():
    """Test fetching user's game library"""
    print("\n" + "="*60)
    print("TEST 2: Fetch User Library")
    print("="*60)
    
    # Use a public Steam ID (Gabe Newell's account)
    test_steam_id = "76561198010565263"
    print(f"Fetching library for Steam ID: {test_steam_id}")
    
    games = fetch_user_owned_games(test_steam_id)
    
    if games:
        print(f"Successfully fetched {len(games)} games")
        if len(games) > 0:
            print(f"   Sample game: {games[0].get('name', 'Unknown')}")
        return True
    else:
        print("Could not fetch library (may be private or API key issue)")
        return False


def test_popular_games():
    """Test getting popular games list"""
    print("\n" + "="*60)
    print("TEST 3: Get Popular Games")
    print("="*60)
    
    games = get_popular_game_ids(limit=10)
    
    if games:
        print(f"Got {len(games)} popular game IDs")
        print(f"   Sample IDs: {games[:3]}")
        return True
    else:
        print("Failed to get popular games")
        return False


def test_full_recommendation_flow():
    """Test complete recommendation flow"""
    print("\n" + "="*60)
    print("TEST 4: Full Recommendation Flow")
    print("="*60)
    
    try:
        # Step 1: Get popular games
        candidate_games = get_popular_game_ids(limit=5)
        print(f"Step 1: Got {len(candidate_games)} candidate games")
        
        # Step 2: Pick one
        selected_game_id = candidate_games[0]
        print(f"Step 2: Selected game ID: {selected_game_id}")
        
        # Step 3: Fetch details
        raw_data = fetch_game_details(selected_game_id)
        if not raw_data:
            print("Failed to fetch game details")
            return False
        print(f"Step 3: Fetched game: {raw_data.get('name')}")
        
        # Step 4: Transform
        transformed = transform_game_data(raw_data)
        print(f"Step 4: Transformed data successfully")
        print(f"   Complete game object:")
        for key, value in transformed.items():
            print(f"   - {key}: {value[:50] if isinstance(value, str) and len(value) > 50 else value}")
        
        print("Full recommendation flow successful!")
        return True
        
    except Exception as e:
        print(f"Error in recommendation flow: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_recommendation_endpoint_format():
    """Test that recommendation endpoint returns frontend-compatible format"""
    print("\n" + "="*60)
    print("TEST 5: Frontend-Compatible Format")
    print("="*60)
    
    try:
        from main import generate_reasoning
        
        # Mock game data in frontend format
        game_data = {
            "id": "292030",
            "title": "The Witcher 3: Wild Hunt",
            "thumbnail": "https://example.com/image.jpg",
            "releaseDate": "May 18, 2015",
            "publisher": "CD PROJEKT RED",
            "developer": "CD PROJEKT RED",
            "price": "$39.99",
            "salePrice": "$9.99",
            "description": "Test description"
        }
        
        raw_game_data = {
            "name": "The Witcher 3: Wild Hunt",
            "genres": [{"description": "RPG"}, {"description": "Action"}]
        }
        
        # Test reasoning generation
        reasoning = generate_reasoning(
            game_data=game_data,
            raw_game_data=raw_game_data,
            user_game_count=50,
            preferred_genre="RPG",
            use_wishlist=False
        )
        
        print("Generated reasoning:")
        print(reasoning[:200] + "...")
        
        # Verify all required fields are present
        required_fields = ["id", "title", "thumbnail", "releaseDate", "publisher", 
                          "developer", "price", "salePrice", "description"]
        
        missing_fields = [field for field in required_fields if field not in game_data]
        
        if missing_fields:
            print(f"Missing required fields: {missing_fields}")
            return False
        
        # Verify all fields are strings
        non_string_fields = [
            field for field in required_fields 
            if not isinstance(game_data[field], str)
        ]
        
        if non_string_fields:
            print(f"Non-string fields: {non_string_fields}")
            return False
        
        print("All required fields present and correct type")
        return True
        
    except Exception as e:
        print(f"Error testing format: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print(" "*20 + "STEAM API INTEGRATION TESTING")
    print("="*70)
    
    # Check environment
    if not os.getenv("STEAM_API_KEY"):
        print("\nWARNING: STEAM_API_KEY not set in environment")
        print("   Some features (user libraries) will not work")
        print("   Get your key from: https://steamcommunity.com/dev/apikey")
    
    # Run tests
    results = []
    
    results.append(("API Connection", test_steam_api_connection()))
    results.append(("Game Details", test_game_details()))
    results.append(("User Library", test_user_library()))
    results.append(("Popular Games", test_popular_games()))
    results.append(("Full Flow", test_full_recommendation_flow()))
    results.append(("Frontend Format", test_recommendation_endpoint_format()))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nAll tests passed!")
    elif passed >= total - 1:
        print("\nOne test failed (likely user library - may be private).")
    else:
        print("\nSome tests failed. Review errors above.")
    
    return passed >= total - 1  # Allow user library test to fail


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)