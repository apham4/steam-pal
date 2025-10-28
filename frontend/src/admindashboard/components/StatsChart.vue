<script setup>
import { computed, watch, ref } from 'vue';
import { Line } from 'vue-chartjs';
import {
  Chart,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

Chart.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const props = defineProps({
  data: {
    type: Object,
    required: true
  }
});

const chartOptions = computed(() => ({
  responsive: true,
  plugins: {
    legend: { position: 'top' },
    title: { display: true, text: 'User Events Over Time' }
  },
  scales: {
    x: { title: { display: true, text: 'Date' } },
    y: { title: { display: true, text: 'Event Count' }, beginAtZero: true }
  }
}));
</script>

<template>
  <v-card class="mb-6">
    <v-card-title>User Events Chart</v-card-title>
    <v-card-text>
      <Line v-if="data && data.labels && data.labels.length" :data="data" :options="chartOptions" />
      <div v-else class="text-center py-6">
        No Data
      </div>
    </v-card-text>
  </v-card>
</template>