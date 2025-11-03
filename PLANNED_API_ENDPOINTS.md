# Planned API Endpoints

### Base URL
http://localhost:8000

### Authentication
All protected endpoints require a **JWT token** sent in **Bearer format**:
```
Authorization: Bearer <token>
```

## Feature 1: Steam OAuth Authentication

### Overview
Authenticate user via Steam OpenID protocol. Users log in through Steam's official login page, and the backend creates a JWT token containing their Steam profile information. The JWT token is used to authenticate all subsequent API requests.

#### 1. Get Steam Login URL
- **Endpoint**: `GET /api/auth/steam/login`
- **Description**: Returns Steam OpenID login URL for user authentication
- **Authentication**: None required
- **Response**:
```json
{
  "login_url": "https://steamcommunity.com/openid/login?openid.ns=http%3A//specs.openid.net/auth/2.0&openid.mode=checkid_setup&..."
}
```

#### 2. Steam OAuth Callback (Automatic)
- **Endpoint**: `GET /api/auth/steam/callback`
- **Description**: Handles Steam OAuth callback, verifies authentication, creates JWT token, and redirects to frontend
- **Authentication**: None required (handled by Steam)
- **Query Parameters**: Steam OpenID parameters (automatically provided by Steam)
- **Response:** Redirects to frontend with token: `http://localhost:5173/auth-callback.html?token=<token>`

#### 3. Get Current User
- **Endpoint**: `GET /api/auth/me`
- **Description**: Get current authenticated user's Steam profile
- **Authentication**: Required (Bearer token)
- **Response**:
```json
{
  "steamId": "76561197960287930",
  "displayName": "Jane Doe",
  "avatarUrl": "https://avatars.steamstatic.com/...",
  "profileUrl": "https://steamcommunity.com/profiles/76561197960287930",
  "lastLogin": "2025-09-30T12:00:00Z"
}
```

#### 4. Logout
- **Endpoint**: `POST /api/auth/logout`
- **Description**: Logout (client should discard token, server will invalidate)
- **Authentication**: Required (Bearer token)
- **Response**:
```json
{
  "status": "success",
  "message": "Logged out successfully"
}
```


## Feature 2: AI-Powered Game Recommendations

### Overview
Generate personalized game recommendations using Google Gemini AI. The system analyzes the user's Steam library (owned games, playtime, genres) and uses AI to discover games that match their preferences. Users can specify genres for targeted recommendations, or let the AI recommend based on their gaming profile. The system automatically excludes owned games, previously recommended games, and disliked games.

#### Get Game Recommendation
- **Endpoint**: `POST /api/recommendations`
- **Description**: Get AI-powered personalized game recommendations
- **Authentication**: Required (Bearer token)
- **Request Body (Option 1: Specify Genres)**: Genres are automatically saved for future use
```json
{
  "genres": ["Action", "Anime"]
}
```
- **Request Body (Option 2: Use Saved Genres)**: Uses previously saved genres from a list of popular genres, otherwise uses gaming profile
```json
{
  "genres": []
}
```
- **Request Body (Option 3: Open Recommendation)**: No saved genres - AI recommends based purely on gaming profile
```json
{
  "genres": []
}
```
- **Response**:
```json
{
  "game": {
    "gameId": "292030",
    "title": "The Witcher 3: Wild Hunt",
    "thumbnail": "https://cdn.akamai.steamstatic.com/steam/apps/292030/header.jpg",
    "releaseDate": "May 18, 2015",
    "publisher": "CD PROJEKT RED",
    "developer": "CD PROJEKT RED",
    "price": "$39.99",
    "salePrice": "$9.99",
    "description": "As war rages on throughout the Northern Realms..."
  },
  "reasoning": "Based on your Steam library of 150 games and your interest in...",
  "matchScore": 92
```


## Feature 3: Recommendation History

### Overview
Track and retrieve past game recommendations with full details. The system stores every recommendation generated, including the game details, AI reasoning, match score, and requested genres. Users can paginate through their history to revisit past suggestions.

#### Get Recommendation History
- **Endpoint**: `GET /api/recommendations/history`
- **Description**: Get paginated history of past recommendations for current user
- **Authentication**: Required (Bearer token)
- **Query Parameters:**
  - `page`: Page number (default: 1, min: 1)
  - `limit`: Items per page (default: 20, min: 1, max: 100)
- **Response**:
```json
{
  "recommendations": [
    {
      "steamId": "76561197960287930",
      "gameId": "570", 
      "title": "Dota 2",
      "thumbnail": "https://cdn.akamai.steamstatic.com/steam/apps/570/header.jpg",
      "releaseDate": "2011-04-19",
      "publisher": "Valve",
      "developer": "Valve",
      "price": "$9.99",
      "salePrice": "",
      "description": "Every day, millions of players worldwide enter battle...",
      "reasoning": "Based on your Steam library of 150 games, we recommend **Dota 2**...",
      "requestedGenres": ["Action", "Strategy"],
      "createdAt": 1735689600,
      "createdAtIso": "2025-01-01T00:00:00"
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 50,
  "pages": 3
}
```


## Feature 4: Admin Dashboard

### Overview
Endpoints for admin dashboard statistics, including logins, recommendation requests, actions taken, and aggregate/average stats. All endpoints support filtering by date range and aggregation type.

#### 1. Log User Events
- **Endpoint**: `POST /api/events/new`
- **Description**: Log that a user performed an action (login, logout, request recommendation, like, dislike, view, etc.).
- **Authentication**: Required (Bearer token)
- **Request Body**:
```json
{
  "steamId": "76561197960287930",
  "eventType": "like_recommendation",
  "gameId": "abc123"
}
```
- **Response**:
```json
{ "message": "Action logged" }
```
#### 2. Get User Events
- **Endpoint**: `GET /api/events`
- **Description**: Get user events data following optional filters.
- **Query Parameters:**
  - `steamId`: (Optional) filter by user.
  - `eventType`: (Optional) filter by comma-separated list of event types.
  - `from`: UNIX timestamp, inclusive lower bound.
  - `to`: UNIX timestamp, inclusive upper bound.
- **Request Body**:
```json
{
  "steamId": "76561197960287930",
  "eventType": "login,logout",
  "from": "1234567890",
  "to": "1234567890"
}
```
- **Response**:
```json
{
  "events": [
    {
      "steamId": "76561197960287930",
      "eventType": "login",
      "gameId": null,
      "timestamp": 1735689600
    },
    {
      "steamId": "76561197960287930",
      "eventType": "logout",
      "gameId": null,
      "timestamp": 1735693200
    }
  ]
}
```


## Feature 5: User Preferences/Recommendation Feedback

### Overview
Allow users to like or dislike games to improve future recommendations. The system stores user preferences and uses them to exclude disliked games from future recommendations. Users can manage their preferences (view, add, remove) across all recommendation interactions.

#### 1. Like a Game
- **Endpoint**: `POST /api/preferences/{gameId}/like`
- **Description**: Mark a game as liked
- **Authentication**: Required (Bearer token)
- **Path Parameters:**
  - `gameId`: Steam app ID
- **Response**:
```json
{
  "status": "success",
  "gameId": "570",
  "preference": "liked",
  "message": "Game 570 liked"
}
```

#### 2. Dislike a Game
- **Endpoint**: `POST /api/preferences/{gameId}/dislike`
- **Description**: Mark a game as disliked
- **Authentication**: Required (Bearer token)
- **Path Parameters:**
  - `gameId`: Steam app ID
- **Response**:
```json
{
  "status": "success",
  "gameId": "570",
  "preference": "disliked",
  "message": "Game 570 disliked"
}
```

#### 3. Remove Preference
- **Endpoint**: `DELETE /api/preferences/{gameId}`
- **Description**: Remove like/dislike preference for a game
- **Authentication**: Required (Bearer token)
- **Path Parameters:**
  - `gameId`: Steam app ID
- **Response**:
```json
{
  "status": "success",
  "gameId": "570",
  "message": "Preference removed for game 570"
}
```

#### 4. Get Liked Games
- **Endpoint**: `GET /api/preferences/liked`
- **Description**: Get all liked games with full details
- **Authentication**: Required (Bearer token)
- **Response**:
```json
{
  "games": [
    {
      "gameId": "570",
      "title": "Dota 2",
      "thumbnail": "https://cdn.akamai.steamstatic.com/steam/apps/570/header.jpg",
      "releaseDate": "2011-04-19",
      "publisher": "Valve",
      "developer": "Valve",
      "price": "$9.99",
      "salePrice": "",
      "description": "Every day, millions of players worldwide enter battle..."
    }
  ],
  "count": 15
}
```

#### 5. Get Disliked Games
- **Endpoint**: `GET /api/preferences/disliked`
- **Description**: Get all disliked games with full details
- **Authentication**: Required (Bearer token)
- **Response**: Same format as `/api/preferences/liked`

#### 6. Get All Preferences
- **Endpoint**: `GET /api/preferences/all`
- **Description**: Get all user preferences grouped by type (liked/disliked)
- **Authentication**: Required (Bearer token)
- **Response**:
```json
{
  "preferences": {
    "liked": [
      {
        "gameId": "570",
      }
    ],
    "disliked": [
      {
        "gameId": "730",
      }
    ]
  },
  "totals": {
    "liked": 15,
    "disliked": 8
  }
}
```


## Feature 6: Advanced Filtering

### Overview
Provide users with a curated list of popular genres, tags, and game modes for filtering recommendations. When a user requests a recommendation with specific genres, those genres are automatically saved as the user's filter preference for future use, eliminating the need to specify genres with every recommendation request. This feature works in conjunction with Feature 2's recommendation system.

#### 1. Get Available Genres/Tags/Modes
- **Endpoint**: `GET /api/filters/available-genres`
- **Description**: Get a curated list of popular genres, tags, and game modes for filtering
- **Authentication**: None required
- **Response**: 
```json
{
  "genres": [
    "Action", "Adventure", "Casual", "Farming", "Racing", "Strategy",
    "Simulation", "Sports", "Indie", "Puzzle", "Arcade", "Story Rich"
  ],
  "tags": [
    "Horror", "Sci-Fi", "Space", "Open World", "Anime", "Fantasy",
    "Survival", "Detective", "Mystery", "Retro", "Pixel Graphics"
  ],
  "modes": [
    "Single-player", "Multiplayer", "Co-op", "Remote Play", "VR Support",
    "First-Person", "Third-Person", "Online PvP", "Local Multiplayer"
  ]
}
```

#### 2. Get Saved Filter Preferences
- **Endpoint**: `GET /api/filters/genres`
- **Description**: Get user's previously saved genres
- **Authentication**: Required (Bearer token)
- **Response:**
```json
{
  "steamId": "76561198271182337",
  "savedGenres": ["Action", "Anime"]
}
```
