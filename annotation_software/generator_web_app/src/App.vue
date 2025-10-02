<script setup lang="ts">
import Header from './components/Header.vue'
import Menu from './components/Menu.vue'
import { RouterView } from 'vue-router'
import { useUserStore } from './modules/stores/userStore';
import { usePreferenceStore } from './modules/stores/preferencesStore';

// Do this first
const user_store = useUserStore();
if (user_store.user == undefined) user_store.get_current_user();

const pref_store = usePreferenceStore();

if (pref_store.first_login) {
	pref_store.getBrowserPreference();
	pref_store.first_login = false; 
} else {
	pref_store.setTheme(pref_store.theme);
}

</script>

<template>
  <Header />
  <main>
    <Menu v-if="!$route.meta.requiresNoLayout" />
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
    height: 95.5vh;
    width: 100%;
	max-width: 100%;
    max-width: 100%;
    overflow: none;
  }
</style>
