# Planned API Endpoints

### Base URL
http://localhost:8000


## Feature 1: Steam OAuth Authentication

#### 1. Get Steam Login URL
- **Endpoint**: `GET /api/auth/steam/login`
- **Description**: Returns Steam OpenID login URL
- **Authentication**: None required
- **Response**:
```json
{
  "login_url": "https://steamcommunity.com/openid/login?openid.ns=http%3A//specs.openid.net/auth/2.0&openid.mode=checkid_setup&..."
}
```


#### 2. Steam OAuth Callback (Automatic)
- **Endpoint**: `GET /api/auth/steam/callback`
- **Description**: Handles Steam OAuth callback and redirects to frontend with JWT token
- **Authentication**: None (handled by Steam)
- **Query Parameters:**
- `openid.ns` - OpenID namespace
- `openid.mode` - OpenID mode (should be "id_res")
- `openid.op_endpoint` - OpenID endpoint
- `openid.claimed_id` - User's Steam ID URL
- `openid.identity` - User identity
- `openid.return_to` - Return URL
- `openid.response_nonce` - Nonce
- `openid.assoc_handle` - Association handle
- `openid.signed` - Signed fields
- `openid.sig` - Signature

- **Response:**
Redirects to frontend with token as query parameter.


#### 3. Get Current User
- **Endpoint**: `GET /api/auth/me`
- **Description**: Get current authenticated user's Steam profile
- **Authentication**: Required (Bearer token)
- **Headers**:
```
Authorization: Bearer YOUR_JWT_TOKEN
```

- **Response**:
```json
{
  "steam_id": "76561197960287930",
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
- **Headers**:
```
Authorization: Bearer YOUR_JWT_TOKEN
```

- **Response**:
```json
{
  "status": "success",
  "message": "Logged out successfully"
}
```


## Feature 2: AI-Powered Game Recommendations

### Get Game Recommendation
- **Endpoint**: `POST /api/recommendations`
- **Description**: Get AI-powered game recommendations
- **Authentication**: Required (Bearer token - user identity extracted from token)
- **Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```
- **Request Body**:
```json
{
  "genres": ["RPG", "Action"],
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
  "reasoning": "Based on your Steam library of 150 games and your interest in RPG games, we recommend **The Witcher 3: Wild Hunt**.\n\nAs war rages on throughout the Northern Realms...\n\n**Genres:** RPG, Open World, Action\n**Released:** May 18, 2015\n**Developer:** CD PROJEKT RED\n\n**On Sale!** ~~$39.99~~ → $9.99"
}
```


## Feature 3: Recommendation History

### Get Recommendation History
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

### 1. Like a Game
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

### 2. Dislike a Game
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

### 3. Remove Preference
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

### 4. Get Liked Games
- **Endpoint**: `GET /api/preferences/liked`
- **Description**: Get all games liked by current user with full game details
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

### 5. Get Disliked Games
- **Endpoint**: `GET /api/preferences/disliked`
- **Description**: Get all games disliked by current user with full game details
- **Authentication**: Required (Bearer token)
- **Response**: Same format as `/api/preferences/liked`

### 6. Get All Preferences
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