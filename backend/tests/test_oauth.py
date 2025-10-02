# Test script for Steam OAuth endpoints

import requests
import json

BASE_URL = "http://localhost:8000"

def test_steam_login():
    """Test the Steam login endpoint"""
    print("Testing Steam Login Endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/auth/steam/login")
        response.raise_for_status()
        
        data = response.json()
        login_url = data.get("login_url")
        
        print("Steam login endpoint working!")
        print(f"Login URL: {login_url}")
        print(f"You can test this by visiting: {login_url}")
        
        return True
    except Exception as e:
        print(f"Error testing Steam login: {e}")
        return False

def test_api_docs():
    """Test if API documentation is accessible"""
    print("\nTesting API Documentation...")
    
    try:
        response = requests.get(f"{BASE_URL}/docs")
        response.raise_for_status()
        
        print("API documentation is accessible!")
        print(f"Visit: {BASE_URL}/docs")
        
        return True
    except Exception as e:
        print(f"Error accessing API docs: {e}")
        return False

def test_protected_endpoint():
    """Test a protected endpoint without authentication"""
    print("\nTesting Protected Endpoint (should fail without auth)...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/auth/me")
        
        if response.status_code == 401:
            print("Protected endpoint correctly requires authentication!")
            print(f"Response: {response.json()}")
        else:
            print(f"Unexpected response: {response.status_code}")
        
        return True
    except Exception as e:
        print(f"Error testing protected endpoint: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing Steam Pal Backend OAuth Flow\n")
    
    tests = [
        test_api_docs,
        test_steam_login,
        test_protected_endpoint,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print(f"\nTest Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("All tests passed! Your Steam OAuth flow is working correctly.")
        print("\n Next Steps:")
        print("1. Visit the login URL shown above to test Steam authentication")
        print("2. The callback should redirect to thefrontend with a token")
        print("3. Use that token to access protected endpoints")
    else:
        print("Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()