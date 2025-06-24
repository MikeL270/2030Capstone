import { createRouter, createWebHistory } from 'vue-router';
import Authenticate  from '@/components/Authenticate.vue';
import { useUserStore } from '@/modules/userManagement';


const router = createRouter({
  history: createWebHistory(),
  routes: [
    
     { 
      path: '/authenticate', 
      name: 'authenticator', 
      component: Authenticate, 
      meta: {requiresNoLayout: true},
    },
    { 
      path: '/', 
      name: 'Dashboard', 
      component: () => import('./components/pages/Dashboard.vue'),
      meta: {
        requiresAuth: true,
        requiresNoLayout: false,
      },
    },
    { 
      path: '/profile', 
      name: 'profile', 
      component: () => import('./components/pages/Profile.vue'), 
      meta: {
        requiresAuth: true,
        requiresNoLayout: false,
      },
    },
    { 
      path: '/auto-cropper', 
      name: 'Auto-Cropper', 
      component: () => import('./components/pages/Auto-Cropper.vue'),
      meta: {
        requiresAuth: true,
        requiresNoLayout: false,
      },
    },
    { 
      path: '/settings', 
      name: 'settings', 
      component: () => import('./components/pages/Settings.vue'),
      meta: {
        requiresAuth: true,
        requiresNoLayout: false,
      },
    },
    { 
      path: '/statistics', 
      name: 'statistics', 
      component: () => import('./components/pages/Statistics.vue'),
      meta: {
        requiresAuth: true,
        requiresNoLayout: false,
      },
    },
    { 
      path: '/api-tester', 
      name: 'api-tester', 
      component: () => import('./components/pages/api_tester/ApiTesterMain.vue'),
      meta: {
        requiresAuth: true,
        requiresNoLayout: false
      },
    }
  ],
});

router.beforeEach(async (to, from, next) => { 
  const user_store = useUserStore();

  if (to.meta.requiresAuth) {
    
    if (user_store.logged_in) {
      next();
    } else {
      await user_store.check_auth();
      if (await user_store.check_auth()) {
          next();
      } else {
        next({
          name: 'authenticator',
          query: { redirect: to.fullPath },
        });
      }
    }
    
  } else {
    next()
  }
 });


export default router;