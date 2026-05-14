<script setup lang="ts">
import { ref, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'
import ChatLog from './ChatLog.vue'
import type { ChatMessage } from '../types'

const props = defineProps<{
  code: string
  targetName: string
  note?: string
  notesEnabled?: boolean
  senderLabel?: string
}>()

const message = ref('')
const localNote = ref(props.note ?? '')
const noteField = ref<HTMLTextAreaElement | null>(null)
const chatContainer = ref<InstanceType<typeof ChatLog> | null>(null)
const chatLog = ref<ChatMessage[]>([])
const isLoading = ref(false)
let pollTimer: number | null = null

const loadChatHistory = async () => {
  try {
    const { data } = await axios.get(`/api/leitstelle/${props.code}/chat_history`, {
      params: { target_name: props.targetName },
    })
    chatLog.value = data?.messages ?? []
    await nextTick()
    const root = (chatContainer.value as any)?.root as HTMLDivElement | undefined
    if (root) root.scrollTop = root.scrollHeight
  } catch { /* ignore */ }
}

const resizeNote = async () => {
  if (!props.notesEnabled) return
  await nextTick()
  if (noteField.value) {
    noteField.value.style.height = 'auto'
    noteField.value.style.height = `${noteField.value.scrollHeight}px`
  }
}

watch(() => props.note, (v) => {
  localNote.value = v ?? ''
  void resizeNote()
})

onMounted(() => {
  void resizeNote()
  isLoading.value = true
  loadChatHistory().finally(() => { isLoading.value = false })
  pollTimer = window.setInterval(loadChatHistory, 3000)
})

onBeforeUnmount(() => {
  if (pollTimer) clearInterval(pollTimer)
})

const sendMessage = async () => {
  if (!message.value.trim()) return
  await axios.post(`/api/leitstelle/${props.code}/message`, {
    message: message.value,
    target_name: props.targetName,
  })
  message.value = ''
  await loadChatHistory()
}

const updateNote = async () => {
  if (!props.notesEnabled) return
  await axios.post(`/api/leitstelle/${props.code}/update_note`, {
    target_name: props.targetName,
    note: localNote.value,
  })
}
</script>

<template>
  <div>
    <ChatLog ref="chatContainer" :messages="chatLog" :is-loading="isLoading" height-class="h-[160px]" class="mb-2" />
    <form @submit.prevent="sendMessage" class="flex gap-1.5 items-center">
      <input v-model="message" type="text" placeholder="Nachricht..." class="input-sm flex-1">
      <button type="submit" class="btn btn-secondary p-1.5 px-2.5 text-sm">Senden</button>
    </form>
    <div v-if="notesEnabled" class="mt-2.5">
      <label class="label text-xs">Notizen:</label>
      <textarea
        ref="noteField"
        v-model="localNote"
        @blur="updateNote"
        class="w-full min-h-[60px] bg-themed-overlay text-themed border border-themed rounded p-2 text-sm outline-none focus:border-primary resize-none overflow-hidden"
      />
    </div>
  </div>
</template>
