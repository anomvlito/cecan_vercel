import { createRouter, createWebHistory } from 'vue-router'
import PublicationsView from '../views/PublicationsView.vue'
import UploadView from '../views/UploadView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      redirect: '/publications',
    },
    {
      path: '/publications',
      name: 'publications',
      component: PublicationsView,
    },
    {
      path: '/upload',
      name: 'upload',
      component: UploadView,
    },
  ],
})

export default router
