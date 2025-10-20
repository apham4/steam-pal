from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator
from typing import List

# Pydantic models define the "shape" of your API data.

class UserResponse(BaseModel):
    """User response model with snake_case aliases for frontend"""
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )
    
    steamId: str = Field(..., serialization_alias="steam_id")
    displayName: str = Field(..., serialization_alias="display_name")
    avatarUrl: str = Field(..., serialization_alias="avatar_url")
    profileUrl: str = Field(..., serialization_alias="profile_url")
    lastLogin: str = Field(..., serialization_alias="last_login")
    
class RecommendationRequest(BaseModel):
    """Model for recommendation request"""
    genres: List[str] = []

class GameDetail(BaseModel):
    """Model for detailed game information"""
    gameId: str = ""
    title: str = ""
    thumbnail: str = ""
    releaseDate: str = ""
    publisher: str = ""
    developer: str = ""
    price: str = ""
    salePrice: str = ""
    description: str = ""

    # Validator to convert int to string for gameId
    @field_validator('gameId', mode='before')
    @classmethod
    def convert_id_to_str(cls, v):
        """Convert integer game IDs to strings"""
        if isinstance(v, int):
            return str(v)
        return v if v is not None else ""

    # Computed field to provide 'id' alias for frontend
    @computed_field
    @property
    def id(self) -> str:
        """Provide 'id' as alias for frontend compatibility"""
        return self.gameId   

class Recommendation(BaseModel):
    """Model for a game recommendation"""
    game: GameDetail
    reasoning: str
    matchScore: int = Field(85, serialization_alias="match_score")