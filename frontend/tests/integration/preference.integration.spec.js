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
    likeGame: vi.fn(() => Promise.resolve({ success: true })),
    dislikeGame: vi.fn(() => Promise.resolve({ success: true })),
    removePreference: vi.fn(() => Promise.resolve({ success: true })),
    getLikedGames: vi.fn(() => Promise.resolve([])),
    getDislikedGames: vi.fn(() => Promise.resolve([])),
    getAvailableGenres: vi.fn(() => Promise.resolve({ genres: [] })),
    getSavedFilterPreferences: vi.fn(() => Promise.resolve({ saved_genres: [] })),
    logUserEvent: vi.fn(() => Promise.resolve({})),
  }
})

describe('Preference Management Integration', () => {
  let pinia
  let vuetify
  let wrapper
  let preferenceStore

  beforeEach(() => {
    pinia = createTestPinia()
    vuetify = createTestVuetify()
    setActivePinia(pinia)
    
    const userStore = useUserStore()
    userStore.setProfile({
      steam_id: '12345',
      display_name: 'Test User',
    })
    
    preferenceStore = usePreferenceStore()
    vi.clearAllMocks()
  })

  it('completes like game workflow', async () => {
    const mockGame = {
      gameId: '123',
      title: 'Test Game',
      thumbnail: 'https://example.com/image.jpg',
    }

    wrapper = mount(MainPage, {
      global: {
        plugins: [pinia, vuetify],
      },
    })
    await flushPromises()

    // 1. Initial state - no preferences
    expect(preferenceStore.liked).toHaveLength(0)
    expect(preferenceStore.isLiked(mockGame)).toBe(false)

    // 2. Like a game
    await wrapper.vm.likeRecommendation(mockGame)
    await flushPromises()

    // 3. Verify API was called
    expect(api.likeGame).toHaveBeenCalledWith('123')

    // 4. Verify store was updated
    expect(preferenceStore.isLiked(mockGame)).toBe(true)
    expect(preferenceStore.liked).toHaveLength(1)
    expect(preferenceStore.liked[0].gameId).toBe('123')
  })

  it('completes dislike game workflow', async () => {
    const mockGame = {
      gameId: '456',
      title: 'Test Game 2',
    }

    wrapper = mount(MainPage, {
      global: {
        plugins: [pinia, vuetify],
      },
    })
    await flushPromises()

    // 1. Dislike a game
    await wrapper.vm.dislikeRecommendation(mockGame)
    await flushPromises()

    // 2. Verify API was called
    expect(api.dislikeGame).toHaveBeenCalledWith('456')

    // 3. Verify store was updated
    expect(preferenceStore.isDisliked(mockGame)).toBe(true)
    expect(preferenceStore.disliked).toHaveLength(1)
  })

  it('removes preference workflow', async () => {
    const mockGame = {
      gameId: '789',
      title: 'Test Game 3',
    }

    // 1. Add to liked
    preferenceStore.addLiked(mockGame)
    expect(preferenceStore.isLiked(mockGame)).toBe(true)

    wrapper = mount(MainPage, {
      global: {
        plugins: [pinia, vuetify],
      },
    })
    await flushPromises()

    // 2. Remove preference
    await wrapper.vm.removeRecommendationPreference(mockGame)
    await flushPromises()

    // 3. Verify API was called
    expect(api.removePreference).toHaveBeenCalledWith('789')

    // 4. Verify store was updated
    expect(preferenceStore.isLiked(mockGame)).toBe(false)
    expect(preferenceStore.isDisliked(mockGame)).toBe(false)
  })

  it('fetches preferences on mount', async () => {
    api.getLikedGames.mockResolvedValue([
      { gameId: '1', title: 'Game 1' },
    ])
    api.getDislikedGames.mockResolvedValue([
      { gameId: '2', title: 'Game 2' },
    ])

    wrapper = mount(MainPage, {
      global: {
        plugins: [pinia, vuetify],
      },
    })
    await flushPromises()

    // Verify preferences were fetched
    expect(api.getLikedGames).toHaveBeenCalled()
    expect(api.getDislikedGames).toHaveBeenCalled()
  })
})