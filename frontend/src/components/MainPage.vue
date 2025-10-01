<template>
  <v-container fluid>
    <!-- Steam Pal Title Header -->
    <v-row>
      <v-col>
        <v-toolbar color="primary" dark>
          <v-toolbar-title>Steam Pal</v-toolbar-title>
        </v-toolbar>
      </v-col>
    </v-row>

    <!-- Current User Section -->
    <v-row>
      <v-col>
        <v-card class="mb-4" color="surface" dark>
          <v-card-title>
            <v-avatar size="40" class="mr-2">
              <img :src="userProfile?.avatar" alt="Profile" />
            </v-avatar>
            {{ userProfile?.name || userStore.steamId }}
            <v-spacer />
            <v-btn color="secondary" @click="$emit('changeUser')">Change User</v-btn>
          </v-card-title>
        </v-card>
      </v-col>
    </v-row>

    <!-- Action & Preferences Section -->
    <v-row>
      <v-col>
        <v-tabs v-model="tab" background-color="primary" dark>
          <v-tab>Get Recommendation</v-tab>
          <v-tab>Past Recommendations</v-tab>
          <v-tab>Manage Preferences</v-tab>
        </v-tabs>
        <v-tabs-items v-model="tab">
          <v-tab-item>
            <!-- Genre filter, Get AI Recommendation button -->
            <v-row>
              <v-col cols="12" md="6">
                <v-select
                  v-model="selectedGenre"
                  :items="genres"
                  label="Genre Filter"
                  color="secondary"
                  outlined
                />
              </v-col>
              <v-col cols="12" md="6">
                <v-btn color="accent" @click="fetchRecommendation">
                  <template v-if="loading">
                    <v-progress-circular indeterminate color="primary" size="20" />
                    Loading...
                  </template>
                  <template v-else>
                    Get AI Recommendation
                  </template>
                </v-btn>
              </v-col>
            </v-row>
            <v-checkbox
              v-if="userStore.role === 'authenticated'"
              v-model="useWishlist"
              label="Use my Steam Wishlist"
              color="secondary"
            />
          </v-tab-item>
          <v-tab-item>
            <!-- Past Recommendations scrollbox -->
            <v-list>
              <v-list-item
                v-for="game in userStore.pastRecommendations"
                :key="game.id"
                @click="showPastRecommendation(game)"
              >
                <v-list-item-title>{{ game.title }}</v-list-item-title>
                <v-btn icon @click.stop="removePastRecommendation(game.id)"><v-icon>mdi-delete</v-icon></v-btn>
              </v-list-item>
            </v-list>
            <v-btn color="error" @click="clearPastRecommendations">Clear All</v-btn>
          </v-tab-item>
          <v-tab-item>
            <!-- Liked/Disliked lists -->
            <v-row>
              <v-col>
                <h4>Liked</h4>
                <v-list>
                  <v-list-item
                    v-for="game in userStore.liked"
                    :key="game.id"
                    @click="showRecommendationDetails(game)"
                  >
                    <v-list-item-title>{{ game.title }}</v-list-item-title>
                    <v-btn icon @click.stop="removeLiked(game.id)"><v-icon>mdi-delete</v-icon></v-btn>
                    <v-btn icon @click.stop="moveLikedToDisliked(game.id)"><v-icon>mdi-arrow-right</v-icon></v-btn>
                  </v-list-item>
                </v-list>
              </v-col>
              <v-col>
                <h4>Disliked</h4>
                <v-list>
                  <v-list-item
                    v-for="game in userStore.disliked"
                    :key="game.id"
                    @click="showRecommendationDetails(game)"
                  >
                    <v-list-item-title>{{ game.title }}</v-list-item-title>
                    <v-btn icon @click.stop="removeDisliked(game.id)"><v-icon>mdi-delete</v-icon></v-btn>
                    <v-btn icon @click.stop="moveDislikedToLiked(game.id)"><v-icon>mdi-arrow-left</v-icon></v-btn>
                  </v-list-item>
                </v-list>
              </v-col>
            </v-row>
          </v-tab-item>
        </v-tabs-items>
      </v-col>
    </v-row>

    <!-- Recommendation Result Section (hidden initially) -->
    <v-row v-if="showRecommendation">
      <v-col>
        <v-card color="surface" dark>
          <v-card-title>Recommendation Result</v-card-title>
          <v-card-text>
            <div v-if="reasoning" class="mb-2"><strong>AI Reasoning:</strong> {{ reasoning }}</div>
            <div v-if="recommendation">
              <v-img :src="recommendation.thumbnail" height="120" contain />
              <div class="mt-2"><strong>{{ recommendation.title }}</strong></div>
              <div>Release Date: {{ recommendation.releaseDate }}</div>
              <div>Publisher: {{ recommendation.publisher }}</div>
              <div>Developer: {{ recommendation.developer }}</div>
              <div>
                Price: <span :style="recommendation.salePrice ? 'text-decoration: line-through;' : ''">{{ recommendation.price }}</span>
                <span v-if="recommendation.salePrice" class="ml-2">{{ recommendation.salePrice }}</span>
              </div>
              <v-card class="mt-2 pa-2" color="background" dark>
                <div style="max-height: 80px; overflow-y: auto;">{{ recommendation.description }}</div>
              </v-card>
              <v-btn color="success" class="mt-2" @click="likeRecommendation(recommendation)">Like</v-btn>
              <v-btn color="error" class="mt-2" @click="dislikeRecommendation(recommendation)">Dislike</v-btn>
              <v-btn color="info" class="mt-2" :href="steamStoreUrl(recommendation.id)" target="_blank">View on Steam</v-btn>
              <v-btn v-if="userStore.role === 'authenticated'" color="accent" class="mt-2">Add to Wishlist</v-btn>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Error Snackbar -->
    <v-row>
      <v-col>
        <v-snackbar v-model="snackbar" color="error" timeout="4000">
          {{ errorMsg }}
        </v-snackbar>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useUserStore } from '../stores/user'
import { getRecommendation, updatePreferences } from '../services/api'

const tab = ref(0)
const showRecommendation = ref(false)
const userStore = useUserStore()
const userProfile = computed(() => userStore.profile)
const recommendation = ref(null)
const reasoning = ref('')
const selectedGenre = ref('')
const useWishlist = ref(false)
const genres = [
  'Action', 'Adventure', 'RPG', 'Strategy', 'Simulation', 'Puzzle', 'Sports', 'Indie', 'Horror', 'Multiplayer'
]

const loading = ref(false)
const errorMsg = ref('')
const snackbar = ref(false)

function steamStoreUrl(gameId) {
  return `https://store.steampowered.com/app/${gameId}`
}

async function fetchRecommendation() {
  loading.value = true
  errorMsg.value = ''
  try {
    const result = await getRecommendation({
      steamId: userStore.steamId,
      genre: selectedGenre.value,
      useWishlist: useWishlist.value,
    })
    recommendation.value = result.game
    reasoning.value = result.reasoning
    showRecommendation.value = true
    userStore.addPastRecommendation(result.game)
    await updatePreferences({
      steamId: userStore.steamId,
      liked: userStore.liked,
      disliked: userStore.disliked,
      pastRecommendations: userStore.pastRecommendations,
    })
  } catch (err) {
    errorMsg.value = err?.message || 'Failed to get recommendation.'
    snackbar.value = true
  } finally {
    loading.value = false
  }
}

function showPastRecommendation(game) {
  recommendation.value = game
  reasoning.value = ''
  showRecommendation.value = true
}

function showRecommendationDetails(game) {
  recommendation.value = game
  reasoning.value = ''
  showRecommendation.value = true
}

async function likeRecommendation(game) {
  loading.value = true
  errorMsg.value = ''
  try {
    userStore.addLiked(game)
    await updatePreferences({
      steamId: userStore.steamId,
      liked: userStore.liked,
      disliked: userStore.disliked,
      pastRecommendations: userStore.pastRecommendations,
    })
  } catch (err) {
    errorMsg.value = err?.message || 'Failed to update preferences.'
    snackbar.value = true
  } finally {
    loading.value = false
  }
}

async function dislikeRecommendation(game) {
  loading.value = true
  errorMsg.value = ''
  try {
    userStore.addDisliked(game)
    await updatePreferences({
      steamId: userStore.steamId,
      liked: userStore.liked,
      disliked: userStore.disliked,
      pastRecommendations: userStore.pastRecommendations,
    })
  } catch (err) {
    errorMsg.value = err?.message || 'Failed to update preferences.'
    snackbar.value = true
  } finally {
    loading.value = false
  }
}

async function removePastRecommendation(gameId) {
  loading.value = true
  errorMsg.value = ''
  try {
    userStore.removePastRecommendation(gameId)
    await updatePreferences({
      steamId: userStore.steamId,
      liked: userStore.liked,
      disliked: userStore.disliked,
      pastRecommendations: userStore.pastRecommendations,
    })
  } catch (err) {
    errorMsg.value = err?.message || 'Failed to update preferences.'
    snackbar.value = true
  } finally {
    loading.value = false
  }
}

async function clearPastRecommendations() {
  loading.value = true
  errorMsg.value = ''
  try {
    userStore.clearPastRecommendations()
    await updatePreferences({
      steamId: userStore.steamId,
      liked: userStore.liked,
      disliked: userStore.disliked,
      pastRecommendations: userStore.pastRecommendations,
    })
  } catch (err) {
    errorMsg.value = err?.message || 'Failed to update preferences.'
    snackbar.value = true
  } finally {
    loading.value = false
  }
}

async function removeLiked(gameId) {
  loading.value = true
  errorMsg.value = ''
  try {
    userStore.removeLiked(gameId)
    await updatePreferences({
      steamId: userStore.steamId,
      liked: userStore.liked,
      disliked: userStore.disliked,
      pastRecommendations: userStore.pastRecommendations,
    })
  } catch (err) {
    errorMsg.value = err?.message || 'Failed to update preferences.'
    snackbar.value = true
  } finally {
    loading.value = false
  }
}

async function removeDisliked(gameId) {
  loading.value = true
  errorMsg.value = ''
  try {
    userStore.removeDisliked(gameId)
    await updatePreferences({
      steamId: userStore.steamId,
      liked: userStore.liked,
      disliked: userStore.disliked,
      pastRecommendations: userStore.pastRecommendations,
    })
  } catch (err) {
    errorMsg.value = err?.message || 'Failed to update preferences.'
    snackbar.value = true
  } finally {
    loading.value = false
  }
}

async function moveLikedToDisliked(gameId) {
  loading.value = true
  errorMsg.value = ''
  try {
    userStore.moveLikedToDisliked(gameId)
    await updatePreferences({
      steamId: userStore.steamId,
      liked: userStore.liked,
      disliked: userStore.disliked,
      pastRecommendations: userStore.pastRecommendations,
    })
  } catch (err) {
    errorMsg.value = err?.message || 'Failed to update preferences.'
    snackbar.value = true
  } finally {
    loading.value = false
  }
}

async function moveDislikedToLiked(gameId) {
  loading.value = true
  errorMsg.value = ''
  try {
    userStore.moveDislikedToLiked(gameId)
    await updatePreferences({
      steamId: userStore.steamId,
      liked: userStore.liked,
      disliked: userStore.disliked,
      pastRecommendations: userStore.pastRecommendations,
    })
  } catch (err) {
    errorMsg.value = err?.message || 'Failed to update preferences.'
    snackbar.value = true
  } finally {
    loading.value = false
  }
}
</script>