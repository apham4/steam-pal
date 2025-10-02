# Backend

## Steam OAuth Authentication Setup

### 1. Get Steam Web API Key
1. Go to https://steamcommunity.com/dev/apikey
2. Sign in with your Steam account
3. Enter your domain name (use `localhost` for development)
4. Copy the generated API key

### 2. Environment Setup
1. Copy `.env.example` to `.env`

2. Generate a secure SECRET_KEY for JWT tokens:
```bash
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
```

3. Fill in your `.env` file with:
```env
SECRET_KEY=your-generated-secret-key
STEAM_API_KEY=your-steam-web-api-key
```

**Note**: 
- Keep your SECRET_KEY private and never commit it to version control
- Use a different SECRET_KEY for production
- The key should be at least 32 characters long for security

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Server
```bash
uvicorn main:app --reload
```


## Steam OAuth Flow

### Protected Endpoints (require JWT token):
- `GET /api/auth/me` - Get current authenticated user
- `POST /api/recommendations` - Get game recommendations
- `GET /api/recommendations/history` - Get user's past recommendation history (not yet implemented)

### Unprotected Endpoints (no token required):
- `GET /` - Root endpoint (API status)
- `GET /health` - Health check
- `GET /api/auth/steam/login` - Get Steam login URL
- `GET /api/auth/steam/callback` - Steam OAuth callback (automatic)
- `POST /api/auth/logout` - Logout

### How it works:
1. User clicks "Login with Steam" -> Frontend calls `/api/auth/steam/login` to get Steam login URL
2. User is redirected to Steam to authenticate 
3. Steam redirects back to `/api/auth/steam/callback`
4. Backend verifies with Steam and creates JWT token containing user info
5. User is redirected to frontend with token
6. Frontend stores token and uses it for API calls


## API Documentation
```
http://localhost:8000/docs
```

## API Health Test
```bash
curl http://localhost:8000/health
```

