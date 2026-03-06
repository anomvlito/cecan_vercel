<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as THREE from 'three'
import { Network, type Node, type Edge } from 'vis-network'
import { DataSet } from 'vis-data'
import {
  Network as NetworkIcon, X, Users, FolderOpen, BookOpen, Layers,
  Sun, Moon, Box, LayoutGrid, RefreshCw,
} from 'lucide-vue-next'
import api from '@/services/api'

// ─── Types ────────────────────────────────────────────────────────────────────
type GraphNode = Node & { group?: string; data?: Record<string, unknown> }
type GraphEdge = Edge
interface Stats { researchers: number; wps: number; projects: number; nodes_thematic: number; edges: number }

// ─── State ────────────────────────────────────────────────────────────────────
const containerRef = ref<HTMLDivElement | null>(null)
const loading      = ref(true)
const error        = ref<string | null>(null)
const stats        = ref<Stats | null>(null)
const selected     = ref<Record<string, unknown> | null>(null)
const darkMode     = ref(true)
const view3D       = ref(false)

// Tooltip
const tooltipNode = ref<Record<string, unknown> | null>(null)
const tipX = ref(0)
const tipY = ref(0)

// 2D controls
const gravity         = ref(-800)
const springLength    = ref(180)
const showUnconnected = ref(false)   // ← apagado por defecto

// 3D controls
const linkDist3D   = ref(150)
const charge3D     = ref(-300)
const autoRotate   = ref(true)       // ← encendido por defecto en 3D
const zoomPct3D    = ref(60)

const MIN_3D = 50
const MAX_3D = 2000

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let network:  Network | null = null
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let graph3d:  any = null
let allNodes: DataSet<GraphNode>
let allEdges: DataSet<GraphEdge>
let rawData:  { nodes: Record<string, unknown>[]; edges: Record<string, unknown>[] } | null = null

// ─── Themes ───────────────────────────────────────────────────────────────────
const THEMES = {
  dark: {
    bg: '#020617',
    topBar:   'bg-slate-900/80 border-slate-800',
    titleCls: 'text-white',
    textCls:  'text-slate-400',
    legendCls:'text-slate-400',
    panelCls: 'bg-slate-900/95 border-slate-700',
    labelCls: 'text-slate-500',
    valueCls: 'text-slate-300',
    tipBg: '#1e293b', tipBorder: '#334155', tipSh: '0 10px 28px rgba(0,0,0,.55)',
    tipTitle: '#f1f5f9', tipLabel: '#64748b', tipVal: '#cbd5e1',
    investigator: '#e2e8f0', wp: '#818cf8', nodo: '#67e8f9', project: '#6ee7b7',
  },
  light: {
    bg: '#f1f5f9',
    topBar:   'bg-white/90 border-slate-200',
    titleCls: 'text-slate-900',
    textCls:  'text-slate-600',
    legendCls:'text-slate-600',
    panelCls: 'bg-white/95 border-slate-200',
    labelCls: 'text-slate-400',
    valueCls: 'text-slate-800',
    tipBg: '#ffffff', tipBorder: '#e2e8f0', tipSh: '0 10px 28px rgba(0,0,0,.1)',
    tipTitle: '#111827', tipLabel: '#9ca3af', tipVal: '#374151',
    investigator: '#3b82f6', wp: '#6366f1', nodo: '#0891b2', project: '#10b981',
  },
}
// En modo 3D usamos siempre el fondo espacial — mismo que HomeView
const BG_3D = '#06080f'

const theme = computed(() => THEMES[darkMode.value ? 'dark' : 'light'])

const BADGE_COLORS: Record<string, string> = {
  'Investigador': '#818cf8', 'WP': '#6366f1', 'Nodo': '#0891b2', 'Proyecto': '#10b981',
}

function typeToGroup(t: string) {
  return t === 'Investigador' ? 'investigator' : t === 'WP' ? 'wp' : t === 'Nodo' ? 'nodo' : 'project'
}

// ─── Node color / font ────────────────────────────────────────────────────────
function getNodeColor(group: string) {
  const d = darkMode.value
  return ({
    investigator: d
      ? { background: '#e2e8f0', border: '#94a3b8', highlight: { background: '#bfdbfe', border: '#3b82f6' } }
      : { background: '#3b82f6', border: '#2563eb', highlight: { background: '#bfdbfe', border: '#1d4ed8' } },
    wp: d
      ? { background: '#818cf8', border: '#6366f1', highlight: { background: '#a5b4fc', border: '#4f46e5' } }
      : { background: '#6366f1', border: '#4f46e5', highlight: { background: '#a5b4fc', border: '#4338ca' } },
    nodo: d
      ? { background: '#164e63', border: '#0e7490', highlight: { background: '#0e7490', border: '#06b6d4' } }
      : { background: '#0891b2', border: '#0e7490', highlight: { background: '#22d3ee', border: '#0891b2' } },
    project: d
      ? { background: '#065f46', border: '#059669', highlight: { background: '#059669', border: '#10b981' } }
      : { background: '#10b981', border: '#059669', highlight: { background: '#6ee7b7', border: '#047857' } },
  } as Record<string, unknown>)[group]
}

function getNodeFont(group: string) {
  const d = darkMode.value
  return ({
    investigator: { size: 11, color: d ? '#1e293b' : '#ffffff', face: 'Inter, sans-serif' },
    wp:           { size: 16, color: '#ffffff', bold: true, face: 'Inter, sans-serif' },
    nodo:         { size: 11, color: d ? '#67e8f9' : '#ffffff', face: 'Inter, sans-serif' },
    project:      { size: 10, color: d ? '#6ee7b7' : '#ffffff', face: 'Inter, sans-serif' },
  } as Record<string, unknown>)[group]
}

// ─── Mouse ────────────────────────────────────────────────────────────────────
function onMouseMove(e: MouseEvent) {
  tipX.value = e.clientX + 18
  tipY.value = e.clientY - 10
}

// ─── Build 2D ─────────────────────────────────────────────────────────────────
function build2D() {
  if (!containerRef.value || !rawData) return

  // Pre-calcular nodos conectados para aplicar filtro desde el inicio
  const connected = new Set<string>()
  rawData.edges.forEach(e => {
    if (e['from'] != null) connected.add(String(e['from']))
    if (e['to'] != null)   connected.add(String(e['to']))
  })

  allNodes = new DataSet<GraphNode>(rawData.nodes.map(n => ({
    ...n,
    color:  getNodeColor(n['group'] as string),
    font:   getNodeFont(n['group'] as string),
    hidden: !showUnconnected.value && !connected.has(String(n['id'])),
  })) as GraphNode[])
  allEdges = new DataSet<GraphEdge>(rawData.edges as GraphEdge[])
  containerRef.value.style.background = theme.value.bg

  network = new Network(containerRef.value, { nodes: allNodes, edges: allEdges }, {
    physics: {
      enabled: true,
      solver: 'forceAtlas2Based',
      forceAtlas2Based: {
        gravitationalConstant: gravity.value,
        springLength: springLength.value,
        springConstant: 0.04, damping: 0.9, avoidOverlap: 0.4,
      },
      stabilization: { iterations: 150, updateInterval: 25 },
    },
    nodes: {
      borderWidth: 1.5,
      shadow: { enabled: true, size: 8, x: 2, y: 2, color: 'rgba(0,0,0,0.25)' },
    },
    edges: {
      smooth: { enabled: true, type: 'dynamic', roundness: 0.3 },
      arrows: { to: { enabled: false } },
    },
    interaction: { hover: true, hideEdgesOnDrag: true, navigationButtons: false, keyboard: false },
  })

  network.on('hoverNode', (params) => {
    const node = allNodes.get(params.node as string) as GraphNode | null
    tooltipNode.value = (node?.data as Record<string, unknown>) ?? null
  })
  network.on('blurNode', () => { tooltipNode.value = null })
  network.on('click', (params) => {
    tooltipNode.value = null
    selected.value = params.nodes.length > 0
      ? ((allNodes.get(params.nodes[0] as string) as GraphNode | null)?.data as Record<string, unknown> ?? null)
      : null
  })

  // Auto-fit al terminar la estabilización (evita que aparezca muy pequeño)
  network.once('stabilized', () => {
    network?.fit({ animation: { duration: 500, easingFunction: 'easeInOutQuad' } })
  })
}

// ─── Datos 3D filtrados (compartido por build3D y toggle) ────────────────────
function get3DGraphData() {
  if (!rawData) return { nodes: [], links: [] }
  const links = rawData.edges.map(e => ({
    source: e['from'], target: e['to'],
    color:  (e['color'] as Record<string, string> | undefined)?.color ?? '#334155',
    width:  (e['width'] as number) ?? 1,
  }))
  if (showUnconnected.value) {
    return { nodes: rawData.nodes.map(n => ({ ...n })), links }
  }
  const connected = new Set<unknown>()
  rawData.edges.forEach(e => { connected.add(e['from']); connected.add(e['to']) })
  return {
    nodes: rawData.nodes.filter(n => connected.has(n['id'])).map(n => ({ ...n })),
    links,
  }
}

// ─── Build 3D ─────────────────────────────────────────────────────────────────
async function build3D() {
  if (!containerRef.value || !rawData) return

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const { default: ForceGraph3D } = await import('3d-force-graph') as any

  const nodeColorFn = (n: Record<string, unknown>) => {
    const m: Record<string, string> = {
      investigator: theme.value.investigator,
      wp:   theme.value.wp,
      nodo: theme.value.nodo,
      project: theme.value.project,
    }
    return m[n['group'] as string] ?? '#888'
  }

  const w = containerRef.value.clientWidth
  const h = containerRef.value.clientHeight

  graph3d = ForceGraph3D({ controlType: 'orbit' })(containerRef.value)
    .width(w).height(h)
    .backgroundColor(BG_3D)           // siempre fondo espacial, igual que HomeView
    .showNavInfo(false)
    .nodeLabel('')                     // tooltip gestionado por Vue
    .graphData(get3DGraphData())
    .nodeColor(nodeColorFn)
    .nodeVal((n: Record<string, unknown>) => Math.max(1, ((n['size'] as number) ?? 20) / 6))
    .linkColor((l: Record<string, unknown>) => l['color'] as string ?? '#334155')
    .linkWidth((l: Record<string, unknown>) => (l['width'] as number) ?? 1)
    .linkOpacity(0.4)
    .onNodeHover((n: Record<string, unknown> | null) => {
      tooltipNode.value = n ? (n['data'] as Record<string, unknown> ?? null) : null
      if (containerRef.value) containerRef.value.style.cursor = n ? 'pointer' : 'default'
    })
    .onNodeClick((n: Record<string, unknown>) => {
      selected.value = (n['data'] as Record<string, unknown>) ?? null
    })

  // ── Estrellas de fondo (igual que HomeView) ──────────────────────────────
  setTimeout(() => {
    const scene = graph3d?.scene?.()
    if (scene) {
      const count = 800
      const pos = new Float32Array(count * 3)
      for (let i = 0; i < count; i++) {
        pos[i * 3]     = (Math.random() - 0.5) * 2000
        pos[i * 3 + 1] = (Math.random() - 0.5) * 2000
        pos[i * 3 + 2] = (Math.random() - 0.5) * 2000
      }
      const geo = new THREE.BufferGeometry()
      geo.setAttribute('position', new THREE.BufferAttribute(pos, 3))
      scene.add(new THREE.Points(geo, new THREE.PointsMaterial({
        color: 0xffffff, size: 1.2, transparent: true, opacity: 0.3,
      })))
    }

    // ── OrbitControls: auto-rotate + zoom sync ───────────────────────────
    const ctrl = graph3d?.controls?.()
    if (ctrl) {
      ctrl.autoRotate = autoRotate.value
      ctrl.autoRotateSpeed = 0.5   // mismo feel que HomeView (0.4)
      ctrl.enableDamping = true
      ctrl.dampingFactor = 0.06

      // Sincronizar slider desde movimientos de cámara
      ctrl.addEventListener('change', () => {
        const cam = graph3d?.camera?.()
        if (!cam || !ctrl) return
        const p = cam.position, t = ctrl.target
        const dist = Math.sqrt((p.x-t.x)**2 + (p.y-t.y)**2 + (p.z-t.z)**2)
        zoomPct3D.value = Math.round(100 - Math.min(100, Math.max(0, (dist - MIN_3D) / (MAX_3D - MIN_3D) * 100)))
      })

      // Leer posición inicial para setear el slider
      const cam = graph3d?.camera?.()
      if (cam) {
        const p = cam.position, t = ctrl.target
        const dist = Math.sqrt((p.x-t.x)**2 + (p.y-t.y)**2 + (p.z-t.z)**2)
        zoomPct3D.value = Math.round(100 - Math.min(100, Math.max(0, (dist - MIN_3D) / (MAX_3D - MIN_3D) * 100)))
      }
    }

    // ── Física inicial ────────────────────────────────────────────────────
    graph3d?.d3Force('link')?.distance(linkDist3D.value)
    graph3d?.d3Force('charge')?.strength(charge3D.value)

  }, 400)
}

// ─── 3D zoom slider ───────────────────────────────────────────────────────────
function onZoomSlider3D(e: Event) {
  if (!graph3d) return
  const val = Number((e.target as HTMLInputElement).value)
  const cam = graph3d.camera?.()
  const ctrl = graph3d.controls?.()
  if (!cam || !ctrl) return
  const p = cam.position, t = ctrl.target
  const dx = p.x - t.x, dy = p.y - t.y, dz = p.z - t.z
  const len = Math.sqrt(dx*dx + dy*dy + dz*dz) || 1
  const newDist = MIN_3D + ((100 - val) / 100) * (MAX_3D - MIN_3D)
  cam.position.set(t.x + (dx/len) * newDist, t.y + (dy/len) * newDist, t.z + (dz/len) * newDist)
  ctrl.update()
  zoomPct3D.value = val
}

// ─── Switch 2D ↔ 3D ──────────────────────────────────────────────────────────
async function switchView() {
  selected.value = null; tooltipNode.value = null
  const goTo3D = !view3D.value
  network?.destroy(); network = null
  graph3d?._destructor?.(); graph3d = null
  if (containerRef.value) containerRef.value.innerHTML = ''
  view3D.value = goTo3D
  await nextTick()
  goTo3D ? await build3D() : build2D()
}

// ─── Toggle day / night ───────────────────────────────────────────────────────
function toggleDarkMode() {
  darkMode.value = !darkMode.value
  if (view3D.value && graph3d) {
    // 3D siempre mantiene fondo espacial — solo actualizamos colores de nodos
    graph3d.nodeColor((n: Record<string, unknown>) => {
      const m: Record<string, string> = {
        investigator: theme.value.investigator, wp: theme.value.wp,
        nodo: theme.value.nodo, project: theme.value.project,
      }
      return m[n['group'] as string] ?? '#888'
    })
  } else if (!view3D.value && network && rawData) {
    if (containerRef.value) containerRef.value.style.background = theme.value.bg
    allNodes.update(rawData.nodes.map(n => ({
      id:    n['id'],
      color: getNodeColor(n['group'] as string),
      font:  getNodeFont(n['group'] as string),
    })) as GraphNode[])
  }
}

// ─── 2D physics ───────────────────────────────────────────────────────────────
function applyPhysics2D() {
  network?.setOptions({ physics: { forceAtlas2Based: {
    gravitationalConstant: gravity.value, springLength: springLength.value,
  }}})
}

function toggleUnconnected() {
  showUnconnected.value = !showUnconnected.value
  if (view3D.value) {
    graph3d?.graphData(get3DGraphData())
  } else {
    if (!allNodes || !allEdges) return
    const connected = new Set<string>()
    allEdges.get().forEach(e => {
      if (e.from != null) connected.add(String(e.from))
      if (e.to != null)   connected.add(String(e.to))
    })
    allNodes.update(allNodes.get().map((n: GraphNode) => ({
      id: n.id, hidden: !showUnconnected.value && !connected.has(String(n.id)),
    })))
  }
}

// ─── 3D physics ───────────────────────────────────────────────────────────────
function apply3DPhysics() {
  if (!graph3d) return
  graph3d.d3Force('link')?.distance(linkDist3D.value)
  graph3d.d3Force('charge')?.strength(charge3D.value)
  graph3d.d3ReheatSimulation?.()
}

function toggleAutoRotate() {
  autoRotate.value = !autoRotate.value
  const ctrl = graph3d?.controls?.()
  if (ctrl) { ctrl.autoRotate = autoRotate.value; ctrl.autoRotateSpeed = 0.5 }
}

// ─── Fit ──────────────────────────────────────────────────────────────────────
function fitAll() {
  if (!view3D.value) network?.fit({ animation: { duration: 600, easingFunction: 'easeInOutQuad' } })
  else graph3d?.zoomToFit?.(600)
}

// ─── Init ─────────────────────────────────────────────────────────────────────
async function init() {
  try {
    const { data } = await api.get('/graph/data')
    stats.value = data.stats
    rawData = data
    loading.value = false
    await nextTick()
    build2D()
  } catch (e) {
    loading.value = false
    error.value = `Error: ${e instanceof Error ? e.message : 'Sin conexión'}`
  }
}

onMounted(init)
onUnmounted(() => { network?.destroy(); graph3d?._destructor?.() })

// ─── Legend ───────────────────────────────────────────────────────────────────
const legendItems = computed(() => ([
  { key: 'investigator', label: 'Investigador',  color: theme.value.investigator },
  { key: 'wp',           label: 'Work Package',  color: theme.value.wp },
  { key: 'nodo',         label: 'Nodo Temático', color: theme.value.nodo },
  { key: 'project',      label: 'Proyecto',      color: theme.value.project },
]))
</script>

<template>
  <div
    class="fixed inset-0 md:left-56 overflow-hidden flex flex-col transition-colors duration-300"
    :style="{ backgroundColor: view3D ? BG_3D : theme.bg }"
    @mousemove="onMouseMove"
  >

    <!-- ── Top bar ─────────────────────────────────────────────────────────── -->
    <div
      class="flex items-center justify-between px-4 py-2 backdrop-blur border-b flex-shrink-0 z-10 transition-colors duration-300"
      :class="view3D ? 'bg-slate-950/70 border-slate-800/60' : theme.topBar"
    >
      <!-- Título + stats -->
      <div class="flex items-center gap-2 min-w-0">
        <NetworkIcon class="w-4 h-4 text-indigo-400 flex-shrink-0" />
        <span
          class="text-sm font-semibold flex-shrink-0"
          :class="view3D ? 'text-white' : theme.titleCls"
        >Mapa de Colaboración</span>
        <div
          v-if="stats"
          class="hidden md:flex items-center gap-3 ml-3 text-xs"
          :class="view3D ? 'text-slate-400' : theme.textCls"
        >
          <span class="flex items-center gap-1"><Users class="w-3 h-3" />{{ stats.researchers }}</span>
          <span class="flex items-center gap-1"><FolderOpen class="w-3 h-3" />{{ stats.projects }}</span>
          <span class="flex items-center gap-1"><Layers class="w-3 h-3" />{{ stats.wps }} WPs</span>
          <span class="flex items-center gap-1"><BookOpen class="w-3 h-3" />{{ stats.nodes_thematic }}</span>
          <span class="opacity-30">·</span>
          <span>{{ stats.edges }} conexiones</span>
        </div>
      </div>

      <!-- Controles derechos -->
      <div class="flex items-center gap-2 flex-shrink-0">

        <!-- ── 2D controls ── -->
        <template v-if="!view3D">
          <div class="hidden xl:flex items-center gap-2 text-xs" :class="theme.textCls">
            <span>Gravedad</span>
            <input type="range" min="-3000" max="-100" step="50" v-model.number="gravity"
              class="w-20 h-1 cursor-pointer" style="accent-color:#818cf8" @change="applyPhysics2D" />
            <span class="w-12 tabular-nums">{{ gravity }}</span>
          </div>
          <div class="hidden xl:flex items-center gap-2 text-xs" :class="theme.textCls">
            <span>Distancia</span>
            <input type="range" min="50" max="400" step="10" v-model.number="springLength"
              class="w-20 h-1 cursor-pointer" style="accent-color:#818cf8" @change="applyPhysics2D" />
            <span class="w-8 tabular-nums">{{ springLength }}</span>
          </div>
          <button
            class="hidden lg:block px-2 py-1 text-xs rounded border transition-colors"
            :class="showUnconnected
              ? `border-slate-600 hover:border-slate-400 ${theme.textCls}`
              : 'border-indigo-500 text-indigo-400'"
            @click="toggleUnconnected"
          >{{ showUnconnected ? 'Ocultar aislados' : 'Mostrar todos' }}</button>
        </template>

        <!-- ── 3D controls ── -->
        <template v-if="view3D">
          <div class="hidden xl:flex items-center gap-2 text-xs text-slate-400">
            <span>Distancia</span>
            <input type="range" min="30" max="400" step="10" v-model.number="linkDist3D"
              class="w-20 h-1 cursor-pointer" style="accent-color:#818cf8" @change="apply3DPhysics" />
            <span class="w-8 tabular-nums">{{ linkDist3D }}</span>
          </div>
          <div class="hidden xl:flex items-center gap-2 text-xs text-slate-400">
            <span>Carga</span>
            <input type="range" min="-1000" max="-30" step="10" v-model.number="charge3D"
              class="w-20 h-1 cursor-pointer" style="accent-color:#818cf8" @change="apply3DPhysics" />
            <span class="w-14 tabular-nums">{{ charge3D }}</span>
          </div>
          <button
            class="flex items-center gap-1.5 px-2 py-1 text-xs rounded border transition-colors"
            :class="autoRotate
              ? 'border-indigo-500 text-indigo-400 bg-indigo-500/10'
              : 'border-slate-600 text-slate-400 hover:border-slate-400'"
            @click="toggleAutoRotate"
          >
            <RefreshCw class="w-3 h-3" :class="autoRotate ? 'animate-spin' : ''" style="animation-duration:2.5s" />
            Rotar
          </button>
          <button
            class="px-2 py-1 text-xs rounded border transition-colors"
            :class="showUnconnected
              ? 'border-slate-600 text-slate-400 hover:border-slate-400'
              : 'border-indigo-500 text-indigo-400'"
            @click="toggleUnconnected"
          >{{ showUnconnected ? 'Ocultar aislados' : 'Mostrar todos' }}</button>
        </template>

        <!-- Encuadrar -->
        <button
          class="px-2 py-1 text-xs rounded border transition-colors"
          :class="view3D ? 'border-slate-600 text-slate-400 hover:border-slate-400' : `border-slate-500 ${theme.textCls} hover:border-slate-400`"
          @click="fitAll"
        >Encuadrar</button>

        <!-- 2D / 3D toggle -->
        <button
          class="flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-lg border font-medium transition-colors"
          :class="view3D
            ? 'border-indigo-500 text-indigo-400 bg-indigo-500/10'
            : `border-slate-500 ${theme.textCls} hover:border-slate-400`"
          @click="switchView"
        >
          <component :is="view3D ? LayoutGrid : Box" class="w-3.5 h-3.5" />
          {{ view3D ? '2D' : '3D' }}
        </button>

        <!-- Day / Night (solo en 2D; en 3D es siempre oscuro) -->
        <button
          v-if="!view3D"
          class="p-1.5 rounded-lg border transition-colors"
          :class="darkMode
            ? 'border-slate-700 text-yellow-400 hover:bg-yellow-400/10'
            : 'border-slate-300 text-indigo-600 hover:bg-indigo-50'"
          :title="darkMode ? 'Modo día' : 'Modo noche'"
          @click="toggleDarkMode"
        >
          <component :is="darkMode ? Sun : Moon" class="w-3.5 h-3.5" />
        </button>
      </div>
    </div>

    <!-- ── Loading ───────────────────────────────────────────────────────────── -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <div class="w-8 h-8 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p class="text-indigo-400 text-sm">Construyendo red de colaboración…</p>
      </div>
    </div>
    <div v-else-if="error" class="flex-1 flex items-center justify-center">
      <p class="text-red-400 text-sm">{{ error }}</p>
    </div>

    <!-- ── Contenedor del grafo ───────────────────────────────────────────────── -->
    <div v-show="!loading && !error" ref="containerRef" class="flex-1 w-full" />

    <!-- ── Leyenda (bottom-left) ─────────────────────────────────────────────── -->
    <div class="absolute bottom-6 left-4 z-10 flex flex-col gap-1.5 pointer-events-none">
      <div v-for="item in legendItems" :key="item.key" class="flex items-center gap-2">
        <span class="w-2.5 h-2.5 rounded-full border border-white/20" :style="{ backgroundColor: item.color }" />
        <span class="text-xs" :class="view3D ? 'text-slate-400' : theme.legendCls">{{ item.label }}</span>
      </div>
    </div>

    <!-- ── Zoom slider 3D (bottom-right) — igual que Mapa 3D ─────────────────── -->
    <div v-if="view3D" class="absolute bottom-6 right-6 z-10 flex flex-col items-end gap-1">
      <p class="text-xs text-slate-600 tabular-nums">Zoom {{ zoomPct3D }}%</p>
      <div class="flex items-center gap-2">
        <span class="text-xs text-slate-700">−</span>
        <input
          type="range" min="0" max="100" :value="zoomPct3D"
          class="w-28 h-1 appearance-none rounded-full cursor-pointer"
          style="accent-color:#818cf8; background:rgba(255,255,255,0.08)"
          @input="onZoomSlider3D"
        />
        <span class="text-xs text-slate-700">+</span>
      </div>
      <p class="text-xs text-slate-700">Arrastrar para rotar</p>
    </div>

    <!-- ── Tooltip hover (Vue, ambos modos) ──────────────────────────────────── -->
    <Transition name="tip">
      <div
        v-if="tooltipNode"
        class="fixed z-50 pointer-events-none"
        :style="{ left: tipX + 'px', top: tipY + 'px' }"
      >
        <div
          class="rounded-xl p-3 w-56"
          :style="{
            background: view3D ? '#1e293b' : theme.tipBg,
            border: `1px solid ${(BADGE_COLORS[tooltipNode['type'] as string] ?? '#334155') + '44'}`,
            boxShadow: view3D ? '0 10px 28px rgba(0,0,0,.6)' : theme.tipSh,
            fontFamily: 'Inter, system-ui, sans-serif',
          }"
        >
          <div
            class="inline-block text-xs font-bold px-2 py-0.5 rounded-full mb-2"
            :style="{
              background: (BADGE_COLORS[tooltipNode['type'] as string] ?? '#94a3b8') + '28',
              color: BADGE_COLORS[tooltipNode['type'] as string] ?? '#94a3b8',
              textTransform: 'uppercase', letterSpacing: '.05em', fontSize: '10px',
            }"
          >{{ tooltipNode['type'] }}</div>

          <div class="text-sm font-bold leading-snug mb-2" :style="{ color: view3D ? '#f1f5f9' : theme.tipTitle }">
            {{ tooltipNode['name'] }}
          </div>

          <template v-if="tooltipNode['type'] === 'Investigador'">
            <div v-if="tooltipNode['institution']" class="tip-row">
              <span :style="{ color: view3D ? '#64748b' : theme.tipLabel }">🏛 Institución</span>
              <span class="truncate" :style="{ color: view3D ? '#cbd5e1' : theme.tipVal }">{{ tooltipNode['institution'] }}</span>
            </div>
            <div v-if="tooltipNode['category']" class="tip-row">
              <span :style="{ color: view3D ? '#64748b' : theme.tipLabel }">🔖 Categoría</span>
              <span class="truncate" :style="{ color: view3D ? '#cbd5e1' : theme.tipVal }">{{ tooltipNode['category'] }}</span>
            </div>
            <div v-if="tooltipNode['orcid']" class="tip-row">
              <span :style="{ color: view3D ? '#64748b' : theme.tipLabel }">ORCID</span>
              <span class="font-mono truncate" style="color:#818cf8;font-size:10px">{{ tooltipNode['orcid'] }}</span>
            </div>
            <div v-if="tooltipNode['h_index'] != null" class="tip-row items-baseline">
              <span :style="{ color: view3D ? '#64748b' : theme.tipLabel }">H-index</span>
              <span class="font-black text-xl leading-none" style="color:#60a5fa">{{ tooltipNode['h_index'] }}</span>
            </div>
            <div v-if="tooltipNode['citations'] != null" class="tip-row">
              <span :style="{ color: view3D ? '#64748b' : theme.tipLabel }">📊 Citas</span>
              <span :style="{ color: view3D ? '#cbd5e1' : theme.tipVal }">{{ Number(tooltipNode['citations']).toLocaleString('es-CL') }}</span>
            </div>
            <div v-if="tooltipNode['works'] != null" class="tip-row">
              <span :style="{ color: view3D ? '#64748b' : theme.tipLabel }">📄 Publicaciones</span>
              <span :style="{ color: view3D ? '#cbd5e1' : theme.tipVal }">{{ tooltipNode['works'] }}</span>
            </div>
          </template>
          <template v-else>
            <div class="text-xs" :style="{ color: view3D ? '#64748b' : theme.tipLabel }">
              {{ tooltipNode['type'] === 'WP' ? 'Línea de investigación del consorcio'
               : tooltipNode['type'] === 'Proyecto' ? 'Proyecto científico asociado'
               : 'Área temática transversal' }}
            </div>
          </template>
        </div>
      </div>
    </Transition>

    <!-- ── Panel detalle click ────────────────────────────────────────────────── -->
    <Transition name="slide">
      <div
        v-if="selected"
        class="absolute top-14 right-3 z-20 w-64 backdrop-blur border rounded-xl p-4 shadow-2xl"
        :class="view3D ? 'bg-slate-900/95 border-slate-700' : theme.panelCls"
      >
        <div class="flex items-start justify-between mb-3">
          <span
            class="text-xs font-semibold px-2 py-0.5 rounded-full"
            :style="{
              backgroundColor: legendItems.find(i => i.key === typeToGroup(selected!['type'] as string))?.color + '28',
              color: legendItems.find(i => i.key === typeToGroup(selected!['type'] as string))?.color,
            }"
          >{{ selected['type'] }}</span>
          <button
            class="text-slate-500 hover:text-slate-300 transition-colors"
            @click="selected = null"
          ><X class="w-4 h-4" /></button>
        </div>

        <p
          class="font-semibold text-sm leading-snug mb-3"
          :class="view3D ? 'text-white' : theme.titleCls"
        >{{ selected['name'] }}</p>

        <div class="space-y-1.5 text-xs">
          <div v-if="selected['institution']" class="flex gap-2">
            <span class="w-20 flex-shrink-0" :class="view3D ? 'text-slate-500' : theme.labelCls">Institución</span>
            <span class="truncate" :class="view3D ? 'text-slate-300' : theme.valueCls">{{ selected['institution'] }}</span>
          </div>
          <div v-if="selected['orcid']" class="flex gap-2">
            <span class="w-20 flex-shrink-0" :class="view3D ? 'text-slate-500' : theme.labelCls">ORCID</span>
            <span class="font-mono text-indigo-400 text-xs truncate">{{ selected['orcid'] }}</span>
          </div>
          <div v-if="selected['h_index'] != null" class="flex gap-2 items-baseline">
            <span class="w-20 flex-shrink-0" :class="view3D ? 'text-slate-500' : theme.labelCls">H-index</span>
            <span class="font-black text-2xl leading-none text-blue-400">{{ selected['h_index'] }}</span>
          </div>
          <div v-if="selected['citations'] != null" class="flex gap-2">
            <span class="w-20 flex-shrink-0" :class="view3D ? 'text-slate-500' : theme.labelCls">Citas</span>
            <span :class="view3D ? 'text-slate-300' : theme.valueCls">{{ Number(selected['citations']).toLocaleString('es-CL') }}</span>
          </div>
          <div v-if="selected['works'] != null" class="flex gap-2">
            <span class="w-20 flex-shrink-0" :class="view3D ? 'text-slate-500' : theme.labelCls">Publicaciones</span>
            <span :class="view3D ? 'text-slate-300' : theme.valueCls">{{ selected['works'] }}</span>
          </div>
          <div v-if="selected['category']" class="flex gap-2">
            <span class="w-20 flex-shrink-0" :class="view3D ? 'text-slate-500' : theme.labelCls">Categoría</span>
            <span :class="view3D ? 'text-slate-300' : theme.valueCls">{{ selected['category'] }}</span>
          </div>
          <div v-if="selected['email']" class="flex gap-2">
            <span class="w-20 flex-shrink-0" :class="view3D ? 'text-slate-500' : theme.labelCls">Email</span>
            <span class="truncate" :class="view3D ? 'text-slate-300' : theme.valueCls">{{ selected['email'] }}</span>
          </div>
        </div>
      </div>
    </Transition>

  </div>
</template>

<style scoped>
.slide-enter-active, .slide-leave-active { transition: opacity 0.15s, transform 0.15s; }
.slide-enter-from, .slide-leave-to { opacity: 0; transform: translateX(8px); }

.tip-enter-active, .tip-leave-active { transition: opacity 0.1s, transform 0.1s; }
.tip-enter-from, .tip-leave-to { opacity: 0; transform: translateY(-4px); }

.tip-row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
  font-size: 11px;
  align-items: center;
}
</style>
