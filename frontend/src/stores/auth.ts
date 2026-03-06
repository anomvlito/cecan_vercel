import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/services/api'

interface AuthUser {
  email: string
  role: string
  academic_member_id: number | null
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('cecan_token'))
  const user = ref<AuthUser | null>(
    JSON.parse(localStorage.getItem('cecan_user') ?? 'null'),
  )

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function login(email: string, password: string) {
    const data = await authApi.login(email, password)
    token.value = data.access_token
    user.value = { email: data.email, role: data.role, academic_member_id: data.academic_member_id }
    localStorage.setItem('cecan_token', data.access_token)
    localStorage.setItem('cecan_user', JSON.stringify(user.value))
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('cecan_token')
    localStorage.removeItem('cecan_user')
  }

  return { token, user, isAuthenticated, isAdmin, login, logout }
})
