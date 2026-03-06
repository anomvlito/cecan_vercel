<script setup lang="ts">
import { ref, watch } from 'vue'
import { X } from 'lucide-vue-next'
import type { ProjectActivity } from '@/types/publication'

const props = defineProps<{
  activity: ProjectActivity | null
}>()

const emit = defineEmits<{
  close: []
  save: [status: string, progress: number, budget: number | null, paymentStatus: string]
}>()

// Local form state
const localStatus = ref('pending')
const localProgress = ref(0)
const localBudget = ref<number | null>(null)
const localPaymentStatus = ref('pending')

// Sync form state when activity changes
watch(
  () => props.activity,
  (act) => {
    if (!act) return
    localStatus.value = act.status
    localProgress.value = act.progress
    localBudget.value = act.budget_allocated
    localPaymentStatus.value = act.payment_status ?? 'pending'
  },
  { immediate: true },
)

function selectStatus(s: string) {
  localStatus.value = s
  if (s === 'done') {
    localProgress.value = 100
  } else if (s === 'pending') {
    localProgress.value = 0
  }
}

function onProgressChange(val: number) {
  localProgress.value = val
  if (val === 100) {
    localStatus.value = 'done'
  } else if (val > 0 && localStatus.value === 'pending') {
    localStatus.value = 'in_progress'
  }
}

function onSave() {
  emit('save', localStatus.value, localProgress.value, localBudget.value, localPaymentStatus.value)
}

const statusOptions: { value: string; label: string; cls: string }[] = [
  { value: 'pending',     label: 'Pendiente',  cls: 'bg-gray-100 text-gray-700 border-gray-300 hover:bg-gray-200' },
  { value: 'in_progress', label: 'En curso',   cls: 'bg-blue-100 text-blue-700 border-blue-300 hover:bg-blue-200' },
  { value: 'done',        label: 'Terminada',  cls: 'bg-green-100 text-green-700 border-green-300 hover:bg-green-200' },
  { value: 'blocked',     label: 'Bloqueada',  cls: 'bg-red-100 text-red-700 border-red-300 hover:bg-red-200' },
]

const activeStatusCls: Record<string, string> = {
  pending:     'ring-2 ring-gray-500 bg-gray-200',
  in_progress: 'ring-2 ring-blue-500 bg-blue-200',
  done:        'ring-2 ring-green-500 bg-green-200',
  blocked:     'ring-2 ring-red-500 bg-red-200',
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="activity !== null"
      class="fixed inset-0 bg-black/40 z-50 flex items-center justify-center p-4"
      @click.self="emit('close')"
    >
      <div class="bg-white rounded-xl shadow-2xl w-full max-w-md">
        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <div>
            <h2 class="text-base font-semibold text-gray-900">Actualizar estado</h2>
            <p class="text-xs text-gray-500 mt-0.5 line-clamp-2">{{ activity?.description }}</p>
          </div>
          <button class="text-gray-400 hover:text-gray-600 ml-4 flex-shrink-0" @click="emit('close')">
            <X class="w-5 h-5" />
          </button>
        </div>

        <!-- Body -->
        <div class="p-6 space-y-5">
          <!-- Status grid -->
          <div>
            <p class="text-sm font-medium text-gray-700 mb-2">Estado</p>
            <div class="grid grid-cols-2 gap-2">
              <button
                v-for="opt in statusOptions"
                :key="opt.value"
                type="button"
                class="px-3 py-2 rounded-lg border text-sm font-medium transition-all"
                :class="[opt.cls, localStatus === opt.value ? activeStatusCls[opt.value] : '']"
                @click="selectStatus(opt.value)"
              >
                {{ opt.label }}
              </button>
            </div>
          </div>

          <!-- Progress slider -->
          <div>
            <div class="flex items-center justify-between mb-1">
              <p class="text-sm font-medium text-gray-700">Avance</p>
              <span class="text-sm font-bold text-gray-900">{{ localProgress }}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="100"
              step="5"
              :value="localProgress"
              :disabled="localStatus === 'pending'"
              class="w-full accent-blue-600 disabled:opacity-40 disabled:cursor-not-allowed"
              @input="onProgressChange(Number(($event.target as HTMLInputElement).value))"
            />
            <div class="flex justify-between text-xs text-gray-400 mt-0.5">
              <span>0%</span>
              <span>50%</span>
              <span>100%</span>
            </div>
          </div>

          <!-- Budget -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Presupuesto asignado</label>
            <div class="relative">
              <span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">$</span>
              <input
                v-model.number="localBudget"
                type="number"
                min="0"
                step="1000"
                placeholder="Opcional"
                class="w-full pl-7 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <!-- Payment status -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">Estado de pago</label>
            <select
              v-model="localPaymentStatus"
              class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="pending">Pendiente</option>
              <option value="paid">Pagado</option>
            </select>
          </div>
        </div>

        <!-- Footer -->
        <div class="flex justify-end gap-3 px-6 py-4 border-t border-gray-200">
          <button
            type="button"
            class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 rounded-lg hover:bg-gray-50"
            @click="emit('close')"
          >
            Cancelar
          </button>
          <button
            type="button"
            class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
            @click="onSave"
          >
            Guardar
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
