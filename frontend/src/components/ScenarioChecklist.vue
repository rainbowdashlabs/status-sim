<script setup lang="ts">
import { computed, ref } from 'vue';

const props = defineProps<{
  scenario: any;
  checklistState?: {
    expanded_einsaetze: Record<string, boolean>;
    expanded_schritte: Record<string, boolean>;
    checked_entries: Record<string, boolean>;
  } | null;
}>();

const emit = defineEmits<{
  (e: 'update:state', state: any): void;
}>();

const expandedEinsaetze = ref<Record<string, boolean>>({});
const expandedSchritte = ref<Record<string, boolean>>({});
const checkedEntries = computed(() => props.checklistState?.checked_entries || {});

const updateState = (newPartialState: any) => {
  const currentState = {
    expanded_einsaetze: {}, // Do not sync
    expanded_schritte: {},  // Do not sync
    checked_entries: { ...checkedEntries.value },
    ...newPartialState
  };
  emit('update:state', currentState);
};

const toggleEinsatz = (index: any) => {
  const idx = typeof index === 'string' ? index : index.toString();
  expandedEinsaetze.value[idx] = !expandedEinsaetze.value[idx];
};

const toggleSchritt = (eIdx: any, sIdx: any) => {
  const e = typeof eIdx === 'string' ? eIdx : eIdx.toString();
  const s = typeof sIdx === 'string' ? sIdx : sIdx.toString();
  const key = `${e}-${s}`;
  expandedSchritte.value[key] = !expandedSchritte.value[key];
};

const toggleEntry = (eIdx: any, sIdx: any, fIdx: any) => {
  const e = typeof eIdx === 'string' ? eIdx : eIdx.toString();
  const s = typeof sIdx === 'string' ? sIdx : sIdx.toString();
  const f = typeof fIdx === 'string' ? fIdx : fIdx.toString();
  const key = `${e}-${s}-${f}`;
  const next = { ...checkedEntries.value };
  next[key] = !next[key];
  updateState({ checked_entries: next });
};

const getFunkspruecheForSchritt = (einsatzIndex: any, schrittIndex: any) => {
  const e = typeof einsatzIndex === 'string' ? parseInt(einsatzIndex) : einsatzIndex;
  const s = typeof schrittIndex === 'string' ? parseInt(schrittIndex) : schrittIndex;
  const prefix = `[[E${e}]][[S${s}]]`;
  return (props.scenario.generated_entries || [])
    .filter((entry: any) => entry.message.startsWith(prefix))
    .map((entry: any) => ({
      ...entry,
      message: entry.message.replace(prefix, '')
    }));
};

const getSchrittLabel = (einsatz: any, sIdx: number) => {
  if (sIdx === 0) return "Alarmierung";
  const schritt = einsatz.schritte[sIdx - 1];
  if (!schritt) return `Schritt ${sIdx}`;
  
  switch (schritt.typ) {
    case 'eigenunfall': return 'Eigenunfall';
    case 'neue_taetigkeit_mit_fzn': return 'Neue Tätigkeit (FZN)';
    case 'neue_taetigkeit_ohne_fzn': return 'Neue Tätigkeit';
    case 'einsatzstellenkorrektur': return 'Einsatzstellenkorrektur';
    case 'ankommen': return 'Ankunft am Einsatzort';
    case 'kurzlagemeldung': return 'Kurzlagemeldung';
    case 'lagemeldung': return 'Lagemeldung';
    case 'ohne_lagemeldung': return 'Abschluss ohne Lagemeldung';
    case 'nachalarmierung': return 'Nachalarmierung';
    case 'fehlalarm_lagemeldung': return 'Fehlalarm BMA';
    default: return schritt.typ;
  }
};

const getActorColor = (actor: string) => {
  switch (actor) {
    case 'LS': return 'text-primary';
    case 'SF': return 'text-danger';
    case 'FZ': return 'text-success';
    default: return 'text-white';
  }
};
</script>

<template>
  <div class="mt-4 border border-gray-700 rounded overflow-hidden bg-gray-900/50">
    <div class="bg-gray-800 p-2 px-3 font-bold text-sm uppercase tracking-wider border-b border-gray-700 flex justify-between items-center">
      <span>Szenario: {{ scenario.name }}</span>
    </div>
    <div class="p-3">
      <p class="text-xs text-gray-400 mb-3 italic">{{ scenario.beschreibung }}</p>
      
      <div v-for="(einsatz, eIdx) in scenario.einsaetze" :key="eIdx" class="mb-4 last:mb-0">
        <!-- Einsatz Header -->
        <div 
          @click="toggleEinsatz(eIdx)"
          class="bg-gray-800 p-2 rounded cursor-pointer hover:bg-gray-700 transition-colors flex justify-between items-center border border-gray-600 shadow-sm"
        >
          <div class="flex flex-col">
            <span class="font-bold text-sm text-primary">{{ einsatz.stichwort }}</span>
            <span class="text-xs text-gray-300">{{ einsatz.adresse }}, {{ einsatz.ortsteil }}</span>
          </div>
          <span class="text-xs">{{ expandedEinsaetze[eIdx.toString()] ? '▲' : '▼' }}</span>
        </div>
        
        <!-- Einsatz Content (Schritte) -->
        <div v-if="expandedEinsaetze[eIdx.toString()]" class="mt-2 ml-3 pl-3 border-l-2 border-gray-700 flex flex-col gap-2">
          <div v-for="sIdx in (einsatz.schritte.length + 1)" :key="sIdx-1" class="flex flex-col">
            <!-- Schritt Header -->
            <div 
              @click="toggleSchritt(eIdx, sIdx-1)"
              class="bg-gray-800/60 p-2 rounded cursor-pointer hover:bg-gray-700/60 flex justify-between items-center border border-gray-700/50"
            >
              <span class="text-xs font-bold text-gray-200">{{ getSchrittLabel(einsatz, sIdx-1) }}</span>
              <span class="text-[10px]">{{ expandedSchritte[`${eIdx}-${sIdx-1}`] ? '▲' : '▼' }}</span>
            </div>

            <!-- Schritt Content (Funksprüche) -->
            <div v-if="expandedSchritte[`${eIdx}-${sIdx-1}`]" class="mt-1 ml-2 flex flex-col gap-1">
              <div 
                v-for="(entry, fIdx) in getFunkspruecheForSchritt(eIdx, sIdx-1)" 
                :key="fIdx"
                class="flex items-start gap-2 p-1.5 rounded bg-black/20 border border-gray-800/50 hover:bg-black/30 transition-colors group"
                @click="toggleEntry(eIdx, sIdx-1, fIdx)"
              >
                <div class="mt-0.5">
                  <input 
                    type="checkbox" 
                    :checked="checkedEntries[`${eIdx}-${sIdx-1}-${fIdx}`]" 
                    @click.stop="toggleEntry(eIdx, sIdx-1, fIdx)"
                    class="accent-primary w-3.5 h-3.5"
                  >
                </div>
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 mb-0.5">
                    <span class="text-[10px] font-mono text-gray-500">#{{ entry.enr }}</span>
                    <span class="text-xs font-bold" :class="getActorColor(entry.actor)">{{ entry.actor }}</span>
                  </div>
                  <div
                    class="text-xs leading-relaxed transition-all" 
                    :class="checkedEntries[`${eIdx}-${sIdx-1}-${fIdx}`] ? 'line-through text-gray-600' : 'text-gray-200'"
                  >
                    {{ entry.message }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
