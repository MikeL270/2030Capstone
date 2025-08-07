import { createRouter, createWebHistory } from 'vue-router';
import Authenticate  from '@/components/Authenticate.vue';
import { useUserStore } from '@/modules/stores/userStore';


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
      path: '/user/:uuid', 
      name: 'user', 
      component: () => import('./components/pages/User.vue'), 
      meta: {
        requiresAuth: true,
        requiresNoLayout: false,
      },
    },
    { 
      path: '/auto-cropper/:projects?/:uuid?', 
      name: 'auto-cropper', 
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
      path: '/upload/:project?/:uuid?',
      name: 'upload',
      component: () => import('./components/pages/Uploader.vue'),
      meta: {
        requiresAuth: true,
        requiresNoLayout: false,
      }
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
      if (user_store.logged_in) {
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