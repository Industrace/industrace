import { computed } from 'vue'
import { useAuthStore } from '@/store/auth'

/**
 * Per-tenant feature flags (from GET /users/me → features).
 * Defaults to enabled when not yet loaded (backward compatible).
 */
export function useTenantFeatures() {
  const authStore = useAuthStore()

  const features = computed(() => authStore.user?.features || { iec62443: true })

  const isIec62443Enabled = computed(() => features.value.iec62443 !== false)

  return {
    features,
    isIec62443Enabled,
  }
}
