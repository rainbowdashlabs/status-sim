<script setup lang="ts">
import { ref } from 'vue';

type ChatMessage = {
  sender: string;
  text: string;
  time: string;
  timestamp?: number;
};

const props = withDefaults(defineProps<{
  messages: ChatMessage[];
  isLoading?: boolean;
  heightClass?: string;
  emptyText?: string;
  loadingText?: string;
}>(), {
  isLoading: false,
  heightClass: 'h-[160px]',
  emptyText: 'Keine Nachrichten',
  loadingText: 'Chatverlauf wird geladen...'
});

const root = ref<HTMLDivElement | null>(null);

defineExpose({ root });
</script>

<template>
  <div ref="root" class="bg-black border border-gray-800 rounded-lg overflow-y-auto flex flex-col" :class="heightClass">
    <div v-if="isLoading" class="flex-1 flex items-center justify-center text-gray-600 italic">{{ loadingText }}</div>
    <div v-else-if="messages.length === 0" class="flex-1 flex items-center justify-center text-gray-600 italic">{{ emptyText }}</div>
    <div v-else>
      <div v-for="(msg, i) in messages" :key="i" class="p-2 px-3 border-b border-gray-900 flex gap-2.5 items-start last:border-0">
        <span class="p-0.5 px-1.5 rounded text-[0.75rem] font-bold text-white uppercase min-w-[25px] text-center mt-0.5"
              :class="msg.sender === 'LS' ? 'bg-info' : 'bg-danger'">
          {{ msg.sender }}
        </span>
        <span class="text-gray-500 text-[0.8rem] whitespace-nowrap min-w-[65px] flex items-center mt-0.5">{{ msg.time }}</span>
        <span class="flex-grow break-all">{{ msg.text }}</span>
      </div>
    </div>
  </div>
</template>