import { createRouter, createWebHistory } from 'vue-router';
import HomeView from './components/pages/Home.vue';
import ProfileView from './components/pages/Profile.vue'


const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: HomeView },
    {path: '/profile', name: 'profile', component: ProfileView}
  ],
});

export default router;