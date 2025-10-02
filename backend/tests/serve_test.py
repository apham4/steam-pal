# Simple HTTP server to serve the Steam OAuth test page

import http.server
import socketserver
import webbrowser
import os

PORT = 3000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def main():
    print("Starting Steam OAuth Test Server...")
    print(f"Serving directory: {DIRECTORY}")
    print(f"Test page will be available at: http://localhost:{PORT}/test_steam_oauth.html")
    print("\nInstructions:")
    print("1. Make sure your FastAPI backend is running on http://localhost:8000")
    print("2. Open the test page in your browser")
    print("3. Click 'Login with Steam' to test the OAuth flow")
    print("4. You'll be redirected to Steam, then back to the test page with authentication")
    print("Press Ctrl+C to stop the server\n")
    
    try:
        with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
            print(f"Server started at http://localhost:{PORT}")
            
            # Open the test page in browser
            test_url = f"http://localhost:{PORT}/test_steam_oauth.html"
            print(f"Opening test page: {test_url}")
            webbrowser.open(test_url)
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")

if __name__ == "__main__":
    main()