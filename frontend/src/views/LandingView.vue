<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import {
  Upload, BookOpen, BookMarked, Users, GraduationCap,
  Network, GanttChartSquare, ClipboardList, Globe, FlaskConical,
  ArrowRight,
} from 'lucide-vue-next'
import { publicationsApi, researchersApi, projectsApi } from '@/services/api'

const stats = ref({ publications: 0, researchers: 0, projects: 0 })

onMounted(async () => {
  try {
    const [pubs, res, proj] = await Promise.all([
      publicationsApi.getAll(),
      researchersApi.search({ limit: 1 }),
      projectsApi.search({ limit: 1 }),
    ])
    stats.value = {
      publications: pubs.length,
      researchers: res.total ?? 0,
      projects: proj.total ?? 0,
    }
  } catch {
    // stats quedan en 0 si falla, no es crítico
  }
})

const sections = [
  {
    to: '/upload',
    icon: Upload,
    color: 'bg-blue-500',
    light: 'bg-blue-50',
    text: 'text-blue-600',
    label: 'Subir PDF',
    description: 'Sube un paper PDF y extraemos automáticamente el DOI, cuartil JCR, Impact Factor y percentil.',
  },
  {
    to: '/publications',
    icon: BookOpen,
    color: 'bg-indigo-500',
    light: 'bg-indigo-50',
    text: 'text-indigo-600',
    label: 'Publicaciones',
    description: 'Tabla completa con métricas JCR, filtros por cuartil y año, y exportación de datos.',
  },
  {
    to: '/gantt',
    icon: GanttChartSquare,
    color: 'bg-violet-500',
    light: 'bg-violet-50',
    text: 'text-violet-600',
    label: 'Planificación',
    description: 'Gantt interactivo con drag & drop, dependencias entre tareas y asignaciones RACI.',
  },
  {
    to: '/map',
    icon: Globe,
    color: 'bg-cyan-500',
    light: 'bg-cyan-50',
    text: 'text-cyan-600',
    label: 'Mapa 3D',
    description: 'Visualización espacial 3D de publicaciones agrupadas por cluster temático.',
  },
  {
    to: '/researchers',
    icon: Users,
    color: 'bg-emerald-500',
    light: 'bg-emerald-50',
    text: 'text-emerald-600',
    label: 'Investigadores',
    description: 'Directorio de investigadores con índice H, citas totales y perfil ORCID.',
  },
  {
    to: '/students',
    icon: GraduationCap,
    color: 'bg-amber-500',
    light: 'bg-amber-50',
    text: 'text-amber-600',
    label: 'Estudiantes',
    description: 'Tesistas y estudiantes de postgrado: programas, tutores y fechas de graduación.',
  },
  {
    to: '/journals',
    icon: BookMarked,
    color: 'bg-rose-500',
    light: 'bg-rose-50',
    text: 'text-rose-600',
    label: 'Revistas JCR',
    description: 'Busca entre 35.000+ revistas científicas con cuartil, Impact Factor y percentil JIF.',
  },
  {
    to: '/collaboration-map',
    icon: Network,
    color: 'bg-orange-500',
    light: 'bg-orange-50',
    text: 'text-orange-600',
    label: 'Colaboración',
    description: 'Grafo de redes de colaboración entre investigadores, proyectos y work packages.',
  },
  {
    to: '/my-tasks',
    icon: ClipboardList,
    color: 'bg-teal-500',
    light: 'bg-teal-50',
    text: 'text-teal-600',
    label: 'Mis Tareas',
    description: 'Actividades asignadas a ti mediante la matriz de responsabilidades RACI.',
  },
]
</script>

<template>
  <div class="min-h-full bg-gray-50">

    <!-- Hero -->
    <div class="bg-white border-b border-gray-100">
      <div class="max-w-5xl mx-auto px-6 py-12 md:py-16">
        <div class="flex items-center gap-3 mb-5">
          <div class="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center shadow-sm">
            <FlaskConical class="w-5 h-5 text-white" />
          </div>
          <span class="text-sm font-semibold text-blue-600 tracking-widest uppercase">Plataforma CECAN</span>
        </div>

        <h1 class="text-3xl md:text-4xl font-bold text-gray-900 leading-tight mb-3">
          Gestión inteligente de<br class="hidden md:block" />
          investigación científica
        </h1>
        <p class="text-gray-500 text-base md:text-lg max-w-xl mb-8">
          Sube publicaciones, planifica proyectos, visualiza colaboraciones y accede a métricas JCR en un solo lugar.
        </p>

        <!-- Stats -->
        <div class="flex flex-wrap gap-6">
          <div class="flex items-baseline gap-1.5">
            <span class="text-2xl font-bold text-gray-900">{{ stats.publications }}</span>
            <span class="text-sm text-gray-500">publicaciones</span>
          </div>
          <div class="w-px h-6 bg-gray-200 self-center hidden sm:block" />
          <div class="flex items-baseline gap-1.5">
            <span class="text-2xl font-bold text-gray-900">{{ stats.researchers }}</span>
            <span class="text-sm text-gray-500">investigadores</span>
          </div>
          <div class="w-px h-6 bg-gray-200 self-center hidden sm:block" />
          <div class="flex items-baseline gap-1.5">
            <span class="text-2xl font-bold text-gray-900">{{ stats.projects }}</span>
            <span class="text-sm text-gray-500">proyectos</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Cards grid -->
    <div class="max-w-5xl mx-auto px-6 py-10">
      <h2 class="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-5">Módulos disponibles</h2>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <RouterLink
          v-for="s in sections"
          :key="s.to"
          :to="s.to"
          class="group bg-white rounded-2xl border border-gray-100 p-5 hover:border-gray-200 hover:shadow-md transition-all duration-200 flex flex-col gap-3"
        >
          <!-- Ícono -->
          <div class="flex items-center justify-between">
            <div :class="['w-10 h-10 rounded-xl flex items-center justify-center', s.light]">
              <component :is="s.icon" :class="['w-5 h-5', s.text]" />
            </div>
            <ArrowRight
              class="w-4 h-4 text-gray-300 group-hover:text-gray-500 group-hover:translate-x-0.5 transition-all duration-200"
            />
          </div>

          <!-- Texto -->
          <div>
            <h3 class="text-sm font-semibold text-gray-900 mb-1">{{ s.label }}</h3>
            <p class="text-xs text-gray-500 leading-relaxed">{{ s.description }}</p>
          </div>
        </RouterLink>
      </div>
    </div>

  </div>
</template>
