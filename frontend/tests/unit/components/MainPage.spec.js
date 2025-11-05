import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import MainPage from '@/components/MainPage.vue'
import { useUserStore } from '@/stores/user'
import { usePreferenceStore } from '@/stores/preference'
import * as api from '@/services/api'

// Mock API module
vi.mock('@/services/api', () => ({
  getAvailableGenres: vi.fn(),
  getSavedFilterPreferences: vi.fn(),
  getRecommendation: vi.fn(),
  getRecommendationHistory: vi.fn(),
  likeGame: vi.fn(),
  dislikeGame: vi.fn(),
  removePreference: vi.fn(),
  getLikedGames: vi.fn(),
  getDislikedGames: vi.fn(),
  logUserEvent: vi.fn(),
}))

describe('MainPage Component', () => {
  let wrapper
  let pinia
  let vuetify
  let userStore
  let preferenceStore

  beforeEach(() => {
    pinia = createPinia()
    vuetify = createVuetify({
      components,
      directives,
    })
    userStore = useUserStore(pinia)
    preferenceStore = usePreferenceStore(pinia)
    
    // Set up user
    userStore.setProfile({
      steam_id: '12345',
      display_name: 'TestUser',
      avatar_url: 'https://example.com/avatar.jpg'
    })
    
    // Mock API responses with default empty values
    api.getLikedGames.mockResolvedValue([])
    api.getDislikedGames.mockResolvedValue([])
    api.getAvailableGenres.mockResolvedValue({ genres: [] })
    api.getSavedFilterPreferences.mockResolvedValue({ saved_genres: [] })
    api.logUserEvent.mockResolvedValue({})
    
    vi.clearAllMocks()
  })

  const createWrapper = () => {
    return mount(MainPage, {
      global: {
        plugins: [pinia, vuetify],
      },
    })
  }

  it('renders main page for authenticated user', () => {
    wrapper = createWrapper()
    
    expect(wrapper.exists()).toBe(true)
  })

  it('fetches preferences on mount', async () => {
    wrapper = createWrapper()
    await flushPromises()
    
    expect(api.getLikedGames).toHaveBeenCalled()
    expect(api.getDislikedGames).toHaveBeenCalled()
  })

  it('adds game to liked preferences', async () => {
    const mockGame = { gameId: '123', title: 'Test Game' }
    api.likeGame.mockResolvedValue({})
    
    wrapper = createWrapper()
    await flushPromises()
    
    await wrapper.vm.likeRecommendation(mockGame)
    await flushPromises()
    
    expect(preferenceStore.isLiked(mockGame)).toBe(true)
    expect(api.likeGame).toHaveBeenCalledWith('123')
  })

  it('adds game to disliked preferences', async () => {
    const mockGame = { gameId: '456', title: 'Test Game 2' }
    api.dislikeGame.mockResolvedValue({})
    
    wrapper = createWrapper()
    await flushPromises()
    
    await wrapper.vm.dislikeRecommendation(mockGame)
    await flushPromises()
    
    expect(preferenceStore.isDisliked(mockGame)).toBe(true)
    expect(api.dislikeGame).toHaveBeenCalledWith('456')
  })

  it('removes preference when already liked and disliking', async () => {
    const mockGame = { gameId: '789', title: 'Test Game 3' }
    preferenceStore.addLiked(mockGame)
    
    api.removePreference.mockResolvedValue({})
    api.dislikeGame.mockResolvedValue({})
    
    wrapper = createWrapper()
    await flushPromises()
    
    await wrapper.vm.dislikeRecommendation(mockGame)
    await flushPromises()
    
    // Note: Your component logic doesn't call removePreference - it just removes from store
    // If you want to test removePreference API call, update your component code
    expect(preferenceStore.isLiked(mockGame)).toBe(false)
    expect(preferenceStore.isDisliked(mockGame)).toBe(true)
  })

  it('generates Steam store URL correctly', () => {
    wrapper = createWrapper()
    
    const url = wrapper.vm.steamStoreUrl('123')
    
    expect(url).toBe('https://store.steampowered.com/app/123')
  })

  it('displays sale price when available and different from regular price', () => {
    wrapper = createWrapper()
    
    const recommendation1 = {
      price: '$19.99',
      salePrice: '$9.99'
    }
    
    const recommendation2 = {
      price: '$19.99',
      salePrice: '$19.99'
    }
    
    const recommendation3 = {
      price: '$19.99',
      salePrice: ''
    }
    
    const recommendation4 = {
      price: '$19.99',
      salePrice: null
    }
    
    expect(wrapper.vm.shouldDisplaySalePrice(recommendation1)).toBe(true)
    expect(wrapper.vm.shouldDisplaySalePrice(recommendation2)).toBe(false)
    expect(wrapper.vm.shouldDisplaySalePrice(recommendation3)).toBe(false)
    expect(wrapper.vm.shouldDisplaySalePrice(recommendation4)).toBe(false)
  })
})