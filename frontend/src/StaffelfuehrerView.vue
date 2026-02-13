<script setup lang="ts">
import {computed, ref, onMounted} from 'vue';
import axios from 'axios';
import type {StatusUpdate} from './composables/useWebSocket';
import {useWebSocket} from './composables/useWebSocket';
import Footer from './components/Footer.vue';
import Timer from './components/Timer.vue';
import VehicleChatPanel from './components/VehicleChatPanel.vue';
import StatusBadge from './components/StatusBadge.vue';
import ScenarioChecklist from './components/ScenarioChecklist.vue';

const props = defineProps<{
  name: string;
  sfCode: string;
}>();

const sfName = ref(new URLSearchParams(window.location.search).get('name') || localStorage.getItem(`sf_name_${props.sfCode}`) || props.name);
const radioChannel = ref(new URLSearchParams(window.location.search).get('channel') || localStorage.getItem(`radio_channel_${props.sfCode}`) || '');
const status = ref<StatusUpdate | null>(null);

const onMessage = (data: any) => {
  if (data.type === 'status_update') {
    status.value = data;
  }
};

const {isConnected, send} = useWebSocket(`/ws/${props.sfCode}?name=${encodeURIComponent(sfName.value)}`, onMessage);

onMounted(() => {
  document.title = `Staffelführer: ${sfName.value} - Funk Simulator`;
  if (radioChannel.value) {
    send(JSON.stringify({type: 'set_channel', value: radioChannel.value}));
  }
});

const updateUrlParams = () => {
  const url = new URL(window.location.href);
  url.searchParams.set('name', sfName.value);
  if (radioChannel.value) {
    url.searchParams.set('channel', radioChannel.value);
  } else {
    url.searchParams.delete('channel');
  }
  window.history.replaceState({}, '', url.toString());
};

const updateSfName = () => {
  localStorage.setItem(`sf_name_${props.sfCode}`, sfName.value);
  updateUrlParams();
  window.location.reload(); // Reload to reconnect with new name
};

const updateRadioChannel = () => {
  localStorage.setItem(`radio_channel_${props.sfCode}`, radioChannel.value);
  updateUrlParams();
  send(JSON.stringify({type: 'set_channel', value: radioChannel.value}));
};

const claimVehicle = async (carName: string) => {
  await axios.post(`/api/staffelfuehrer/${props.sfCode}/claim`, {
    target_name: carName,
    sf_name: sfName.value
  });
};

const unclaimVehicle = async (carName: string) => {
  await axios.post(`/api/staffelfuehrer/${props.sfCode}/unclaim`, {
    target_name: carName
  });
};

const connections = computed(() => [...(status.value?.connections || [])].sort((a, b) => a.last_activity - b.last_activity));
const openCar = ref<string | null>(null);

const sendNotice = async (carName: string) => {
  await axios.post(`/api/staffelfuehrer/${props.sfCode}/notice`, {
    target_name: carName,
    text: 'Sprechwunsch Staffelführer',
    sf_name: sfName.value
  });
};

const ackNotice = async (carName: string) => {
  await axios.post(`/api/staffelfuehrer/${props.sfCode}/acknowledge`, {
    target_name: carName
  });
};

const toggleCar = (carName: string) => {
  openCar.value = openCar.value === carName ? null : carName;
};

const updateChecklistState = async (carName: string, state: any) => {
  await axios.post(`/api/leitstelle/${props.sfCode}/scenario/update_state`, {
    target_name: carName,
    state: state
  });
};

const getNotice = (name: string) => status.value?.notices[name];
</script>

<template>
  <div class="max-w-[1200px] min-w-[320px] mx-auto p-5 flex flex-col min-h-screen">
    <div class="flex-1">
      <div class="bg-card rounded-lg p-5 mb-5 shadow-lg border border-gray-800">
        <div class="flex justify-between items-start mb-4">
          <div>
            <h1 class="text-primary uppercase tracking-widest text-2xl font-bold m-0">Staffelführer: {{ sfName }}</h1>
            <p class="mt-2 text-sm text-gray-400">Standardname: {{ name }}</p>
          </div>
          <div class="flex flex-col gap-2">
            <div class="flex gap-2 items-center">
              <input 
                v-model="sfName" 
                class="bg-black border border-gray-700 rounded px-2 py-1 text-sm text-white focus:outline-none focus:border-primary w-40"
                placeholder="Eigener Name"
              >
              <button @click="updateSfName" class="bg-primary text-white px-3 py-1 rounded text-sm font-bold hover:brightness-110">Speichern</button>
            </div>
            <div class="flex gap-2 items-center">
              <input 
                v-model="radioChannel" 
                class="bg-black border border-gray-700 rounded px-2 py-1 text-sm text-white focus:outline-none focus:border-primary w-40"
                placeholder="Funkkanal (z.B. 401)"
              >
              <button @click="updateRadioChannel" class="bg-info text-white px-3 py-1 rounded text-sm font-bold hover:brightness-110">Kanal setzen</button>
            </div>
          </div>
        </div>
        <p>Code: <span
            class="bg-black p-1.5 px-3 rounded font-mono font-bold text-xl text-primary border border-gray-800">{{
            sfCode
          }}</span></p>
        <div v-if="!isConnected" class="text-warning font-bold mt-2">Verbindung unterbrochen...</div>
      </div>

      <div class="flex flex-col gap-3">
        <div v-if="connections.length === 0"
             class="text-gray-500 italic text-center p-10 bg-card rounded-lg border border-gray-800">Lade Fahrzeuge...
        </div>

        <div v-for="car in connections" :key="car.name"
             class="bg-card p-3 px-4 rounded-lg border-l-[5px] flex flex-col cursor-pointer"
             :class="car.status === '4' ? 'border-l-danger' : (car.status === '3' ? 'border-l-warning' : (car.status === '2' ? 'border-l-success' : 'border-l-info'))"
             @click="toggleCar(car.name)"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-4">
              <div class="flex flex-col">
                <span class="font-bold text-lg min-w-[120px]">{{ car.name }}</span>
                <div v-if="car.next_todo" class="bg-gray-800 border border-gray-700 px-2 py-0.5 rounded text-[10px] text-gray-300" :title="car.next_todo">
                   <span class="text-primary-light font-bold">TODO:</span> {{ car.next_todo }}
                </div>
                <div v-if="car.claimed_by" class="text-[10px] text-primary-light uppercase tracking-tighter">
                  Übernommen von: {{ car.claimed_by }}
                </div>
              </div>
              <div class="flex items-center gap-2">
                <StatusBadge :status="car.status"/>
                <Timer :timestamp="car.last_status_update" :active="car.is_online"/>
              </div>

              <div v-if="car.radio_channel" class="bg-info/20 border border-info/50 text-info px-2 py-0.5 rounded text-xs font-mono font-bold">
                CH: {{ car.radio_channel }}
              </div>

              <div v-if="getNotice(car.name)" class="p-1 px-3 rounded flex items-center gap-2 font-bold text-[0.85rem]"
                   :class="getNotice(car.name)?.status === 'confirmed' ? 'bg-success/10 border border-success text-success' : 'bg-warning/10 border border-warning text-warning'">
                <span>{{ getNotice(car.name)?.status === 'confirmed' ? 'Spricht' : 'Angef.' }}</span>
                <button v-if="getNotice(car.name)?.status === 'confirmed'" @click.stop="ackNotice(car.name)"
                        class="ml-2 bg-success text-white p-0.5 px-2 rounded hover:brightness-110">Fertig
                </button>
              </div>

              <div v-if="car.talking_to_sf"
                   class="bg-danger text-white p-1 px-2.5 rounded text-[0.85rem] font-bold flex items-center gap-2">
                <span>AKTIV</span>
                <Timer :timestamp="car.last_update" :active="true" class="!text-white bg-black/20 p-0.5 px-1 rounded"/>
              </div>
            </div>
            <div class="flex gap-2">
              <button
                  v-if="!car.claimed_by"
                  @click.stop="claimVehicle(car.name)"
                  class="bg-success/80 text-white p-1.5 px-3 rounded text-sm font-bold hover:brightness-110"
              >
                Übernehmen
              </button>
              <button
                  v-else-if="car.claimed_by === sfName"
                  @click.stop="unclaimVehicle(car.name)"
                  class="bg-danger/80 text-white p-1.5 px-3 rounded text-sm font-bold hover:brightness-110"
              >
                Freigeben
              </button>
              <button
                  v-if="!car.talking_to_sf && car.claimed_by === sfName"
                  @click.stop="sendNotice(car.name)"
                  class="bg-primary text-white p-1.5 px-3 rounded text-sm font-bold hover:brightness-110"
              >
                Anfrage
              </button>
            </div>
          </div>
            <div v-if="openCar === car.name" class="mt-2.5 pt-2.5 border-t border-gray-800" @click.stop>
            <ScenarioChecklist 
               v-if="car.active_scenario" 
               :scenario="car.active_scenario" 
               :checklist-state="car.checklist_state"
               @update:state="(state) => updateChecklistState(car.name, state)"
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
    </div>
    <Footer/>
  </div>
</template>
