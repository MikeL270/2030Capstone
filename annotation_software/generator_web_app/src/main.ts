import './assets/main.css';
import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import router from './router' ;
import { Icon } from '@iconify/vue';

const pinia = createPinia()
const app = createApp(App);

app.use(pinia);
app.use(router);

await router.isReady();

app.component('Icon', Icon);

app.mount('#app');