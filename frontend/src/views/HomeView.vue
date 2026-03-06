<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import api from '@/services/api'

// ─── Types ───────────────────────────────────────────────────────────────────
interface MapPoint {
  id: number
  x: number
  y: number
  z: number
  cluster_id: number
  cluster_label: string
  color: string
  publication_id: number | null
  title: string | null
  year: number | null
  authors: string | null
  quartile: string | null
  doi: string | null
}

interface Cluster {
  id: number
  label: string
  color: string
  count: number
}

// ─── State ───────────────────────────────────────────────────────────────────
const canvasRef = ref<HTMLCanvasElement | null>(null)
const loading = ref(true)
const error = ref<string | null>(null)
const points = ref<MapPoint[]>([])
const clusters = ref<Cluster[]>([])
const hovered = ref<MapPoint | null>(null)
const tooltipPos = ref({ x: 0, y: 0 })
const visibleClusters = ref<Set<number>>(new Set())

// Three.js objects
let renderer: THREE.WebGLRenderer
let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let controls: OrbitControls
let starField: THREE.Points
let animationId: number
let raycaster: THREE.Raycaster
let mouse: THREE.Vector2
const pointObjects: { mesh: THREE.Mesh; point: MapPoint }[] = []

const CLUSTER_COLORS: Record<number, number> = {
  0: 0x60a5fa,
  1: 0xa78bfa,
  2: 0x34d399,
  3: 0xfb923c,
  4: 0xf472b6,
}

const QUARTILE_BADGE: Record<string, string> = {
  Q1: 'bg-green-100 text-green-800',
  Q2: 'bg-blue-100 text-blue-800',
  Q3: 'bg-yellow-100 text-yellow-800',
  Q4: 'bg-red-100 text-red-800',
}

// ─── Fetch data ───────────────────────────────────────────────────────────────
async function fetchMap() {
  const { data } = await api.get('/research-map')
  points.value = data.points
  clusters.value = data.clusters
  visibleClusters.value = new Set(data.clusters.map((c: Cluster) => c.id))
}

// ─── Dimensiones del canvas ───────────────────────────────────────────────────
function canvasSize(): { w: number; h: number } {
  const sidebar = 224 // w-56
  const topbar = window.innerWidth < 768 ? 56 : 0
  return {
    w: window.innerWidth - sidebar,
    h: window.innerHeight - topbar,
  }
}

// ─── Three.js setup ───────────────────────────────────────────────────────────
function initScene() {
  const canvas = canvasRef.value!
  const { w, h } = canvasSize()

  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  renderer.setSize(w, h)
  renderer.setClearColor(0x06080f, 1)

  scene = new THREE.Scene()
  scene.fog = new THREE.FogExp2(0x06080f, 0.04)

  camera = new THREE.PerspectiveCamera(60, w / h, 0.1, 200)

  camera.position.set(5, 8, 18)

  controls = new OrbitControls(camera, canvas)
  controls.enableDamping = true
  controls.dampingFactor = 0.06
  controls.minDistance = 3
  controls.maxDistance = 40
  controls.autoRotate = true
  controls.autoRotateSpeed = 0.4

  raycaster = new THREE.Raycaster()
  raycaster.params.Points = { threshold: 0.3 }
  mouse = new THREE.Vector2()

  buildScene()
}

function buildScene() {
  pointObjects.length = 0
  // Remover todo excepto fog
  while (scene.children.length > 0) scene.remove(scene.children[0]!)

  // Centro de masa de los puntos para centrar la escena
  const cx = (p: MapPoint) => p.x - 5.2
  const cy = (p: MapPoint) => p.y - 5.6
  const cz = (p: MapPoint) => p.z - 9.9

  // ── Estrellas de fondo ────────────────────────────────────────────────────
  const bgCount = 800
  const bgPos = new Float32Array(bgCount * 3)
  for (let i = 0; i < bgCount; i++) {
    bgPos[i * 3] = (Math.random() - 0.5) * 80
    bgPos[i * 3 + 1] = (Math.random() - 0.5) * 80
    bgPos[i * 3 + 2] = (Math.random() - 0.5) * 80
  }
  const bgGeo = new THREE.BufferGeometry()
  bgGeo.setAttribute('position', new THREE.BufferAttribute(bgPos, 3))
  starField = new THREE.Points(
    bgGeo,
    new THREE.PointsMaterial({ color: 0xffffff, size: 0.06, transparent: true, opacity: 0.35 }),
  )
  scene.add(starField)

  // ── Puntos de publicaciones ───────────────────────────────────────────────
  const filtered = points.value.filter(p => visibleClusters.value.has(p.cluster_id))

  filtered.forEach(p => {
    const color = CLUSTER_COLORS[p.cluster_id] ?? 0x94a3b8
    const geo = new THREE.SphereGeometry(0.14, 16, 16)
    const mat = new THREE.MeshStandardMaterial({
      color,
      emissive: color,
      emissiveIntensity: 0.5,
      roughness: 0.3,
      metalness: 0.1,
    })
    const mesh = new THREE.Mesh(geo, mat)
    mesh.position.set(cx(p), cy(p), cz(p))
    scene.add(mesh)
    pointObjects.push({ mesh, point: p })

    // Halo suave
    const haloGeo = new THREE.SphereGeometry(0.26, 8, 8)
    const haloMat = new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity: 0.07,
      side: THREE.BackSide,
    })
    mesh.add(new THREE.Mesh(haloGeo, haloMat))
  })

  // ── Líneas dentro de cada cluster ─────────────────────────────────────────
  const byCluster: Record<number, MapPoint[]> = {}
  filtered.forEach(p => {
    if (!byCluster[p.cluster_id]) byCluster[p.cluster_id] = [] as MapPoint[]
    byCluster[p.cluster_id]!.push(p)
  })

  Object.entries(byCluster).forEach(([cid, pts]) => {
    const color = CLUSTER_COLORS[Number(cid)] ?? 0x94a3b8
    if (pts.length < 2) return
    const verts: number[] = []
    pts.forEach((a, i) => {
      pts.slice(i + 1).forEach(b => {
        const dx = cx(a) - cx(b), dy = cy(a) - cy(b), dz = cz(a) - cz(b)
        if (Math.sqrt(dx * dx + dy * dy + dz * dz) < 2.5) {
          verts.push(cx(a), cy(a), cz(a), cx(b), cy(b), cz(b))
        }
      })
    })
    if (verts.length > 0) {
      const lineGeo = new THREE.BufferGeometry()
      lineGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(verts), 3))
      scene.add(
        new THREE.LineSegments(
          lineGeo,
          new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.18 }),
        ),
      )
    }
  })

  // ── Luces ─────────────────────────────────────────────────────────────────
  scene.add(new THREE.AmbientLight(0xffffff, 0.3))
  const dirLight = new THREE.DirectionalLight(0xffffff, 1)
  dirLight.position.set(10, 20, 10)
  scene.add(dirLight)
}

// ─── Animation loop ───────────────────────────────────────────────────────────
function animate() {
  animationId = requestAnimationFrame(animate)
  controls.update()
  if (starField) starField.rotation.y += 0.00015

  const t = Date.now() * 0.001
  pointObjects.forEach(({ mesh }, i) => {
    mesh.scale.setScalar(1 + Math.sin(t * 1.2 + i * 0.7) * 0.12)
  })

  renderer.render(scene, camera)
}

// ─── Mouse interaction ────────────────────────────────────────────────────────
function onMouseMove(e: MouseEvent) {
  const canvas = canvasRef.value!
  const rect = canvas.getBoundingClientRect()
  mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1
  mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1

  raycaster.setFromCamera(mouse, camera)
  const meshes = pointObjects.map(p => p.mesh)
  const intersects = raycaster.intersectObjects(meshes)

  if (intersects.length > 0) {
    const hit = intersects[0]!.object as THREE.Mesh
    const found = pointObjects.find(p => p.mesh === hit)
    if (found) {
      // Restaurar anterior
      if (hovered.value && hovered.value.id !== found.point.id) {
        const prev = pointObjects.find(p => p.point.id === hovered.value!.id)
        if (prev) (prev.mesh.material as THREE.MeshStandardMaterial).emissiveIntensity = 0.5
      }
      hovered.value = found.point
      tooltipPos.value = { x: e.clientX, y: e.clientY }
      canvas.style.cursor = 'pointer'
      ;(hit.material as THREE.MeshStandardMaterial).emissiveIntensity = 1.8
    }
  } else {
    if (hovered.value) {
      const prev = pointObjects.find(p => p.point.id === hovered.value!.id)
      if (prev) (prev.mesh.material as THREE.MeshStandardMaterial).emissiveIntensity = 0.5
    }
    hovered.value = null
    canvas.style.cursor = 'default'
  }
}

// ─── Resize ───────────────────────────────────────────────────────────────────
function onResize() {
  const { w, h } = canvasSize()
  camera.aspect = w / h
  camera.updateProjectionMatrix()
  renderer.setSize(w, h)
}

// ─── Toggle cluster visibility ────────────────────────────────────────────────
function toggleCluster(id: number) {
  const next = new Set(visibleClusters.value)
  if (next.has(id)) {
    if (next.size === 1) return
    next.delete(id)
  } else {
    next.add(id)
  }
  visibleClusters.value = next
  buildScene()
}

// ─── Lifecycle ────────────────────────────────────────────────────────────────
onMounted(async () => {
  try {
    await fetchMap()
    loading.value = false
    await new Promise(r => setTimeout(r, 50))
    initScene()
    animate()
    window.addEventListener('resize', onResize)
    canvasRef.value?.addEventListener('mousemove', onMouseMove)
  } catch (e) {
    loading.value = false
    error.value = `Error cargando el mapa: ${e instanceof Error ? e.message : 'Sin conexión al servidor'}`
  }
})

onUnmounted(() => {
  cancelAnimationFrame(animationId)
  window.removeEventListener('resize', onResize)
  canvasRef.value?.removeEventListener('mousemove', onMouseMove)
  renderer?.dispose()
})

const truncate = (s: string | null, n: number) =>
  s && s.length > n ? s.slice(0, n) + '…' : (s ?? '—')

const hoveredClusterColor = computed(
  () => clusters.value.find(c => c.id === hovered.value?.cluster_id)?.color ?? '#94a3b8',
)
</script>

<template>
  <div class="fixed inset-0 md:left-56 bg-[#06080f] overflow-hidden select-none" style="top: 0">

    <!-- Loading -->
    <div v-if="loading" class="absolute inset-0 flex items-center justify-center z-10">
      <div class="text-center">
        <div class="w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p class="text-blue-300 text-sm">Cargando constelaciones…</p>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="error" class="absolute inset-0 flex items-center justify-center z-10">
      <div class="text-center max-w-sm px-6">
        <p class="text-red-400 text-sm font-medium mb-1">No se pudo cargar el mapa</p>
        <p class="text-gray-600 text-xs">{{ error }}</p>
      </div>
    </div>

    <!-- Canvas 3D -->
    <canvas ref="canvasRef" />

    <!-- Título flotante -->
    <div class="absolute top-4 left-6 z-10 pointer-events-none">
      <p class="text-xs font-semibold text-blue-400 tracking-widest uppercase mb-1">CECAN Research Map</p>
      <h1 class="text-2xl font-bold text-white leading-tight">Mapa de Publicaciones</h1>
      <p class="text-sm text-gray-400 mt-0.5">
        {{ points.length }} publicaciones · {{ clusters.length }} clusters temáticos
      </p>
    </div>

    <!-- Leyenda de clusters -->
    <div class="absolute bottom-6 left-6 z-10 space-y-1.5">
      <button
        v-for="c in clusters"
        :key="c.id"
        class="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium transition-all border backdrop-blur-sm"
        :style="{
          borderColor: visibleClusters.has(c.id) ? c.color : 'transparent',
          backgroundColor: visibleClusters.has(c.id) ? c.color + '22' : '#ffffff0a',
          color: visibleClusters.has(c.id) ? c.color : '#4b5563',
        }"
        @click="toggleCluster(c.id)"
      >
        <span
          class="w-2 h-2 rounded-full flex-shrink-0 transition-colors"
          :style="{ backgroundColor: visibleClusters.has(c.id) ? c.color : '#4b5563' }"
        />
        {{ c.label }}
        <span class="opacity-50">({{ c.count }})</span>
      </button>
    </div>

    <!-- Hint controles -->
    <div class="absolute bottom-6 right-6 z-10 text-right pointer-events-none">
      <p class="text-xs text-gray-700">Arrastrar para rotar · Scroll para zoom</p>
    </div>

    <!-- Tooltip hover -->
    <Transition name="tooltip">
      <div
        v-if="hovered"
        class="fixed z-20 pointer-events-none"
        :style="{ left: `${tooltipPos.x + 16}px`, top: `${tooltipPos.y - 12}px` }"
      >
        <div
          class="bg-gray-900/95 backdrop-blur-sm border rounded-xl px-4 py-3 max-w-xs shadow-2xl"
          :style="{ borderColor: hoveredClusterColor + '55' }"
        >
          <div class="flex items-start gap-2 mb-2">
            <span
              class="w-2 h-2 rounded-full flex-shrink-0 mt-1"
              :style="{ backgroundColor: hoveredClusterColor }"
            />
            <p class="text-xs font-semibold text-white leading-snug">
              {{ truncate(hovered.title, 80) }}
            </p>
          </div>
          <div class="space-y-0.5 text-xs text-gray-400">
            <p v-if="hovered.authors">{{ truncate(hovered.authors, 60) }}</p>
            <div class="flex items-center gap-2 mt-1.5">
              <span v-if="hovered.year" class="text-gray-300">{{ hovered.year }}</span>
              <span
                v-if="hovered.quartile"
                class="px-1.5 py-0.5 rounded text-xs font-bold"
                :class="QUARTILE_BADGE[hovered.quartile] ?? 'bg-gray-700 text-gray-300'"
              >{{ hovered.quartile }}</span>
              <span class="text-gray-600">{{ hovered.cluster_label }}</span>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.tooltip-enter-active,
.tooltip-leave-active {
  transition: opacity 0.12s, transform 0.12s;
}
.tooltip-enter-from,
.tooltip-leave-to {
  opacity: 0;
  transform: translateY(4px);
}
</style>
