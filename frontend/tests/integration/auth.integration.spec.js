import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia } from 'pinia'
import App from '@/App.vue'
import UserPage from '@/components/UserPage.vue'
import { useUserStore } from '@/stores/user'
import * as api from '@/services/api'
import { createTestPinia, createTestVuetify } from './testHelpers'

// Ensure mock API is used
vi.mock('@/services/api', async () => {
  const actual = await vi.importActual('@/services/api')
  return {
    ...actual,
    getSteamLoginUrl: vi.fn(() => Promise.resolve('https://steamcommunity.com/openid/login?test=true')),
    getCurrentUser: vi.fn(() => Promise.resolve({
      steam_id: '12345678901234567',
      display_name: 'Test User',
      avatar_url: 'https://example.com/avatar.jpg',
      profile_url: 'https://steamcommunity.com/id/testuser',
    })),
    logOut: vi.fn(() => Promise.resolve({ success: true })),
    logUserEvent: vi.fn(() => Promise.resolve({})),
  }
})

describe('Authentication Flow Integration', () => {
  let pinia
  let vuetify

  beforeEach(() => {
    pinia = createTestPinia()
    vuetify = createTestVuetify()
    setActivePinia(pinia)
    vi.clearAllMocks()
  })

  it('completes full login workflow', async () => {
    // 1. Mount UserPage
    const wrapper = mount(UserPage, {
      global: {
        plugins: [pinia, vuetify],
      },
    })
    await flushPromises()

    // 2. Verify initial state
    const userStore = useUserStore()
    expect(userStore.profile).toBeNull()
    expect(userStore.jwt).toBeNull()

    // 3. Mock Steam login URL request
    const windowOpenSpy = vi.spyOn(window, 'open').mockImplementation(() => null)
    
    // 4. Click sign in button
    const signInButton = wrapper.find('button')
    await signInButton.trigger('click')
    await flushPromises()

    // 5. Verify Steam login URL was called
    expect(api.getSteamLoginUrl).toHaveBeenCalled()
    expect(windowOpenSpy).toHaveBeenCalledWith(
      expect.stringContaining('steamcommunity.com/openid/login'),
      '_blank'
    )

    // 6. Simulate successful authentication (JWT token received)
    userStore.setJwt('mock-jwt-token')
    
    // 7. Fetch user profile
    const profile = await api.getCurrentUser()
    userStore.setProfile(profile)
    await flushPromises()

    // 8. Verify user is logged in
    expect(userStore.jwt).toBe('mock-jwt-token')
    expect(userStore.profile).toEqual({
      steam_id: '12345678901234567',
      display_name: 'Test User',
      avatar_url: 'https://example.com/avatar.jpg',
      profile_url: 'https://steamcommunity.com/id/testuser',
    })

    windowOpenSpy.mockRestore()
  })

  it('handles logout workflow', async () => {
    const userStore = useUserStore()
    
    // 1. Set up logged-in state
    userStore.setJwt('mock-jwt-token')
    userStore.setProfile({
      steam_id: '12345',
      display_name: 'Test User',
    })

    // 2. Verify logged in
    expect(userStore.jwt).toBe('mock-jwt-token')
    expect(userStore.profile).not.toBeNull()

    // 3. Call logout
    await api.logOut()
    userStore.logout()
    await flushPromises()

    // 4. Verify logged out
    expect(userStore.jwt).toBeNull()
    expect(userStore.profile).toBeNull()
    expect(api.logOut).toHaveBeenCalled()
  })
})