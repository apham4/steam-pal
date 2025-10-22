import { defineStore } from 'pinia'

export const usePreferenceStore = defineStore('preference', {
  state: () => ({
    liked: [],
    disliked: [],
  }),
  actions: {
    setLiked(items) {
      this.liked = items
    },
    setDisliked(items) {
      this.disliked = items
    },
    addLiked(item) {
      if (!this.liked.some((i) => i.gameId === item.gameId)) {
        this.liked.push(item)
      }
    },
    addDisliked(item) {
      if (!this.disliked.some((i) => i.gameId === item.gameId)) {
        this.disliked.push(item)
      }
    },
    removeStoredPreference(item) {
      console.log('removeStoredPreference called with:', item)
      this.liked = this.liked.filter((i) => i.gameId !== item.gameId)
      this.disliked = this.disliked.filter((i) => i.gameId !== item.gameId)
    },
    clearPreferences() {
      this.liked = []
      this.disliked = []
    },
    isLiked(item) {
      return this.liked.some((i) => i.gameId === item.gameId)
    },
    isDisliked(item) {
      return this.disliked.some((i) => i.gameId === item.gameId)
    },
  },
})