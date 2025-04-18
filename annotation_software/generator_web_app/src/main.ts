import './assets/main.css'
import { createApp } from 'vue'
import App from './App.vue'
import router from './router' // Import your router instance

const app = createApp(App)

app.use(router) // Install the router plugin

app.mount('#app')