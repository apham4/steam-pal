<script setup>
const props = defineProps({
  data: {
    type: [Object, Array],
    required: true
  },
  raw: {
    type: Boolean,
    default: false
  }
});

function exportCSV() {
  if (!props.data) return;
  let csv = '';
  if (props.raw) {
    // Raw data export (array of objects)
    if (!Array.isArray(props.data) || !props.data.length) return;
    const keys = Object.keys(props.data[0]);
    csv += keys.join(',') + '\n';
    props.data.forEach(row => {
      csv += keys.map(k => JSON.stringify(row[k] ?? '')).join(',') + '\n';
    });
  } else {
    // Chart data export
    if (!props.data.labels || !props.data.datasets) return;
    csv = 'Label';
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
  }
  const blob = new Blob([csv], { type: 'text/csv' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = 'events.csv';
  link.click();
  URL.revokeObjectURL(link.href);
}
</script>

<template>
  <v-btn
    color="secondary"
    @click="exportCSV"
    :disabled="!props.data"
    >
    Export to CSV
  </v-btn>
</template>