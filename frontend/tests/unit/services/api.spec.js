import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from '@/stores/user'
import * as api from '@/services/api'

describe('API Service - Mock Functions', () => {
  beforeEach(() => {
    // Create fresh Pinia instance for each test
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('Authentication', () => {
    it('getSteamLoginUrl returns mock login URL', async () => {
      const result = await api.getSteamLoginUrl()
      
      expect(result).toBeTruthy()
      expect(typeof result).toBe('string')
      expect(result).toContain('steamcommunity.com/openid/login')
    })

    it('getCurrentUser returns mock user profile', async () => {
      const result = await api.getCurrentUser()
      
      expect(result).toHaveProperty('steam_id')
      expect(result).toHaveProperty('display_name')
      expect(result).toHaveProperty('avatar_url')
      expect(result).toHaveProperty('profile_url')
      expect(result.steam_id).toBe('12345678901234567')
      expect(result.display_name).toBe('Mock User')
    })

    it('logOut returns success', async () => {
      const result = await api.logOut()
      
      expect(result).toHaveProperty('success')
      expect(result.success).toBe(true)
    })
  })

  describe('Genres and Filters', () => {
    it('getAvailableGenres returns genres, tags, and modes', async () => {
      const result = await api.getAvailableGenres()
      
      expect(result).toHaveProperty('genres')
      expect(result).toHaveProperty('tags')
      expect(result).toHaveProperty('modes')
      expect(Array.isArray(result.genres)).toBe(true)
      expect(Array.isArray(result.tags)).toBe(true)
      expect(Array.isArray(result.modes)).toBe(true)
      expect(result.genres.length).toBeGreaterThan(0)
    })

    it('getSavedFilterPreferences returns user filter preferences', async () => {
      const result = await api.getSavedFilterPreferences()
      
      expect(result).toHaveProperty('steamId')
      expect(result).toHaveProperty('genres')
      expect(Array.isArray(result.genres)).toBe(true)
    })
  })

  describe('Recommendations', () => {
    it('getRecommendation returns game recommendation with reasoning and score', async () => {
      const result = await api.getRecommendation(['Action'], false)
      
      expect(result).toHaveProperty('game')
      expect(result).toHaveProperty('reasoning')
      expect(result).toHaveProperty('matchScore')
      expect(result.game).toHaveProperty('id')
      expect(result.game).toHaveProperty('title')
      expect(typeof result.reasoning).toBe('string')
      expect(typeof result.matchScore).toBe('number')
    })

    it('getRecommendation accepts genres array and wishlist flag', async () => {
      const genres = ['Action', 'Adventure']
      const result = await api.getRecommendation(genres, true)
      
      expect(result).toBeTruthy()
      expect(result.game).toBeTruthy()
    })

    it('getRecommendationHistory returns paginated results', async () => {
      const result = await api.getRecommendationHistory(1, 10)
      
      expect(result).toHaveProperty('recommendations')
      expect(result).toHaveProperty('currentPage')
      expect(result).toHaveProperty('pageSize')
      expect(result).toHaveProperty('totalRecommendations')
      expect(result).toHaveProperty('pages')
      expect(Array.isArray(result.recommendations)).toBe(true)
      expect(result.currentPage).toBe(1)
      expect(result.pageSize).toBe(10)
    })

    it('getRecommendationHistory handles different page numbers', async () => {
      const result = await api.getRecommendationHistory(2, 5)
      
      expect(result.currentPage).toBe(2)
      expect(result.pageSize).toBe(5)
    })
  })

  describe('Preferences', () => {
    it('likeGame sends like request and returns success', async () => {
      const gameId = '123'
      const result = await api.likeGame(gameId)
      
      expect(result).toHaveProperty('status')
      expect(result).toHaveProperty('gameId')
      expect(result).toHaveProperty('preference')
      expect(result.status).toBe('success')
      expect(result.gameId).toBe(gameId)
      expect(result.preference).toBe('liked')
    })

    it('dislikeGame sends dislike request and returns success', async () => {
      const gameId = '456'
      const result = await api.dislikeGame(gameId)
      
      expect(result).toHaveProperty('status')
      expect(result).toHaveProperty('gameId')
      expect(result).toHaveProperty('preference')
      expect(result.status).toBe('success')
      expect(result.gameId).toBe(gameId)
      expect(result.preference).toBe('disliked')
    })

    it('removePreference removes game preference', async () => {
      const gameId = '789'
      const result = await api.removePreference(gameId)
      
      expect(result).toHaveProperty('status')
      expect(result).toHaveProperty('gameId')
      expect(result.status).toBe('success')
      expect(result.gameId).toBe(gameId)
    })

    it('getLikedGames returns array of liked games', async () => {
      const result = await api.getLikedGames()
      
      expect(Array.isArray(result)).toBe(true)
      result.forEach(game => {
        expect(game).toHaveProperty('id')
        expect(game).toHaveProperty('title')
      })
    })

    it('getDislikedGames returns array of disliked games', async () => {
      const result = await api.getDislikedGames()
      
      expect(Array.isArray(result)).toBe(true)
      result.forEach(game => {
        expect(game).toHaveProperty('id')
        expect(game).toHaveProperty('title')
      })
    })

    it('getAllPreferences returns all preferences with totals', async () => {
      const result = await api.getAllPreferences()
      
      expect(result).toHaveProperty('preferences')
      expect(result).toHaveProperty('totals')
      expect(result.preferences).toHaveProperty('liked')
      expect(result.preferences).toHaveProperty('disliked')
      expect(result.totals).toHaveProperty('liked')
      expect(result.totals).toHaveProperty('disliked')
      expect(Array.isArray(result.preferences.liked)).toBe(true)
      expect(Array.isArray(result.preferences.disliked)).toBe(true)
    })
  })

  describe('User Events', () => {
    it('logUserEvent logs event without gameId', async () => {
      const userStore = useUserStore()
      userStore.setProfile({
        steam_id: '12345',
        display_name: 'Test User',
        avatar_url: 'https://example.com/avatar.jpg'
      })

      const result = await api.logUserEvent('login')
      
      expect(result).toHaveProperty('success')
      expect(result.success).toBe(true)
    })

    it('logUserEvent logs event with gameId', async () => {
      const userStore = useUserStore()
      userStore.setProfile({
        steam_id: '12345',
        display_name: 'Test User',
        avatar_url: 'https://example.com/avatar.jpg'
      })

      const result = await api.logUserEvent('view_game', '123')
      
      expect(result).toHaveProperty('success')
      expect(result.success).toBe(true)
    })
  })

  describe('Mock Data Structure', () => {
    it('game objects have required fields', async () => {
      const result = await api.getRecommendation(['Action'], false)
      const game = result.game
      
      expect(game).toHaveProperty('id')
      expect(game).toHaveProperty('title')
      expect(game).toHaveProperty('thumbnail')
      expect(game).toHaveProperty('releaseDate')
      expect(game).toHaveProperty('publisher')
      expect(game).toHaveProperty('developer')
      expect(game).toHaveProperty('price')
      expect(game).toHaveProperty('description')
    })

    it('game objects may have sale price', async () => {
      const result = await api.getRecommendation(['Action'], false)
      const game = result.game
      
      if (game.salePrice) {
        expect(typeof game.salePrice).toBe('string')
      }
    })
  })
})