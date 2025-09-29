from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import models

app = FastAPI()

# --- IMPORTANT: CORS Middleware ---
# This allows your Vue front-end (running on a different port)
# to communicate with your FastAPI back-end.
origins = [
    "http://localhost:5173", # The default Vue dev server port
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MOCKED API Endpoints ---

@app.get("/api/me", response_model=models.User)
def get_current_user():
    """Returns a mock user for development."""
    return {"steam_id": "76561197960287930", "display_name": "Gabe Newell"}

@app.post("/api/recommendations", response_model=models.Recommendation)
def get_recommendation(filters: models.RecommendationFilters):
    """Returns a hardcoded mock game recommendation."""
    print(f"Received filters: {filters.genres}, {filters.tags}")
    return {
        "game_id": "292030",
        "game_name": "The Witcher 3: Wild Hunt",
        "reasoning": "Based on your interest in RPG and Story Rich games, this is a perfect match."
    }