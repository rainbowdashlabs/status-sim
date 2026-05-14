<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'
import Footer from './components/Footer.vue'

const emit = defineEmits<{
  (e: 'created', data: { adminCode: string, name: string, vehicleCode: string, staffelfuehrerCode: string }): void
  (e: 'joined', code: string, name: string): void
}>()

const leitstelleName = ref('Florian Berlin')
const joinCode = ref('')
const userName = ref('')
const errorMessage = ref(false)

const generateRandomFunkrufname = () => {
  let num
  do {
    num = Math.floor(Math.random() * (65 - 10 + 1)) + 10
  } while (num % 10 === 0)
  return `LHF ${num}00/1`
}

onMounted(() => {
  document.title = 'Funk Simulator'
  userName.value = generateRandomFunkrufname()

  const urlParams = new URLSearchParams(window.location.search)
  if (urlParams.get('error') === 'name_taken') {
    errorMessage.value = true
    if (urlParams.has('code')) joinCode.value = urlParams.get('code') || ''
  }
})

const createLeitstelle = async () => {
  try {
    const { data } = await axios.post('/leitstelle', { name: leitstelleName.value })
    if (data.status === 'success') {
      emit('created', {
        adminCode: data.admin_code,
        name: leitstelleName.value,
        vehicleCode: data.vehicle_code,
        staffelfuehrerCode: data.staffelfuehrer_code,
      })
    }
  } catch (error) {
    console.error(error)
  }
}

const joinLeitstelle = () => {
  if (joinCode.value && userName.value) {
    emit('joined', joinCode.value.toUpperCase(), userName.value)
  }
}
</script>

<template>
  <div class="page">
    <div class="flex-1">
      <h1 class="section-title text-2xl mb-2 text-center">Funk Simulator</h1>
      <p class="text-center text-themed-muted text-sm mb-8">
        Neu hier? <a href="/hilfe" target="_blank" class="text-primary hover:underline font-bold">Hilfe & Anleitung</a>
      </p>

      <div class="card p-5 mb-8 max-w-md mx-auto">
        <h2 class="section-title text-lg mb-5">Neue Leitstelle erstellen</h2>
        <form @submit.prevent="createLeitstelle">
          <div class="mb-4">
            <label for="leitstelleName" class="label">Name der Leitstelle:</label>
            <input v-model="leitstelleName" type="text" id="leitstelleName" required class="input">
          </div>
          <button type="submit" class="btn btn-primary btn-press w-full p-3">Erstellen</button>
        </form>
      </div>

      <div class="card p-5 max-w-md mx-auto">
        <h2 class="section-title text-lg mb-5">Einer Leitstelle beitreten</h2>
        <form @submit.prevent="joinLeitstelle">
          <div class="mb-4">
            <label for="joinCode" class="label">Leitstellen-Code:</label>
            <input v-model="joinCode" type="text" id="joinCode" required class="input focus:border-success">
          </div>
          <div class="mb-4">
            <label for="userName" class="label">Name (Funkrufname):</label>
            <input v-model="userName" type="text" id="userName" required class="input focus:border-success">
            <div v-if="errorMessage" class="text-danger text-xs mt-1 font-bold">
              Name bereits vergeben. Ein neuer Name wurde generiert.
            </div>
          </div>
          <button type="submit" class="btn btn-success btn-press w-full p-3">Beitreten</button>
        </form>
      </div>
    </div>

    <Footer />
  </div>
</template>
