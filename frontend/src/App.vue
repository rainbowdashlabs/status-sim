<script setup lang="ts">
import {onMounted, ref} from 'vue';
import axios from 'axios';
import LandingPage from './LandingPage.vue';
import LeitstelleView from './LeitstelleView.vue';
import StatusView from './StatusView.vue';
import StaffelfuehrerView from './StaffelfuehrerView.vue';

type View =
    | { type: 'landing' }
    | { type: 'leitstelle', adminCode: string, leitstelleName: string, vehicleCode: string, staffelfuehrerCode: string }
    | { type: 'status', code: string, name: string, leitstelleName: string }
    | { type: 'staffelfuehrer', sfCode: string, name: string };

const currentView = ref<View>({type: 'landing'});

const handleCreated = (data: { adminCode: string, name: string, vehicleCode: string, staffelfuehrerCode: string }) => {
  currentView.value = {
    type: 'leitstelle',
    adminCode: data.adminCode,
    leitstelleName: data.name,
    vehicleCode: data.vehicleCode,
    staffelfuehrerCode: data.staffelfuehrerCode
  };
  window.history.pushState({}, '', `/leitstelle/${data.adminCode}`);
};

const handleJoined = async (code: string, name: string) => {
  try {
    const response = await axios.get(`/status?code=${code}&name=${name}`, {
      maxRedirects: 0,
      validateStatus: (status) => status >= 200 && status < 400
    });

    const responseData = response as any;
    const locationStr = (response.headers.location || (responseData.request && responseData.request.responseURL)) as string;

    if (locationStr) {
      const url = new URL(locationStr, window.location.origin);
      if (url.pathname.startsWith('/staffelfuehrer/')) {
        const sfCode = url.pathname.split('/').pop()!;
        const info = await axios.get(`/api/staffelfuehrer_info/${sfCode}`);
        currentView.value = {type: 'staffelfuehrer', sfCode, name: info.data.name};
        window.history.pushState({}, '', `/staffelfuehrer/${sfCode}`);
      } else if (url.pathname === '/status') {
        const info = await axios.get(`/api/status_info?code=${code}&name=${name}`);
        currentView.value = {
          type: 'status',
          code,
          name,
          leitstelleName: info.data.leitstelle_name
        };
        window.history.pushState({}, '', `/status?code=${code}&name=${encodeURIComponent(name)}`);
      }
    }
  } catch (e) {
    console.error(e);
  }
};

onMounted(async () => {
  const path = window.location.pathname;
  const params = new URLSearchParams(window.location.search);

  if (path === '/') {
    currentView.value = {type: 'landing'};
  } else if (path.startsWith('/leitstelle/')) {
    const adminCode = path.split('/').pop()!;
    try {
      const response = await axios.get(`/api/leitstelle_info/${adminCode}`);
      if (response.data.status === 'success') {
        currentView.value = {
          type: 'leitstelle',
          adminCode,
          leitstelleName: response.data.name,
          vehicleCode: response.data.vehicle_code,
          staffelfuehrerCode: response.data.staffelfuehrer_code
        };
      }
    } catch (e) {
      currentView.value = {type: 'landing'};
    }
  } else if (path.startsWith('/staffelfuehrer/')) {
    const sfCode = path.split('/').pop()!;
    try {
      const response = await axios.get(`/api/staffelfuehrer_info/${sfCode}`);
      if (response.data.status === 'success') {
        currentView.value = {type: 'staffelfuehrer', sfCode, name: response.data.name};
      }
    } catch (e) {
      currentView.value = {type: 'landing'};
    }
  } else if (path === '/status') {
    const code = params.get('code');
    const name = params.get('name');
    if (code && name) {
      try {
        const response = await axios.get(`/api/status_info?code=${code}&name=${name}`);
        if (response.data.status === 'success') {
          currentView.value = {type: 'status', code, name, leitstelleName: response.data.leitstelle_name};
        }
      } catch (e) {
        currentView.value = {type: 'landing'};
      }
    }
  }
});
</script>

<template>
  <LandingPage v-if="currentView.type === 'landing'" @created="handleCreated" @joined="handleJoined"/>
  <LeitstelleView v-else-if="currentView.type === 'leitstelle'" v-bind="currentView"/>
  <StatusView v-else-if="currentView.type === 'status'" v-bind="currentView"/>
  <StaffelfuehrerView v-else-if="currentView.type === 'staffelfuehrer'" v-bind="currentView"/>
</template>
