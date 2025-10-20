# AI integration for smart game recommendations

from turtle import title
import google.generativeai as genai
import os
import json
import re
from typing import Dict, List, Optional, Set
from dotenv import load_dotenv
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Load environment variables
load_dotenv()

class LLMHandler:
    """
    Handles LLM interactions
    """
    def __init__(self, provider: str="gemini"):
        """
        Initialize LLM provider
        """
        self.provider = provider

        if provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not found in environment variables")
            
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-flash-latest')
        else:
            raise ValueError(f"Unsupported provider: {provider}")


    # AI-Powered Game Discovery
    def discoverGame(
        self, 
        gamingProfile: Dict,
        requestedGenres: List[str],
        excludeGameIds: Set[str],
    ) -> Optional[Dict]:
        """
        Use AI to discover the perfect game
        """ 
        # Build rich context prompt
        prompt = self.buildPrompt(
            gamingProfile,
            requestedGenres,
            excludeGameIds,
        )

        print(f"Asking AI for recommendation...")

        try:
            # Define the generation config
            config = genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.95,
                    top_k=50,
                    max_output_tokens=2048,
                    response_mime_type="application/json" # Force JSON output
                )

            # Define safety settings
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            }

            # Call AI
            response = self.model.generate_content(
                prompt,
                generation_config=config,
                safety_settings=safety_settings
            )

            # Parse response
            result = self.parseResponse(response.text)

            if result:
                print(f"AI recommended: {result['title']} (ID: {result['gameId']})")
                return result
            else:
                print(f"Failed to parse AI response")
                return None

        except Exception as e:
            print(f"LLM API error: {e}")
            return None


    # Prompt Engineering
    def buildPrompt(
        self,
        gamingProfile: Dict,
        requestedGenres: List[str],
        excludeGameIds: Set[str],
    ) -> str:
        """
        Build comprehensive AI prompt
        """
        # Extract profile details
        topGames = gamingProfile.get('topGames', [])
        totalPlaytime = gamingProfile.get('totalPlaytime', 0)
        gameCount = gamingProfile.get('gameCount', 0)
        recentlyActiveGames = gamingProfile.get('recentlyActiveGames', [])
        mostPlayedGames = gamingProfile.get('mostPlayedGames', [])
        favoriteGenres = gamingProfile.get('favoriteGenres', [])


        # Format top games list
        topGamesList = "\n".join([
            f"  {i+1}. {title} — {hours:.0f} hours"
            for i, (gameId, title, hours) in enumerate(topGames)
        ]) if topGames else "  (No significant playtime data)"
    
        # Format recently active games list
        recentlyActiveList = "\n".join([
            f" {title} — {hours:.0f} hours (last 2 weeks)"
            for gameId, title, hours in recentlyActiveGames[:5]
        ]) if recentlyActiveGames else "  (No recent activity)"
    
        # Format most played games list
        mostPlayedList = "\n".join([
            f" {title} — {hours:.0f} hours"
            for gameId, title, hours in mostPlayedGames
        ]) if mostPlayedGames else "  (None yet)"

        # Format genres
        if favoriteGenres:
            favoriteGenresStr = ", ".join(favoriteGenres[:5])
        else:
            favoriteGenresStr = "Not enough data - analyzing top games instead"

        if requestedGenres:
            requestedGenresStr = ", ".join(requestedGenres)
        else:
            requestedGenresStr = "No specific genres requested - recommend based on their play history"    
        
        # Format excluded games
        excludedList = ", ".join(list(excludeGameIds)[:10])
        if len(excludeGameIds) > 10:
            excludedList += f"... and {len(excludeGameIds) - 10} more"

        if topGames and len(topGames) > 0:
            topGameHours = topGames[0][2]
            topGameTitle = topGames[0][1]
            thinkingSection = f"""Think about:
    - What made them spend {topGameHours:.0f} hours in {topGameTitle}?
    - What gameplay elements do their top games share?
    - What would be a natural progression from their current favorites?"""
        else:
            thinkingSection = """Think about:
    - What types of games are popular and highly rated?
    - What games would appeal to a new or casual gamer?
    - What games have broad appeal across genres?"""

        # Gaming experience level
        if totalPlaytime > 1000:
            experience = "Hardcore"
        elif totalPlaytime > 100:
            experience = "Casual"
        else:
            experience = "New"

        # Build prompt
        prompt = f"""You are an expert Steam game recommendation AI with deep knowledge of:
        - 50,000+ games in Steam's catalog
        - Gaming trends and hidden gems
        - Player preferences and playstyles

        **USER'S GAMING PROFILE**

        LIBRARY STATS:
        - Total Games Owned: {gameCount}
        - Total Playtime: {totalPlaytime:.0f} hours
        - Gaming Experience: {experience}

        TOP 10 MOST-PLAYED GAMES:
        {topGamesList}

        RECENTLY ACTIVE GAMES (Last 2 Weeks):
        {recentlyActiveList}

        MOST-PLAYED GAMES (50+ hours):
        {mostPlayedList}

        FAVORITE GENRES (by playtime):
        {favoriteGenresStr}

        **RECOMMENDATION REQUIREMENTS**

        USER REQUESTED:
        {f"Genres: {requestedGenresStr}"}

        CONSTRAINTS:
        - Must NOT be: {excludedList}
        - Must be available on Steam
        - Should have positive reviews (Metacritic 70+)
        - Should match their playtime preferences

        **YOUR TASK**
        Recommend ONE perfect game to the user that:
        1. Matches their requested genres and favorite genres
        2. Is similar to their most-played games
        3. They do not already own
        4. Has strong reviews

        {thinkingSection}

        **RESPONSE FORMAT (JSON ONLY)**
        You MUST return ONLY a valid JSON object matching this exact schema. Do not add any other text, explanations, or markdown formatting. The entire response must be the raw JSON object.

        {{
          "gameId": "1621690",
          "title": "Core Keeper",
          "reasoning": "Since you loved the farming and exploration in Stardew Valley, you'll feel right at home in Core Keeper. It takes those ideas and adds co-op, massive underground caverns to mine, and epic boss fights.",
          "matchScore": 92,
          "similarTo": ["Stardew Valley", "Terraria"]
        }}

        **REASONING INSTRUCTIONS::**
        - The "reasoning" text MUST be engaging and written directly to the user (e.g., "You'll like this because...", "Since you enjoyed...").
        - It must clearly connect one of their most-played games to the new recommendation.
        - Do NOT say "Based on your gaming profile."

        **IMPORTANT:**
        - gameId MUST be the actual Steam App ID (numeric string)
        - reasoning should be 2-3 sentences mentioning their specific games and play patterns
        - matchScore should be 0-100 (confidence level)
        - similarTo should list 1-3 games from their library
        - NO additional text outside the JSON
        - Ensure the game exists on Steam and is currently available

        JSON Response:
        """
    
        return prompt


    # Response Parsing
    def parseResponse(
            self,
            responseText: str
    ) -> Optional[Dict]:
        """
        Parse AI JSON response
        """
        try:
            # Try direct JSON parse
            result = json.loads(responseText.strip())
        
            # Validate required fields
            if "gameId" in result and "title" in result and "reasoning" in result:
                return {
                    "gameId": str(result["gameId"]),
                    "title": result["title"],
                    "reasoning": result["reasoning"],
                    "matchScore": result.get("matchScore", 85),
                    "similarTo": result.get("similarTo", [])
                }
            else:
                # The JSON was valid but missing required fields
                print(f"Failed to parse AI response: JSON missing required fields. Got: {responseText[:200]}")
                return None
        
        except json.JSONDecodeError as e:
            print(f"Failed to decode AI JSON response: {e}")
            print(f"Received text: {responseText[:200]}")
            return None


def getLLMHandler(provider: str = "gemini") -> LLMHandler:
    return LLMHandler(provider)