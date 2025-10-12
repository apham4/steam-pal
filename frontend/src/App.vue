<script setup>
import { ref, markRaw } from 'vue'
import UserPage from './components/UserPage.vue'
import MainPage from './components/MainPage.vue'
import { onMounted, computed } from 'vue'
import { useUserStore } from './stores/user'
import { logUserLogin, getCurrentUser, logOut } from './services/api'

const currentView = ref(markRaw(UserPage))
const userStore = useUserStore()
const userDisplayName = computed(() => userStore.profile?.display_name)

onMounted(() => {
  updateTitle()
  window.addEventListener('message', async (event) => {
    // Ensure the message is from a trusted origin
    if (event.origin !== window.location.origin) return
    const token = event.data.steamPalToken
    if (token) {
      userStore.setJwt(token)
      // Clean up the URL (remove token param)
      window.history.replaceState({}, document.title, window.location.pathname)
      // Fetch user profile
      try {
        const profile = await getCurrentUser()
        userStore.setProfile(profile)
        // Switch to MainPage if authenticated
        currentView.value = markRaw(MainPage)
        logUserLogin() // Log the login event
      } catch (err) {
        // Handle errors (e.g., invalid token)
        console.error('Failed to fetch user profile:', err)
      }
    } else if (userStore.isAuthenticated) {
      // If already authenticated (e.g., from previous session), show MainPage
      currentView.value = markRaw(MainPage)
    } else {
      currentView.value = markRaw(UserPage)
    }
    updateTitle()
  })
})

function updateTitle() {
  if (userDisplayName.value) {
    document.title = `Steam Pal | ${userDisplayName.value}`
  } else {
    document.title = 'Steam Pal'
  }
}

function handleChangeUser() {
  userStore.logout()
  logOut() // Call the logout API
  currentView.value = markRaw(UserPage)
}
</script>

<template>
  <component :is="currentView" @changeUser="handleChangeUser" />
</template>