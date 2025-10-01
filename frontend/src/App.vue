<template>
  <component :is="currentView" @authenticated="handleAuthenticated" @guest="handleGuest" @changeUser="handleChangeUser" />
</template>

<script setup>
import { ref, markRaw } from 'vue'
import UserPage from './components/UserPage.vue'
import MainPage from './components/MainPage.vue'
import { useUserStore } from './stores/user'

const currentView = ref(markRaw(UserPage))
const userStore = useUserStore()

function handleAuthenticated({ steamId, profile, jwt }) {
  userStore.setAuthenticated({ steamId, profile, jwt })
  currentView.value = markRaw(MainPage)
}

function handleGuest(steamId) {
  userStore.setGuest(steamId)
  currentView.value = markRaw(MainPage)
}

function handleChangeUser() {
  userStore.logout()
  currentView.value = markRaw(UserPage)
}
</script>