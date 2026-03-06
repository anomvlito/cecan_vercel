import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import PublicationsView from '../views/PublicationsView.vue'
import UploadView from '../views/UploadView.vue'
import JournalsView from '../views/JournalsView.vue'
import ResearchersView from '../views/ResearchersView.vue'
import StudentsView from '../views/StudentsView.vue'
import ProjectsView from '../views/ProjectsView.vue'
import CollaborationMapView from '../views/CollaborationMapView.vue'
import GanttView from '../views/GanttView.vue'
import MyTasksView from '../views/MyTasksView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
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
      path: '/projects',
      name: 'projects',
      component: ProjectsView,
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

export default router
