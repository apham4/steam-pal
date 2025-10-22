<script setup>
import { ref, computed, watch } from 'vue'
import { useUserStore } from '../stores/user'
import { getRecommendation, getRecommendationHistory, logRecommendationRequest, logRecommendationActionTaken } from '../services/api'

//#region General
const tab = ref(0)
const userStore = useUserStore()
const userProfile = computed(() => userStore.profile)

const errorMsg = ref('')
const snackbar = ref(false)

// Watch for tab change
watch(tab, async (newVal) => {
  if (newVal === 1) {
    // Past Recommendations tab
    fetchRecommendationHistory(pastRecommendationsPage.value, pastRecommendationsPageSize.value)
  } 
})
//#endregion


//#region Recommendation Details
const showRecommendation = ref(false)
const recommendation = ref(null)
const reasoning = ref('')

function steamStoreUrl(gameId) {
  return `https://store.steampowered.com/app/${gameId}`
}

function showRecommendationDetails(game) {
  recommendation.value = game
  reasoning.value = ''
  showRecommendation.value = true
}
//#endregion


//#region Get Recommendation
const genres = [
  'Action', 'Adventure', 'RPG', 'Strategy', 'Simulation', 'Puzzle', 'Sports', 'Indie', 'Horror', 'Multiplayer'
]
const selectedGenres = ref([])
const customGenre = ref('')
const customGenres = ref([])
const useWishlist = ref(false)
const loading = ref(false)

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

async function fetchRecommendation() {
  loading.value = true
  errorMsg.value = ''
  try {
    await logRecommendationRequest();
    const allGenres = [...selectedGenres.value, ...customGenres.value]
    const result = await getRecommendation({
      genres: allGenres, // send array, can be empty
      useWishlist: useWishlist.value,
    })
    recommendation.value = result.game
    reasoning.value = result.reasoning
    showRecommendation.value = true
  } catch (err) {
    errorMsg.value = err?.message || 'Failed to get recommendation.'
    snackbar.value = true
  } finally {
    loading.value = false
  }
}
//#endregion


//#region Past Recommendations
// -- Past Recommendations data & states
const pastRecommendations = ref([])
const pastRecommendationsLoading = ref(false)
const pastRecommendationsError = ref('')
// -- Past Recommendations pagination
const pastRecommendationsPage = ref(1)
const pastRecommendationsPageSize = ref(7)
const pastRecommendationsTotalPages = ref(1)

function handlePastRecommendationsPageChange(newPage) {
  fetchRecommendationHistory(newPage, pastRecommendationsPageSize.value)
}

async function fetchRecommendationHistory(pageNum, pageSize) {
  pastRecommendationsLoading.value = true
  pastRecommendationsError.value = ''
  try {
    const result = await getRecommendationHistory(pageNum, pageSize)
    pastRecommendations.value = result.recommendations || []
    pastRecommendationsTotalPages.value = result.pages || 1
    pastRecommendationsPage.value = result.currentPage || pageNum
  } catch (err) {
    pastRecommendationsError.value = err?.message || 'Failed to load history.'
    pastRecommendations.value = []
  } finally {
    pastRecommendationsLoading.value = false
  }
}
//#endregion


//#region Manage Preferences
async function likeRecommendation(game) {
  await logRecommendationActionTaken('like', game.id);
  //
}
async function dislikeRecommendation(game) {
  await logRecommendationActionTaken('dislike', game.id);
  //
}
async function handleViewOnSteam(game) {
  await logRecommendationActionTaken('view_store', game.id);
}
function removeLiked(gameId) {
  //
}
function removeDisliked(gameId) {
  //
}
function moveLikedToDisliked(gameId) {
  //
}
function moveDislikedToLiked(gameId) {
  //
}
//#endregion
</script>

<template>
  <v-container fluid>
    <!-- Steam Pal Title Header -->
    <v-row justify="center">
      <v-col cols="12" md="8">
        <div class="d-flex flex-column align-center">
          <div class="d-flex align-center justify-center mb-2">
            <img src="/icon.png" alt="Steam Pal Icon" style="width:48px; height:48px;" class="mr-2" />
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
              <template v-if="userProfile?.avatar_url">
                <img :src="userProfile?.avatar_url" alt="Avatar" style="object-fit: contain; width: 100%; height: 100%;" />
              </template>
              <template v-else>
                <v-icon size="40">mdi-account-circle</v-icon>
              </template>
            </v-avatar>
            <span class="font-weight-bold font-size-1">{{ userProfile?.display_name || "Steam User" }}</span>
            <span class="ml-2 font-size-1">(Steam ID: {{ userProfile?.steam_id }})</span>
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
            <!-- [V2 TODO] Preferences <v-tab>Manage Preferences</v-tab> -->
          </v-tabs>
        </div>
        <v-tabs-items v-model="tab">
          <v-tab-item>
            <!-- Get Recommendation tab content -->
            <div v-if="tab === 0" class="d-flex flex-column align-center mt-4" style="gap: 8px;">
            <!-- [V2 TODO] Filters
              <div class="genre-checkbox-grid d-flex flex-column align-center" style="gap: 4px;">
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
                  placeholder="Type in genres and press Enter."
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
              -->
              <!-- [ADDITIONAL] Wishlist-related features
              <v-checkbox
                v-model="useWishlist"
                label="Consider my Steam Wishlist"
                color="secondary"
                hide-details="auto"
              />
              -->
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
                <div v-if="pastRecommendationsLoading" class="d-flex align-center justify-center" style="height:100%;">
                  <v-progress-circular indeterminate color="primary" />
                </div>
                <div v-else-if="pastRecommendationsError" class="d-flex align-center justify-center" style="height:100%;">
                  <span class="text-center">{{ pastRecommendationsError }}</span>
                </div>
                <div v-else-if="pastRecommendations.length === 0" class="d-flex align-center justify-center" style="height:100%;">
                  <span class="text-center">No recommendation history. Get started by going to the Get Recommendation tab.</span>
                </div>
                <v-list v-else>
                  <v-list-item
                    v-for="game in pastRecommendations"
                    :key="game.id"
                    @click="showRecommendationDetails(game)"
                  >
                    <div style="display: flex; align-items: center; width: 100%;">
                      <span style="flex: 1;">{{ game.title }}</span>
                        <!-- Cut 
                        <v-btn icon @click.stop="removePastRecommendation(game.id)">
                            <v-icon>mdi-delete</v-icon>
                        </v-btn>
                        -->
                    </div>
                  </v-list-item>
                </v-list>
              </v-card>
              <!-- Cut content 
              <div class="d-flex justify-center mt-2">
                <v-btn color="error" @click="clearPastRecommendations">Clear All</v-btn>
              </div> 
              -->
              <div class="d-flex justify-center mt-2" v-if="pastRecommendationsTotalPages > 1">
                <v-pagination
                  v-model="pastRecommendationsPage"
                  :length="pastRecommendationsTotalPages"
                  @input="handlePastRecommendationsPageChange"
                  color="primary"
                />
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
          <v-card-title class="text-center text-h5 font-weight-bold" style="justify-content: center;">
            {{ reasoning ? 'Your Next Favorite Game' : 'Looking Back' }}
          </v-card-title>
          <v-card-text>
            <div v-if="recommendation" class="d-flex flex-row align-center mb-2" style="min-height:190px;">
              <div style="display:flex; align-items:center;">
                <v-img :src="recommendation.thumbnail" height="190" width="400" contain style="margin-right:16px;" />
              </div>
              <v-card class="pa-2" color="background" dark style="flex:1; height:190px; display:flex; flex-direction:column; align-items:flex-start; justify-content:flex-start; overflow-y:auto;">
                <div class="recommendation-title">{{ recommendation.title }}</div>
                <div>
                  <span class="header">Release Date:</span> {{ recommendation.releaseDate }}
                </div>
                <div>
                  <span class="header">Publisher:</span> {{ recommendation.publisher }}
                </div>
                <div>
                  <span class="header">Developer:</span> {{ recommendation.developer }}
                </div>
                <div>
                  <span class="header">Price:</span> <span :style="recommendation.salePrice ? 'text-decoration: line-through;' : ''">{{ recommendation.price }}</span>
                  <span v-if="recommendation.salePrice" class="ml-2">{{ recommendation.salePrice }}</span>
                </div>
                <div>
                  <span class="header">Short Description:</span> {{ recommendation.description }}
                </div>
              </v-card>
            </div>
            <v-card v-if="reasoning" class="mt-2 pa-2" color="background" dark>
              <div class="header">
                <v-icon left style="color: #66c0f4; vertical-align: middle;">mdi-alert-circle-outline</v-icon>
                Why Steam Pal thinks this is your next favorite game:
              </div>
              <div style="max-height: 80px; overflow-y: auto;">{{ reasoning }}</div>
            </v-card>
            <div class="d-flex justify-center mt-4" style="gap:20px;">
                <!-- [V2 TODO] Preferences 
                <v-btn color="success" class="mt-2" @click="likeRecommendation(recommendation)">
                  <v-icon class="mr-2">mdi-thumb-up</v-icon> Like
                </v-btn>
                <v-btn color="error" class="mt-2" @click="dislikeRecommendation(recommendation)">
                  <v-icon class="mr-2">mdi-thumb-down</v-icon> Dislike
                </v-btn>
                -->
                <v-btn color="info" class="mt-2" @click="handleViewOnSteam(recommendation)" :href="steamStoreUrl(recommendation.id)" target="_blank">
                  <v-icon class="mr-2">mdi-cart</v-icon> View on Steam
                </v-btn>
                <!-- [ADDITIONAL] Wishlist-related features
                <v-btn color="info" class="mt-2">
                  <v-icon class="mr-2">mdi-star</v-icon> Add to Wishlist
                </v-btn>
                -->
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

<style scoped>
.genre-checkbox-grid {
  width: 100%;
  max-width: 600px;
}
</style>