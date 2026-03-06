import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useGuideStore = defineStore('guide', () => {
  const active = ref(false)

  function toggle() {
    active.value = !active.value
  }

  return { active, toggle }
})
