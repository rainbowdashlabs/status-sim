<script setup lang="ts">
import { ref } from 'vue';

const props = defineProps<{
  code: string;
  label?: string;
  successClass?: string;
}>();

const copied = ref(false);
const visible = ref(false);

const showCopied = () => {
  copied.value = true;
  setTimeout(() => {
    copied.value = false;
  }, 1000);
};

const copyToClipboard = async () => {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(props.code);
      showCopied();
      return;
    }
  } catch (e) {
    // fall through to legacy fallback
  }

  const textarea = document.createElement('textarea');
  textarea.value = props.code;
  textarea.setAttribute('readonly', '');
  textarea.style.position = 'absolute';
  textarea.style.left = '-9999px';
  document.body.appendChild(textarea);
  textarea.select();
  const success = document.execCommand('copy');
  document.body.removeChild(textarea);
  if (success) {
    showCopied();
  }
};
</script>

<template>
  <div class="text-center">
    <label v-if="label" class="block mb-0.5 font-bold text-gray-400 text-[0.7rem] uppercase">{{ label }}</label>
    <div 
      class="relative overflow-visible font-mono font-bold p-1.5 px-2.5 rounded border border-gray-800 cursor-pointer select-none transition-all hover:border-gray-600 bg-black text-lg"
      :class="[
        visible ? (successClass || 'text-primary') : 'text-transparent',
        copied ? 'after:content-[\'Kopiert!\'] after:absolute after:bg-success after:text-white after:text-[0.7rem] after:px-1.5 after:py-0.5 after:rounded after:-top-6 after:left-1/2 after:-translate-x-1/2 after:animate-fade-out after:z-10 after:whitespace-nowrap after:pointer-events-none' : ''
      ]"
      :style="{ textShadow: visible ? 'none' : '0 0 8px rgba(255, 255, 255, 0.5)' }"
      title="Klicken zum Kopieren"
      @mousedown="visible = true"
      @mouseleave="visible = false"
      @click="copyToClipboard"
    >
      {{ code }}
    </div>
  </div>
</template>

<style scoped>
@keyframes fade-out {
  0% { opacity: 1; }
  80% { opacity: 1; }
  100% { opacity: 0; }
}

.animate-fade-out {
  animation: fade-out 1s forwards;
}
</style>
