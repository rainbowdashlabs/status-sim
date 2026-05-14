<script setup lang="ts">
import { useTheme } from '../composables/useTheme'

const currentYear = new Date().getFullYear()
const { isLight, toggle } = useTheme()
</script>

<template>
  <footer class="mt-10 py-5 text-center border-t border-themed text-themed-faint text-sm">
    <p class="my-1">
      <a href="/hilfe" target="_blank" class="text-themed-muted no-underline transition-colors hover:text-primary hover:underline">Hilfe</a>
      |
      <a href="https://github.com/rainbowdashlabs/status-sim" target="_blank" class="text-themed-muted no-underline transition-colors hover:text-primary hover:underline">GitHub</a>
      |
      <button @click="toggle" class="text-themed-muted hover:text-primary transition-colors">
        {{ isLight ? 'Dark Mode' : 'Light Mode' }}
      </button>
    </p>
    <p class="my-1">&copy; {{ currentYear }} Rainbowdashlabs and Contributor GPL-3.0</p>
  </footer>
</template>
