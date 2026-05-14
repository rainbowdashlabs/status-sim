import { ref, watchEffect } from 'vue'

const isLight = ref(localStorage.getItem('theme') === 'light')

watchEffect(() => {
  document.documentElement.classList.toggle('light', isLight.value)
  localStorage.setItem('theme', isLight.value ? 'light' : 'dark')
})

export function useTheme() {
  const toggle = () => { isLight.value = !isLight.value }
  return { isLight, toggle }
}
