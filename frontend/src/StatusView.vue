<script setup lang="ts">
import {computed, onMounted, ref, watch} from 'vue';
import axios from 'axios';
import type {StatusUpdate} from './composables/useWebSocket';
import {useWebSocket} from './composables/useWebSocket';
import {backendBaseUrl} from './config/backend';
import Footer from './components/Footer.vue';
import StatusKeypad from './components/StatusKeypad.vue';
import ChatLog from './components/ChatLog.vue';

const props = defineProps<{
  name: string;
  code: string;
  leitstelleName: string;
}>();

const messages = ref<{ sender: string; text: string; time: string; timestamp: number }[]>([]);
const activeTab = ref<'kurzstatus' | 'nachrichten'>('kurzstatus');
const hasNewMessage = ref(false);
const statusUpdate = ref<StatusUpdate | null>(null);
const isLoadingMessages = ref(false);

const formatTime = (timestamp: number) => {
  const nowSeconds = Date.now() / 1000;
  const diffSeconds = Math.max(0, Math.round(nowSeconds - timestamp));
  const rtf = new Intl.RelativeTimeFormat('de', {numeric: 'auto'});
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
  isLoadingMessages.value = true;
  try {
    const response = await axios.get(`/api/leitstelle/${props.code}/chat_history`, {
      params: {
        target_name: props.name
      }
    });
    const history = response.data?.messages ?? [];
    messages.value = history
        .map((entry: { sender: string; text: string; timestamp: number }) => ({
          sender: entry.sender,
          text: entry.text,
          timestamp: entry.timestamp,
          time: formatTime(entry.timestamp)
        }))
        .reverse();
  } finally {
    isLoadingMessages.value = false;
  }
};

const statusSound = new Audio(`/assets/fns_status_1.mp3`);
statusSound.volume = 0.5;

const onMessage = (data: any) => {
  if (data.connections) {
    statusUpdate.value = data;
  } else if (data.type === 'text' || typeof data.message === 'string') {
    const text = data.message || data;
    const parts = text.split(': ');
    const sender = parts[0];
    const msgText = parts.slice(1).join(': ');
    const timestamp = Date.now() / 1000;
    messages.value.unshift({
      sender: sender === 'LS' ? 'LS' : (sender === 'SF' ? 'SF' : '??'),
      text: msgText,
      timestamp,
      time: formatTime(timestamp)
    });
    if (activeTab.value !== 'nachrichten') {
      hasNewMessage.value = true;
    }
  }
};

const {send} = useWebSocket(`/ws/${props.code}?name=${encodeURIComponent(props.name)}`, onMessage);

const myStatus = computed(() => statusUpdate.value?.connections.find(c => c.name === props.name));
const myNotice = computed(() => statusUpdate.value?.notices[props.name]);
const lastPressed = ref<string | null>(null);

const press = (key: string) => {
  lastPressed.value = key;
  statusSound.currentTime = 0;
  void statusSound.play().catch((e) => {
    console.warn('Status-Sound konnte nicht abgespielt werden.', e);
  });
  if (key === '9') return;
  send({type: 'status', value: key});
};

watch(() => [myStatus.value?.status, myStatus.value?.special], () => {
  lastPressed.value = null;
});

const sendKurzstatus = (text: string) => {
  send({type: 'kurzstatus', value: text});
};

const confirmNotice = () => {
  send({type: 'confirm_notice'});
};

const toggleTalkingToSF = () => {
  send({type: 'toggle_talking_to_sf'});
};

const openTab = (tab: 'kurzstatus' | 'nachrichten') => {
  activeTab.value = tab;
  if (tab === 'nachrichten') {
    hasNewMessage.value = false;
  }
};

const kurzstatusOptions = [
  'Lage bestä., Maßn. eing.',
  'Lage bestä., Gef-Abw. eing.',
  'Keine Feststellung, Erk. läuft',
  'Fehlalarm BMA',
  'Müco, 1 C-Rohr, EstuK'
];

onMounted(() => {
  void loadChatHistory();
});
</script>

<template>
  <div class="max-w-[1200px] min-w-[320px] mx-auto p-5 flex flex-col min-h-screen">
    <div class="flex-1">
      <div class="flex justify-between items-center mb-2.5">
        <h1 class="text-primary uppercase tracking-widest text-2xl font-bold m-0">Status: {{ name }}</h1>
        <button
            v-if="!myStatus?.talking_to_sf"
            @click="toggleTalkingToSF"
            class="p-1.5 px-3 text-[0.85rem] font-bold rounded border border-white whitespace-nowrap transition-all bg-info"
        >
          Mit SF sprechen
        </button>
        <button
            v-else-if="myStatus?.talking_to_sf"
            @click="toggleTalkingToSF"
            class="p-1.5 px-3 text-[0.85rem] font-bold rounded border border-white whitespace-nowrap transition-all bg-danger"
        >
          Gespräch beenden
        </button>
      </div>
      <p class="text-gray-500 text-[0.9rem] -mt-1 mb-4">Verbunden mit: {{ leitstelleName }}</p>

      <div v-if="myNotice || myStatus?.talking_to_sf" class="w-full mb-5 overflow-hidden rounded-lg">
        <div v-if="myNotice?.status === 'pending'"
             class="bg-danger text-white p-4 flex justify-between items-center animate-pulse">
          <span class="font-bold uppercase tracking-widest">{{ myNotice.text }}</span>
          <button @click="confirmNotice" class="bg-success text-white p-2 px-4 rounded font-bold hover:brightness-110">
            Kanal gewechselt
          </button>
        </div>

        <div v-else
             class="bg-success text-white p-4 flex justify-between items-center border-2 border-white shadow-[0_0_15px_rgba(46,125,50,0.8)]">
          <div class="flex items-center gap-2.5 font-bold uppercase tracking-widest">
            <span class="w-3 h-3 bg-white rounded-full animate-ping"></span>
            <span>Spricht mit Staffelführer</span>
          </div>
        </div>
      </div>

      <StatusKeypad
          :status="myStatus?.status"
          :special="myStatus?.special"
          :last-pressed="lastPressed"
          @press="press"
      />

      <div class="flex border-b-2 border-gray-800 mb-5">
        <button
            @click="openTab('kurzstatus')"
            class="flex-1 p-3 text-sm font-bold uppercase transition-all border-b-3"
            :class="activeTab === 'kurzstatus' ? 'text-primary border-primary' : 'text-gray-500 border-transparent'"
        >
          Kurzlagemeldung
        </button>
        <button
            @click="openTab('nachrichten')"
            class="flex-1 p-3 text-sm font-bold uppercase transition-all border-b-3 relative"
            :class="[
            activeTab === 'nachrichten' ? 'text-primary border-primary' : 'text-gray-500 border-transparent',
            hasNewMessage && activeTab !== 'nachrichten' ? 'animate-tab-flash' : ''
          ]"
        >
          Nachrichten
          <span v-if="hasNewMessage" class="absolute top-2 right-2 w-2 h-2 bg-danger rounded-full"></span>
        </button>
      </div>

      <div v-if="activeTab === 'kurzstatus'">
        <h3 class="text-primary text-lg mb-2 font-bold uppercase">Kurzlagemeldung</h3>
        <div class="border border-gray-800 rounded-lg overflow-hidden">
          <div
              v-for="opt in kurzstatusOptions" :key="opt"
              @click="sendKurzstatus(opt)"
              class="p-3 px-4 bg-[#252525] border-b border-gray-800 cursor-pointer flex justify-between items-center last:border-0 hover:bg-[#333]"
              :class="{ 'bg-info/20 text-info font-bold': myStatus?.kurzstatus === opt }"
          >
            {{ opt }}
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'nachrichten'">
        <h3 class="text-primary text-lg mb-2 font-bold uppercase">Nachrichten</h3>
        <ChatLog
            :messages="messages"
            :is-loading="isLoadingMessages"
            height-class="h-[200px]"
        />
      </div>
    </div>
    <Footer/>
  </div>
</template>

<style scoped>
@keyframes tab-flash {
  from {
    background-color: transparent;
  }
  to {
    background-color: var(--danger-color);
    color: white;
  }
}

.animate-tab-flash {
  animation: tab-flash 1s infinite alternate;
}
</style>
