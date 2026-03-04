<template>
  <div class="space-y-4">
    <!-- Status Banner -->
    <div
      class="rounded-2xl border shadow-sm p-6"
      :class="result.journal_found ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'"
    >
      <div class="flex items-start gap-4">
        <div
          class="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
          :class="result.journal_found ? 'bg-green-100' : 'bg-yellow-100'"
        >
          <CheckCircle v-if="result.journal_found" class="w-5 h-5 text-green-600" />
          <AlertTriangle v-else class="w-5 h-5 text-yellow-600" />
        </div>
        <div>
          <h3 class="font-semibold text-gray-900">{{ result.message }}</h3>
          <p v-if="result.doi" class="text-sm text-gray-500 mt-1 font-mono">
            DOI: {{ result.doi }}
            <span class="text-xs text-gray-400 ml-2">(via {{ result.doi_method }})</span>
          </p>
        </div>
      </div>
    </div>

    <!-- Publication Info -->
    <div class="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
      <h3 class="font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <FileText class="w-5 h-5 text-gray-400" />
        Publicación
      </h3>
      <div class="space-y-2 text-sm">
        <InfoRow label="Archivo" :value="result.publication.pdf_filename ?? '—'" />
        <InfoRow label="Título" :value="result.publication.title ?? 'No detectado'" />
        <InfoRow label="Año" :value="result.publication.year?.toString() ?? '—'" />
        <InfoRow label="Estado" :value="result.publication.status" />
      </div>
    </div>

    <!-- Journal Metrics -->
    <div
      v-if="result.publication.journal_id"
      class="bg-white rounded-2xl border border-gray-200 shadow-sm p-6"
    >
      <h3 class="font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <BarChart2 class="w-5 h-5 text-gray-400" />
        Métricas JCR
      </h3>

      <div class="grid grid-cols-2 gap-4 mb-4">
        <MetricCard
          label="Impact Factor"
          :value="formatNum(result.publication.impact_factor_snapshot)"
          icon="trend"
        />
        <MetricCard
          label="Quartil"
          :value="result.publication.quartile_snapshot ?? '—'"
          :badge-color="quartileColor(result.publication.quartile_snapshot)"
          icon="rank"
        />
        <MetricCard
          label="JIF Percentile"
          :value="formatNum(result.publication.jif_percentile_snapshot, 1) + '%'"
          icon="percent"
        />
      </div>
    </div>

    <div v-else-if="result.doi_found" class="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
      <p class="text-sm text-gray-500 text-center py-2">
        La revista con ISSN <strong>{{ result.publication.journal_issn_raw }}</strong> no se encontró en la base de datos JCR.
      </p>
    </div>

    <!-- Actions -->
    <div class="flex justify-end">
      <button
        class="px-6 py-2.5 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-colors"
        @click="emit('uploadAnother')"
      >
        Subir otro PDF
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { CheckCircle, AlertTriangle, FileText, BarChart2 } from 'lucide-vue-next'
import type { UploadResult } from '@/types/publication'
import { QUARTILE_COLORS } from '@/types/publication'
import InfoRow from '@/components/ui/InfoRow.vue'
import MetricCard from '@/components/ui/MetricCard.vue'

const props = defineProps<{ result: UploadResult }>()
const emit = defineEmits<{ uploadAnother: [] }>()

function formatNum(value: number | null | undefined, decimals = 3): string {
  if (value == null) return '—'
  return value.toFixed(decimals)
}

function quartileColor(q: string | null): string {
  return q ? (QUARTILE_COLORS[q] ?? '') : ''
}
</script>
