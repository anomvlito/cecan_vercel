<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { Network, type Node, type Edge } from 'vis-network'
import { DataSet } from 'vis-data'
import { Network as NetworkIcon, X, Users, FolderOpen, BookOpen, Layers, Sun, Moon, Box, LayoutGrid } from 'lucide-vue-next'
import api from '@/services/api'

// ─── Types ────────────────────────────────────────────────────────────────────
type GraphNode = Node & { group?: string; data?: Record<string, unknown> }
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
const darkMode = ref(true)
const view3D = ref(false)

// 2D controls
const gravity = ref(-800)
const springLength = ref(180)
const showUnconnected = ref(true)

let network: Network | null = null
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let graph3d: any = null
let allNodes: DataSet<GraphNode>
let allEdges: DataSet<GraphEdge>
let rawData: { nodes: Record<string, unknown>[]; edges: Record<string, unknown>[] } | null = null

// ─── Themes ───────────────────────────────────────────────────────────────────
const THEMES = {
  dark: {
    bg: '#020617',
    topBar: 'bg-slate-900/80 border-slate-800',
    titleCls: 'text-white',
    textCls: 'text-slate-400',
    legendCls: 'text-slate-400',
    panelCls: 'bg-slate-900/95 border-slate-700',
    labelCls: 'text-slate-500',
    valueCls: 'text-slate-300',
    investigator: '#e2e8f0',
    wp: '#818cf8',
    nodo: '#67e8f9',
    project: '#6ee7b7',
  },
  light: {
    bg: '#f1f5f9',
    topBar: 'bg-white/90 border-slate-200',
    titleCls: 'text-slate-900',
    textCls: 'text-slate-600',
    legendCls: 'text-slate-700',
    panelCls: 'bg-white/95 border-slate-200',
    labelCls: 'text-slate-400',
    valueCls: 'text-slate-800',
    investigator: '#3b82f6',
    wp: '#6366f1',
    nodo: '#0891b2',
    project: '#10b981',
  },
}

const theme = computed(() => THEMES[darkMode.value ? 'dark' : 'light'])

// ─── Node colors per theme ────────────────────────────────────────────────────
function getNodeColor(group: string) {
  const d = darkMode.value
  const map: Record<string, unknown> = {
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
  }
  return map[group]
}

function getNodeFont(group: string) {
  const d = darkMode.value
  const map: Record<string, unknown> = {
    investigator: { size: 11, color: d ? '#1e293b' : '#ffffff', face: 'Inter, sans-serif' },
    wp:           { size: 16, color: '#ffffff', bold: true, face: 'Inter, sans-serif' },
    nodo:         { size: 11, color: d ? '#67e8f9' : '#ffffff', face: 'Inter, sans-serif' },
    project:      { size: 10, color: d ? '#6ee7b7' : '#ffffff', face: 'Inter, sans-serif' },
  }
  return map[group]
}

// ─── Rich tooltip builder ─────────────────────────────────────────────────────
function buildTooltip(data: Record<string, unknown>): HTMLElement {
  const d = darkMode.value
  const el = document.createElement('div')
  const bg  = d ? '#1e293b' : '#ffffff'
  const bd  = d ? '#334155' : '#e2e8f0'
  const sh  = d ? 'rgba(0,0,0,.5)' : 'rgba(0,0,0,.08)'
  el.style.cssText = `background:${bg};border:1px solid ${bd};border-radius:10px;padding:13px 15px;max-width:250px;font-family:Inter,system-ui,sans-serif;box-shadow:0 10px 28px ${sh};pointer-events:none;`

  const lc = d ? '#64748b' : '#9ca3af'
  const tc = d ? '#f1f5f9' : '#111827'
  const vc = d ? '#cbd5e1' : '#374151'
  const type = data['type'] as string

  const row = (k: string, v: string) =>
    `<div style="display:flex;justify-content:space-between;gap:8px;margin-bottom:4px;font-size:11px">
       <span style="color:${lc};flex-shrink:0">${k}</span>
       <span style="color:${vc};text-align:right;max-width:150px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${v}</span>
     </div>`

  const typeColors: Record<string, string> = {
    'Investigador': '#818cf8',
    'WP': '#6366f1',
    'Nodo': '#0891b2',
    'Proyecto': '#10b981',
  }
  const badge = typeColors[type] ?? '#94a3b8'

  let html = `
    <div style="display:flex;align-items:center;gap:6px;margin-bottom:8px">
      <span style="font-size:10px;font-weight:700;color:${badge};background:${badge}22;padding:2px 7px;border-radius:99px;text-transform:uppercase;letter-spacing:.05em">${type}</span>
    </div>
    <div style="font-size:13px;font-weight:700;color:${tc};line-height:1.35;margin-bottom:${type === 'Investigador' ? '10px' : '4px'}">${data['name']}</div>
  `

  if (type === 'Investigador') {
    if (data['institution'])
      html += row('🏛 Institución', String(data['institution']))
    if (data['category'])
      html += row('🔖 Categoría', String(data['category']))
    if (data['orcid'])
      html += `<div style="display:flex;justify-content:space-between;gap:8px;margin-bottom:4px;font-size:11px">
        <span style="color:${lc}">ORCID</span>
        <span style="color:#818cf8;font-family:monospace;font-size:10px">${data['orcid']}</span>
      </div>`
    if (data['h_index'] != null)
      html += `<div style="display:flex;justify-content:space-between;gap:8px;margin-bottom:4px;font-size:11px">
        <span style="color:${lc}">H-index</span>
        <span style="color:#60a5fa;font-weight:800;font-size:15px;line-height:1">${data['h_index']}</span>
      </div>`
    if (data['citations'] != null)
      html += row('📊 Citas totales', Number(data['citations']).toLocaleString('es-CL'))
    if (data['works'] != null)
      html += row('📄 Publicaciones', String(data['works']))
    if (data['email'])
      html += row('✉ Email', String(data['email']))
  } else if (type === 'WP') {
    html += `<div style="font-size:11px;color:${lc};line-height:1.5">Línea de investigación del consorcio CECAN</div>`
  } else if (type === 'Proyecto') {
    html += `<div style="font-size:11px;color:${lc};line-height:1.5">Proyecto científico asociado</div>`
  } else if (type === 'Nodo') {
    html += `<div style="font-size:11px;color:${lc};line-height:1.5">Área temática transversal</div>`
  }

  el.innerHTML = html
  return el
}

// ─── 3D tooltip string ────────────────────────────────────────────────────────
function build3DLabel(data: Record<string, unknown> | undefined, label: string): string {
  if (!data) return `<span style="font-family:Inter,sans-serif">${label}</span>`
  const d = darkMode.value
  const bg = d ? '#1e293b' : '#fff'
  const bd = d ? '#334155' : '#e2e8f0'
  const tc = d ? '#f1f5f9' : '#111827'
  const lc = d ? '#94a3b8' : '#6b7280'
  const type = data['type'] as string
  const badge: Record<string, string> = { 'Investigador':'#818cf8','WP':'#6366f1','Nodo':'#0891b2','Proyecto':'#10b981' }
  let tip = `<div style="background:${bg};border:1px solid ${bd};border-radius:9px;padding:10px 13px;font-family:Inter,sans-serif;max-width:210px">
    <div style="font-size:10px;font-weight:700;color:${badge[type]??'#94a3b8'};text-transform:uppercase;margin-bottom:4px">${type}</div>
    <div style="font-size:13px;font-weight:700;color:${tc};margin-bottom:6px;line-height:1.3">${data['name']}</div>`
  if (data['institution']) tip += `<div style="font-size:11px;color:${lc}">🏛 ${data['institution']}</div>`
  if (data['h_index'] != null) tip += `<div style="font-size:11px;color:#60a5fa;margin-top:3px">H-index <b>${data['h_index']}</b></div>`
  if (data['citations'] != null) tip += `<div style="font-size:11px;color:${lc}">📊 ${Number(data['citations']).toLocaleString('es-CL')} citas</div>`
  if (data['category']) tip += `<div style="font-size:11px;color:${lc}">🔖 ${data['category']}</div>`
  tip += '</div>'
  return tip
}

// ─── Build 2D vis-network ─────────────────────────────────────────────────────
function build2D() {
  if (!containerRef.value || !rawData) return

  const processed = rawData.nodes.map(n => ({
    ...n,
    title: n['data'] ? buildTooltip(n['data'] as Record<string, unknown>) : undefined,
    color: getNodeColor(n['group'] as string),
    font:  getNodeFont(n['group'] as string),
  }))

  allNodes = new DataSet<GraphNode>(processed as GraphNode[])
  allEdges = new DataSet<GraphEdge>(rawData.edges as GraphEdge[])
  containerRef.value.style.background = theme.value.bg

  network = new Network(containerRef.value, { nodes: allNodes, edges: allEdges }, {
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
    },
    edges: {
      smooth: { enabled: true, type: 'dynamic', roundness: 0.3 },
      arrows: { to: { enabled: false } },
    },
    interaction: {
      hover: true,
      tooltipDelay: 80,
      hideEdgesOnDrag: true,
      navigationButtons: false,
      keyboard: false,
    },
  })

  network.on('click', (params) => {
    if (params.nodes.length > 0) {
      const node = allNodes.get(params.nodes[0] as string) as GraphNode | null
      selected.value = (node?.data as Record<string, unknown>) ?? null
    } else {
      selected.value = null
    }
  })
}

// ─── Build 3D force-graph ─────────────────────────────────────────────────────
async function build3D() {
  if (!containerRef.value || !rawData) return

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const { default: ForceGraph3D } = await import('3d-force-graph') as any
  const t = theme.value

  const nodeColorFn = (node: Record<string, unknown>) => {
    const m: Record<string, string> = { investigator: t.investigator, wp: t.wp, nodo: t.nodo, project: t.project }
    return m[node['group'] as string] ?? '#888'
  }

  const links = rawData.edges.map(e => ({
    source: e['from'],
    target: e['to'],
    color: (e['color'] as Record<string, string> | undefined)?.color ?? '#4b5563',
    width: (e['width'] as number) ?? 1,
  }))

  const w = containerRef.value.clientWidth
  const h = containerRef.value.clientHeight

  graph3d = ForceGraph3D({ controlType: 'orbit' })(containerRef.value)
    .width(w)
    .height(h)
    .backgroundColor(t.bg)
    .showNavInfo(false)
    .graphData({ nodes: rawData.nodes.map(n => ({ ...n })), links })
    .nodeLabel((node: Record<string, unknown>) =>
      build3DLabel(node['data'] as Record<string, unknown> | undefined, node['label'] as string))
    .nodeColor(nodeColorFn)
    .nodeVal((node: Record<string, unknown>) => Math.max(1, ((node['size'] as number) ?? 20) / 6))
    .linkColor((link: Record<string, unknown>) => link['color'] as string ?? '#4b5563')
    .linkWidth((link: Record<string, unknown>) => link['width'] as number ?? 1)
    .linkOpacity(0.5)
    .onNodeClick((node: Record<string, unknown>) => {
      selected.value = (node['data'] as Record<string, unknown>) ?? null
    })
    .onNodeHover((node: unknown) => {
      if (containerRef.value) containerRef.value.style.cursor = node ? 'pointer' : 'default'
    })
}

// ─── Switch 2D ↔ 3D ──────────────────────────────────────────────────────────
async function switchView() {
  selected.value = null
  const goingTo3D = !view3D.value

  // Destroy current renderer
  if (network) { network.destroy(); network = null }
  if (graph3d) { graph3d._destructor?.(); graph3d = null }
  if (containerRef.value) containerRef.value.innerHTML = ''

  view3D.value = goingTo3D
  await nextTick()
  if (goingTo3D) {
    await build3D()
  } else {
    build2D()
  }
}

// ─── Toggle day / night ───────────────────────────────────────────────────────
async function toggleDarkMode() {
  darkMode.value = !darkMode.value
  const t = theme.value

  if (view3D.value && graph3d) {
    graph3d.backgroundColor(t.bg)
    graph3d.nodeColor((node: Record<string, unknown>) => {
      const m: Record<string, string> = { investigator: t.investigator, wp: t.wp, nodo: t.nodo, project: t.project }
      return m[node['group'] as string] ?? '#888'
    })
  } else if (!view3D.value && network && rawData) {
    if (containerRef.value) containerRef.value.style.background = t.bg
    const updates = rawData.nodes.map(n => ({
      id: n['id'],
      color: getNodeColor(n['group'] as string),
      font:  getNodeFont(n['group'] as string),
      title: n['data'] ? buildTooltip(n['data'] as Record<string, unknown>) : undefined,
    }))
    allNodes.update(updates as GraphNode[])
  }
}

// ─── 2D controls ─────────────────────────────────────────────────────────────
function applyPhysics() {
  network?.setOptions({ physics: { forceAtlas2Based: { gravitationalConstant: gravity.value, springLength: springLength.value } } })
}

function toggleUnconnected() {
  if (!network || !allNodes) return
  showUnconnected.value = !showUnconnected.value
  const connected = new Set<string>()
  allEdges.get().forEach(e => {
    if (e.from != null) connected.add(String(e.from))
    if (e.to != null) connected.add(String(e.to))
  })
  allNodes.update(allNodes.get().map((n: GraphNode) => ({
    id: n.id,
    hidden: !showUnconnected.value && !connected.has(String(n.id)),
  })))
}

function fitAll() {
  if (!view3D.value) {
    network?.fit({ animation: { duration: 600, easingFunction: 'easeInOutQuad' } })
  } else {
    graph3d?.zoomToFit?.(600)
  }
}

// ─── Fetch + init ─────────────────────────────────────────────────────────────
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
onUnmounted(() => {
  network?.destroy()
  graph3d?._destructor?.()
})

// ─── Legend items ─────────────────────────────────────────────────────────────
const legendItems = computed(() => [
  { key: 'investigator', label: 'Investigador',   color: theme.value.investigator },
  { key: 'wp',           label: 'Work Package',   color: theme.value.wp },
  { key: 'nodo',         label: 'Nodo Temático',  color: theme.value.nodo },
  { key: 'project',      label: 'Proyecto',       color: theme.value.project },
])

function typeToGroup(type: string) {
  return type === 'Investigador' ? 'investigator' : type === 'WP' ? 'wp' : type === 'Nodo' ? 'nodo' : 'project'
}
</script>

<template>
  <div
    class="fixed inset-0 md:left-56 overflow-hidden flex flex-col transition-colors duration-300"
    :style="{ backgroundColor: theme.bg }"
  >

    <!-- ── Top bar ──────────────────────────────────────────────────────────── -->
    <div
      class="flex items-center justify-between px-4 py-2 backdrop-blur border-b flex-shrink-0 z-10 transition-colors duration-300"
      :class="theme.topBar"
    >
      <!-- Left: title + stats -->
      <div class="flex items-center gap-2 min-w-0">
        <NetworkIcon class="w-4 h-4 text-indigo-400 flex-shrink-0" />
        <span class="text-sm font-semibold flex-shrink-0" :class="theme.titleCls">Mapa de Colaboración</span>
        <div v-if="stats" class="hidden sm:flex items-center gap-3 ml-3 text-xs flex-shrink-0" :class="theme.textCls">
          <span class="flex items-center gap-1"><Users class="w-3 h-3" />{{ stats.researchers }}</span>
          <span class="flex items-center gap-1"><FolderOpen class="w-3 h-3" />{{ stats.projects }}</span>
          <span class="flex items-center gap-1"><Layers class="w-3 h-3" />{{ stats.wps }} WPs</span>
          <span class="flex items-center gap-1"><BookOpen class="w-3 h-3" />{{ stats.nodes_thematic }}</span>
          <span class="opacity-30">·</span>
          <span>{{ stats.edges }} conexiones</span>
        </div>
      </div>

      <!-- Right: controls -->
      <div class="flex items-center gap-2 flex-shrink-0">

        <!-- 2D-only physics controls -->
        <template v-if="!view3D">
          <div class="hidden lg:flex items-center gap-2 text-xs" :class="theme.textCls">
            <span>Gravedad</span>
            <input type="range" min="-3000" max="-100" step="50" v-model.number="gravity"
              class="w-20 h-1 cursor-pointer" style="accent-color:#818cf8" @change="applyPhysics" />
            <span class="w-12 tabular-nums">{{ gravity }}</span>
          </div>
          <div class="hidden lg:flex items-center gap-2 text-xs" :class="theme.textCls">
            <span>Distancia</span>
            <input type="range" min="50" max="400" step="10" v-model.number="springLength"
              class="w-20 h-1 cursor-pointer" style="accent-color:#818cf8" @change="applyPhysics" />
            <span class="w-8 tabular-nums">{{ springLength }}</span>
          </div>
          <button
            class="hidden lg:block px-2 py-1 text-xs rounded border transition-colors"
            :class="[showUnconnected ? 'border-slate-600 hover:border-slate-400' : 'border-indigo-500 text-indigo-400', theme.textCls]"
            @click="toggleUnconnected"
          >
            {{ showUnconnected ? 'Ocultar aislados' : 'Mostrar todos' }}
          </button>
        </template>

        <!-- Encuadrar -->
        <button
          class="px-2 py-1 text-xs rounded border border-slate-500 transition-colors"
          :class="theme.textCls"
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

        <!-- Day / Night toggle -->
        <button
          class="p-1.5 rounded-lg border transition-colors"
          :class="darkMode
            ? 'border-slate-700 text-yellow-400 hover:border-slate-500 hover:bg-yellow-400/10'
            : 'border-slate-300 text-indigo-600 hover:border-indigo-400 hover:bg-indigo-50'"
          :title="darkMode ? 'Cambiar a modo día' : 'Cambiar a modo noche'"
          @click="toggleDarkMode"
        >
          <component :is="darkMode ? Sun : Moon" class="w-3.5 h-3.5" />
        </button>
      </div>
    </div>

    <!-- ── Loading ────────────────────────────────────────────────────────────── -->
    <div v-if="loading" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <div class="w-8 h-8 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p class="text-indigo-400 text-sm">Construyendo red de colaboración…</p>
      </div>
    </div>

    <!-- ── Error ──────────────────────────────────────────────────────────────── -->
    <div v-else-if="error" class="flex-1 flex items-center justify-center">
      <p class="text-red-400 text-sm">{{ error }}</p>
    </div>

    <!-- ── Graph container (2D + 3D comparten el mismo div) ───────────────────── -->
    <div v-show="!loading && !error" ref="containerRef" class="flex-1 w-full" />

    <!-- ── Leyenda ─────────────────────────────────────────────────────────────── -->
    <div class="absolute bottom-4 left-4 z-10 flex flex-col gap-1.5 pointer-events-none">
      <div v-if="view3D" class="mb-1 flex items-center gap-1.5 text-xs font-medium text-indigo-400">
        <Box class="w-3 h-3" /> Vista 3D — arrastra para rotar
      </div>
      <div v-for="item in legendItems" :key="item.key" class="flex items-center gap-2">
        <span class="w-3 h-3 rounded-full border border-white/20" :style="{ backgroundColor: item.color }" />
        <span class="text-xs" :class="theme.legendCls">{{ item.label }}</span>
      </div>
    </div>

    <!-- ── Panel detalle nodo seleccionado ────────────────────────────────────── -->
    <Transition name="slide">
      <div
        v-if="selected"
        class="absolute top-14 right-3 z-20 w-64 backdrop-blur border rounded-xl p-4 shadow-2xl transition-colors duration-200"
        :class="theme.panelCls"
      >
        <!-- Header tipo -->
        <div class="flex items-start justify-between mb-3">
          <span
            class="text-xs font-semibold px-2 py-0.5 rounded-full"
            :style="{
              backgroundColor: legendItems.find(i => i.key === typeToGroup(selected!['type'] as string))?.color + '28',
              color: legendItems.find(i => i.key === typeToGroup(selected!['type'] as string))?.color
            }"
          >{{ selected['type'] }}</span>
          <button :class="darkMode ? 'text-slate-500 hover:text-slate-300' : 'text-slate-400 hover:text-slate-700'" @click="selected = null">
            <X class="w-4 h-4" />
          </button>
        </div>

        <!-- Nombre -->
        <p class="font-semibold text-sm leading-snug mb-3" :class="theme.titleCls">{{ selected['name'] }}</p>

        <!-- Datos -->
        <div class="space-y-1.5 text-xs">
          <div v-if="selected['institution']" class="flex gap-2">
            <span class="w-20 flex-shrink-0" :class="theme.labelCls">Institución</span>
            <span class="truncate" :class="theme.valueCls">{{ selected['institution'] }}</span>
          </div>
          <div v-if="selected['orcid']" class="flex gap-2">
            <span class="w-20 flex-shrink-0" :class="theme.labelCls">ORCID</span>
            <span class="font-mono text-indigo-400 text-xs truncate">{{ selected['orcid'] }}</span>
          </div>
          <div v-if="selected['h_index'] != null" class="flex gap-2 items-baseline">
            <span class="w-20 flex-shrink-0" :class="theme.labelCls">H-index</span>
            <span class="font-bold text-blue-400 text-xl leading-none">{{ selected['h_index'] }}</span>
          </div>
          <div v-if="selected['citations'] != null" class="flex gap-2">
            <span class="w-20 flex-shrink-0" :class="theme.labelCls">Citas</span>
            <span :class="theme.valueCls">{{ Number(selected['citations']).toLocaleString('es-CL') }}</span>
          </div>
          <div v-if="selected['works'] != null" class="flex gap-2">
            <span class="w-20 flex-shrink-0" :class="theme.labelCls">Publicaciones</span>
            <span :class="theme.valueCls">{{ selected['works'] }}</span>
          </div>
          <div v-if="selected['category']" class="flex gap-2">
            <span class="w-20 flex-shrink-0" :class="theme.labelCls">Categoría</span>
            <span :class="theme.valueCls">{{ selected['category'] }}</span>
          </div>
          <div v-if="selected['email']" class="flex gap-2">
            <span class="w-20 flex-shrink-0" :class="theme.labelCls">Email</span>
            <span class="truncate" :class="theme.valueCls">{{ selected['email'] }}</span>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.slide-enter-active, .slide-leave-active { transition: opacity 0.15s, transform 0.15s; }
.slide-enter-from, .slide-leave-to { opacity: 0; transform: translateX(8px); }
</style>
