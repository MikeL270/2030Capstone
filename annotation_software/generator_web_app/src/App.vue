<script setup lang="ts">
import Header from './components/Header.vue'
import Menu from './components/Menu.vue'
import { RouterView} from 'vue-router'
</script>

<template>
  <header>
    <Header />
  </header>

  <main>
    <Menu />
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
  height: 10vh;
  top: 0;
  left: 0;
  padding-right: calc(var(--section-gap) / 2);
  color: rgb(255, 255, 255);
  background-color: var(--wygf-bg-blue);
  border-bottom: 1px solid var(--vt-c-black-mute);
  padding: 1%;
  box-shadow: 0 4px 6px 2px rgba(0,0,0,0.25);
}

main {
  position: absolute;
  bottom: 0;
  left: 0;
  display: flex;
  justify-content: flex-start;
  height: 90vh;
  width: 100vw;
}

</style>
