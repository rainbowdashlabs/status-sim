<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import axios from 'axios'
import { usePolling } from './composables/usePolling'
import Footer from './components/Footer.vue'
import Timer from './components/Timer.vue'
import VehicleChatPanel from './components/VehicleChatPanel.vue'
import StatusBadge from './components/StatusBadge.vue'
import ScenarioChecklist from './components/ScenarioChecklist.vue'

const props = defineProps<{
  name: string
  sfCode: string
}>()

const sfName = ref(
  new URLSearchParams(window.location.search).get('name')
  || localStorage.getItem(`sf_name_${props.sfCode}`)
  || props.name
)
const radioChannel = ref(
  new URLSearchParams(window.location.search).get('channel')
  || localStorage.getItem(`radio_channel_${props.sfCode}`)
  || ''
)

const { state, isConnected, refresh } = usePolling(props.sfCode, sfName.value)

onMounted(() => {
  document.title = `Staffelführer: ${sfName.value} - Funk Simulator`
  if (radioChannel.value) {
    axios.post(`/api/staffelfuehrer/${props.sfCode}/channel`, {
      name: sfName.value,
      channel: radioChannel.value,
    })
  }
})

const updateUrlParams = () => {
  const url = new URL(window.location.href)
  url.searchParams.set('name', sfName.value)
  if (radioChannel.value) {
    url.searchParams.set('channel', radioChannel.value)
  } else {
    url.searchParams.delete('channel')
  }
  window.history.replaceState({}, '', url.toString())
}

const updateSfName = () => {
  localStorage.setItem(`sf_name_${props.sfCode}`, sfName.value)
  updateUrlParams()
  window.location.reload()
}

const updateRadioChannel = () => {
  localStorage.setItem(`radio_channel_${props.sfCode}`, radioChannel.value)
  updateUrlParams()
  axios.post(`/api/staffelfuehrer/${props.sfCode}/channel`, {
    name: sfName.value,
    channel: radioChannel.value,
  })
}

const claimVehicle = async (carName: string) => {
  await axios.post(`/api/staffelfuehrer/${props.sfCode}/claim`, { target_name: carName, sf_name: sfName.value })
  refresh()
}

const unclaimVehicle = async (carName: string) => {
  await axios.post(`/api/staffelfuehrer/${props.sfCode}/unclaim`, { target_name: carName })
  refresh()
}

const allConnections = computed(() => [...(state.value?.connections || [])].sort((a, b) => a.last_activity - b.last_activity))
const claimed = computed(() => allConnections.value.filter(c => c.claimed_by === sfName.value))
const unclaimed = computed(() => allConnections.value.filter(c => c.claimed_by !== sfName.value))
const sfActionVehicles = computed(() => claimed.value.filter(c => c.next_todo === 'SF'))
const otherVehicles = computed(() => claimed.value.filter(c => c.next_todo !== 'SF'))
const openCar = ref<string | null>(null)

const sendNotice = async (carName: string) => {
  await axios.post(`/api/staffelfuehrer/${props.sfCode}/notice`, {
    target_name: carName,
    text: 'Sprechwunsch Staffelführer',
    sf_name: sfName.value,
  })
  refresh()
}

const ackNotice = async (carName: string) => {
  await axios.post(`/api/staffelfuehrer/${props.sfCode}/acknowledge`, { target_name: carName })
  refresh()
}

const toggleCar = (carName: string) => {
  openCar.value = openCar.value === carName ? null : carName
}

const updateChecklistState = async (carName: string, checklist: any) => {
  await axios.post(`/api/leitstelle/${props.sfCode}/scenario/update_state`, {
    target_name: carName,
    state: checklist,
  })
  refresh()
}

const getNotice = (name: string) => state.value?.notices[name]

const borderColor = (status: string) => {
  switch (status) {
    case '4': return 'border-l-danger'
    case '3': return 'border-l-warning'
    case '2': return 'border-l-success'
    default: return 'border-l-info'
  }
}
</script>

<template>
  <div class="page">
    <div class="flex-1">
      <div class="card p-5 mb-5">
        <div class="flex justify-between items-start mb-4">
          <div>
            <h1 class="section-title text-2xl m-0">Staffelführer: {{ sfName }}</h1>
            <p class="mt-2 text-sm text-themed-muted">Standardname: {{ name }}</p>
          </div>
          <div class="flex flex-col gap-2">
            <div class="flex gap-2 items-center">
              <input v-model="sfName" class="input-sm w-40" placeholder="Eigener Name">
              <button @click="updateSfName" class="btn btn-primary p-1 px-3 text-sm">Speichern</button>
            </div>
            <div class="flex gap-2 items-center">
              <input v-model="radioChannel" class="input-sm w-40" placeholder="Funkkanal (z.B. 401)">
              <button @click="updateRadioChannel" class="btn btn-info p-1 px-3 text-sm">Kanal setzen</button>
            </div>
          </div>
        </div>
        <p>Code: <span class="bg-themed-overlay p-1.5 px-3 rounded font-mono font-bold text-xl text-primary border border-themed">{{ sfCode }}</span></p>
        <div v-if="!isConnected" class="disconnected">Verbindung unterbrochen...</div>
      </div>

      <div v-if="unclaimed.length > 0" class="card p-3 mb-5 flex items-center gap-3 border-l-4 border-l-warning">
        <span class="text-warning font-bold text-sm uppercase tracking-wider">{{ unclaimed.length }} nicht übernommen</span>
        <span class="text-themed-muted text-sm">Fahrzeuge ohne Zuordnung warten auf Übernahme</span>
      </div>

      <div class="flex flex-col gap-5">
        <div v-if="allConnections.length === 0" class="text-themed-faint italic text-center p-10 card">Lade Fahrzeuge...</div>

        <div v-if="sfActionVehicles.length > 0" class="vehicle-group border-t-4 border-t-danger">
          <h3 class="vehicle-group-title text-danger">Aktion erforderlich (SF)</h3>
          <div
            v-for="car in sfActionVehicles" :key="'sf-' + car.name"
            class="card mb-2 p-3 px-4 border-l-[5px] flex flex-col cursor-pointer"
            :class="borderColor(car.status)"
            @click="toggleCar(car.name)"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-4">
                <div class="flex flex-col">
                  <span class="font-bold text-lg min-w-[120px]">{{ car.name }}</span>
                  <div v-if="car.next_todo" class="bg-themed-input border border-themed px-2 py-0.5 rounded text-[10px] text-themed-muted">
                    <span class="text-primary-light font-bold">TODO:</span> {{ car.next_todo }}
                  </div>
                  <div v-if="car.claimed_by" class="text-[10px] text-primary-light uppercase tracking-tighter">
                    Übernommen von: {{ car.claimed_by }}
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <StatusBadge :status="car.status" />
                  <Timer :timestamp="car.last_status_update" :active="car.is_online" />
                </div>
                <div v-if="car.radio_channel" class="bg-info/20 border border-info/50 text-info px-2 py-0.5 rounded text-xs font-mono font-bold">
                  CH: {{ car.radio_channel }}
                </div>
                <div v-if="getNotice(car.name)" class="p-1 px-3 rounded flex items-center gap-2 font-bold text-sm"
                     :class="getNotice(car.name)?.status === 'confirmed' ? 'bg-success/10 border border-success text-success' : 'bg-warning/10 border border-warning text-warning'">
                  <span>{{ getNotice(car.name)?.status === 'confirmed' ? 'Spricht' : 'Angef.' }}</span>
                  <button v-if="getNotice(car.name)?.status === 'confirmed'" @click.stop="ackNotice(car.name)"
                          class="btn btn-success ml-2 p-0.5 px-2">Fertig</button>
                </div>
                <div v-if="car.talking_to_sf" class="bg-danger text-white p-1 px-2.5 rounded text-sm font-bold flex items-center gap-2">
                  <span>AKTIV</span>
                  <Timer :timestamp="car.talking_to_sf_since" :active="true" class="!text-white bg-black/20 p-0.5 px-1 rounded" />
                </div>
              </div>
              <div class="flex gap-2">
                <button v-if="!car.claimed_by" @click.stop="claimVehicle(car.name)" class="btn bg-success/80 text-white p-1.5 px-3 text-sm">Übernehmen</button>
                <button v-else-if="car.claimed_by === sfName" @click.stop="unclaimVehicle(car.name)" class="btn bg-danger/80 text-white p-1.5 px-3 text-sm">Freigeben</button>
                <button v-if="!car.talking_to_sf && car.claimed_by === sfName" @click.stop="sendNotice(car.name)" class="btn btn-primary p-1.5 px-3 text-sm">Anfrage</button>
              </div>
            </div>
            <div v-if="openCar === car.name" class="mt-2.5 pt-2.5 border-t border-themed" @click.stop>
              <ScenarioChecklist v-if="car.active_scenario" :scenario="car.active_scenario" :checklist-state="car.checklist_state" @update:state="(s) => updateChecklistState(car.name, s)" class="mb-3" />
              <VehicleChatPanel :code="sfCode" :target-name="car.name" :note="car.sf_note ?? ''" :notes-enabled="true" sender-label="SF" />
            </div>
          </div>
        </div>

        <div v-if="otherVehicles.length > 0" class="vehicle-group">
          <h3 class="vehicle-group-title text-primary">Alle Fahrzeuge</h3>
          <div
            v-for="car in otherVehicles" :key="'other-' + car.name"
            class="card mb-2 p-3 px-4 border-l-[5px] flex flex-col cursor-pointer"
            :class="borderColor(car.status)"
            @click="toggleCar(car.name)"
          >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-4">
              <div class="flex flex-col">
                <span class="font-bold text-lg min-w-[120px]">{{ car.name }}</span>
                <div v-if="car.next_todo" class="bg-themed-input border border-themed px-2 py-0.5 rounded text-[10px] text-themed-muted">
                  <span class="text-primary-light font-bold">TODO:</span> {{ car.next_todo }}
                </div>
                <div v-if="car.claimed_by" class="text-[10px] text-primary-light uppercase tracking-tighter">
                  Übernommen von: {{ car.claimed_by }}
                </div>
              </div>
              <div class="flex items-center gap-2">
                <StatusBadge :status="car.status" />
                <Timer :timestamp="car.last_status_update" :active="car.is_online" />
              </div>

              <div v-if="car.radio_channel" class="bg-info/20 border border-info/50 text-info px-2 py-0.5 rounded text-xs font-mono font-bold">
                CH: {{ car.radio_channel }}
              </div>

              <div v-if="getNotice(car.name)" class="p-1 px-3 rounded flex items-center gap-2 font-bold text-sm"
                   :class="getNotice(car.name)?.status === 'confirmed' ? 'bg-success/10 border border-success text-success' : 'bg-warning/10 border border-warning text-warning'">
                <span>{{ getNotice(car.name)?.status === 'confirmed' ? 'Spricht' : 'Angef.' }}</span>
                <button v-if="getNotice(car.name)?.status === 'confirmed'" @click.stop="ackNotice(car.name)"
                        class="btn btn-success ml-2 p-0.5 px-2">Fertig</button>
              </div>

              <div v-if="car.talking_to_sf" class="bg-danger text-white p-1 px-2.5 rounded text-sm font-bold flex items-center gap-2">
                <span>AKTIV</span>
                <Timer :timestamp="car.talking_to_sf_since" :active="true" class="!text-white bg-black/20 p-0.5 px-1 rounded" />
              </div>
            </div>
            <div class="flex gap-2">
              <button
                v-if="!car.claimed_by"
                @click.stop="claimVehicle(car.name)"
                class="btn bg-success/80 text-white p-1.5 px-3 text-sm"
              >
                Übernehmen
              </button>
              <button
                v-else-if="car.claimed_by === sfName"
                @click.stop="unclaimVehicle(car.name)"
                class="btn bg-danger/80 text-white p-1.5 px-3 text-sm"
              >
                Freigeben
              </button>
              <button
                v-if="!car.talking_to_sf && car.claimed_by === sfName"
                @click.stop="sendNotice(car.name)"
                class="btn btn-primary p-1.5 px-3 text-sm"
              >
                Anfrage
              </button>
            </div>
          </div>
          <div v-if="openCar === car.name" class="mt-2.5 pt-2.5 border-t border-themed" @click.stop>
            <ScenarioChecklist
              v-if="car.active_scenario"
              :scenario="car.active_scenario"
              :checklist-state="car.checklist_state"
              @update:state="(s) => updateChecklistState(car.name, s)"
              class="mb-3"
            />
            <VehicleChatPanel
              :code="sfCode"
              :target-name="car.name"
              :note="car.sf_note ?? ''"
              :notes-enabled="true"
              sender-label="SF"
            />
          </div>
        </div>
        </div>

        <div v-if="unclaimed.length > 0" class="vehicle-group border-t-4 border-t-warning opacity-70">
          <h3 class="vehicle-group-title text-warning">Nicht übernommen</h3>
          <div
            v-for="car in unclaimed" :key="'unclaimed-' + car.name"
            class="card mb-2 p-3 px-4 border-l-[5px] flex flex-col cursor-pointer"
            :class="borderColor(car.status)"
            @click="toggleCar(car.name)"
          >
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-4">
                <div class="flex flex-col">
                  <span class="font-bold text-lg min-w-[120px]">{{ car.name }}</span>
                  <div v-if="car.claimed_by" class="text-[10px] text-primary-light uppercase tracking-tighter">
                    Übernommen von: {{ car.claimed_by }}
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <StatusBadge :status="car.status" />
                  <Timer :timestamp="car.last_status_update" :active="car.is_online" />
                </div>
              </div>
              <div class="flex gap-2">
                <button
                  v-if="!car.claimed_by"
                  @click.stop="claimVehicle(car.name)"
                  class="btn bg-success/80 text-white p-1.5 px-3 text-sm"
                >
                  Übernehmen
                </button>
              </div>
            </div>
            <div v-if="openCar === car.name" class="mt-2.5 pt-2.5 border-t border-themed" @click.stop>
              <ScenarioChecklist v-if="car.active_scenario" :scenario="car.active_scenario" :checklist-state="car.checklist_state" @update:state="(s) => updateChecklistState(car.name, s)" class="mb-3" />
              <VehicleChatPanel :code="sfCode" :target-name="car.name" :note="car.sf_note ?? ''" :notes-enabled="true" sender-label="SF" />
            </div>
          </div>
        </div>
      </div>
    </div>
    <Footer />
  </div>
</template>
