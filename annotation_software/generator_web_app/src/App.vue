<script setup lang="ts">
import Header from './components/Header.vue'
import Menu from './components/Menu.vue'
import { RouterView, useRoute } from 'vue-router'

const route = useRoute();
</script>

<template>
  <header>
    <Header />
  </header>

  <main>
    <Menu v-if="!route.meta.requiresNoLayout" />
      <RouterView />
  </main>


</template>

<style scoped>

header {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  position: absolute;
  width: 100%;
  height: 7vh;
  top: 0;
  left: 0;
  padding-right: calc(var(--section-gap) / 2);
  color: rgb(255, 255, 255);
  background-color: var(--wygf-bg-blue);
  border-bottom: 1px solid var(--color-border);
  padding: 1%;
  box-shadow: 0 4px 6px 2px var(--color-background-soft);
}

main {
  position: absolute;
  bottom: 0;
  left: 0;
  display: flex;
  justify-content: flex-start;
  height: 93vh;
  width: 100%;
  max-width: 100%;
  overflow: hidden;

}



</style>
