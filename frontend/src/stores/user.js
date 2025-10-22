import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    profile: null,
    jwt: null,
  }),
  actions: {
    setJwt(token) {
      this.jwt = token
      localStorage.setItem('jwt', token)
    },
    setProfile(profile) {
      this.profile = profile
    },
    logout() {
      this.profile = null
      this.jwt = null
    },
  },
})