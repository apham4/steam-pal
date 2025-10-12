import { createApp } from 'vue';
import App from './App.vue';
import { createVuetify } from 'vuetify';
import 'vuetify/styles'; // Ensure global Vuetify styles are loaded
import '../assets/styles.css'; // Reuse global styles if needed

const vuetify = createVuetify();

createApp(App)
  .use(vuetify)
  .mount('#admin-dashboard-app');