import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  { path: '/login', component: () => import('@/views/Login.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    redirect: '/workspaces',
    children: [
      { path: 'workspaces', component: () => import('@/views/Workspaces.vue'), name: 'workspaces' },
      { path: 'tasks', component: () => import('@/views/Tasks.vue'), name: 'tasks' },
      { path: 'agents', component: () => import('@/views/Agents.vue'), name: 'agents' },
      { path: 'conversations', component: () => import('@/views/Conversations.vue'), name: 'conversations' },
      { path: 'knowledge', component: () => import('@/views/Knowledge.vue'), name: 'knowledge' },
      { path: 'profile', component: () => import('@/views/Profile.vue'), name: 'profile' },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isLoggedIn) {
    return '/login'
  }
  if (to.path === '/login' && auth.isLoggedIn) {
    return '/'
  }
})

export default router
