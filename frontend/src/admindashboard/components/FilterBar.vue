<script setup>
import { ref, watch, computed } from 'vue';

const emit = defineEmits(['retrieve-data']);

const steamId = ref('');
const eventTypes = ref(['login', 'logout']);
const allEventTypes = [
  { label: 'Login', value: 'login' },
  { label: 'Logout', value: 'logout' },
  { label: 'Request Recommendation', value: 'recommendation_request' },
  { label: 'View Past Recommendation', value: 'view_past_recommendation' },
  { label: 'View Store', value: 'view_store' },
  { label: 'Like Recommendation', value: 'like_recommendation' },
  { label: 'Dislike Recommendation', value: 'dislike_recommendation' },
  { label: 'Remove Preference', value: 'remove_preference' }
];

const chunkedEventTypes = computed(() => {
  const chunkSize = 4;
  const chunks = [];
  for (let i = 0; i < allEventTypes.length; i += chunkSize) {
    chunks.push(allEventTypes.slice(i, i + chunkSize));
  }
  return chunks;
});

const timeRangeOptions = [
  { label: 'Past 3 days', value: '3d' },
  { label: 'Past week', value: '1w' },
  { label: 'Past month', value: '1m' },
  { label: 'Past 3 months', value: '3m' }
];
const timeRange = ref('3d');
const from = ref(null);
const to = ref(null);

const fromMenu = ref(false);
const toMenu = ref(false);

const fromDisplay = computed(() => from.value ? new Date(from.value).toLocaleDateString() : '');
const toDisplay = computed(() => to.value ? new Date(to.value).toLocaleDateString() : '');

function setRange(range) {
  const now = new Date();
  let fromDate;
  switch (range) {
    case '3d':
      fromDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 2);
      break;
    case '1w':
      fromDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 6);
      break;
    case '1m':
      fromDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 29);
      break;
    case '3m':
      fromDate = new Date(now.getFullYear(), now.getMonth(), now.getDate() - 89);
      break;
    default:
      return;
  }
  from.value = fromDate;
  to.value = now;
}

watch(timeRange, (val) => {
  if (val !== 'custom') setRange(val);
});

function onRetrieve() {
  if (!from.value || !to.value) return;
  // Convert to UTC UNIX timestamps (seconds)
  const fromTs = Math.floor(new Date(from.value).getTime() / 1000);
  const toTs = Math.floor(new Date(to.value).getTime() / 1000);
  emit('retrieve-data', {
    steamId: steamId.value || undefined,
    eventTypes: [...eventTypes.value],
    from: fromTs,
    to: toTs
  });
}
</script>

<template>
  <v-card class="mb-6">
    <v-card-title>Filters</v-card-title>
    <v-card-text>
      <v-row>
        <v-col cols="12" md="6">
          <v-row>
            <v-col
              v-for="(chunk, idx) in chunkedEventTypes"
              :key="idx"
              cols="12"
              sm="14"
              md="14"
              lg="6"
            >
              <v-checkbox
                v-for="et in chunk"
                :key="et.value"
                v-model="eventTypes"
                :label="et.label"
                :value="et.value"
                hide-details
                density="compact"
                class="mr-2"
              />
            </v-col>
          </v-row>
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12" md="6">
          <v-text-field v-model="steamId" label="User Steam ID (optional)" />
        </v-col>
      </v-row>
      <v-row>
        <v-col cols="12" md="3">
          <v-select
            v-model="timeRange"
            :items="timeRangeOptions"
            item-title="label"
            item-value="value"
            label="Time Range"
          />
        </v-col>
        <v-col cols="12" md="3">
          <v-menu
            v-model="fromMenu"
            :close-on-content-click="false"
            transition="scale-transition"
            offset-y
          >
            <template v-slot:activator="{ props }">
              <v-text-field
                :model-value="fromDisplay"
                label="From"
                readonly
                v-bind="props"
              />
            </template>
            <v-date-picker v-model="from" @update:modelValue="fromMenu = false" />
          </v-menu>
          <v-menu
            v-model="toMenu"
            :close-on-content-click="false"
            transition="scale-transition"
            offset-y
          >
            <template v-slot:activator="{ props }">
              <v-text-field
                :model-value="toDisplay"
                label="To"
                readonly
                v-bind="props"
              />
            </template>
            <v-date-picker v-model="to" @update:modelValue="toMenu = false" />
          </v-menu>
        </v-col>
      </v-row>
      <v-btn class="mt-6" color="primary" @click="onRetrieve" :disabled="!from || !to">Retrieve Data</v-btn>
    </v-card-text>
  </v-card>
</template>