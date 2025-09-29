<script setup>
import { ref, onMounted } from 'vue';
import api from './services/api'; // Import our API service

const currentUser = ref(null);
const recommendation = ref(null);
const isLoading = ref(false);

// Fetch the current user when the component is created
onMounted(async () => {
  try {
    const response = await api.getCurrentUser();
    currentUser.value = response.data;
  } catch (error) {
    console.error("Could not fetch user:", error);
  }
});

// Function to get a new recommendation
const handleGetRecommendation = async () => {
  isLoading.value = true;
  recommendation.value = null;
  try {
    // These filters would come from user input in the real app
    const filters = { genres: ["RPG"], tags: ["Story Rich"] };
    const response = await api.getNewRecommendation(filters);
    recommendation.value = response.data;
  } catch (error) {
    console.error("Could not fetch recommendation:", error);
  } finally {
    isLoading.value = false;
  }
};
</script>

<template>
  <main>
    <h1>Steam Pal 🎮</h1>
    <p v-if="currentUser">Welcome, {{ currentUser.display_name }}!</p>
    <hr />
    <button @click="handleGetRecommendation" :disabled="isLoading">
      {{ isLoading ? 'Thinking...' : 'Get AI Recommendation' }}
    </button>

    <div v-if="recommendation" class="card">
      <h2>{{ recommendation.game_name }}</h2>
      <p><strong>AI Reasoning:</strong> {{ recommendation.reasoning }}</p>
    </div>
  </main>
</template>

<style scoped>
  main { max-width: 600px; margin: 2rem auto; font-family: sans-serif; }
  .card { margin-top: 1.5rem; padding: 1rem; border: 1px solid #ccc; border-radius: 8px; }
</style>