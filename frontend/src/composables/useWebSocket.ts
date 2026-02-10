import { useWebSocket as useVueUseWebSocket } from '@vueuse/core';
import { watch, computed } from 'vue';
import { backendWsBaseUrl } from '../config/backend';

export interface VehicleStatus {
  name: string;
  status: string;
  special: string | null;
  kurzstatus: string | null;
  last_update: number;
  last_status_update: number;
  last_blitz_update: number | null;
  last_sprechwunsch_update: number | null;
  is_staffelfuehrer: boolean;
  note: string;
  sf_note: string;
  is_online: boolean;
  talking_to_sf: boolean;
}

export interface Notice {
  text: string;
  status: string;
  confirmed_at?: number;
}

export interface StatusUpdate {
  connections: VehicleStatus[];
  notices: Record<string, Notice>;
}

export function useWebSocket(url: string, onMessage?: (data: any) => void) {
  const fullUrl = `${backendWsBaseUrl}${url}`;

  const { status, data, send, close } = useVueUseWebSocket(fullUrl, {
    autoReconnect: {
      retries: 10,
      delay: 2000,
    },
    heartbeat: {
      message: 'heartbeat',
      interval: 20000,
      pongTimeout: 5000,
    },
  });

  const isConnected = computed(() => status.value === 'OPEN');

  watch(data, (newData) => {
    if (!newData || newData === 'heartbeat') return;
    if (onMessage) {
      try {
        const parsedData = JSON.parse(newData);
        onMessage(parsedData);
      } catch (e) {
        // Handle non-JSON messages (like private messages)
        onMessage({ type: 'text', message: newData });
      }
    }
  });

  return {
    isConnected,
    data,
    send: (data: string | object) => {
      if (typeof data === 'string') {
        send(data);
      } else {
        send(JSON.stringify(data));
      }
    },
    close: () => close()
  };
}
