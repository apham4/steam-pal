# Database helper functions for Steam Pal

import sqlite3
import json
import time
from datetime import datetime
from typing import List, Dict, Optional


DB_FILE = "steampal.db"


def getConnection():
    """
    Get database connection with row factory
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def initDatabase():
    """
    Initialize database tables
    """
    conn = getConnection()
    cursor = conn.cursor()
    
    try:
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                steamId TEXT PRIMARY KEY,
                displayName TEXT NOT NULL,
                avatarUrl TEXT,
                profileUrl TEXT,
                createdAt INTEGER NOT NULL,
                lastLogin INTEGER NOT NULL
            )
        """)
        
        # Recommendation table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                steamId TEXT NOT NULL,
                gameId TEXT NOT NULL,
                title TEXT NOT NULL,
                thumbnail TEXT DEFAULT '',
                releaseDate TEXT DEFAULT '',
                publisher TEXT DEFAULT '',
                developer TEXT DEFAULT '',
                price TEXT DEFAULT '',
                salePrice TEXT DEFAULT '',
                description TEXT DEFAULT '',
                reasoning TEXT NOT NULL,
                requestedGenres TEXT,
                createdAt INTEGER NOT NULL,
                matchScore INTEGER DEFAULT 80,
                UNIQUE(steamId, gameId),
                FOREIGN KEY (steamId) REFERENCES users(steamId)
        )
    """)
        
        # Preferences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                steamId TEXT NOT NULL,
                gameId TEXT NOT NULL,
                preference TEXT NOT NULL CHECK(preference IN ('liked', 'disliked')),
                createdAt INTEGER NOT NULL,
                UNIQUE(steamId, gameId),
                FOREIGN KEY (steamId) REFERENCES users(steamId)
            )
        """)
        
        # Owned games cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ownedGames (
                steamId TEXT NOT NULL,
                gameId TEXT NOT NULL,
                title TEXT NOT NULL,
                playtimeForever INTEGER DEFAULT 0,
                playtime2Weeks INTEGER DEFAULT 0,
                cachedAt INTEGER NOT NULL,
                PRIMARY KEY (steamId, gameId),
                FOREIGN KEY (steamId) REFERENCES users(steamId)
            )
        """)
        
        # Game details cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gameCache (
                gameId TEXT PRIMARY KEY,
                gameData TEXT NOT NULL,       
                cachedAt INTEGER NOT NULL
            )
        """)

        # User events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS userEvents (
                eventId INTEGER PRIMARY KEY AUTOINCREMENT,
                steamId TEXT NOT NULL,
                eventType TEXT NOT NULL,
                gameId TEXT,
                timestamp INTEGER NOT NULL,
                FOREIGN KEY (steamId) REFERENCES users(steamId)
            )
        """)

        # User filter genres table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS filterGenres (
                steamId TEXT PRIMARY KEY,
                savedGenres TEXT DEFAULT '[]',
                updatedAt INTEGER NOT NULL,
                FOREIGN KEY (steamId) REFERENCES users(steamId)
            )
        """)
        
        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_recommendations_user 
            ON recommendations(steamId, createdAt DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_preferences_user 
            ON preferences(steamId, preference)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ownedGames_user 
            ON ownedGames(steamId)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ownedGames_playtime
            ON ownedGames(steamId, playtimeForever DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_filter_genres_user
            on filterGenres(steamId)
        """)
        
        conn.commit()
        print("Database initialized successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"Database initialization error: {e}")
        raise
    finally:
        conn.close()


# User Management Functions
def saveUser(steamId: str, displayName: str, avatarUrl: str = "", profileUrl : str = "") -> bool:
    """
    Save or update user in database
    """
    conn = getConnection()
    cursor = conn.cursor()
    
    try:
        currentTime = int(time.time())

        cursor.execute("""
            INSERT INTO users (steamId, displayName, avatarUrl, profileUrl, createdAt, lastLogin)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(steamId) DO UPDATE SET
                displayName = excluded.displayName,
                avatarUrl = excluded.avatarUrl,
                profileUrl = excluded.profileUrl,
                lastLogin = excluded.lastLogin
        """, (steamId, displayName, avatarUrl, profileUrl, currentTime, currentTime))
        
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Error saving user: {e}")
        raise
    finally:
        conn.close()

def getUser(steamId: str) -> Optional[Dict]:
    """
    Get user from database
    """
    conn = getConnection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM users WHERE steamId = ?", (steamId,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        return None
        
    except Exception as e:
        print(f"Error getting user: {e}")
        return None
    finally:
        conn.close()


# Owned Cached Games Functions
def cacheOwnedGames(steamId: str, games: List[Dict]) -> bool:
    """
    Cache user's owned games from Steam API
    """
    conn = getConnection()
    cursor = conn.cursor()
    
    try:
        currentTime = int(time.time())
        
        # Clear old cache
        cursor.execute("DELETE FROM ownedGames WHERE steamId = ?", (steamId,))
        
        # Insert with playtime data
        for game in games:
            cursor.execute("""
                INSERT INTO ownedGames (
                    steamId, gameId, title, playtimeForever, 
                    playtime2weeks, cachedAt
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                steamId,
                str(game.get('appid', '')),
                game.get('name', 'Unknown'),
                game.get('playtime_forever', 0),
                game.get('playtime_2weeks', 0),
                currentTime
            ))
        
        conn.commit()
        print(f"Cached {len(games)} games with playtime data for user {steamId}")
        
    except Exception as e:
        conn.rollback()
        print(f"Error caching owned games: {e}")
        raise
    finally:
        conn.close()

def getOwnedGamesIds(steamId: str) -> List[str]:
    """
    Get cached owned games IDs
    """
    conn = getConnection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT gameId FROM ownedGames 
                       WHERE steamId = ?
        """, (steamId,))
        
        rows = cursor.fetchall()
        return [row['gameId'] for row in rows]
        
    except Exception as e:
        print(f"Error fetching owned games IDs: {e}")
        return []
    finally:
        conn.close()

def isOwnedGamesCacheRecent(steamId: str, maxAgeHours: int = 24) -> bool:
    """Check if owned games cache is recent enough"""
    conn = getConnection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT cachedAt FROM ownedGames 
            WHERE steamId = ?
            ORDER BY cachedAt DESC 
            LIMIT 1
        """, (steamId,))
        
        row = cursor.fetchone()

        # Check if row exists and has value
        if not row:
            return False
        
        cachedAt = row['cachedAt']
        currentTime = int(time.time())
        ageHours = (currentTime - cachedAt) / 3600
        
        return ageHours < maxAgeHours

    except Exception as e:
        print(f"Error checking cache freshness: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

def getUserGamingProfile(steamId: str) -> Dict:
    """
    Analyze user's gaming preferences from cached owned games
    """

    conn = getConnection()
    cursor = conn.cursor()

    try:
        # Get all owned games with playtime
        cursor.execute("""
            SELECT gameId, title, playtimeForever, playtime2Weeks 
            FROM ownedGames 
            WHERE steamId = ?
            ORDER BY playtimeForever DESC
        """, (steamId,))
        
        rows = cursor.fetchall()

        if not rows:
            return {
                'topGames': [],
                'totalPlaytime': 0,
                'recentlyActiveGames': [],
                'gameCount': 0,
                'mostPlayedGames': [],
                'favoriteGenres': []
            }

        # Convert to list
        games = [dict(row) for row in rows]

        # Total playtime in hours
        totalMinutes = sum(game['playtimeForever'] for game in games)
        totalPlaytime = round(totalMinutes / 60, 1)

        # Top 10 games by playtime
        topGames = [
            (str(game['gameId']), game['title'], round(game['playtimeForever'] / 60, 1))
            for game in games[:10]
        ]
        
        # Recently active games (played in last 2 weeks)
        recentlyActiveGames = [
            (str(game['gameId']), game['title'], round(game['playtime2Weeks'] / 60, 1))
            for game in games
            if game['playtime2Weeks'] and game['playtime2Weeks'] > 0
        ]
        # Sort by recent playtime
        recentlyActiveGames.sort(key=lambda x: x[2], reverse=True)

        # Most played games (50+ hours = 3000+ minutes)
        mostPlayedGames = [
            (str(game['gameId']), game['title'], round(game['playtimeForever'] / 60, 1))
            for game in games
            if game['playtimeForever'] >= 3000
        ]
        
        # Favorite genres from top games
        favoriteGenres = getUserFavoriteGenres(steamId, topGames)

        return {
            'topGames': topGames,
            'totalPlaytime': totalPlaytime,
            'recentlyActiveGames': recentlyActiveGames,
            'gameCount': len(games),
            'mostPlayedGames': mostPlayedGames,
            'favoriteGenres': favoriteGenres
        }
        
    except Exception as e:
        print(f"Error getting gaming profile: {e}")
        import traceback
        traceback.print_exc()
        return {
            'topGames': [],
            'totalPlaytime': 0,
            'recentlyActiveGames': [],
            'gameCount': 0,
            'mostPlayedGames': [],
            'favoriteGenres': []
        }
    finally:
        conn.close()

def getUserFavoriteGenres(steamId: str, topGames: List[tuple]) -> List[str]:
    """
    Get user's favorite genres using cached game data
    """
    genreCount = {}
    
    for gameId, title, hours in topGames:
        if hours < 5.0:
            continue
        
        # Get cached game data
        gameData = getCachedGameDetails(gameId)
        if not gameData:
            continue
        
        # Extract Steam's official genres
        genres = gameData.get('genres', [])
        for genre in genres:
            genreName = genre.get('description', '')
            if genreName:
                # Weight by playtime
                genreCount[genreName] = genreCount.get(genreName, 0) + hours
    
    # If we found genres from played games, sort and return top 5
    if genreCount:
        sortedGenres = sorted(
            genreCount.items(),
            key=lambda x: x[1],
            reverse=True
        )
    
        favoriteGenres = [genre for genre, hours in sortedGenres[:5]]
        return favoriteGenres
    
    # If no genre data found, return empty list
    return []


# Game Details Cache Funtions
def cacheGameDetails(gameId: str, gameData: Dict) -> bool:
    """
    Cache game details from Steam API (expires after 7 days by default)
    """
    conn = getConnection()
    cursor = conn.cursor()
    
    try:
        currentTime = int(time.time())
        
        cursor.execute("""
            INSERT OR REPLACE INTO gameCache
            (gameId, gameData, cachedAt)
            VALUES (?, ?, ?)
        """, (
            gameId,
            json.dumps(gameData),
            currentTime
        ))
        
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Error caching game: {e}")
        return False
    finally:
        conn.close()


def getCachedGameDetails(gameId: str, maxAgeHours: int = 168) -> Optional[Dict]:
    """
    Get cached game details (returns None if expired or not found)
    Default expiry: 7 days (168 hours)
    """
    conn = getConnection()
    cursor = conn.cursor()
    
    try:
        currentTime = int(time.time())
        maxAgeSeconds = maxAgeHours * 3600

        cursor.execute("""
            SELECT gameData, cachedAt FROM gameCache
            WHERE gameId = ? AND (? - cachedAt) < ?
        """, (gameId, currentTime, maxAgeSeconds))

        row = cursor.fetchone()
        
        if row:
            return json.loads(row['gameData'])

        return None
        
    except Exception as e:
        print(f"Error fetching cached game: {e}")
        return None
    finally:
        conn.close()


# Recommendation History Functions
def saveRecommendation(
    steamId: str, 
    game: Dict, 
    reasoning: str,
    matchScore: int,
    requestedGenres: List[str] = None
) -> Optional[int]:
    """
    Save a recommendation to database
    Returns recommendation ID if successful, None if duplicate
    """
    conn = getConnection()
    cursor = conn.cursor()
    
    try:
        currentTime = int(time.time())
        gameId = str(game.get('gameId', ''))
        
        # Check for duplicate
        cursor.execute("""
            SELECT rowid FROM recommendations 
            WHERE steamId = ? AND gameId = ?
        """, (steamId, gameId))

        if cursor.fetchone():
            return None
        
        # Insert new recommendation
        cursor.execute("""
            INSERT INTO recommendations 
            (steamId, gameId, title, thumbnail, 
             releaseDate, publisher, developer, price, salePrice, description,
             reasoning, requestedGenres, createdAt, matchScore)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            steamId,
            gameId,
            game.get('title', 'Unknown'),
            game.get('thumbnail', ''),
            game.get('releaseDate', ''),    
            game.get('publisher', ''),       
            game.get('developer', ''),       
            game.get('price', ''),            
            game.get('salePrice', ''),        
            game.get('description', ''),      
            reasoning,
            json.dumps(requestedGenres or []),
            currentTime,
            matchScore
        ))
        
        conn.commit()
        recId = cursor.lastrowid
        return recId

    except sqlite3.IntegrityError:
        # Duplicate recommendation
        conn.rollback()
        print(f"Duplicate recommendation prevented for game {gameId}")
        return None
    except Exception as e:
        conn.rollback()
        print(f"Error saving recommendation: {e}")
        raise
    finally:
        conn.close()

def getUserRecommendations(
    steamId: str, 
    limit: int = 20, 
    offset: int = 0
) -> List[Dict]:
    """
    Get user's recommendation history
    """
    conn = getConnection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT * FROM recommendations 
            WHERE steamId = ? 
            ORDER BY createdAt DESC 
            LIMIT ? OFFSET ?
        """, (steamId, limit, offset))
        
        rows = cursor.fetchall()

        recommendations = []
        for row in rows:
            recommendations.append({
                'steamId': row['steamId'],
                'gameId': row['gameId'],            
                'title': row['title'],
                'thumbnail': row['thumbnail'],        
                'releaseDate': row['releaseDate'],
                'publisher': row['publisher'],
                'developer': row['developer'],
                'price': row['price'],
                'salePrice': row['salePrice'],
                'description': row['description'],
                'reasoning': row['reasoning'],
                'requestedGenres': json.loads(row['requestedGenres']) if row['requestedGenres'] else [],
                'createdAt': row['createdAt'],
                'createdAtIso': datetime.fromtimestamp(row['createdAt']).isoformat(),
                'matchScore': row['matchScore']
            })
        
        return recommendations
        
    except Exception as e:
        print(f"Error getting recommendations: {e}")
        return []
    finally:
        conn.close()

def getRecommendationsCount(steamId: str) -> int:
    """Get total number of recommendations for a user"""
    conn = getConnection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT COUNT(*) as count FROM recommendations 
            WHERE steamId = ?
        """, (steamId,))
        
        row = cursor.fetchone()
        return row['count'] if row else 0
        
    except Exception as e:
        print(f"Error counting recommendations: {e}")
        return 0
    finally:
        conn.close()

def getRecommendedGameIds(steamId: str) -> set:
    """
    Get set of game IDs already recommended to user
    """
    conn = getConnection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT gameId FROM recommendations 
            WHERE steamId = ?
        """, (steamId,))
        
        rows = cursor.fetchall()
        return [row['gameId'] for row in rows]
        
    except Exception as e:
        print(f"Error getting recommended game IDs: {e}")
        return []
    finally:
        conn.close()


# Preference Management Functions
def savePreference(steamId: str, gameId: str, preference: str):
    """
    Save user preference (liked/disliked)
    """
    conn = getConnection()
    cursor = conn.cursor()
    
    try:
        currentTime = int(time.time())
        
        cursor.execute("""
            INSERT INTO preferences (steamId, gameId, preference, createdAt)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(steamId, gameId) DO UPDATE SET
                preference = excluded.preference,
                createdAt = excluded.createdAt
        """, (steamId, gameId, preference, currentTime))
        
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Error saving preference: {e}")
        raise
    finally:
        conn.close()

def getPreferenceGameIds(steamId: str, preference: str) -> List[str]:
    """
    Get list of game IDs for a specific preference type
    """
    conn = getConnection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT gameId FROM preferences
            WHERE steamId = ? AND preference = ?
            ORDER by createdAt DESC
            """, (steamId, preference))
        
        rows = cursor.fetchall()
        return [row['gameId'] for row in rows]
        
    except Exception as e:
        print(f"Error getting preference IDs: {e}")
        return []
    finally:
        conn.close()

def deletePreference(steamId: str, gameId: str) -> bool:
    """Remove a preference (undo like/dislike)"""
    conn = getConnection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            DELETE FROM preferences 
            WHERE steamId = ? AND gameId = ?
        """, (steamId, gameId))
        
        conn.commit()
        return True
        print(f"Deleted preference for game {gameId}")
        
    except Exception as e:
        conn.rollback()
        print(f"Error deleting preference: {e}")
        raise
    finally:
        conn.close()

# User Events Functions
def saveUserEvent(steamId: str, eventType: str, gameId: str = None, timestamp: int = None) -> bool:
    """
    Save a user event to the userEvents table.
    """
    import time
    if timestamp is None:
        timestamp = int(time.time())
    conn = getConnection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO userEvents (steamId, eventType, gameId, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (steamId, eventType, gameId, timestamp)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"[saveUserEvent] Error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def getUserEvents(steamId: str = None, eventTypes: list = None, from_ts: int = None, to_ts: int = None) -> list:
    """
    Fetch user events filtered by steamId, eventTypes, and timestamp range.
    """
    conn = getConnection()
    cursor = conn.cursor()
    try:
        query = "SELECT steamId, eventType, gameId, timestamp FROM userEvents WHERE 1=1"
        params = []
        if steamId:
            query += " AND steamId = ?"
            params.append(steamId)
        if eventTypes:
            query += " AND eventType IN ({})".format(",".join("?" for _ in eventTypes))
            params.extend(eventTypes)
        if from_ts is not None:
            query += " AND timestamp >= ?"
            params.append(from_ts)
        if to_ts is not None:
            query += " AND timestamp <= ?"
            params.append(to_ts)
        query += " ORDER BY timestamp DESC"
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error fetching user events: {e}")
        return []
    finally:
        conn.close()


# Filter Management Functions
def saveFilterGenres(steamId: str, savedGenres: List[str]) -> bool:
    """
    Save user's requested genres/tags/mechanics filter preferences
    """
    conn = getConnection()
    cursor = conn.cursor()
    
    try:
        currentTime = int(time.time())
        
        cursor.execute("""
            INSERT OR REPLACE INTO filterGenres
            (steamId, savedGenres, updatedAt)
            VALUES (?, ?, ?)
        """, (
            steamId,
            json.dumps(savedGenres),
            currentTime
        ))
        
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Error saving filter preferences: {e}")
        return False
    finally:
        conn.close()

def getFilterGenres(steamId: str) -> Optional[List[str]]:
    """
    Get user's saved requested genres/tags/mechanics
    """
    conn = getConnection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT savedGenres FROM filterGenres WHERE steamId = ?
        """, (steamId,))
        
        row = cursor.fetchone()
        
        if row:
            return json.loads(row["savedGenres"])
        
        return None
        
    except Exception as e:
        print(f"Error getting filter preferences: {e}")
        return None
    finally:
        conn.close()

def deleteFilterGenres(steamId: str) -> bool:
    """
    Clear user's filter preferences (reset to defaults)
    """
    conn = getConnection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            DELETE FROM filterGenres WHERE steamId = ?
        """, (steamId,))
        
        conn.commit()
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Error deleting filter preferences: {e}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print("Initializing database...")
    initDatabase()
    print("Database ready")