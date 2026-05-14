<script setup lang="ts">
import { ref, computed, inject } from 'vue'
import axios from 'axios'
import type { VehicleStatus } from '../types'
import { REFRESH_KEY } from '../composables/usePolling'
import Timer from './Timer.vue'
import VehicleChatPanel from './VehicleChatPanel.vue'
import StatusBadge from './StatusBadge.vue'
import ScenarioChecklist from './ScenarioChecklist.vue'

const props = defineProps<{
  car: VehicleStatus
  adminCode: string
  lsName?: string
}>()

const refresh = inject(REFRESH_KEY, () => {})
const isOpen = ref(false)

const setStatus = async (status: string) => {
  await axios.post(`/api/leitstelle/${props.adminCode}/set_status`, {
    target_name: props.car.name,
    status,
  })
  refresh()
}

const clearSpecial = async () => {
  await axios.post(`/api/leitstelle/${props.adminCode}/clear_special`, { target_name: props.car.name })
  refresh()
}

const clearKurzstatus = async () => {
  await axios.post(`/api/leitstelle/${props.adminCode}/clear_kurzstatus`, { target_name: props.car.name })
  refresh()
}

const discardScenario = async () => {
  await axios.post(`/api/leitstelle/${props.adminCode}/scenario/discard`, { target_name: props.car.name })
  refresh()
}

const newEinsatz = async () => {
  if (props.car.active_scenario) {
    await axios.post(`/api/leitstelle/${props.adminCode}/scenario/discard`, { target_name: props.car.name })
  }
  try {
    const { data } = await axios.post(`/api/leitstelle/${props.adminCode}/scenario/next`, { target_name: props.car.name })
    if (data.status === 'success' && data.scenario?.name) {
      await axios.post(`/api/leitstelle/${props.adminCode}/scenario/start`, {
        target_name: props.car.name,
        scenario_name: data.scenario.name,
      })
      refresh()
      return
    }
  } catch { /* fallback below */ }
  const { data } = await axios.get(`/api/leitstelle/${props.adminCode}/scenarios`)
  if (data.scenarios?.length) {
    const random = data.scenarios[Math.floor(Math.random() * data.scenarios.length)]
    await axios.post(`/api/leitstelle/${props.adminCode}/scenario/start`, {
      target_name: props.car.name,
      scenario_name: random.name,
    })
  }
  refresh()
}

const claimVehicle = async () => {
  await axios.post(`/api/leitstelle/${props.adminCode}/claim`, {
    target_name: props.car.name,
    sf_name: props.lsName,
  })
  refresh()
}

const unclaimVehicle = async () => {
  await axios.post(`/api/leitstelle/${props.adminCode}/unclaim`, { target_name: props.car.name })
  refresh()
}

const borderClass = computed(() => {
  switch (props.car.status) {
    case '1': return 'border-l-info'
    case '2': return 'border-l-success'
    case '3': return 'border-l-warning'
    case '4': return 'border-l-danger'
    default: return 'border-l-gray-600'
  }
})

const updateChecklistState = async (state: any) => {
  await axios.post(`/api/leitstelle/${props.adminCode}/scenario/update_state`, {
    target_name: props.car.name,
    state,
  })
  refresh()
}
</script>

<template>
  <div class="card mb-2 p-2.5 px-3.5 flex flex-col border-l-[5px]" :class="borderClass">
    <div class="flex items-center justify-between w-full cursor-pointer gap-2.5" @click="isOpen = !isOpen">
      <div class="flex items-center gap-2.5">
        <StatusBadge :status="car.status" />
        <span class="font-bold whitespace-nowrap overflow-hidden text-ellipsis max-w-[150px]" :title="car.name">{{ car.name }}</span>

        <div v-if="car.next_todo" class="bg-themed-input border border-themed px-2 py-0.5 rounded text-xs text-themed-muted font-bold">
          {{ car.next_todo }}
        </div>

        <div v-if="car.kurzstatus" class="text-sm bg-info/10 p-1.5 px-2.5 rounded flex gap-2.5 items-center whitespace-nowrap">
          <span class="font-bold text-info">K:</span>
          <span>{{ car.kurzstatus }}</span>
          <button @click.stop="clearKurzstatus" class="btn btn-info p-0.5 px-2 text-xs">OK</button>
        </div>

        <div v-if="car.talking_to_sf" class="bg-danger text-white p-1 px-2.5 rounded text-sm font-bold flex items-center gap-2">
          <span>SF</span>
          <Timer :timestamp="car.talking_to_sf_since" :active="true" class="!text-white bg-black/20 p-0.5 px-1 rounded" />
        </div>

        <div v-if="car.ls_claimed_by" class="text-[10px] text-primary-light uppercase tracking-tighter">
          LS: {{ car.ls_claimed_by }}
        </div>
      </div>

      <div class="flex items-center gap-4">
        <div v-if="lsName" class="flex gap-1.5">
          <button
            v-if="!car.ls_claimed_by"
            @click.stop="claimVehicle"
            class="btn bg-primary/80 text-white p-1 px-2.5 text-xs"
          >
            Übernehmen
          </button>
          <button
            v-else-if="car.ls_claimed_by === lsName"
            @click.stop="unclaimVehicle"
            class="btn bg-danger/80 text-white p-1 px-2.5 text-xs"
          >
            Freigeben
          </button>
        </div>
        <div v-if="car.special" class="bg-accent text-black font-extrabold uppercase text-sm p-1.5 px-3 rounded shadow-[0_0_10px_var(--accent-color)] flex items-center gap-2">
          <span>{{ car.special === '0' ? '0 BLITZ' : '5 SPR-W' }}</span>
          <Timer :timestamp="car.special === '0' ? car.last_blitz_update : car.last_sprechwunsch_update" :active="true" class="!text-black" />
          <button @click.stop="clearSpecial" class="btn btn-danger p-1 px-2.5 text-sm">X</button>
        </div>
        <Timer :timestamp="car.last_status_update" :active="car.is_online" />
      </div>
    </div>

    <div v-if="isOpen" class="mt-2.5 pt-2.5 border-t border-themed w-full">
      <div class="flex flex-col gap-2.5 items-center justify-between">
        <div class="flex gap-2 w-full">
          <button @click="setStatus('1')" class="btn btn-info flex-1 p-2 py-1.5 text-sm font-extrabold">1</button>
          <button @click="setStatus('2')" class="btn btn-success flex-1 p-2 py-1.5 text-sm font-extrabold">2</button>
          <button @click="setStatus('3')" class="btn btn-warning flex-1 p-2 py-1.5 text-sm font-extrabold">3</button>
          <button @click="setStatus('4')" class="btn btn-danger flex-1 p-2 py-1.5 text-sm font-extrabold">4</button>
        </div>

        <div class="w-full flex gap-2">
          <button v-if="!car.active_scenario" @click="newEinsatz" class="btn btn-primary flex-1 p-2">Einsatz erstellen</button>
          <button v-else @click="discardScenario" class="btn btn-danger flex-1 p-2">Einsatz verwerfen</button>
          <button @click="newEinsatz" class="btn btn-secondary flex-1 p-2">Neuer Einsatz</button>
        </div>

        <ScenarioChecklist
          v-if="car.active_scenario"
          :scenario="car.active_scenario"
          :checklist-state="car.checklist_state"
          @update:state="updateChecklistState"
          class="w-full"
        />

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
