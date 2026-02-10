<script setup lang="ts">
const props = defineProps<{
  status?: string | null;
  special?: string | null;
  lastPressed?: string | null;
}>();

const emit = defineEmits<{
  (e: 'press', key: string): void;
}>();

const keys = ['1','2','3','4','5','6','7','8','9'];

const pressKey = (key: string) => {
  emit('press', key);
};

const keyClass = (key: string) => [
  (props.status === key || props.special === key || (props.lastPressed === key && props.status !== key && props.special !== key))
    ? ''
    : 'bg-[#333] border-[#444] text-[#bbb] hover:bg-[#444] hover:border-[#666]',
  {
    'bg-success text-white border-success shadow-[0_0_20px_rgba(46,125,50,0.5)] hover:bg-success hover:border-success': props.status === key,
    'bg-accent text-black border-accent shadow-[0_0_20px_rgba(255,152,0,0.5)] hover:bg-accent hover:border-accent': props.special === key,
    'bg-primary text-white border-primary shadow-[0_0_20px_rgba(33,150,243,0.45)] hover:bg-primary hover:border-primary': props.lastPressed === key && props.status !== key && props.special !== key
  }
];
</script>

<template>
  <div class="grid grid-cols-3 gap-2.5 mx-auto w-full max-w-[300px] mb-4">
    <div v-for="n in keys" :key="n"
         @click="pressKey(n)"
         class="aspect-square flex flex-col items-center justify-center text-lg font-extrabold rounded-xl border-2 cursor-pointer transition-all"
         :class="keyClass(n)"
    >
      {{ n }}
    </div>
    <div class="aspect-square flex items-center justify-center text-lg font-extrabold rounded-xl border-2 bg-[#333] border-[#444] text-[#bbb]">*</div>
    <div
      @click="pressKey('0')"
      class="aspect-square flex flex-col items-center justify-center text-lg font-extrabold rounded-xl border-2 cursor-pointer transition-all"
      :class="keyClass('0')"
    >
      0
    </div>
    <div class="aspect-square flex items-center justify-center text-lg font-extrabold rounded-xl border-2 bg-[#333] border-[#444] text-[#bbb]">#</div>
  </div>
</template>