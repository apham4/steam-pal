import { config } from '@vue/test-utils'
import { vi, beforeAll, afterAll } from 'vitest'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

// Mock CSS imports
vi.mock('*.css', () => ({}))
vi.mock('*.scss', () => ({}))
vi.mock('*.sass', () => ({}))

// Mock ResizeObserver for Vuetify components
global.ResizeObserver = class ResizeObserver {
  constructor(callback) {
    this.callback = callback
  }
  observe() {}
  unobserve() {}
  disconnect() {}
}

// Create Vuetify instance for tests
const vuetify = createVuetify({
  components,
  directives,
})

// Global test config
config.global.plugins = [vuetify]

// Mock window.matchMedia (required by Vuetify)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock localStorage
global.localStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}

// Alternative: Suppress all console warnings during tests
const originalWarn = console.warn
const originalError = console.error

beforeAll(() => {
  console.warn = vi.fn()
  console.error = vi.fn((message) => {
    // Still log actual errors, filter out Vue warnings
    if (typeof message === 'string' && message.includes('[Vue warn]')) {
      return
    }
    originalError(message)
  })
})

afterAll(() => {
  console.warn = originalWarn
  console.error = originalError
})