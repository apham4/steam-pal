Backend:
- Create virtual environment: 
	python -m venv .venv
- Activate it: 
	.venv\Scripts\activate
- Install dependencies from requirements.txt: 
	pip install -r requirements.txt
- To run app at http://localhost:8000
	unicorn main:app --reload

Frontend:
- Install dependencies (this might not be needed?):
	npm install
- Install Axios for making API calls:
	npm install axios (this might not be needed?)
- To run app at http://localhost:5173
	npm run dev

-----

DATA STRUCTURES:
profile: {
	steamId,
	name,
	avatar (link)
}

game: {
	id,
	title,
	thumbnail (link),
	releaseDate,
	publisher,
	developer,
	price
	salePrice,
	description (short version)
}

PLANNED API ENDPOINTS (Subject to change):
** POST /auth/steam
- Purpose: Authenticate user via Steam OpenID.
- Response: { 
	jwt_token, 
	profile, 
	liked (list of game objects), 
	disliked (list of game objects), 
	pastRecommendations (list of game objects) 
}

** POST /auth/guest
- Purpose: Guest login with Steam ID.
- Request body: { steamId }
- Response: {
	profile, 
	liked (list of game objects), 
	disliked (list of game objects), 
	pastRecommendations (list of game objects) 
}

** POST /recommendation
- Purpose: Request a new game recommendation.
- Include JWT token in Authorization header.
- Request body: {
	steamId, 
	genre (list of strings), 
	useWishlist (bool)}
- Response: {
	game (object),
	reasoning
}

** POST /recommendation/past
- Purpose: Request past recommendations.
- Include JWT token in Authorization header.
- Request body: {
	steamId
}
- Response: {
	array of game objects
}

** POST /preferences/update
- Purpose: Update liked/disliked/past recommendations lists for a user.
- Include JWT token in Authorization header.
- Request body: {
	steamId,
	liked (array of game objects), // Maybe this should just be an array of game ids?
	disliked (array of game objects), // Maybe this should just be an array of game ids?
	pastRecommendations (array of game objects), // Maybe this should just be an array of game ids?
}
- Response: {
	success: bool
}