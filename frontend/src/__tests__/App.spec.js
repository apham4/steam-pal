import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import App from '../App.vue'
import vuetify from '../plugins/vuetify'

// Mock the API module to avoid real API calls
vi.mock('../services/api', () => ({
  getCurrentUser: vi.fn(() => Promise.resolve({ 
    steam_id: '123', 
    display_name: 'Test User' 
  })),
  logOut: vi.fn(() => Promise.resolve({ success: true })),
  logUserEvent: vi.fn(() => Promise.resolve({ success: true })),
}))

describe('App', () => {
  let wrapper

  beforeEach(() => {
    wrapper = mount(App, {
      global: {
        plugins: [createPinia(), vuetify],
        stubs: {
          // Stub child components to simplify testing
          UserPage: { template: '<div>User Page</div>' },
          MainPage: { template: '<div>Main Page</div>' },
        },
      },
    })
  })

  it('mounts and renders properly', () => {
    expect(wrapper.exists()).toBe(true)
  })

  it('initially shows UserPage', () => {
    expect(wrapper.text()).toContain('User Page')
  })
})