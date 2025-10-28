import { createApp } from 'vue'
import App from './App.vue'
import vuetify from '../plugins/vuetify'
import 'vuetify/styles' // Ensure global Vuetify styles are loaded
import '../assets/styles.css' // Reuse global styles if needed

createApp(App)
  .use(vuetify)
  .mount('#admin-dashboard-app')