<script setup lang="ts">
import { ref, computed } from 'vue';
import axios from 'axios';
import { useWebSocket } from './composables/useWebSocket';
import type { StatusUpdate } from './composables/useWebSocket';
import Footer from './components/Footer.vue';
import CodeCopyable from './components/CodeCopyable.vue';
import VehicleItem from './components/VehicleItem.vue';

const props = defineProps<{
  adminCode: string;
  leitstelleName: string;
  vehicleCode: string;
  staffelfuehrerCode: string;
}>();

const status = ref<StatusUpdate | null>(null);

const onMessage = (data: any) => {
  if (data.connections) {
    status.value = data;
  }
};

const { isConnected } = useWebSocket(`/ws/${props.adminCode}`, onMessage);

const vehiclesWithTalkingState = computed(() => {
  const notices = status.value?.notices ?? {};
  return (status.value?.connections || []).map((car) => ({
    ...car,
    talking_to_sf: car.talking_to_sf || notices[car.name]?.status === 'confirmed'
  })).sort((a, b) => a.last_activity - b.last_activity);
});

const blitzVehicles = computed(() => vehiclesWithTalkingState.value.filter(c => c.special === '0'));
const sprechwunschVehicles = computed(() => vehiclesWithTalkingState.value.filter(c => c.special === '5'));
const staffelfuehrerVehicles = computed(() => vehiclesWithTalkingState.value.filter(c => c.talking_to_sf));
const otherVehicles = computed(() => vehiclesWithTalkingState.value.filter(c => c.special !== '0' && c.special !== '5' && !c.talking_to_sf));

const message = ref('');
const sendMessage = async () => {
  if (!message.value) return;
  await axios.post(`/api/leitstelle/${props.adminCode}/message`, {
    message: message.value
  });
  message.value = '';
};
</script>

<template>
  <div class="max-w-[1200px] min-w-[320px] mx-auto p-5 flex flex-col min-h-screen">
    <div class="flex-1">
      <div class="bg-card rounded-lg p-4 mb-5 shadow-lg border border-gray-800 flex flex-wrap justify-between items-center gap-5">
        <div class="flex-1 min-w-[250px]">
          <h1 class="text-primary uppercase tracking-widest text-2xl font-bold m-0">Leitstelle: {{ leitstelleName }}</h1>
          <p class="mt-1 text-gray-500 text-sm">Admin-Code: <span class="font-mono font-bold text-gray-400">{{ adminCode }}</span></p>
        </div>
        <div class="flex gap-4">
          <CodeCopyable :code="vehicleCode" label="Fahrzeug-Code" />
          <CodeCopyable :code="staffelfuehrerCode" label="Staffelführer-Code" success-class="text-success" />
        </div>
      </div>

      <div class="bg-card rounded-lg p-5 mb-5 shadow-lg border border-gray-800">
        <h2 class="text-primary uppercase tracking-widest text-lg mb-3 font-bold">Nachricht an alle</h2>
        <form @submit.prevent="sendMessage" class="flex gap-2">
          <input 
            v-model="message" 
            type="text" 
            placeholder="Nachricht eingeben" 
            required 
            class="flex-[7] p-3 border border-gray-700 bg-gray-800 text-white rounded outline-none focus:border-primary"
          >
          <button type="submit" class="flex-[3] bg-secondary text-white p-3 rounded font-bold transition-all hover:brightness-110 active:translate-y-0.5">Senden</button>
        </form>
        <div v-if="!isConnected" class="text-warning font-bold mt-2">Verbindung unterbrochen...</div>
      </div>

      <div class="flex flex-col gap-5">
        <div v-if="blitzVehicles.length > 0" class="border border-gray-800 bg-[#1a1a1a] rounded-lg p-4 border-t-4 border-t-warning">
          <h3 class="text-warning uppercase tracking-widest text-sm mb-4 font-bold border-b border-gray-800 pb-2">0 Blitz</h3>
          <VehicleItem v-for="car in blitzVehicles" :key="car.name" :car="car" :admin-code="adminCode" />
        </div>

        <div v-if="sprechwunschVehicles.length > 0" class="border border-gray-800 bg-[#1a1a1a] rounded-lg p-4 border-t-4 border-t-accent">
          <h3 class="text-accent uppercase tracking-widest text-sm mb-4 font-bold border-b border-gray-800 pb-2">5 Sprechwunsch</h3>
          <VehicleItem v-for="car in sprechwunschVehicles" :key="car.name" :car="car" :admin-code="adminCode" />
        </div>

        <div v-if="staffelfuehrerVehicles.length > 0" class="border border-gray-800 bg-[#1a1a1a] rounded-lg p-4 border-t-4 border-t-danger">
          <h3 class="text-danger uppercase tracking-widest text-sm mb-4 font-bold border-b border-gray-800 pb-2">Gespräch mit Staffelführer</h3>
          <VehicleItem v-for="car in staffelfuehrerVehicles" :key="car.name" :car="car" :admin-code="adminCode" />
        </div>

        <div class="border border-gray-800 bg-[#1a1a1a] rounded-lg p-4">
          <h3 class="text-primary uppercase tracking-widest text-sm mb-4 font-bold border-b border-gray-800 pb-2">Alle Fahrzeuge</h3>
          <div v-if="otherVehicles.length === 0" class="text-gray-500 italic">Keine weiteren Fahrzeuge verbunden.</div>
          <VehicleItem v-for="car in otherVehicles" :key="car.name" :car="car" :admin-code="adminCode" />
        </div>
      </div>
    </div>
    <Footer />
  </div>
</template>
