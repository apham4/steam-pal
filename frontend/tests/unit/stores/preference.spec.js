import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { usePreferenceStore } from '@/stores/preference'

describe('Preference Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  const mockGame1 = { gameId: '1', title: 'Game 1' }
  const mockGame2 = { gameId: '2', title: 'Game 2' }

  it('initializes with empty liked and disliked arrays', () => {
    const store = usePreferenceStore()
    expect(store.liked).toEqual([])
    expect(store.disliked).toEqual([])
  })

  it('sets liked items', () => {
    const store = usePreferenceStore()
    const items = [mockGame1, mockGame2]
    
    store.setLiked(items)
    
    expect(store.liked).toEqual(items)
  })

  it('sets disliked items', () => {
    const store = usePreferenceStore()
    const items = [mockGame1]
    
    store.setDisliked(items)
    
    expect(store.disliked).toEqual(items)
  })

  it('adds liked item if not already present', () => {
    const store = usePreferenceStore()
    
    store.addLiked(mockGame1)
    expect(store.liked).toHaveLength(1)
    expect(store.liked[0]).toEqual(mockGame1)
    
    // Try to add same game again
    store.addLiked(mockGame1)
    expect(store.liked).toHaveLength(1)
  })

  it('adds disliked item if not already present', () => {
    const store = usePreferenceStore()
    
    store.addDisliked(mockGame1)
    expect(store.disliked).toHaveLength(1)
    expect(store.disliked[0]).toEqual(mockGame1)
    
    // Try to add same game again
    store.addDisliked(mockGame1)
    expect(store.disliked).toHaveLength(1)
  })

  it('removes item from both liked and disliked', () => {
    const store = usePreferenceStore()
    
    store.addLiked(mockGame1)
    store.addDisliked(mockGame2)
    
    store.removeStoredPreference(mockGame1)
    
    expect(store.liked).toHaveLength(0)
    expect(store.disliked).toHaveLength(1)
  })

  it('clears all preferences', () => {
    const store = usePreferenceStore()
    
    store.addLiked(mockGame1)
    store.addDisliked(mockGame2)
    
    store.clearPreferences()
    
    expect(store.liked).toEqual([])
    expect(store.disliked).toEqual([])
  })

  it('checks if item is liked', () => {
    const store = usePreferenceStore()
    
    store.addLiked(mockGame1)
    
    expect(store.isLiked(mockGame1)).toBe(true)
    expect(store.isLiked(mockGame2)).toBe(false)
  })

  it('checks if item is disliked', () => {
    const store = usePreferenceStore()
    
    store.addDisliked(mockGame1)
    
    expect(store.isDisliked(mockGame1)).toBe(true)
    expect(store.isDisliked(mockGame2)).toBe(false)
  })
})