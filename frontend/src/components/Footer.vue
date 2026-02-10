<script setup lang="ts">
const currentYear = new Date().getFullYear();
</script>

<template>
  <footer class="mt-10 py-5 text-center border-t border-gray-800 text-gray-500 text-sm">
    <p class="my-1">
      Made with ❤️ and 🏳️‍🌈 | 
      <a href="https://github.com/rainbowdashlabs/status-sim" target="_blank" class="text-gray-400 no-underline transition-colors hover:text-primary hover:underline">GitHub</a>
    </p>
    <p class="my-1">&copy; {{ currentYear }} Rainbowdashlabs and Contributor GPL-3.0</p>
  </footer>
</template>
