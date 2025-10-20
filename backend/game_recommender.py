# Main recommendation engine

from typing import Dict, List, Optional, Set
from llm_handler import getLLMHandler
from steam_api import fetchGameDetailsWithRetry, transformGameData
from db_helper import getCachedGameDetails, cacheGameDetails


class GameRecommender:
    """
    Recommendation orchestrator
    """
    def __init__(self, llmProvider: str = "gemini"):
        """
        Initialize recommender
        """
        self.llm = getLLMHandler(llmProvider)
    
    def generateRecommendation(
        self,
        steamId: str,
        gamingProfile: Dict,
        requestedGenres: List[str],
        excludeGameIds: Set[str]
    ) -> Optional[Dict]:
        """
        Generate AI-Powered game recommendation
        """
        print(f"Generating recommendation for user {steamId}")
        
        # Ask AI to discover game
        aiResult = self.llm.discoverGame(
            gamingProfile=gamingProfile,
            requestedGenres=requestedGenres,
            excludeGameIds=excludeGameIds
        )
        
        if not aiResult:
            print("AI failed to generate recommendation")
            return None
        
        # Extract AI result
        gameId = aiResult['gameId']
        title = aiResult['title']
        reasoning = aiResult['reasoning']
        matchScore = aiResult.get('matchScore', 85)
        
        print(f"The AI has recommended {title} with match score {matchScore}%")

        # Fetch game details from Steam
        gameData = self._getGameDetails(gameId)
        
        if not gameData:
            print(f"Failed to fetch game {gameId}")
            return None
        
        # Transform to frontend format
        transformedGame = transformGameData(gameData)

        return {
            "game": transformedGame,
            "reasoning": reasoning,
            "matchScore": matchScore
        }
    
    def _getGameDetails(self, gameId: str) -> Optional[Dict]:
        """
        Get game details (cached or fetch)
        """
        
        # Check cache first
        gameData = getCachedGameDetails(gameId)
        
        if not gameData:
            # Cache miss, fetch from Steam API
            gameData = fetchGameDetailsWithRetry(gameId)
            
            if gameData:
                cacheGameDetails(gameId, gameData)
        
        return gameData
    

def generateSmartRecommendation(
    steamId: str,
    gamingProfile: Dict,
    requestedGenres: List[str],
    excludeGameIds: Set[str],
) -> Optional[Dict]:
    """
    Public API for generating recommendations
    """
    recommender = GameRecommender()
    return recommender.generateRecommendation(
        steamId=steamId,
        gamingProfile=gamingProfile,
        requestedGenres=requestedGenres,
        excludeGameIds=excludeGameIds
    )
