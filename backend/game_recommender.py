# Main recommendation engine

import re

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
    
    def normalizeTitle(self, title: str) -> str:
        """
        Remove non-alphanumeric chars and convert to lowercase
        """
        if not title:
            return ""
        return re.sub(r'[^a-zA-Z0-9]', '', title).lower()

    def generateRecommendation(
        self,
        gamingProfile: Dict,
        requestedGenres: List[str],
        excludeGameIds: Set[str],
        logPrefix: str,
        maxRetries: int = 3
    ) -> Optional[Dict]:
        """
        Generate AI-Powered game recommendation
        """
        
        # Validation loop
        for attempt in range(maxRetries):
            print(f"[{logPrefix}] > AI Attempt {attempt + 1}/{maxRetries}")

            # Ask AI to discover game
            aiResult = self.llm.discoverGame(
                gamingProfile=gamingProfile,
                requestedGenres=requestedGenres,
                excludeGameIds=excludeGameIds
            )
            
            if not aiResult:
                print(f"[{logPrefix}] > AI failed to generate recommendation, retrying...")
                continue
        
            # Extract AI result
            gameId = aiResult['gameId']
            title = aiResult['title']
            reasoning = aiResult['reasoning']
            matchScore = aiResult.get('matchScore', 85)

            print(f"[{logPrefix}] > AI suggested: {title} (ID: {gameId}) with match score {matchScore}%")

            # Fetch game details from Steam
            gameData = self._getGameDetails(gameId)
        
            if not gameData:
                print(f"[{logPrefix}] > Failed to fetch game {gameId}")
                excludeGameIds.add(gameId)
                continue

            steamTitle = gameData.get('name')
            if not steamTitle:
                print(f"[{logPrefix}] > Fetched game {gameId} has no title")
                excludeGameIds.add(gameId)
                continue

            # Normalize titles for comparison
            titleNorm = self.normalizeTitle(title)
            steamTitleNorm = self.normalizeTitle(steamTitle)

            # Compare recommended title vs Steam API title
            if titleNorm not in steamTitleNorm and steamTitleNorm not in titleNorm:
                print(f"[{logPrefix}] > Title mismatch: AI='{title}', Steam='{steamTitle}'. Retrying...")
                excludeGameIds.add(gameId)
                continue

            # Validation success    
            print(f"[{logPrefix}] > Validation success: {title}")

            # Transform to frontend format
            transformedGame = transformGameData(gameData)

            return {
                "game": transformedGame,
                "reasoning": reasoning,
                "matchScore": matchScore
            }
        
        # If loop finishes, all retries failed
        print(f"[{logPrefix}] > Failed all {maxRetries} attempts.")
        return None

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
    gamingProfile: Dict,
    requestedGenres: List[str],
    excludeGameIds: Set[str],
    logPrefix: str = "[Main:1]"
) -> Optional[Dict]:
    """
    Public API for generating recommendations
    """
    recommender = GameRecommender()
    return recommender.generateRecommendation(
        gamingProfile=gamingProfile,
        requestedGenres=requestedGenres,
        excludeGameIds=excludeGameIds,
        logPrefix=logPrefix
    )
