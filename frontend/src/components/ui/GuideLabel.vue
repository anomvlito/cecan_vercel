<script setup lang="ts">
import { HelpCircle } from 'lucide-vue-next'
import { useGuideStore } from '@/stores/guide'
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue'

const props = withDefaults(defineProps<{
  text: string
  position?: 'top' | 'bottom' | 'left' | 'right'
}>(), {
  position: 'bottom',
})

const guideStore = useGuideStore()
const wrapperRef = ref<HTMLElement | null>(null)
const style = ref<Record<string, string>>({})
const GAP = 10

function computePosition() {
  if (!wrapperRef.value || !guideStore.active) return
  const r = wrapperRef.value.getBoundingClientRect()

  if (props.position === 'bottom') {
    style.value = {
      top: `${r.bottom + GAP}px`,
      left: `${r.left + r.width / 2}px`,
      transform: 'translateX(-50%)',
    }
  } else if (props.position === 'top') {
    style.value = {
      top: `${r.top - GAP}px`,
      left: `${r.left + r.width / 2}px`,
      transform: 'translate(-50%, -100%)',
    }
  } else if (props.position === 'left') {
    style.value = {
      top: `${r.top + r.height / 2}px`,
      left: `${r.left - GAP}px`,
      transform: 'translate(-100%, -50%)',
    }
  } else {
    style.value = {
      top: `${r.top + r.height / 2}px`,
      left: `${r.right + GAP}px`,
      transform: 'translateY(-50%)',
    }
  }
}

watch(() => guideStore.active, async (val) => {
  if (val) { await nextTick(); computePosition() }
})

onMounted(() => {
  window.addEventListener('scroll', computePosition, { passive: true, capture: true })
  window.addEventListener('resize', computePosition, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('scroll', computePosition, true)
  window.removeEventListener('resize', computePosition)
})
</script>

<template>
  <div ref="wrapperRef" class="inline-flex">
    <slot />
  </div>

  <Teleport to="body">
    <Transition name="guide-fade">
      <div
        v-if="guideStore.active"
        class="fixed z-[500] pointer-events-none"
        :style="style"
      >
        <div class="flex items-start gap-1.5 bg-blue-900/95 border border-blue-500 text-white text-xs rounded-lg px-2.5 py-2 shadow-xl backdrop-blur-sm max-w-[220px] whitespace-normal">
          <HelpCircle class="w-3.5 h-3.5 text-blue-300 flex-shrink-0 mt-px" />
          <span class="leading-snug">{{ props.text }}</span>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.guide-fade-enter-active,
.guide-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.guide-fade-enter-from,
.guide-fade-leave-to {
  opacity: 0;
  transform: scale(0.95);
}
</style>
