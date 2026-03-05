import { createRouter, createWebHistory } from 'vue-router'
import PublicationsView from '../views/PublicationsView.vue'
import UploadView from '../views/UploadView.vue'
import JournalsView from '../views/JournalsView.vue'
import ResearchersView from '../views/ResearchersView.vue'
import StudentsView from '../views/StudentsView.vue'
import ProjectsView from '../views/ProjectsView.vue'

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
      path: '/projects',
      name: 'projects',
      component: ProjectsView,
    },
  ],
})

export default router
