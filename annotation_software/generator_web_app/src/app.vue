<script lang="ts">
import { defineComponent } from 'vue';
import Header from './components/header.vue'
import Menu from './components/menu.vue'
import { RouterView } from 'vue-router'
import { useUserStore } from './modules/stores/userStore';
import { usePreferenceStore } from './modules/stores/preferencesStore';

export default defineComponent({
  name: 'App',
  components: {
    RouterView,
    Header,
    Menu
  },
  setup() {
    const user_store = useUserStore();
    const pref_store = usePreferenceStore();
    if (pref_store.first_login) {
      pref_store.getBrowserPreference();
      pref_store.first_login = false; 
    } else {
      pref_store.setTheme(pref_store.theme);
    }
    return { user_store, pref_store }
  },
  async mounted() {
    if (this.user_store.logged_in) {
      await this.user_store.getCurrentUser()
    }
  }
})
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
