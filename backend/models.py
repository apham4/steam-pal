from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Pydantic models define the "shape" of your API data.

class User(BaseModel):
    """Model for a user"""
    steam_id: str
    display_name: str
    avatar_url: str = ""
    profile_url: str = ""
    last_login: Optional[datetime] = None

class RecommendationRequest(BaseModel):
    """Model for recommendation request"""
    steamId: str
    genre: Optional[str] = None
    useWishlist: bool = False

class GameDetail(BaseModel):
    """Model for detailed game information"""
    id: str
    title: str
    thumbnail: str = ""
    releaseDate: str = ""
    publisher: str = ""
    developer: str = ""
    price: str = ""
    salePrice: str = ""
    description: str = ""

class Recommendation(BaseModel):
    """Model for a game recommendation"""
    game: GameDetail
    reasoning: str