import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import { mdi } from 'vuetify/iconsets/mdi'

const steamTheme = {
  dark: true,
  colors: {
    background: '#171a21',
    surface: '#23262e',
    primary: '#1b2838',
    secondary: '#66c0f4',
    accent: '#5c7e10',
    error: '#d32f2f',
    info: '#66c0f4',
    success: '#4caf50',
    warning: '#ffa726',
  },
}

export default createVuetify({
  theme: {
    defaultTheme: 'steamTheme',
    themes: {
      steamTheme,
    },
  },
  icons: {
    defaultSet: 'mdi',
    sets: { mdi },
  },
})