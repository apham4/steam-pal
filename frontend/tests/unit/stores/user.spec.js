import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from '@/stores/user'

describe('User Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('initializes with null profile and jwt', () => {
    const store = useUserStore()
    expect(store.profile).toBe(null)
    expect(store.jwt).toBe(null)
  })

  it('sets JWT token and saves to localStorage', () => {
    const store = useUserStore()
    const token = 'test-jwt-token'
    
    store.setJwt(token)
    
    expect(store.jwt).toBe(token)
    expect(localStorage.getItem('jwt')).toBe(token)
  })

  it('sets user profile', () => {
    const store = useUserStore()
    const profile = {
      steamId: '12345',
      displayName: 'TestUser',
      avatarUrl: 'https://example.com/avatar.jpg'
    }
    
    store.setProfile(profile)
    
    expect(store.profile).toEqual(profile)
  })

  it('clears user data on logout', () => {
    const store = useUserStore()
    
    store.setJwt('test-token')
    store.setProfile({ steamId: '12345', displayName: 'TestUser' })
    
    store.logout()
    
    expect(store.profile).toBe(null)
    expect(store.jwt).toBe(null)
  })
})