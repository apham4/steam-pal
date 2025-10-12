<script setup>
import { ref } from 'vue';
import FilterBar from './components/FilterBar.vue';
import StatsChart from './components/StatsChart.vue';
import ExportButton from './components/ExportButton.vue';

const filter = ref({});
const chartData = ref([]);

function onFilterChanged(newFilter) {
  filter.value = newFilter;
  // TODO: fetch new chart data based on filter
}
</script>

<template>
  <v-app>
    <v-app-bar color="primary" dark>
      <v-toolbar-title>Steam Pal Admin Dashboard</v-toolbar-title>
    </v-app-bar>
    <v-main>
      <v-container class="py-6">
        <filter-bar @filter-changed="onFilterChanged" />
        <stats-chart :filter="filter" />
        <export-button :data="chartData" />
      </v-container>
    </v-main>
  </v-app>
</template>
