import { createApp } from 'vue'
import { createPinia } from 'pinia'
import vuetify from './plugins/vuetify'
import App from './App.vue'
import './assets/styles.css'

createApp(App)
  .use(vuetify)
  .use(createPinia())
  .mount('#app')
