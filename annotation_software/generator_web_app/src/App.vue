<script setup lang="ts">
import Header from './components/Header.vue'
import Menu from './components/Menu.vue'
import { RouterView, useRoute } from 'vue-router'

const route = useRoute();
</script>

<template>
  <Header />
  <main>
    <Menu v-if="!route.meta.requiresNoLayout" />
      <RouterView />
  </main>
</template>

<style scoped>
  main {
    position: absolute;
    bottom: 0;
    left: 0;
    display: flex;
    justify-content: flex-start;
    height: 92vh;
    width: 100%;
    max-width: 100%;
    overflow: hidden;
  }
</style>
