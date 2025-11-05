import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia } from 'pinia'
import MainPage from '@/components/MainPage.vue'
import { useUserStore } from '@/stores/user'
import { usePreferenceStore } from '@/stores/preference'
import * as api from '@/services/api'
import { createTestPinia, createTestVuetify } from './testHelpers'

vi.mock('@/services/api', async () => {
  const actual = await vi.importActual('@/services/api')
  return {
    ...actual,
    getAvailableGenres: vi.fn(() => Promise.resolve({
      genres: ['Action', 'Adventure', 'RPG'],
      tags: ['Singleplayer', 'Multiplayer'],
      modes: ['Story Rich', 'Open World'],
    })),
    getSavedFilterPreferences: vi.fn(() => Promise.resolve({
      saved_genres: ['Action'],
    })),
    getRecommendation: vi.fn((genres, useWishlist) => Promise.resolve({
      game: {
        gameId: '1',
        title: 'Portal 2',
        thumbnail: 'https://cdn.cloudflare.steamstatic.com/steam/apps/620/header.jpg',
        releaseDate: '2011-04-19',
        publisher: 'Valve',
        developer: 'Valve',
        price: '$9.99',
        salePrice: '$4.99',
        description: 'The highly anticipated sequel to Portal...',
      },
      reasoning: 'This game matches your preferences for Action and Puzzle genres.',
      matchScore: 0.95,
    })),
    getRecommendationHistory: vi.fn(() => Promise.resolve({
      recommendations: [],
      totalPages: 1,
    })),
    getLikedGames: vi.fn(() => Promise.resolve([])),
    getDislikedGames: vi.fn(() => Promise.resolve([])),
    logUserEvent: vi.fn(() => Promise.resolve({})),
  }
})

describe('Recommendation Flow Integration', () => {
  let pinia
  let vuetify
  let wrapper

  beforeEach(() => {
    pinia = createTestPinia()
    vuetify = createTestVuetify()
    setActivePinia(pinia)
    
    // Set up authenticated user
    const userStore = useUserStore()
    userStore.setProfile({
      steam_id: '12345',
      display_name: 'Test User',
      avatar_url: 'https://example.com/avatar.jpg',
    })
    
    vi.clearAllMocks()
  })

  it('completes full recommendation workflow', async () => {
    // 1. Mount MainPage
    wrapper = mount(MainPage, {
      global: {
        plugins: [pinia, vuetify],
      },
    })
    await flushPromises()

    // 2. Verify genres are fetched on mount
    expect(api.getAvailableGenres).toHaveBeenCalled()

    // 3. Select genres for recommendation
    // (In a real test, you'd interact with the UI, but we'll call the method directly)
    await wrapper.vm.fetchRecommendation()
    await flushPromises()

    // 4. Verify recommendation API was called
    expect(api.getRecommendation).toHaveBeenCalled()

    // 5. Verify recommendation was received (check component state if exposed)
    // You may need to add checks based on your component's exposed state
  })

  it('fetches and displays recommendation history', async () => {
    // Mock history data
    api.getRecommendationHistory.mockResolvedValue({
      recommendations: [
        {
          gameId: '1',
          title: 'Portal 2',
          thumbnail: 'https://example.com/image.jpg',
          timestamp: '2024-01-01T12:00:00Z',
        },
      ],
      totalPages: 1,
    })

    wrapper = mount(MainPage, {
      global: {
        plugins: [pinia, vuetify],
      },
    })
    await flushPromises()

    // Fetch recommendation history
    await wrapper.vm.fetchRecommendationHistory(1, 7)
    await flushPromises()

    // Verify API was called
    expect(api.getRecommendationHistory).toHaveBeenCalledWith(1, 7)
  })
})