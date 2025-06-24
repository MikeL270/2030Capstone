import './assets/main.css';
import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';
import router from './router' ;
import { Icon } from '@iconify/vue';
import Toast from 'vue-toastification';
import { POSITION, type PluginOptions } from 'vue-toastification';
import 'vue-toastification/dist/index.css';

const pinia = createPinia()
const app = createApp(App);

app.use(pinia);
app.use(router);

await router.isReady();

const options: PluginOptions = {
    position: POSITION.BOTTOM_RIGHT,
    transition: "Vue-Toastification__bounce",
    maxToasts: 1,
    newestOnTop: true
};

app.use(Toast, options);

app.component('Icon', Icon);

app.mount('#app');