import { createRouter, createWebHistory } from 'vue-router'
import LandingView from '../views/LandingView.vue'
import LoginView from '../views/LoginView.vue'
import HomeView from '../views/HomeView.vue'
import PublicationsView from '../views/PublicationsView.vue'
import UploadView from '../views/UploadView.vue'
import JournalsView from '../views/JournalsView.vue'
import ResearchersView from '../views/ResearchersView.vue'
import StudentsView from '../views/StudentsView.vue'
import CollaborationMapView from '../views/CollaborationMapView.vue'
import GanttView from '../views/GanttView.vue'
import MyTasksView from '../views/MyTasksView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: LandingView,
      meta: { public: true },
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { public: true },
    },
    {
      path: '/map',
      name: 'map',
      component: HomeView,
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
    {
      path: '/journals',
      name: 'journals',
      component: JournalsView,
    },
    {
      path: '/researchers',
      name: 'researchers',
      component: ResearchersView,
    },
    {
      path: '/students',
      name: 'students',
      component: StudentsView,
    },
    {
      path: '/collaboration-map',
      name: 'collaboration-map',
      component: CollaborationMapView,
    },
    {
      path: '/gantt',
      name: 'gantt',
      component: GanttView,
    },
    {
      path: '/my-tasks',
      name: 'my-tasks',
      component: MyTasksView,
    },
  ],
})

router.beforeEach((to) => {
  const token = localStorage.getItem('cecan_token')
  if (!to.meta.public && !token) {
    return { name: 'login' }
  }
})

export default router
