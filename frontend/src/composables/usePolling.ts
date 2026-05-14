import { ref, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'
import type { StatusUpdate } from '../types'

export const REFRESH_KEY = Symbol('pollRefresh') as InjectionKey<() => void>

import type { InjectionKey } from 'vue'

export function usePolling(code: string, name?: string, intervalMs = 2000) {
  const state = ref<StatusUpdate | null>(null)
  const isConnected = ref(false)
  let timer: number | null = null

  const fetchState = async () => {
    try {
      const params: Record<string, string> = {}
      if (name) params.name = name
      const { data } = await axios.get(`/api/poll/${code}`, { params })
      if (data?.type === 'status_update') {
        state.value = data
        isConnected.value = true
      }
    } catch {
      isConnected.value = false
    }
  }

  const refresh = () => {
    if (timer) clearInterval(timer)
    fetchState()
    timer = window.setInterval(fetchState, intervalMs)
  }

  onMounted(() => {
    fetchState()
    timer = window.setInterval(fetchState, intervalMs)
  })

  onBeforeUnmount(() => {
    if (timer) clearInterval(timer)
  })

  return { state, isConnected, refresh }
}
