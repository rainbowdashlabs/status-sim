<script setup lang="ts">
import { ref } from 'vue'
import { formatRelativeTime } from '../utils/format'
import type { ChatMessage } from '../types'

withDefaults(defineProps<{
  messages: ChatMessage[]
  isLoading?: boolean
  heightClass?: string
}>(), {
  isLoading: false,
  heightClass: 'h-[160px]',
})

const root = ref<HTMLDivElement | null>(null)
defineExpose({ root })
</script>

<template>
  <div ref="root" class="chat-log" :class="heightClass">
    <div v-if="isLoading" class="chat-empty">Chatverlauf wird geladen...</div>
    <div v-else-if="messages.length === 0" class="chat-empty">Keine Nachrichten</div>
    <div v-else>
      <div v-for="(msg, i) in messages" :key="i" class="chat-message">
        <span class="chat-sender" :class="msg.sender === 'LS' ? 'bg-info' : 'bg-danger'">{{ msg.sender }}</span>
        <span class="chat-time">{{ formatRelativeTime(msg.timestamp) }}</span>
        <span class="flex-grow break-all">{{ msg.text }}</span>
      </div>
    </div>
  </div>
</template>
