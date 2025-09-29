from pydantic import BaseModel
from typing import List, Optional

# Pydantic models define the "shape" of your API data.

class User(BaseModel):
    steam_id: str
    display_name: str

class RecommendationFilters(BaseModel):
    genres: Optional[List[str]] = None
    tags: Optional[List[str]] = None

class Recommendation(BaseModel):
    game_id: str
    game_name: str
    reasoning: str