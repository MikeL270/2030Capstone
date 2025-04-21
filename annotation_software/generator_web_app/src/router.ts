import { createRouter, createWebHistory } from 'vue-router';


const router = createRouter({
  history: createWebHistory(),
  routes: [
    { 
      path: '/', 
      name: 'home', 
      component: () =>  import('./components/pages/Home.vue'),
    },
    { 
      path: '/profile', 
      name: 'profile', 
      component: () => import('./components/pages/Profile.vue'), 
    },
    { 
      path: '/annotate', 
      name: 'annotate', 
      component: () => import('./components/pages/Annotate.vue'),
    },
    { 
      path: '/settings', 
      name: 'settings', 
      component: () => import('./components/pages/Settings.vue'),
    },
    { 
      path: '/statistics', 
      name: 'statistics', 
      component: () => import('./components/pages/Statistics.vue'),
    },
    { 
      path: '/api-tester', 
      name: 'api-tester', 
      component: () => import('./components/pages/api_tester/ApiTesterMain.vue'),
    }
  ],
});

export default router;