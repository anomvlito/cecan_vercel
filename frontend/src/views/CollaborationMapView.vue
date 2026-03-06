<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { Network, type Node, type Edge } from 'vis-network'
import { DataSet } from 'vis-data'
import { Network as NetworkIcon, X, Users, FolderOpen, BookOpen, Layers } from 'lucide-vue-next'
import api from '@/services/api'

// ─── Types ────────────────────────────────────────────────────────────────────
type GraphNode = Node & {
  group?: string
  data?: Record<string, unknown>
}
type GraphEdge = Edge
interface Stats {
  researchers: number
  wps: number
  projects: number
  nodes_thematic: number
  edges: number
}

// ─── State ────────────────────────────────────────────────────────────────────
const containerRef = ref<HTMLDivElement | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const stats = ref<Stats | null>(null)
const selected = ref<Record<string, unknown> | null>(null)

// Controles de física
const gravity = ref(-800)
const springLength = ref(180)
const showUnconnected = ref(true)

let network: Network | null = null
let allNodes: DataSet<GraphNode>
let allEdges: DataSet<GraphEdge>

// ─── Fetch + init ─────────────────────────────────────────────────────────────
async function init() {
  try {
    const { data } = await api.get('/graph/data')
    stats.value = data.stats

    allNodes = new DataSet<GraphNode>(data.nodes)
    allEdges = new DataSet<GraphEdge>(data.edges)

    loading.value = false
    await new Promise(r => setTimeout(r, 30))
    buildNetwork()
  } catch (e) {
    loading.value = false
    error.value = `Error: ${e instanceof Error ? e.message : 'Sin conexión'}`
  }
}

function buildNetwork() {
  if (!containerRef.value) return

  const options = {
    physics: {
      enabled: true,
      solver: 'forceAtlas2Based',
      forceAtlas2Based: {
        gravitationalConstant: gravity.value,
        springLength: springLength.value,
        springConstant: 0.04,
        damping: 0.9,
        avoidOverlap: 0.4,
      },
      stabilization: { iterations: 150, updateInterval: 25 },
    },
    nodes: {
      borderWidth: 1.5,
      shadow: { enabled: true, size: 8, x: 2, y: 2, color: 'rgba(0,0,0,0.25)' },
      font: { face: 'Inter, sans-serif', size: 12, color: '#1e293b' },
    },
    edges: {
      smooth: { enabled: true, type: 'dynamic', roundness: 0.3 },
      arrows: { to: { enabled: false } },
    },
    interaction: {
      hover: true,
      tooltipDelay: 100,
      hideEdgesOnDrag: true,
      navigationButtons: false,
      keyboard: false,
    },
    groups: {
      investigator: {
        shape: 'dot',
        font: { size: 11, color: '#1e293b' },
      },
      wp: {
        shape: 'ellipse',
        font: { size: 16, color: '#ffffff', bold: true },
      },
      nodo: {
        shape: 'box',
        font: { size: 11, color: '#67e8f9' },
      },
      project: {
        shape: 'diamond',
        font: { size: 10, color: '#6ee7b7' },
      },
    },
  }

  network = new Network(
    containerRef.value,
    { nodes: allNodes, edges: allEdges },
    options,
  )

  network.on('click', (params) => {
    if (params.nodes.length > 0) {
      const nodeId = params.nodes[0] as string
      const node = allNodes.get(nodeId) as GraphNode | null
      selected.value = node?.data ?? null
    } else {
      selected.value = null
    }
  })
}

// ─── Controles de física ──────────────────────────────────────────────────────
function applyPhysics() {
  if (!network) return
  network.setOptions({
    physics: {
      forceAtlas2Based: {
        gravitationalConstant: gravity.value,
        springLength: springLength.value,
      },
    },
  })
}

function toggleUnconnected() {
  if (!network || !allNodes) return
  showUnconnected.value = !showUnconnected.value
  const edgeList = allEdges.get()
  const connected = new Set<string>()
  edgeList.forEach(e => {
    if (e.from != null) connected.add(String(e.from))
    if (e.to != null) connected.add(String(e.to))
  })
  const updates = allNodes.get().map((n: GraphNode) => ({
    id: n.id,
    hidden: !showUnconnected.value && !connected.has(String(n.id)),
  }))
  allNodes.update(updates)
}

function fitAll() {
  network?.fit({ animation: { duration: 600, easingFunction: 'easeInOutQuad' } })
}

// ─── Lifecycle ────────────────────────────────────────────────────────────────
onMounted(init)
onUnmounted(() => network?.destroy())

const GROUP_COLORS: Record<string, string> = {
  investigator: '#e2e8f0',
  wp: '#818cf8',
  project: '#6ee7b7',
  nodo: '#67e8f9',
}
</script>

<template>
  <div class="fixed inset-0 md:left-56 bg-slate-950 overflow-hidden flex flex-col">

    <!-- Top bar -->
    <div class="flex items-center justify-between px-4 py-2 bg-slate-900/80 backdrop-blur border-b border-slate-800 flex-shrink-0 z-10">
      <div class="flex items-center gap-2">
        <NetworkIcon class="w-4 h-4 text-indigo-400" />
        <span class="text-sm font-semibold text-white">Mapa de Colaboración</span>
        <div v-if="stats" class="flex items-center gap-3 ml-4 text-xs text-slate-400">
          <span class="flex items-center gap-1"><Users class="w-3 h-3" />{{ stats.researchers }}</span>
          <span class="flex items-center gap-1"><FolderOpen class="w-3 h-3" />{{ stats.projects }}</span>
          <span class="flex items-center gap-1"><Layers class="w-3 h-3" />{{ stats.wps }} WPs</span>
          <span class="flex items-center gap-1"><BookOpen class="w-3 h-3" />{{ stats.nodes_thematic }} nodos</span>
          <span class="text-slate-600">·</span>
          <span>{{ stats.edges }} conexiones</span>
        </div>
      </div>

      <!-- Controles -->
      <div class="flex items-center gap-4">
        <div class="flex items-center gap-2 text-xs text-slate-400">
          <span>Gravedad</span>
          <input type="range" min="-3000" max="-100" step="50" v-model.number="gravity"
            class="w-20 h-1 cursor-pointer" style="accent-color:#818cf8"
            @change="applyPhysics" />
          <span class="w-12 tabular-nums">{{ gravity }}</span>
        </div>
        <div class="flex items-center gap-2 text-xs text-slate-400">
          <span>Distancia</span>
          <input type="range" min="50" max="400" step="10" v-model.number="springLength"
            class="w-20 h-1 cursor-pointer" style="accent-color:#818cf8"
            @change="applyPhysics" />
          <span class="w-8 tabular-nums">{{ springLength }}</span>
        </div>
        <button
          class="px-2 py-1 text-xs rounded border transition-colors"
          :class="showUnconnected ? 'border-slate-600 text-slate-400 hover:border-slate-400' : 'border-indigo-500 text-indigo-400'"
          @click="toggleUnconnected"
        >
          {{ showUnconnected ? 'Ocultar aislados' : 'Mostrar todos' }}
        </button>
        <button class="px-2 py-1 text-xs rounded border border-slate-600 text-slate-400 hover:border-slate-400 transition-colors" @click="fitAll">
          Encuadrar
        </button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <div class="w-8 h-8 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p class="text-indigo-300 text-sm">Construyendo red de colaboración…</p>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="flex-1 flex items-center justify-center">
      <p class="text-red-400 text-sm">{{ error }}</p>
    </div>

    <!-- Grafo -->
    <div v-show="!loading && !error" ref="containerRef" class="flex-1 w-full" />

    <!-- Leyenda -->
    <div class="absolute bottom-4 left-4 z-10 flex flex-col gap-1.5 pointer-events-none">
      <div v-for="(color, group) in GROUP_COLORS" :key="group" class="flex items-center gap-2">
        <span class="w-3 h-3 rounded-full border border-slate-600" :style="{ backgroundColor: color }" />
        <span class="text-xs text-slate-400 capitalize">
          {{ group === 'investigator' ? 'Investigador' : group === 'wp' ? 'Work Package' : group === 'nodo' ? 'Nodo Temático' : 'Proyecto' }}
        </span>
      </div>
    </div>

    <!-- Panel detalle nodo seleccionado -->
    <Transition name="slide">
      <div v-if="selected" class="absolute top-14 right-3 z-20 w-64 bg-slate-900/95 backdrop-blur border border-slate-700 rounded-xl p-4 shadow-2xl">
        <div class="flex items-start justify-between mb-3">
          <span class="text-xs font-semibold px-2 py-0.5 rounded-full" :style="{ backgroundColor: GROUP_COLORS[selected['type'] === 'Investigador' ? 'investigator' : selected['type'] === 'WP' ? 'wp' : selected['type'] === 'Nodo' ? 'nodo' : 'project'] + '33', color: GROUP_COLORS[selected['type'] === 'Investigador' ? 'investigator' : selected['type'] === 'WP' ? 'wp' : selected['type'] === 'Nodo' ? 'nodo' : 'project'] }">
            {{ selected['type'] }}
          </span>
          <button class="text-slate-500 hover:text-slate-300" @click="selected = null">
            <X class="w-4 h-4" />
          </button>
        </div>

        <p class="font-semibold text-white text-sm leading-snug mb-3">{{ selected['name'] }}</p>

        <div class="space-y-1.5 text-xs text-slate-400">
          <div v-if="selected['institution']" class="flex gap-2">
            <span class="text-slate-600 w-20 flex-shrink-0">Institución</span>
            <span class="text-slate-300 truncate">{{ selected['institution'] }}</span>
          </div>
          <div v-if="selected['orcid']" class="flex gap-2">
            <span class="text-slate-600 w-20 flex-shrink-0">ORCID</span>
            <span class="font-mono text-indigo-300 text-xs">{{ selected['orcid'] }}</span>
          </div>
          <div v-if="selected['h_index'] != null" class="flex gap-2">
            <span class="text-slate-600 w-20 flex-shrink-0">H-index</span>
            <span class="font-bold text-blue-400">{{ selected['h_index'] }}</span>
          </div>
          <div v-if="selected['citations'] != null" class="flex gap-2">
            <span class="text-slate-600 w-20 flex-shrink-0">Citas</span>
            <span class="text-slate-300">{{ Number(selected['citations']).toLocaleString('es-CL') }}</span>
          </div>
          <div v-if="selected['works'] != null" class="flex gap-2">
            <span class="text-slate-600 w-20 flex-shrink-0">Obras</span>
            <span class="text-slate-300">{{ selected['works'] }}</span>
          </div>
          <div v-if="selected['category']" class="flex gap-2">
            <span class="text-slate-600 w-20 flex-shrink-0">Categoría</span>
            <span class="text-slate-300">{{ selected['category'] }}</span>
          </div>
          <div v-if="selected['email']" class="flex gap-2">
            <span class="text-slate-600 w-20 flex-shrink-0">Email</span>
            <span class="text-slate-300 truncate text-xs">{{ selected['email'] }}</span>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.slide-enter-active, .slide-leave-active {
  transition: opacity 0.15s, transform 0.15s;
}
.slide-enter-from, .slide-leave-to {
  opacity: 0;
  transform: translateX(8px);
}
</style>
