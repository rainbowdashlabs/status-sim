<script setup lang="ts">
import { ref, watch, nextTick, onMounted } from 'vue';
import axios from 'axios';
import { useWebSocket } from '../composables/useWebSocket';
import ChatLog from './ChatLog.vue';

const props = defineProps<{
  code: string;
  targetName: string;
  note?: string;
  notesEnabled?: boolean;
  senderLabel?: string;
}>();

const message = ref('');
const localNote = ref(props.note ?? '');
const noteField = ref<HTMLTextAreaElement | null>(null);
const chatContainer = ref<InstanceType<typeof ChatLog> | null>(null);
const chatLog = ref<{ sender: string; text: string; timestamp: number; time: string }[]>([]);
const isLoading = ref(false);

const formatTime = (timestamp: number) => {
  const nowSeconds = Date.now() / 1000;
  const diffSeconds = Math.max(0, Math.round(nowSeconds - timestamp));
  const rtf = new Intl.RelativeTimeFormat('de', { numeric: 'auto' });
  if (diffSeconds < 60) {
    return rtf.format(-diffSeconds, 'second');
  }
  if (diffSeconds < 3600) {
    return rtf.format(-Math.round(diffSeconds / 60), 'minute');
  }
  if (diffSeconds < 86400) {
    return rtf.format(-Math.round(diffSeconds / 3600), 'hour');
  }
  return rtf.format(-Math.round(diffSeconds / 86400), 'day');
};

const loadChatHistory = async () => {
  isLoading.value = true;
  try {
    const response = await axios.get(`/api/leitstelle/${props.code}/chat_history`, {
      params: {
        target_name: props.targetName
      }
    });
    const history = response.data?.messages ?? [];
    chatLog.value = history
      .map((entry: { sender: string; text: string; timestamp: number }) => ({
        ...entry,
        time: formatTime(entry.timestamp)
      }));
    await nextTick();
    const root = (chatContainer.value as any)?.root as HTMLDivElement | undefined;
    if (root) {
      root.scrollTop = root.scrollHeight;
    }
  } finally {
    isLoading.value = false;
  }
};

const appendIncomingMessage = async (text: string) => {
  const parts = text.split(': ');
  const sender = parts[0];
  const msgText = parts.slice(1).join(': ');
  const timestamp = Date.now() / 1000;
  chatLog.value.push({
    sender: sender === 'LS' ? 'LS' : (sender === 'SF' ? 'SF' : '??'),
    text: msgText,
    timestamp,
    time: formatTime(timestamp)
  });
  await nextTick();
  const root = (chatContainer.value as any)?.root as HTMLDivElement | undefined;
  if (root) {
    root.scrollTop = root.scrollHeight;
  }
};

const resizeNote = async () => {
  if (!props.notesEnabled) {
    return;
  }
  await nextTick();
  if (noteField.value) {
    noteField.value.style.height = 'auto';
    noteField.value.style.height = `${noteField.value.scrollHeight}px`;
  }
};

watch(() => props.note, (newNote) => {
  if (props.notesEnabled) {
    localNote.value = newNote ?? '';
    void resizeNote();
  }
});

watch(localNote, () => {
  if (props.notesEnabled) {
    void resizeNote();
  }
});

watch(() => props.notesEnabled, (enabled) => {
  if (enabled) {
    void resizeNote();
  }
});

watch(noteField, (field) => {
  if (field && props.notesEnabled) {
    void resizeNote();
  }
});

watch(() => [props.code, props.targetName], () => {
  void loadChatHistory();
});

const wsName = props.senderLabel ?? 'Leitstelle';
useWebSocket(`/ws/${props.code}?name=${encodeURIComponent(wsName)}`, (data: any) => {
  if (data.connections) {
    return;
  }
  if (data.type === 'text' || typeof data.message === 'string') {
    appendIncomingMessage(data.message || data);
  }
});

onMounted(() => {
  void resizeNote();
  void loadChatHistory();
});

const sendMessage = async () => {
  if (!message.value.trim()) {
    return;
  }
  await axios.post(`/api/leitstelle/${props.code}/message`, {
    message: message.value,
    target_name: props.targetName
  });
  message.value = '';
};

const updateNote = async () => {
  if (!props.notesEnabled) {
    return;
  }
  await axios.post(`/api/leitstelle/${props.code}/update_note`, {
    target_name: props.targetName,
    note: localNote.value
  });
};
</script>

<template>
  <div>
    <ChatLog
      ref="chatContainer"
      :messages="chatLog"
      :is-loading="isLoading"
      height-class="h-[160px]"
      class="mb-2"
    />
    <form @submit.prevent="sendMessage" class="flex gap-1.5 items-center flex-1 min-w-[200px]">
      <input
        v-model="message"
        type="text"
        placeholder="Nachricht..."
        class="p-1.5 px-2.5 text-[0.85rem] border border-gray-700 bg-gray-900 text-white rounded w-full outline-none focus:border-primary"
      >
      <button type="submit" class="p-1.5 px-2.5 text-[0.85rem] bg-secondary text-white rounded font-bold hover:brightness-110">Senden</button>
    </form>

    <div v-if="notesEnabled" class="mt-2.5">
      <label class="block text-[0.75rem] text-gray-400 mb-1">Notizen:</label>
      <textarea
        ref="noteField"
        v-model="localNote"
        @blur="updateNote"
        @input="resizeNote"
        class="w-full min-h-[60px] bg-black text-gray-200 border border-gray-700 rounded p-2 text-[0.85rem] outline-none focus:border-primary resize-none overflow-hidden"
      ></textarea>
    </div>
  </div>
</template>