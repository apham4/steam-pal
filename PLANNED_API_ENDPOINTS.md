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
- **Flow**: Steam redirects here → Backend verifies → Redirects to frontend with token
- **Redirect URL**: `http://localhost:5173?token=JWT_TOKEN_HERE`

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

### Get Game Recommendation
- **Endpoint**: `POST /api/recommendations`
- **Description**: Get AI-powered game recommendations
- **Authentication**: Required (Bearer token)
- **Headers**:
```
Authorization: Bearer YOUR_JWT_TOKEN
Content-Type: application/json
```
- **Request Body**:
```json
{
  "genres": ["RPG", "Action"],
  "tags": ["Story Rich", "Open World"],
  "needs format change".
}
```
- **Response**:
```json
{
  "game_id": "292030",
  "game_name": "The Witcher 3: Wild Hunt",
  "reasoning": "Based on your Steam profile and interest in RPG and Story Rich games, this is a perfect match",
  "needs format change".
}
```

## Feature 3: Recommendation History (not yet implemented)
- **Endpoint**: `GET /api/recommedations/history`
- **Description**: Get user's past recommendation history
- **Authentication**: Required (Bearer token)
- **Response**: 
```json
{
  "game_id": "292030",
  "game_name": "The Witcher 3: Wild Hunt",
  "reasoning": "Based on your Steam profile and interest in RPG and Story Rich games, this is a perfect match",
  "recommended_date": "2025-09-30T12:00:00Z",
  "user_feedback": "liked",
  "will add more stuff".
}
```


