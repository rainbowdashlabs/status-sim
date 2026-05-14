<script setup lang="ts">
import { ref, computed, onMounted, provide } from 'vue'
import axios from 'axios'
import { usePolling, REFRESH_KEY } from './composables/usePolling'
import Footer from './components/Footer.vue'
import CodeCopyable from './components/CodeCopyable.vue'
import VehicleItem from './components/VehicleItem.vue'

const props = defineProps<{
  adminCode: string
  leitstelleName: string
  vehicleCode: string
  staffelfuehrerCode: string
}>()

const lsName = ref(
  new URLSearchParams(window.location.search).get('name')
  || localStorage.getItem(`ls_name_${props.adminCode}`)
  || 'Disponent 1'
)
const radioChannel = ref(
  new URLSearchParams(window.location.search).get('channel')
  || localStorage.getItem(`ls_channel_${props.adminCode}`)
  || ''
)

const { state, isConnected, refresh } = usePolling(props.adminCode, lsName.value)
provide(REFRESH_KEY, refresh)

const allVehicles = computed(() => {
  const notices = state.value?.notices ?? {}
  return (state.value?.connections || []).map((car) => ({
    ...car,
    talking_to_sf: car.talking_to_sf || notices[car.name]?.status === 'confirmed',
  })).sort((a, b) => a.last_activity - b.last_activity)
})

const claimed = computed(() => allVehicles.value.filter(c => c.ls_claimed_by === lsName.value))
const unclaimed = computed(() => allVehicles.value.filter(c => c.ls_claimed_by !== lsName.value))

const combineSprechwunsch = ref(localStorage.getItem(`ls_combine_${props.adminCode}`) !== 'false')
const toggleCombine = () => {
  combineSprechwunsch.value = !combineSprechwunsch.value
  localStorage.setItem(`ls_combine_${props.adminCode}`, String(combineSprechwunsch.value))
}

const sortByWait = (a: any, b: any) => {
  const tA = (a.special === '0' ? a.last_blitz_update : a.last_sprechwunsch_update) ?? 0
  const tB = (b.special === '0' ? b.last_blitz_update : b.last_sprechwunsch_update) ?? 0
  return tA - tB
}

const blitzVehicles = computed(() => claimed.value.filter(c => c.special === '0').sort(sortByWait))
const sprechwunschVehicles = computed(() => claimed.value.filter(c => c.special === '5').sort(sortByWait))
const combinedVehicles = computed(() => claimed.value.filter(c => c.special === '0' || c.special === '5').sort(sortByWait))
const staffelfuehrerVehicles = computed(() => claimed.value.filter(c => c.talking_to_sf && !c.special))
const normalVehicles = computed(() => claimed.value.filter(c => !c.special && !c.talking_to_sf))
const lsActionVehicles = computed(() => normalVehicles.value.filter(c => c.next_todo === 'LS'))
const otherVehicles = computed(() => normalVehicles.value.filter(c => c.next_todo !== 'LS'))

const message = ref('')
const sendMessage = async () => {
  if (!message.value) return
  await axios.post(`/api/leitstelle/${props.adminCode}/message`, { message: message.value })
  message.value = ''
  refresh()
}

const updateUrlParams = () => {
  const url = new URL(window.location.href)
  url.searchParams.set('name', lsName.value)
  if (radioChannel.value) {
    url.searchParams.set('channel', radioChannel.value)
  } else {
    url.searchParams.delete('channel')
  }
  window.history.replaceState({}, '', url.toString())
}

const updateLsName = () => {
  localStorage.setItem(`ls_name_${props.adminCode}`, lsName.value)
  updateUrlParams()
  window.location.reload()
}

const updateRadioChannel = () => {
  localStorage.setItem(`ls_channel_${props.adminCode}`, radioChannel.value)
  updateUrlParams()
  axios.post(`/api/leitstelle/${props.adminCode}/channel`, {
    name: lsName.value,
    channel: radioChannel.value,
  }).then(refresh)
}

onMounted(() => {
  document.title = `Leitstelle: ${props.leitstelleName} - Funk Simulator`
  if (radioChannel.value) {
    axios.post(`/api/leitstelle/${props.adminCode}/channel`, {
      name: lsName.value,
      channel: radioChannel.value,
    })
  }
})
</script>

<template>
  <div class="page">
    <div class="flex-1">
      <div class="card p-4 mb-5 flex flex-wrap justify-between items-center gap-5">
        <div class="flex-1 min-w-[250px]">
          <h1 class="section-title text-2xl m-0">Leitstelle: {{ leitstelleName }}</h1>
          <p class="mt-1 text-themed-faint text-sm">Admin-Code: <span class="font-mono font-bold text-themed-muted">{{ adminCode }}</span></p>
        </div>
        <div class="flex flex-col gap-2 items-end">
          <div class="flex gap-4">
            <CodeCopyable :code="vehicleCode" label="Fahrzeug-Code" />
            <CodeCopyable :code="staffelfuehrerCode" label="Staffelführer-Code" success-class="text-success" />
          </div>
          <div class="flex gap-2 items-center">
            <input v-model="lsName" class="input-sm w-40" placeholder="Disponentenname">
            <button @click="updateLsName" class="btn btn-primary p-1 px-3 text-sm">Speichern</button>
          </div>
          <div class="flex gap-2 items-center">
            <input v-model="radioChannel" class="input-sm w-40" placeholder="Funkkanal (z.B. 501)">
            <button @click="updateRadioChannel" class="btn btn-info p-1 px-3 text-sm">Kanal setzen</button>
          </div>
        </div>
      </div>

      <div class="card p-5 mb-5">
        <h2 class="section-title text-lg mb-3">Nachricht an alle</h2>
        <form @submit.prevent="sendMessage" class="flex gap-2">
          <input v-model="message" type="text" placeholder="Nachricht eingeben" required class="input flex-[7]">
          <button type="submit" class="btn btn-secondary btn-press p-3 flex-[3]">Senden</button>
        </form>
        <div v-if="!isConnected" class="disconnected">Verbindung unterbrochen...</div>
      </div>

      <div v-if="unclaimed.length > 0" class="card p-3 mb-5 flex items-center gap-3 border-l-4 border-l-warning">
        <span class="text-warning font-bold text-sm uppercase tracking-wider">{{ unclaimed.length }} nicht übernommen</span>
        <span class="text-themed-muted text-sm">Fahrzeuge ohne Zuordnung warten auf Übernahme</span>
      </div>

      <div class="flex flex-col gap-5">
        <template v-if="combineSprechwunsch">
          <div v-if="combinedVehicles.length > 0" class="vehicle-group border-t-4 border-t-accent">
            <div class="flex justify-between items-center vehicle-group-title text-accent">
              <span>Sprechwünsche</span>
              <button @click="toggleCombine" class="btn text-xs text-gray-400 p-0.5 px-2 border border-gray-700 font-normal normal-case tracking-normal">Aufteilen</button>
            </div>
            <VehicleItem v-for="car in combinedVehicles" :key="car.name" :car="car" :admin-code="adminCode" :ls-name="lsName" />
          </div>
        </template>
        <template v-else>
          <div v-if="blitzVehicles.length > 0" class="vehicle-group border-t-4 border-t-warning">
            <div class="flex justify-between items-center vehicle-group-title text-warning">
              <span>0 Blitz</span>
              <button @click="toggleCombine" class="btn text-xs text-gray-400 p-0.5 px-2 border border-gray-700 font-normal normal-case tracking-normal">Zusammenfassen</button>
            </div>
            <VehicleItem v-for="car in blitzVehicles" :key="car.name" :car="car" :admin-code="adminCode" :ls-name="lsName" />
          </div>
          <div v-if="sprechwunschVehicles.length > 0" class="vehicle-group border-t-4 border-t-accent">
            <div class="flex justify-between items-center vehicle-group-title text-accent">
              <span>5 Sprechwunsch</span>
              <button v-if="blitzVehicles.length === 0" @click="toggleCombine" class="btn text-xs text-gray-400 p-0.5 px-2 border border-gray-700 font-normal normal-case tracking-normal">Zusammenfassen</button>
            </div>
            <VehicleItem v-for="car in sprechwunschVehicles" :key="car.name" :car="car" :admin-code="adminCode" :ls-name="lsName" />
          </div>
        </template>

        <div v-if="staffelfuehrerVehicles.length > 0" class="vehicle-group border-t-4 border-t-danger">
          <h3 class="vehicle-group-title text-danger">Gespräch mit Staffelführer</h3>
          <VehicleItem v-for="car in staffelfuehrerVehicles" :key="car.name" :car="car" :admin-code="adminCode" :ls-name="lsName" />
        </div>

        <div v-if="lsActionVehicles.length > 0" class="vehicle-group border-t-4 border-t-primary">
          <h3 class="vehicle-group-title text-primary">Aktion erforderlich (LS)</h3>
          <VehicleItem v-for="car in lsActionVehicles" :key="car.name" :car="car" :admin-code="adminCode" :ls-name="lsName" />
        </div>

        <div class="vehicle-group">
          <h3 class="vehicle-group-title text-primary">Alle Fahrzeuge</h3>
          <div v-if="otherVehicles.length === 0 && claimed.length === 0" class="text-themed-faint italic">Keine Fahrzeuge übernommen.</div>
          <div v-else-if="otherVehicles.length === 0" class="text-themed-faint italic">Keine weiteren Fahrzeuge.</div>
          <VehicleItem v-for="car in otherVehicles" :key="car.name" :car="car" :admin-code="adminCode" :ls-name="lsName" />
        </div>

        <div v-if="unclaimed.length > 0" class="vehicle-group border-t-4 border-t-warning opacity-70">
          <h3 class="vehicle-group-title text-warning">Nicht übernommen</h3>
          <VehicleItem v-for="car in unclaimed" :key="car.name" :car="car" :admin-code="adminCode" :ls-name="lsName" />
        </div>
      </div>
    </div>
    <Footer />
  </div>
</template>
