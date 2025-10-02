<script setup>
import { ref } from 'vue'
import { useUserStore } from '../stores/user'
import { authenticateWithSteam, guestLogin } from '../services/api'
const steamId = ref('')
const userStore = useUserStore()
const emit = defineEmits(['authenticated', 'guest'])

const loading = ref(false)
const errorMsg = ref('')
const snackbar = ref(false)

async function signInWithSteam() {
  loading.value = true
  errorMsg.value = ''
  try {
    const result = await authenticateWithSteam()
    userStore.setAuthenticated({
      steamId: result.profile.steamId,
      profile: result.profile,
      jwt: result.jwt,
      liked: result.liked,
      disliked: result.disliked,
      pastRecommendations: result.pastRecommendations,
    })
    emit('authenticated', {
      steamId: result.profile.steamId,
      profile: result.profile,
      jwt: result.jwt,
    })
  } catch (err) {
    errorMsg.value = err?.message || 'Failed to authenticate with Steam.'
    snackbar.value = true
  } finally {
    loading.value = false
  }
}

async function continueAsGuest() {
  loading.value = true
  errorMsg.value = ''
  try {
    const result = await guestLogin(steamId.value)
    userStore.setGuest(result.profile.steamId)
    emit('guest', result.profile.steamId)
  } catch (err) {
    errorMsg.value = err?.message || 'Failed to continue as guest.'
    snackbar.value = true
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" md="6">
        <v-card class="pa-6" color="primary" dark>
          <v-card-text>
            <div class="d-flex mb-2">
                <v-icon size="48" color="secondary" class="mr-2">mdi-steam</v-icon>
                <span class="steam-title">Steam Pal</span>
            </div>
            <div class="subtitle mb-6">AI-Powered Game Recommendations for Steam Users</div>
            <v-btn
              color="secondary"
              class="mb-2"
              large
              @click="signInWithSteam"
              :disabled="loading"
            >
              <v-icon left>mdi-steam</v-icon>
              Sign In with Steam
              <v-progress-circular v-if="loading" indeterminate color="primary" size="20" class="ml-2" />
            </v-btn>
            <div class="mt-4">
              <v-text-field
                v-model="steamId"
                label="Or enter your 64-bit Steam ID as guest"
                outlined
                color="secondary"
                :disabled="loading"
              />
              <v-btn
                color="accent"
                :disabled="!steamId || loading"
                @click="continueAsGuest"
              >
                Continue as Guest
                <v-progress-circular v-if="loading" indeterminate color="primary" size="20" class="ml-2" />
              </v-btn>
            </div>
            <v-snackbar v-model="snackbar" color="error" timeout="4000">
              {{ errorMsg }}
            </v-snackbar>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<style scoped>
.fill-height {
  min-height: 100vh;
  background: #171a21;
}
</style>