<template>
  <v-container fluid>
    <!-- Steam Pal Title Header -->
    <v-row justify="center">
      <v-col cols="12" md="8">
        <div class="d-flex flex-column align-center">
          <div class="d-flex align-center justify-center mb-2">
            <v-icon size="48" color="secondary" class="mr-2">mdi-steam</v-icon>
            <span class="steam-title">Steam Pal</span>
          </div>
          <div class="subtitle text-center mb-2">AI-Powered Game Recommendations for Steam Users</div>
        </div>
      </v-col>
    </v-row>

    <!-- Current User Section -->
    <v-row justify="center">
      <v-col cols="12" md="8">
        <v-card color="surface" dark>
          <v-card-title class="d-flex align-center">
            <v-avatar size="50" class="mr-2">
              <img :src="userProfile?.avatar" alt="Avatar" />
            </v-avatar>
            <span class="font-weight-bold font-size-1">{{ userProfile?.name || "Steam User" }}</span>
            <span class="ml-2 font-size-1">(Steam ID: {{ userStore.steamId }})</span>
            <v-spacer />
            <v-btn color="secondary" @click="$emit('changeUser')" class="ml-4">Change User</v-btn>
          </v-card-title>
        </v-card>
      </v-col>
    </v-row>

    <!-- Action & Preferences Section -->
    <v-row justify="center">
      <v-col cols="12" md="8">
        <div class="d-flex flex-column align-center">
          <v-tabs v-model="tab" background-color="primary" dark class="justify-center">
            <v-tab>Get Recommendation</v-tab>
            <v-tab>Past Recommendations</v-tab>
            <v-tab>Manage Preferences</v-tab>
          </v-tabs>
        </div>
        <v-tabs-items v-model="tab">
          <v-tab-item>
            <!-- Get Recommendation tab content -->
            <div v-if="tab === 0" class="d-flex flex-column align-center mt-4" style="gap: 8px;">
              <div class="genre-checkbox-grid mb-2 d-flex flex-column align-center" style="gap: 4px;">
                <v-row class="justify-center" style="gap: 0;">
                  <v-col v-for="genre in genres" :key="genre" cols="6" sm="4" md="3" class="py-0 my-0">
                    <v-checkbox
                      :label="genre"
                      :value="genre"
                      v-model="selectedGenres"
                      color="secondary"
                      hide-details="auto"
                      density="compact"
                    />
                  </v-col>
                </v-row>
                <v-text-field
                  v-model="customGenre"
                  label="Custom Genre(s)"
                  color="secondary"
                  outlined
                  hide-details
                  density="compact"
                  class="mt-1"
                  style="width:500px;"
                  placeholder="Type genres separated by commas."
                  @keydown.enter="addCustomGenre"
                  hint="You can enter multiple genres separated by commas."
                  persistent-hint
                />
                <div v-if="customGenres.length" class="d-flex flex-wrap mt-1">
                  <v-chip
                    v-for="(genre, idx) in customGenres"
                    :key="genre + idx"
                    class="mr-1"
                    color="secondary"
                    label
                    @click:close="removeCustomGenre(idx)"
                    closable
                  >{{ genre }}</v-chip>
                </div>
              </div>
              <v-checkbox
                v-if="userStore.role === 'authenticated'"
                v-model="useWishlist"
                label="Take my Steam Wishlist into account"
                color="secondary"
                hide-details="auto"
              />
              <div class="d-flex justify-center">
                <v-btn color="accent" @click="fetchRecommendation" :disabled="loading" class="elevation-4 px-6 py-3 text-h6 d-flex align-center" style="min-width:220px;">
                  <template v-if="loading">
                    <v-progress-circular indeterminate color="primary" size="20" />
                    <span class="ml-2">Loading...</span>
                  </template>
                  <template v-else>
                    <v-icon left class="mr-2" style="vertical-align:middle;">mdi-lightbulb-on</v-icon>
                    <span style="vertical-align:middle;">Get AI Recommendation</span>
                  </template>
                </v-btn>
              </div>
            </div>
          </v-tab-item>
          <v-tab-item>
            <!-- Past Recommendations tab content -->
            <div v-if="tab === 1" class="d-flex flex-column align-center mt-4">
              <v-card class="pa-2" style="width:100%; max-width:600px; height:250px; overflow-y:auto;">
                <div v-if="userStore.pastRecommendations.length === 0" class="d-flex align-center justify-center" style="height:100%;">
                  <span class="text-center">No recommendation history. Get started by going to the Get Recommendation tab.</span>
                </div>
                <v-list v-else>
                  <v-list-item
                    v-for="game in userStore.pastRecommendations"
                    :key="game.id"
                    @click="showPastRecommendation(game)"
                  >
                    <div style="display: flex; align-items: center; width: 100%;">
                        <span style="flex: 1;">{{ game.title }}</span>
                        <v-btn icon @click.stop="removePastRecommendation(game.id)">
                            <v-icon>mdi-delete</v-icon>
                        </v-btn>
                    </div>
                  </v-list-item>
                </v-list>
              </v-card>
              <div class="d-flex justify-center mt-2">
                <v-btn color="error" @click="clearPastRecommendations">Clear All</v-btn>
              </div>
            </div>
          </v-tab-item>
          <v-tab-item>
            <!-- Manage Preferences tab content -->
            <div v-if="tab === 2" class="d-flex flex-row align-center mt-4">
              <v-col>
                <div class="text-center font-weight-bold mb-2">Liked</div>
                <v-card class="pa-2" style="height:250px; overflow-y:auto;">
                  <div v-if="userStore.liked.length === 0" class="d-flex align-center justify-center" style="height:100%;">
                    <span class="text-center">No liked recommendations.</span>
                  </div>
                  <v-list v-else>
                    <v-list-item
                      v-for="game in userStore.liked"
                      :key="game.id"
                      @click="showRecommendationDetails(game)"
                    >
                        <div style="display: flex; align-items: center; width: 100%;">
                            <span style="flex: 1;">{{ game.title }}</span>
                            <v-btn icon @click.stop="removeLiked(game.id)"><v-icon>mdi-delete</v-icon></v-btn>
                            <v-btn icon @click.stop="moveLikedToDisliked(game.id)"><v-icon>mdi-arrow-right</v-icon></v-btn>
                        </div>
                    </v-list-item>
                  </v-list>
                </v-card>
              </v-col>
              <v-col>
                <div class="text-center font-weight-bold mb-2">Disliked</div>
                <v-card class="pa-2" style="height:250px; overflow-y:auto;">
                  <div v-if="userStore.disliked.length === 0" class="d-flex align-center justify-center" style="height:100%;">
                    <span class="text-center">No disliked recommendations.</span>
                  </div>
                  <v-list v-else>
                    <v-list-item
                      v-for="game in userStore.disliked"
                      :key="game.id"
                      @click="showRecommendationDetails(game)"
                    >
                        <div style="display: flex; align-items: center; width: 100%;">
                            <span style="flex: 1;">{{ game.title }}</span>
                            <v-btn icon @click.stop="removeDisliked(game.id)"><v-icon>mdi-delete</v-icon></v-btn>
                            <v-btn icon @click.stop="moveDislikedToLiked(game.id)"><v-icon>mdi-arrow-left</v-icon></v-btn>
                        </div>
                    </v-list-item>
                  </v-list>
                </v-card>
              </v-col>
            </div>
          </v-tab-item>
        </v-tabs-items>
      </v-col>
    </v-row>

    <!-- Recommendation Result Section (hidden initially) -->
    <v-row v-if="showRecommendation" justify="center">
      <v-col cols="12" md="8">
        <v-card color="surface" dark>
          <v-card-title class="text-center text-h5 font-weight-bold" style="justify-content: center;">Your Next Favorite Game</v-card-title>
          <v-card-text>
            <div v-if="recommendation" class="d-flex flex-row align-center mb-2" style="min-height:190px;">
              <div style="display:flex; align-items:center;">
                <v-img :src="recommendation.thumbnail" height="190" width="400" contain style="margin-right:16px;" />
              </div>
              <v-card class="pa-2" color="background" dark style="flex:1; height:190px; display:flex; flex-direction:column; align-items:flex-start; justify-content:flex-start;">
                <div class="text-h5 font-weight-bold mb-1">{{ recommendation.title }}</div>
                <div>Release Date: {{ recommendation.releaseDate }}</div>
                <div>Publisher: {{ recommendation.publisher }}</div>
                <div>Developer: {{ recommendation.developer }}</div>
                <div>
                  Price: <span :style="recommendation.salePrice ? 'text-decoration: line-through;' : ''">{{ recommendation.price }}</span>
                  <span v-if="recommendation.salePrice" class="ml-2">{{ recommendation.salePrice }}</span>
                </div>
                <div> Short Description: {{ recommendation.description }}</div>
              </v-card>
            </div>
            <v-card v-if="reasoning" class="mt-2 pa-2" color="background" dark>
              <div style="max-height: 80px; overflow-y: auto;">{{ reasoning }}</div>
            </v-card>
            <div class="d-flex justify-center mt-4" style="gap:20px;">
              <v-btn color="success" class="mt-2" @click="likeRecommendation(recommendation)">
                <span class="mr-2">👍</span> Like
              </v-btn>
              <v-btn color="error" class="mt-2" @click="dislikeRecommendation(recommendation)">
                <span class="mr-2">👎</span> Dislike
              </v-btn>
              <v-btn color="info" class="mt-2" :href="steamStoreUrl(recommendation.id)" target="_blank">
                <span class="mr-2">🛒</span> View on Steam
              </v-btn>
              <v-btn v-if="userStore.role === 'authenticated'" color="accent" class="mt-2">
                <span class="mr-2">⭐</span> Add to Wishlist
              </v-btn>
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
const genres = [
  'Action', 'Adventure', 'RPG', 'Strategy', 'Simulation', 'Puzzle', 'Sports', 'Indie', 'Horror', 'Multiplayer'
]
const selectedGenres = ref([])
const customGenre = ref('')
const customGenres = ref([])
const useWishlist = ref(false)
const loading = ref(false)
const errorMsg = ref('')
const snackbar = ref(false)

function addCustomGenre() {
  if (customGenre.value.trim()) {
    // Split by comma, trim, and add unique genres
    const genresToAdd = customGenre.value.split(',').map(g => g.trim()).filter(g => g)
    genresToAdd.forEach(g => {
      if (!customGenres.value.includes(g)) {
        customGenres.value.push(g)
      }
    })
    customGenre.value = ''
  }
}
function removeCustomGenre(idx) {
  customGenres.value.splice(idx, 1)
}

function steamStoreUrl(gameId) {
  return `https://store.steampowered.com/app/${gameId}`
}

async function fetchRecommendation() {
  loading.value = true
  errorMsg.value = ''
  try {
    const allGenres = [...selectedGenres.value, ...customGenres.value]
    const result = await getRecommendation({
      steamId: userStore.steamId,
      genres: allGenres, // send array, can be empty
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

<style scoped>
.genre-checkbox-grid {
  width: 100%;
  max-width: 600px;
}
</style>