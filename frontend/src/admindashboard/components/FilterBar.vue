<script setup>
import { ref, computed } from 'vue';
const emit = defineEmits(['filter-changed']);

const menu = ref(false);
const dateRange = ref([]);
const aggregation = ref('daily');
const statType = ref('Logins');

const dateRangeText = computed(() => {
  if (!dateRange.value.length) return '';
  return dateRange.value.join(' to ');
});

function updateDateRange(val) {
  dateRange.value = val;
}

function emitFilter() {
  emit('filter-changed', {
    dateRange: dateRange.value,
    aggregation: aggregation.value,
    statType: statType.value
  });
}
</script>

<style scoped>
.v-card {
  max-width: 900px;
  margin: auto;
}
</style>

<template>
  <v-card class="mb-6">
    <v-card-title>Filters</v-card-title>
    <v-card-text>
      <v-row>
        <v-col cols="12" md="4">
          <v-menu v-model="menu" :close-on-content-click="false" transition="scale-transition" offset-y>
            <template #activator="{ on, attrs }">
              <v-text-field
                v-model="dateRangeText"
                label="Date Range"
                readonly
                v-bind="attrs"
                v-on="on"
              />
            </template>
            <v-date-picker
              v-model="dateRange"
              range
              @change="updateDateRange"
            />
          </v-menu>
        </v-col>
        <v-col cols="12" md="4">
          <v-select
            v-model="aggregation"
            :items="['daily', 'weekly', 'monthly']"
            label="Aggregation"
          />
        </v-col>
        <v-col cols="12" md="4">
          <v-select
            v-model="statType"
            :items="['Logins', 'Recommendation Requests', 'Actions Taken']"
            label="Stat Type"
          />
        </v-col>
      </v-row>
      <v-btn color="primary" @click="emitFilter">Apply Filters</v-btn>
    </v-card-text>
  </v-card>
</template>