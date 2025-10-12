<script setup>
const props = defineProps({
  data: {
    type: Object,
    required: true
  }
});

function exportCSV() {
  // Simple CSV export for chart.js data
  if (!props.data || !props.data.labels || !props.data.datasets) return;
  let csv = 'Label';
  props.data.datasets.forEach(ds => {
    csv += ',' + ds.label;
  });
  csv += '\n';
  props.data.labels.forEach((label, i) => {
    let row = label;
    props.data.datasets.forEach(ds => {
      row += ',' + (ds.data[i] ?? '');
    });
    csv += row + '\n';
  });
  const blob = new Blob([csv], { type: 'text/csv' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = 'stats.csv';
  link.click();
  URL.revokeObjectURL(link.href);
}
</script>

<style scoped>
.v-btn {
  margin-top: 16px;
}
</style>

<template>
  <v-btn color="secondary" @click="exportCSV">
    Export to CSV
  </v-btn>
</template>