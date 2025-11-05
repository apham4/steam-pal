import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import UserPage from '@/components/UserPage.vue'
import * as api from '@/services/api'

// Mock API module
vi.mock('@/services/api', () => ({
  getSteamLoginUrl: vi.fn(),
}))

describe('UserPage Component', () => {
  let wrapper
  let pinia

  beforeEach(() => {
    pinia = createPinia()
    vi.clearAllMocks()
  })

  const createWrapper = () => {
    return mount(UserPage, {
      global: {
        plugins: [pinia],
      },
    })
  }

  it('renders login button', () => {
    wrapper = createWrapper()
    
    const button = wrapper.find('button')
    expect(button.exists()).toBe(true)
    expect(button.text()).toContain('Sign In with Steam')
  })

  it('calls getSteamLoginUrl when sign in button is clicked', async () => {
    const mockUrl = 'https://steamcommunity.com/openid/login'
    api.getSteamLoginUrl.mockResolvedValue(mockUrl)
    
    // Mock window.open
    const windowOpenSpy = vi.spyOn(window, 'open').mockImplementation(() => {})
    
    wrapper = createWrapper()
    
    const button = wrapper.find('button')
    await button.trigger('click')
    
    expect(api.getSteamLoginUrl).toHaveBeenCalled()
    await wrapper.vm.$nextTick()
    
    expect(windowOpenSpy).toHaveBeenCalledWith(mockUrl, '_blank')
    
    windowOpenSpy.mockRestore()
  })

  it('shows error message on login failure', async () => {
    const errorMessage = 'Failed to get login URL'
    api.getSteamLoginUrl.mockRejectedValue(new Error(errorMessage))
    
    wrapper = createWrapper()
    
    const button = wrapper.find('button')
    await button.trigger('click')
    await wrapper.vm.$nextTick()
    
    // Check if error is displayed (adjust selector based on your Vuetify snackbar)
    expect(wrapper.vm.errorMsg).toBe(errorMessage)
    expect(wrapper.vm.snackbar).toBe(true)
  })

  it('shows loading state when signing in', async () => {
    api.getSteamLoginUrl.mockImplementation(() => new Promise(() => {}))
    
    wrapper = createWrapper()
    
    const button = wrapper.find('button')
    await button.trigger('click')
    
    expect(wrapper.vm.loading).toBe(true)
  })
})