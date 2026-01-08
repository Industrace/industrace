<template>
  <div class="sso-success-container">
    <div class="sso-success-card">
      <div class="success-icon">
        <i class="pi pi-check-circle"></i>
      </div>
      <h1>{{ $t('sso.success.title') }}</h1>
      <p>{{ $t('sso.success.message') }}</p>
      <div v-if="loading" class="loading-spinner">
        <ProgressSpinner />
      </div>
      <div v-if="error" class="error-message">
        <Message severity="error" :closable="false">
          {{ error }}
        </Message>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../store/auth'
import { useI18n } from 'vue-i18n'
import ProgressSpinner from 'primevue/progressspinner'
import Message from 'primevue/message'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const { t } = useI18n()

const loading = ref(true)
const error = ref(null)

onMounted(async () => {
  try {
    // The backend sets a secure httponly cookie, but we also need the token in localStorage
    // for the API interceptor. The backend also passes it as a query parameter for this purpose.
    const token = route.query.token
    
    if (!token) {
      error.value = t('sso.success.noToken')
      loading.value = false
      // Redirect to login after showing error
      setTimeout(() => {
        router.push('/login')
      }, 3000)
      return
    }

    // Validate token format (basic check)
    if (token.length < 10) {
      error.value = t('sso.success.invalidToken')
      loading.value = false
      setTimeout(() => {
        router.push('/login')
      }, 3000)
      return
    }

    // Set token in localStorage (will be picked up by API interceptor)
    // The backend also sets a secure cookie, but localStorage is needed for the interceptor
    localStorage.setItem('access_token', token)
    
    // IMPORTANT: Set isAuthenticated BEFORE fetchUser to prevent logout on error
    // The token is already set, so we're authenticated
    authStore.isAuthenticated = true
    
    // Fetch user info using the auth store
    // Pass suppressLogout=true to prevent automatic logout if fetchUser fails
    // This is important for SSO where we have a valid token but fetchUser might fail temporarily
    try {
      await authStore.fetchUser(true)
      
      // Verify that user was fetched successfully
      if (!authStore.user) {
        throw new Error('User data not available after fetch')
      }
      
      // Start token refresh mechanism
      authStore.startTokenRefresh()
      
      // Redirect to dashboard
      router.push('/')
    } catch (fetchErr) {
      console.error('Failed to fetch user on SSO success:', fetchErr)
      
      // Even if fetchUser fails, try to navigate - the router guard will verify the token
      // If the token is valid, the guard will allow navigation
      // If not, it will redirect to login
      authStore.startTokenRefresh()
      router.push('/')
    }
  } catch (err) {
    console.error('SSO success error:', err)
    error.value = err.response?.data?.detail || err.message || t('sso.success.error')
    loading.value = false
    
    // Clear any partial auth state
    localStorage.removeItem('access_token')
    authStore.isAuthenticated = false
    
    // Redirect to login after showing error
    setTimeout(() => {
      router.push('/login')
    }, 3000)
  }
})
</script>

<style scoped>
.sso-success-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
}

.sso-success-card {
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 3rem;
  box-shadow: 
    0 20px 40px rgba(0,0,0,0.08),
    0 0 0 1px rgba(255,255,255,0.8);
  text-align: center;
  max-width: 500px;
  width: 100%;
}

.success-icon {
  font-size: 4rem;
  color: #10b981;
  margin-bottom: 1rem;
}

.sso-success-card h1 {
  font-size: 2rem;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 1rem 0;
}

.sso-success-card p {
  color: #64748b;
  font-size: 1rem;
  margin: 0 0 2rem 0;
}

.loading-spinner {
  margin: 2rem 0;
}

.error-message {
  margin-top: 1rem;
}
</style>

