import './assets/main.css';
import 'vue-toastification/dist/index.css';
import { createApp } from 'vue';
import { createPinia } from 'pinia'; 
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'; 
import App from './App.vue';
import router from './router' ;
import { Icon } from '@iconify/vue';
import Toast from 'vue-toastification';
import { POSITION, type PluginOptions } from 'vue-toastification';

const pinia = createPinia()
pinia.use(piniaPluginPersistedstate)
const app = createApp(App);

app.use(pinia);
app.use(router);

await router.isReady();

const options: PluginOptions = {
    position: POSITION.BOTTOM_RIGHT,
    transition: "Vue-Toastification__bounce",
    maxToasts: 5,
    newestOnTop: true
};

app.use(Toast, options);

app.component('Icon', Icon);

app.mount('#app');