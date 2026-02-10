<script setup lang="ts">
import {computed, ref} from 'vue';
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

const status = ref<StatusUpdate | null>(null);

const onMessage = (data: any) => {
  if (data.connections) {
    status.value = data;
  }
};

const {isConnected} = useWebSocket(`/ws/${props.sfCode}`, onMessage);

const connections = computed(() => status.value?.connections || []);
const openCar = ref<string | null>(null);

const sendNotice = async (carName: string) => {
  await axios.post(`/api/staffelfuehrer/${props.sfCode}/notice`, {
    target_name: carName,
    text: 'Sprechwunsch Staffelführer'
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

const getNotice = (name: string) => status.value?.notices[name];
</script>

<template>
  <div class="max-w-[1200px] min-w-[320px] mx-auto p-5 flex flex-col min-h-screen">
    <div class="flex-1">
      <div class="bg-card rounded-lg p-5 mb-5 shadow-lg border border-gray-800">
        <h1 class="text-primary uppercase tracking-widest text-2xl font-bold m-0">Staffelführer: {{ name }}</h1>
        <p class="mt-2">Code: <span
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
              <span class="font-bold text-lg min-w-[120px]">{{ car.name }}</span>
              <div class="flex items-center gap-2">
                <StatusBadge :status="car.status"/>
                <Timer :timestamp="car.last_status_update" :active="car.is_online"/>
              </div>

              <div v-if="getNotice(car.name)" class="p-1 px-3 rounded flex items-center gap-2 font-bold text-[0.85rem]"
                   :class="getNotice(car.name)?.status === 'confirmed' ? 'bg-success/10 border border-success text-success' : 'bg-warning/10 border border-warning text-warning'">
                <span>{{ getNotice(car.name)?.status === 'confirmed' ? 'Spricht' : 'Angef.' }}</span>
                <button v-if="getNotice(car.name)?.status === 'confirmed'" @click.stop="ackNotice(car.name)"
                        class="ml-2 bg-success text-white p-0.5 px-2 rounded hover:brightness-110">OK
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
                  v-if="!car.talking_to_sf"
                  @click.stop="sendNotice(car.name)"
                  class="bg-primary text-white p-2 px-4 rounded font-bold hover:brightness-110"
              >
                Anfrage
              </button>
            </div>
          </div>
            <div v-if="openCar === car.name" class="mt-2.5 pt-2.5 border-t border-gray-800" @click.stop>
            <ScenarioChecklist v-if="car.active_scenario" :scenario="car.active_scenario" class="mb-3" />
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
