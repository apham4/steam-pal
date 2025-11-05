import { createPinia } from 'pinia'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

export function createTestPinia() {
  return createPinia()
}

export function createTestVuetify() {
  return createVuetify({
    components,
    directives,
  })
}

export function createMountOptions() {
  return {
    global: {
      plugins: [createTestPinia(), createTestVuetify()],
    },
  }
}