<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';

const props = defineProps<{
  timestamp: number | null;
  active: boolean;
}>();

const now = ref(Date.now() / 1000);
let interval: number | null = null;

onMounted(() => {
  interval = window.setInterval(() => {
    now.value = Date.now() / 1000;
  }, 1000);
});

onBeforeUnmount(() => {
  if (interval) clearInterval(interval);
});

const diff = computed(() => {
  if (!props.timestamp) return 0;
  return Math.floor(now.value - props.timestamp);
});

const formattedTime = computed(() => {
  const d = diff.value;
  const minutes = Math.floor(d / 60);
  const seconds = d % 60;
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
});

const timerClass = computed(() => {
  if (!props.active) return 'text-gray-500';
  if (diff.value < 60) return 'text-success';
  if (diff.value < 180) return 'text-warning';
  if (diff.value < 300) return 'text-accent';
  return 'text-danger';
});
</script>

<template>
  <span class="font-mono text-[0.8rem]" :class="timerClass">
    {{ formattedTime }}
  </span>
</template>
