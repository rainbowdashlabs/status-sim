<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  status: string;
}>();

const statusClass = computed(() => {
  switch (props.status) {
    case '1': return 'bg-info border-l-info shadow-[0_0_10px_var(--info-color)]';
    case '2': return 'bg-success border-l-success shadow-[0_0_10px_var(--success-color)]';
    case '3': return 'bg-warning border-l-warning text-black shadow-[0_0_10px_var(--warning-color)]';
    case '4':
    case '6': return 'bg-danger border-l-danger shadow-[0_0_10px_var(--danger-color)]';
    default: return 'bg-secondary border-l-gray-600';
  }
});
</script>

<template>
  <span
    class="status-badge size-10 rounded-lg font-extrabold text-white uppercase text-lg flex items-center justify-center"
    :class="statusClass"
  >
    {{ status }}
  </span>
</template>