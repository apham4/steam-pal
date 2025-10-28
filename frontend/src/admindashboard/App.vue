<script setup>
import { ref } from 'vue';
import FilterBar from './components/FilterBar.vue';
import StatsChart from './components/StatsChart.vue';
import ExportButton from './components/ExportButton.vue';
import { fetchUserEvents } from './services/api.js';

const filter = ref(null);
const chartData = ref(null);
const rawData = ref([]);
const loading = ref(false);
const error = ref('');
const showNoData = ref(false);
const getRawData = ref(false);

const errorMsg = ref('')
const snackbar = ref(false)

function getAggregation(from, to) {
  const days = (to - from) / 86400;
  return days < 30 ? 'per-day' : 'per-three-days';
}

function groupEvents(events, aggregation, eventTypes) {
  if (!events.length) return { labels: [], datasets: [] };
  const buckets = {};
  const labelsSet = new Set();
  const msPerBucket = aggregation === 'per-day' ? 86400000 : 86400000 * 3;

  const minTs = Math.min(...events.map(e => e.timestamp)) * 1000;
  const maxTs = Math.max(...events.map(e => e.timestamp)) * 1000;

  for (let t = minTs; t <= maxTs; t += msPerBucket) {
    const label = new Date(t).toLocaleDateString();
    labelsSet.add(label);
    eventTypes.forEach(type => {
      buckets[`${label}_${type}`] = 0;
    });
  }

  events.forEach(e => {
    const bucketStart = e.timestamp * 1000 - ((e.timestamp * 1000 - minTs) % msPerBucket);
    const label = new Date(bucketStart).toLocaleDateString();
    buckets[`${label}_${e.eventType}`] = (buckets[`${label}_${e.eventType}`] || 0) + 1;
    labelsSet.add(label);
  });

  const labels = Array.from(labelsSet).sort((a, b) => new Date(a) - new Date(b));
  const datasets = eventTypes.map((type, idx) => ({
    label: type,
    data: labels.map(label => buckets[`${label}_${type}`] || 0),
    borderColor: `hsl(${(idx * 360) / eventTypes.length}, 70%, 50%)`,
    backgroundColor: `hsla(${(idx * 360) / eventTypes.length}, 70%, 50%, 0.2)`,
    tension: 0.2,
    fill: false,
  }));

  return { labels, datasets };
}

async function onRetrieveData(filterObj) {
  filter.value = filterObj;
  chartData.value = null;
  rawData.value = [];
  showNoData.value = false;
  error.value = '';
  loading.value = true;
  try {
    const { steamId, eventTypes, from, to } = filterObj;
    const aggregation = getAggregation(from, to);
    const events = await fetchUserEvents({
      steamId,
      eventType: eventTypes.join(','),
      from,
      to,
    });
    rawData.value = events;
    if (!events.length) {
      showNoData.value = true;
      chartData.value = null;
    } else {
      chartData.value = groupEvents(events, aggregation, eventTypes);
      showNoData.value = false;
    }
  } catch (e) {
    error.value = 'Failed to fetch data';
    errorMsg.value = error.value;
    snackbar.value = true;
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <v-app>
    <v-app-bar color="primary" dark>
      <v-toolbar-title>Steam Pal Admin Dashboard</v-toolbar-title>
    </v-app-bar>
    <v-main>
      <v-container class="py-6">
        <filter-bar @retrieve-data="onRetrieveData" />
        <div v-if="loading" class="text-center my-8">
          <v-progress-circular indeterminate color="primary" />
        </div>
        <div v-else>
          <stats-chart v-if="chartData && !showNoData" :data="chartData" />
          <div v-else-if="showNoData" class="text-center my-8">
            <h2>No Data</h2>
          </div>
        </div>
        <div class="d-flex flex-column align-start mt-4">
          <v-checkbox v-model="getRawData" label="Get raw data" />
          <export-button :data="getRawData ? rawData : chartData" :raw="getRawData" />
        </div>

        <!-- Error Snackbar -->
        <v-row>
          <v-col>
            <v-snackbar v-model="snackbar" color="error" timeout="4000">
              {{ errorMsg }}
            </v-snackbar>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </v-app>
</template>