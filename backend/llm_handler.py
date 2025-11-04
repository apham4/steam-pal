# AI integration for smart game recommendations

import google.generativeai as genai
import os
import json

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

        # DEBUG
        print(f"[DEBUG] Excluding {len(excludeGameIds)} games from recommendations")
        if excludeGameIds and len(excludeGameIds) > 0:
            sample_ids = list(excludeGameIds)[:3]
            in_prompt = sum(1 for game_id in sample_ids if str(game_id) in prompt)
            print(f"[DEBUG] Exclusion verification: {in_prompt}/{len(sample_ids)} sample IDs found in prompt")

        if "CRITICAL EXCLUSION RULES" in prompt:
            print(f"[DEBUG] Exclusion section found in prompt")
        else:
            print(f"[DEBUG] WARNING: Exclusion section not found in prompt")
        
        prompt_length = len(prompt)
        estimated_tokens = prompt_length // 4 
        print(f"[DEBUG] Prompt length: {prompt_length} chars (~{estimated_tokens} tokens)")
        
        if estimated_tokens > 500000:
            print(f"[DEBUG] WARNING: Prompt approaching token limit")

        try:
            # Define the generation config
            config = genai.types.GenerationConfig(
                    temperature=0.8, 
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
                # DEBUG
                print(f"[DEBUG] Suggested: {result['title']} (ID: {result['gameId']}, Score: {result['matchScore']}%)")
                
                if result['gameId'] in excludeGameIds:
                    print(f"[DEBUG] WARNING: Suggested game {result['gameId']} is in exclusion list")
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
        if excludeGameIds:
            excludedList = ", ".join(list(excludeGameIds))
        else:
            excludedList = "None (user has no owned games or recommendations yet)"

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

        **CRITICAL EXCLUSION RULES (VERY IMPORTANT):**
        - You MUST NOT, under any circumstances, recommend any game from the following list.
        Recommending a game from this list will result in a failed response: {excludedList}
        - Recommended game must be available on Steam
        - Recommended game should have positive reviews (Metacritic 70+)
        - Recommended game should match their playtime preferences

        **CRITICAL CONSISTENT RULES:**
        The 'gameId' you provide, the 'title' you provide, and the game discussed in the 'reason' MUST refer to the exact same game. Double-check this consistency before generating the final JSON output. Failure to maintain consistency will result in an invalid response.

        **YOUR TASK**
        Recommend ONE perfect game to the user that:
        1. Matches their requested genres and favorite genres
        2. Is similar to their most-played games
        3. They do not already own
        4. Has strong reviews
        5. **VALIDATION (VERY IMPORTANT):** Before outputting the JSON, verify that the game title mentioned anywhere inside your 'reason' text EXACTLY MATCHES the game corresponding to the 'gameId' you are providing. Do not mention any other game titles in the final 'reason' unless comparing directly to the user's top-played games.

        {thinkingSection}

        **RESPONSE FORMAT (JSON ONLY)**
        Before you output the JSON, double check that the game ID is not excluded AND that the game title in the 'reason' field matches the 'gameId' and 'title' fields. You MUST return ONLY a valid JSON object matching this exact schema. Do not add any other text, explanations, or markdown formatting. The entire response must be the raw JSON object.

        OUTPUT RULES:
        {{
          "gameId": ["The exact Steam App ID of the recommended game"],
          "title": ["The exact, official title of the recommended game"],
          "reasoning": "Write a compelling paragraph explaining WHY this game is a great fit for the user, referencing their specific games and play patterns. Ensure the game mentioned here matches the 'title' and 'gameId' fields.",
          "matchScore": ...,
          "similarTo": ["Up to 3 similar game titles"],
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