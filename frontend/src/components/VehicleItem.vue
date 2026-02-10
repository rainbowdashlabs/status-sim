<script setup lang="ts">
import { ref, computed } from 'vue';
import axios from 'axios';
import type { VehicleStatus } from '../composables/useWebSocket';
import Timer from './Timer.vue';
import VehicleChatPanel from './VehicleChatPanel.vue';
import StatusBadge from './StatusBadge.vue';
import ScenarioChecklist from './ScenarioChecklist.vue';

const props = defineProps<{
  car: VehicleStatus;
  adminCode: string;
}>();

const isOpen = ref(false);

const setStatus = async (status: string) => {
  await axios.post(`/api/leitstelle/${props.adminCode}/set_status`, {
    target_name: props.car.name,
    status: status
  });
};

const clearSpecial = async () => {
  await axios.post(`/api/leitstelle/${props.adminCode}/clear_special`, {
    target_name: props.car.name
  });
};

const clearKurzstatus = async () => {
  await axios.post(`/api/leitstelle/${props.adminCode}/clear_kurzstatus`, {
    target_name: props.car.name
  });
};

const startScenario = async () => {
  // Für die Demo wählen wir einfach das erste verfügbare Szenario
  // In einer echten App gäbe es ein Dropdown.
  const response = await axios.get(`/api/leitstelle/${props.adminCode}/scenarios`);
  if (response.data.scenarios && response.data.scenarios.length > 0) {
    await axios.post(`/api/leitstelle/${props.adminCode}/scenario/start`, {
      target_name: props.car.name,
      scenario_name: response.data.scenarios[0].name
    });
  }
};

const discardScenario = async () => {
  await axios.post(`/api/leitstelle/${props.adminCode}/scenario/discard`, {
    target_name: props.car.name
  });
};

const newEinsatz = async () => {
  // Alten Einsatz als beendet markieren (verwerfen), falls vorhanden
  if (props.car.active_scenario) {
    await axios.post(`/api/leitstelle/${props.adminCode}/scenario/discard`, {
      target_name: props.car.name
    });
  }
  // Nächstes unbenutztes Szenario vom Backend auswählen lassen
  try {
    const nextResp = await axios.post(`/api/leitstelle/${props.adminCode}/scenario/next`, {
      target_name: props.car.name
    });
    const nextData = nextResp.data || {};
    const nextName = nextData?.scenario?.name;
    if (nextData.status === 'success' && nextName) {
      await axios.post(`/api/leitstelle/${props.adminCode}/scenario/start`, {
        target_name: props.car.name,
        scenario_name: nextName
      });
      return;
    }
  } catch (e) {
    // Fallback unten
  }
  // Fallback: Liste laden und erstes Szenario starten
  const response = await axios.get(`/api/leitstelle/${props.adminCode}/scenarios`);
  if (response.data.scenarios && response.data.scenarios.length > 0) {
    await axios.post(`/api/leitstelle/${props.adminCode}/scenario/start`, {
      target_name: props.car.name,
      scenario_name: response.data.scenarios[0].name
    });
  }
};

const borderClass = computed(() => {
    switch (props.car.status) {
        case '1': return 'border-l-info';
        case '2': return 'border-l-success';
        case '3': return 'border-l-warning';
        case '4': return 'border-l-danger';
        default: return 'border-l-gray-600';
    }
});
</script>

<template>
  <div 
    class="bg-card mb-2 p-2.5 px-3.5 rounded-lg flex flex-col border-l-[5px]"
    :class="borderClass"
  >
    <div class="flex items-center justify-between w-full cursor-pointer gap-2.5" @click="isOpen = !isOpen">
      <div class="flex items-center gap-2.5">
        <StatusBadge :status="car.status" />
        <span class="font-bold whitespace-nowrap overflow-hidden text-ellipsis max-w-[150px]" :title="car.name">{{ car.name }}</span>
        
        <div v-if="car.kurzstatus" class="text-[0.85rem] bg-info/10 p-1.5 px-2.5 rounded flex gap-2.5 items-center whitespace-nowrap">
          <span class="font-bold text-info">K:</span>
          <span>{{ car.kurzstatus }}</span>
          <button @click.stop="clearKurzstatus" class="p-0.5 px-2 text-[0.75rem] bg-info text-white rounded font-bold hover:brightness-110">OK</button>
        </div>

        <div v-if="car.talking_to_sf" class="bg-danger text-white p-1 px-2.5 rounded text-[0.85rem] font-bold flex items-center gap-2">
            <span>SF</span>
            <Timer :timestamp="car.last_update" :active="true" class="!text-white bg-black/20 p-0.5 px-1 rounded" />
        </div>
      </div>

      <div class="flex items-center gap-4">
        <div v-if="car.special" class="bg-accent text-black font-extrabold uppercase text-[0.85rem] p-1.5 px-3 rounded shadow-[0_0_10px_var(--accent-color)] flex items-center gap-2">
          <span>{{ car.special === '0' ? '0 BLITZ' : '5 SPR-W' }}</span>
          <Timer :timestamp="car.special === '0' ? car.last_blitz_update : car.last_sprechwunsch_update" :active="true" class="!text-black" />
          <button @click.stop="clearSpecial" class="p-1 px-2.5 text-[0.85rem] bg-danger text-white rounded font-bold hover:brightness-110">X</button>
        </div>
        <Timer :timestamp="car.last_status_update" :active="car.is_online" />
      </div>
    </div>

    <div v-if="isOpen" class="mt-2.5 pt-2.5 border-t border-gray-800 w-full">
      <div class="flex flex-col gap-2.5 items-center justify-between">
        <div class="flex gap-2 w-full">
          <button @click="setStatus('1')" class="flex-1 p-2 py-1.5 text-[0.9rem] font-extrabold bg-info text-white rounded hover:brightness-110">1</button>
          <button @click="setStatus('2')" class="flex-1 p-2 py-1.5 text-[0.9rem] font-extrabold bg-success text-white rounded hover:brightness-110">2</button>
          <button @click="setStatus('3')" class="flex-1 p-2 py-1.5 text-[0.9rem] font-extrabold bg-warning text-black rounded hover:brightness-110">3</button>
          <button @click="setStatus('4')" class="flex-1 p-2 py-1.5 text-[0.9rem] font-extrabold bg-danger text-white rounded hover:brightness-110">4</button>
        </div>
        
        <div class="w-full flex gap-2">
           <button v-if="!car.active_scenario" @click="startScenario" class="flex-1 p-2 bg-primary text-white rounded font-bold hover:brightness-110">Einsatz erstellen</button>
           <button v-else @click="discardScenario" class="flex-1 p-2 bg-danger text-white rounded font-bold hover:brightness-110">Einsatz verwerfen</button>
           <button @click="newEinsatz" class="flex-1 p-2 bg-secondary text-white rounded font-bold hover:brightness-110">Neuer Einsatz</button>
        </div>

        <ScenarioChecklist v-if="car.active_scenario" :scenario="car.active_scenario" class="w-full" />

        <VehicleChatPanel
          :code="adminCode"
          :target-name="car.name"
          :note="car.note"
          :notes-enabled="true"
          sender-label="LS"
          class="w-full"
        />

      </div>

    </div>
  </div>
</template>
