<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import axios from 'axios'
import statusSoundUrl from './assets/fns_status_1.mp3'
import { usePolling } from './composables/usePolling'
import Footer from './components/Footer.vue'
import StatusKeypad from './components/StatusKeypad.vue'
import ChatLog from './components/ChatLog.vue'

const props = defineProps<{
  name: string
  code: string
  leitstelleName: string
}>()

const activeTab = ref<'kurzstatus' | 'nachrichten'>('kurzstatus')
const hasNewMessage = ref(false)
const lastMessageCount = ref(0)

const { state, refresh } = usePolling(props.code, props.name)

const myStatus = computed(() => state.value?.connections.find(c => c.name === props.name))
const myNotice = computed(() => state.value?.notices[props.name])

const messages = computed(() => {
  const raw = state.value?.messages ?? []
  return [...raw].reverse()
})

watch(messages, (msgs) => {
  if (msgs.length > lastMessageCount.value && lastMessageCount.value > 0 && activeTab.value !== 'nachrichten') {
    hasNewMessage.value = true
  }
  lastMessageCount.value = msgs.length
})

const statusSound = new Audio(statusSoundUrl)
statusSound.volume = 0.5
const lastPressed = ref<string | null>(null)

const press = (key: string) => {
  lastPressed.value = key
  statusSound.currentTime = 0
  void statusSound.play().catch(() => {})
  if (key === '9') return
  axios.post(`/api/vehicle/${props.code}/action`, { name: props.name, action: 'status', value: key }).then(refresh)
}

watch(() => [myStatus.value?.status, myStatus.value?.special], () => {
  lastPressed.value = null
})

const sendKurzstatus = (text: string) => {
  axios.post(`/api/vehicle/${props.code}/action`, { name: props.name, action: 'kurzstatus', value: text }).then(refresh)
}

const confirmNotice = () => {
  axios.post(`/api/vehicle/${props.code}/action`, { name: props.name, action: 'confirm_notice' }).then(refresh)
}

const toggleTalkingToSF = () => {
  axios.post(`/api/vehicle/${props.code}/action`, { name: props.name, action: 'toggle_sf' }).then(refresh)
}

const openTab = (tab: 'kurzstatus' | 'nachrichten') => {
  activeTab.value = tab
  if (tab === 'nachrichten') hasNewMessage.value = false
}

const kurzstatusOptions = [
  'Lage bestä., Maßn. eing.',
  'Lage bestä., Gef-Abw. eing.',
  'Keine Feststellung, Erk. läuft',
  'Fehlalarm BMA',
  'Müco, 1 C-Rohr, EstuK',
]

onMounted(() => {
  document.title = `Status: ${props.name} - Funk Simulator`
})
</script>

<template>
  <div class="page">
    <div class="flex-1">
      <div class="flex justify-between items-center mb-2.5">
        <h1 class="section-title text-2xl m-0">Status: {{ name }}</h1>
        <button
          v-if="!myStatus?.talking_to_sf"
          @click="toggleTalkingToSF"
          class="btn btn-info p-1.5 px-3 text-sm border border-white whitespace-nowrap"
        >
          Mit SF sprechen
        </button>
        <button
          v-else
          @click="toggleTalkingToSF"
          class="btn btn-danger p-1.5 px-3 text-sm border border-white whitespace-nowrap"
        >
          Gespräch beenden
        </button>
      </div>
      <p class="text-themed-faint text-sm -mt-1 mb-4">Verbunden mit: {{ leitstelleName }}</p>

      <div v-if="myStatus?.ls_radio_channel || myStatus?.sf_radio_channel" class="flex flex-wrap gap-2 mb-4">
        <div v-if="myStatus?.ls_radio_channel" class="bg-info/20 border border-info/50 text-info px-3 py-1.5 rounded text-sm font-mono font-bold flex items-center gap-2">
          <span class="text-xs uppercase font-sans tracking-wider">LS {{ myStatus.ls_claimed_by }}:</span>
          <span>{{ myStatus.ls_radio_channel }}</span>
        </div>
        <div v-if="myStatus?.sf_radio_channel" class="bg-success/20 border border-success/50 text-success px-3 py-1.5 rounded text-sm font-mono font-bold flex items-center gap-2">
          <span class="text-xs uppercase font-sans tracking-wider">SF {{ myStatus.claimed_by }}:</span>
          <span>{{ myStatus.sf_radio_channel }}</span>
        </div>
      </div>

      <div v-if="myNotice || myStatus?.talking_to_sf" class="w-full mb-5 overflow-hidden rounded-lg">
        <div v-if="myNotice?.status === 'pending'"
             class="bg-danger text-white p-4 flex flex-col gap-3 rounded-lg animate-pulse border-2 border-white shadow-lg">
          <div class="flex justify-between items-center">
            <span class="font-bold uppercase tracking-widest text-lg">{{ myNotice.text }}</span>
            <button @click="confirmNotice" class="btn btn-success p-2 px-6 rounded-full shadow-md border border-white/30 active:scale-95">
              Kanal gewechselt
            </button>
          </div>
          <div v-if="myStatus?.radio_channel" class="bg-black/30 p-2 rounded flex items-center justify-center gap-2 border border-white/20">
            <span class="text-sm font-medium">NEUER FUNKKANAL:</span>
            <span class="text-xl font-black font-mono tracking-wider">{{ myStatus.radio_channel }}</span>
          </div>
        </div>

        <div v-else class="bg-success text-white p-4 flex justify-between items-center border-2 border-white shadow-[0_0_15px_rgba(46,125,50,0.8)]">
          <div class="flex items-center gap-2.5 font-bold uppercase tracking-widest">
            <span class="w-3 h-3 bg-white rounded-full animate-ping"></span>
            <span>Spricht mit Staffelführer</span>
          </div>
        </div>
      </div>

      <StatusKeypad :status="myStatus?.status" :special="myStatus?.special" :last-pressed="lastPressed" @press="press" />

      <div class="flex border-b-2 border-themed mb-5">
        <button
          @click="openTab('kurzstatus')"
          class="flex-1 p-3 text-sm font-bold uppercase transition-all border-b-3"
          :class="activeTab === 'kurzstatus' ? 'text-primary border-primary' : 'text-themed-faint border-transparent'"
        >
          Kurzlagemeldung
        </button>
        <button
          @click="openTab('nachrichten')"
          class="flex-1 p-3 text-sm font-bold uppercase transition-all border-b-3 relative"
          :class="[
            activeTab === 'nachrichten' ? 'text-primary border-primary' : 'text-themed-faint border-transparent',
            hasNewMessage && activeTab !== 'nachrichten' ? 'animate-tab-flash' : '',
          ]"
        >
          Nachrichten
          <span v-if="hasNewMessage" class="absolute top-2 right-2 w-2 h-2 bg-danger rounded-full"></span>
        </button>
      </div>

      <div v-if="activeTab === 'kurzstatus'">
        <h3 class="section-title text-lg mb-2">Kurzlagemeldung</h3>
        <div class="border border-themed rounded-lg overflow-hidden">
          <div
            v-for="opt in kurzstatusOptions" :key="opt"
            @click="sendKurzstatus(opt)"
            class="p-3 px-4 bg-themed-alt border-b border-themed cursor-pointer flex justify-between items-center last:border-0 hover:brightness-110"
            :class="{ 'bg-info/20 text-info font-bold': myStatus?.kurzstatus === opt }"
          >
            {{ opt }}
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'nachrichten'">
        <h3 class="section-title text-lg mb-2">Nachrichten</h3>
        <ChatLog :messages="messages" height-class="h-[200px]" />
      </div>
    </div>
    <Footer />
  </div>
</template>

<style scoped>
@keyframes tab-flash {
  from { background-color: transparent; }
  to { background-color: var(--danger-color); color: white; }
}
.animate-tab-flash {
  animation: tab-flash 1s infinite alternate;
}
</style>
