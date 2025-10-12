import { defineStore } from 'pinia'

export const useUserStore = defineStore('user', {
  state: () => ({
    profile: null,
    jwt: null,
    liked: [], // array of game objects
    disliked: [], // array of game objects
    pastRecommendations: [], // array of game objects
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
      this.liked = []
      this.disliked = []
      this.pastRecommendations = []
    },

    // Liked Games Management
    addLiked(game) {
      if (!this.liked.find(g => g.id === game.id)) {
        this.liked.push(game)
        this.disliked = this.disliked.filter(g => g.id !== game.id)
      }
    },
    removeLiked(gameId) {
      this.liked = this.liked.filter(g => g.id !== gameId)
    },
    moveLikedToDisliked(gameId) {
      const game = this.liked.find(g => g.id === gameId)
      if (game) {
        this.removeLiked(gameId)
        this.addDisliked(game)
      }
    },

    // Disliked Games Management
    addDisliked(game) {
      if (!this.disliked.find(g => g.id === game.id)) {
        this.disliked.push(game)
        this.liked = this.liked.filter(g => g.id !== game.id)
      }
    },
    removeDisliked(gameId) {
      this.disliked = this.disliked.filter(g => g.id !== gameId)
    },
    moveDislikedToLiked(gameId) {
      const game = this.disliked.find(g => g.id === gameId)
      if (game) {
        this.removeDisliked(gameId)
        this.addLiked(game)
      }
    },

    // Past Recommendations Management
    addPastRecommendation(game) {
      if (!this.pastRecommendations.find(g => g.id === game.id)) {
        this.pastRecommendations.push(game)
      }
    },
    removePastRecommendation(gameId) {
      this.pastRecommendations = this.pastRecommendations.filter(g => g.id !== gameId)
    },
    clearPastRecommendations() {
      this.pastRecommendations = []
    },
  },
})