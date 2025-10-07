<script setup>
import { ref } from 'vue'
import { getSteamLoginUrl } from '../services/api'

const loading = ref(false)
const errorMsg = ref('')
const snackbar = ref(false)

async function signInWithSteam() {
  loading.value = true;
  errorMsg.value = '';
  try {
    const loginUrl = await getSteamLoginUrl();
    window.open(loginUrl, '_blank'); // Open login URL in a new tab
  } catch (err) {
    errorMsg.value = err?.message || 'Failed to get Steam login URL.';
    snackbar.value = true;
  } finally {
    loading.value = false;
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
                <img src="/icon.png" alt="Steam Pal Icon" style="width:48px; height:48px;" class="mr-2" />
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