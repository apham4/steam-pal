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
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "steam_id": "76561197960287930",
    "display_name": "PlayerName",
    "avatar_url": "https://avatars.steamstatic.com/...",
    "profile_url": "https://steamcommunity.com/profiles/76561197960287930",
    "last_login": "2025-10-07T12:00:00"
  }
}
```


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
  "display_name": "Jane Doe",
  "avatar_url": "https://avatars.steamstatic.com/...",
  "profile_url": "https://steamcommunity.com/profiles/76561197960287930",
  "last_login": "2025-09-30T12:00:00Z"
}
```


#### 4. Logout
- **Endpoint**: `POST /api/auth/logout`
- **Description**: Logout (client should discard token)
- **Authentication**: None required
- **Response**:
```json
{
  "message": "Logged out successfully"
}
```


## Feature 2: AI-Powered Game Recommendations

### 5. Get Game Recommendation
- **Endpoint**: `POST /api/recommendations`
- **Description**: Get AI-powered game recommendations
- **Authentication**: Required (Bearer token)
- **Headers**:
```
Authorization: Bearer <access_token>
Content-Type: application/json
```
- **Request Body**:
```json
{
  "steamId": "76561197960287930",
  "genre": "RPG",
  "useWishlist": false
}
```
- **Response**:
```json
{
  "game": {
    "id": "292030",
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


