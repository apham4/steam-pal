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

PLANNED API ENDPOINTS (Subject to change):
** GET /api/me
- Purpose: Get the profile of the currently logged-in user.
- Response: { "steam_id": "765...", "display_name": "Gamer123" }

** POST /api/recommendations
- Purpose: Request a new game recommendation. Can optionally include filters.
- Request body: { "genres": ["RPG", "Open World"], "tags": ["Story Rich"] }
- Response: { "game_id": "578080", "game_name": "The Witcher 3: Wild Hunt", "reasoning": "Because you enjoyed similar open-world RPGs..." }

** GET /api/recommendations
- Purpose: Get the list of all past recommendations for the logged-in user.
- Response: [ { "game_id": "578080", ... }, { "game_id": "271590", ... } ]

** POST /api/recommendations/{rec_id}/feedback
- Purpose: Submit feedback (like/dislike) for a specific recommendation.
- Request Body: { "liked": true }
- Response: { "status": "success" }