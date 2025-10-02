from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Pydantic models define the "shape" of your API data.

class User(BaseModel):
    steam_id: str
    display_name: str
    avatar_url: Optional[str] = None
    profile_url: Optional[str] = None
    last_login: Optional[datetime] = None

class SteamAuthCallback(BaseModel):
    """Model for Steam OpenID callback parameters"""
    openid_mode: str
    openid_ns: str
    openid_op_endpoint: str
    openid_claimed_id: str
    openid_identity: str
    openid_return_to: str
    openid_response_nonce: str
    openid_assoc_handle: str
    openid_signed: str
    openid_sig: str

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: User

class RecommendationFilters(BaseModel):
    genres: Optional[List[str]] = None
    tags: Optional[List[str]] = None

class Recommendation(BaseModel):
    game_id: str
    game_name: str
    reasoning: str