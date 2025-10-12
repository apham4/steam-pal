<script setup>

import { computed, watch, ref } from 'vue';
import { Bar, Line } from 'vue-chartjs';
import {
  Chart,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { fetchEvents } from '../services/api.js';

Chart.register(CategoryScale, LinearScale, BarElement, PointElement, LineElement, Title, Tooltip, Legend);

const props = defineProps({
  filter: {
    type: Object,
    default: () => ({})
  }
});
const emit = defineEmits(['chart-data-changed']);

const chartType = ref('bar'); // Could be 'bar', 'line', etc.
const chartData = ref({
  labels: [],
  datasets: []
});

const chartOptions = computed(() => ({
  responsive: true,
  plugins: {
    legend: { position: 'top' },
    title: { display: true, text: 'User Stats' }
  }
}));



function groupEventsBy(events, aggregation) {
  // Simple daily aggregation example, extend for weekly/monthly as needed
  const result = {};
  events.forEach(ev => {
    const date = ev.timestamp.slice(0, 10); // YYYY-MM-DD
    result[date] = (result[date] || 0) + 1;
  });
  return result;
}

async function fetchChartData(filter) {
  try {
    const events = await fetchEvents(filter);
    // Aggregate events by day (can extend for week/month)
    const grouped = groupEventsBy(events, filter.aggregation || 'daily');
    chartData.value = {
      labels: Object.keys(grouped),
      datasets: [
        {
          label: filter.statType,
          data: Object.values(grouped),
          backgroundColor: '#1976d2'
        }
      ]
    };
    emit('chart-data-changed', chartData.value);
  } catch (err) {
    chartData.value = { labels: [], datasets: [] };
    emit('chart-data-changed', chartData.value);
  }
}

watch(() => props.filter, (newFilter) => {
  fetchChartData(newFilter);
}, { immediate: true });
</script>

<style scoped>
.v-card {
  max-width: 900px;
  margin: auto;
}
</style>

<template>
  <v-card class="mb-6">
    <v-card-title>User Statistics</v-card-title>
    <v-card-text>
      <Bar v-if="chartType === 'bar'" :data="chartData" :options="chartOptions" />
      <Line v-else-if="chartType === 'line'" :data="chartData" :options="chartOptions" />
      <!-- Add more chart types as needed -->
      <div v-if="!chartData || chartData.datasets.length === 0" class="text-center py-6">
        No data available for selected filters.
      </div>
    </v-card-text>
  </v-card>
</template>