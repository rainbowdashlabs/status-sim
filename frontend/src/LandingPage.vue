<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import Footer from './components/Footer.vue';

const emit = defineEmits<{
  (e: 'created', data: { adminCode: string, name: string, vehicleCode: string, staffelfuehrerCode: string }): void;
  (e: 'joined', code: string, name: string): void;
}>();

const leitstelleName = ref('Florian Berlin');
const joinCode = ref('');
const userName = ref('');
const errorMessage = ref(false);

const generateRandomFunkrufname = () => {
  let num;
  do {
    num = Math.floor(Math.random() * (65 - 10 + 1)) + 10;
  } while (num % 10 === 0);
  return `LHF ${num}00/1`;
};

onMounted(() => {
  document.title = 'Funk Simulator';
  userName.value = generateRandomFunkrufname();
  
  const urlParams = new URLSearchParams(window.location.search);
  if (urlParams.has('error') && urlParams.get('error') === 'name_taken') {
    errorMessage.value = true;
    if (urlParams.has('code')) {
      joinCode.value = urlParams.get('code') || '';
    }
  }
});

const createLeitstelle = async () => {
  try {
    const response = await axios.post('/leitstelle', {
      name: leitstelleName.value
    });
    if (response.data.status === 'success') {
      emit('created', {
        adminCode: response.data.admin_code,
        name: leitstelleName.value,
        vehicleCode: response.data.vehicle_code,
        staffelfuehrerCode: response.data.staffelfuehrer_code
      });
    } else {
      alert('Fehler beim Erstellen der Leitstelle');
    }
  } catch (error) {
    console.error(error);
    alert('Fehler beim Erstellen der Leitstelle');
  }
};

const joinLeitstelle = () => {
  if (joinCode.value && userName.value) {
    emit('joined', joinCode.value.toUpperCase(), userName.value);
  }
};
</script>

<template>
  <div class="max-w-[1200px] min-w-[320px] mx-auto p-5 flex flex-col min-h-screen">
    <div class="flex-1">
      <h1 class="text-primary uppercase tracking-widest text-2xl mb-8 text-center font-bold">Funk Simulator</h1>

      <div class="bg-card rounded-lg p-5 mb-8 shadow-lg border border-gray-800 max-w-md mx-auto">
        <h2 class="text-primary uppercase tracking-widest text-lg mb-5 font-bold">Neue Leitstelle erstellen</h2>
        <form @submit.prevent="createLeitstelle">
          <div class="mb-4">
            <label for="leitstelleName" class="block mb-1 font-bold text-gray-400 text-sm">Name der Leitstelle:</label>
            <input 
              v-model="leitstelleName" 
              type="text" 
              id="leitstelleName" 
              required
              class="p-3 border border-gray-700 bg-gray-800 text-white rounded w-full outline-none focus:border-primary"
            >
          </div>
          <button 
            type="submit" 
            class="w-full bg-primary text-white p-3 rounded font-bold transition-all hover:brightness-110 active:translate-y-0.5"
          >
            Erstellen
          </button>
        </form>
      </div>

      <div class="bg-card rounded-lg p-5 shadow-lg border border-gray-800 max-w-md mx-auto">
        <h2 class="text-primary uppercase tracking-widest text-lg mb-5 font-bold">Einer Leitstelle beitreten</h2>
        
        <form @submit.prevent="joinLeitstelle">
          <div class="mb-4">
            <label for="joinCode" class="block mb-1 font-bold text-gray-400 text-sm">Leitstellen-Code:</label>
            <input 
              v-model="joinCode" 
              type="text" 
              id="joinCode" 
              required
              class="p-3 border border-gray-700 bg-gray-800 text-white rounded w-full outline-none focus:border-success"
            >
          </div>
          
          <div class="mb-4">
            <label for="userName" class="block mb-1 font-bold text-gray-400 text-sm">Name (Funkrufname):</label>
            <input 
              v-model="userName" 
              type="text" 
              id="userName" 
              required
              class="p-3 border border-gray-700 bg-gray-800 text-white rounded w-full outline-none focus:border-success"
            >
            <div v-if="errorMessage" class="text-danger text-[0.8rem] mt-1 font-bold">
              Name bereits vergeben. Ein neuer Name wurde generiert.
            </div>
          </div>
          
          <button 
            type="submit" 
            class="w-full bg-success text-white p-3 rounded font-bold transition-all hover:brightness-110 active:translate-y-0.5"
          >
            Beitreten
          </button>
        </form>
      </div>
    </div>

    <Footer />
  </div>
</template>
