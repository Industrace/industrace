<template>
  <div class="sso-error-container">
    <div class="sso-error-card">
      <div class="error-icon">
        <i class="pi pi-times-circle"></i>
      </div>
      <h1>{{ $t('sso.error.title') }}</h1>
      <p>{{ errorMessage || $t('sso.error.message') }}</p>
      <Button 
        :label="$t('sso.error.backToLogin')" 
        @click="goToLogin"
        class="back-button"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import Button from 'primevue/button'

const router = useRouter()
const route = useRoute()
const { t } = useI18n()

const errorMessage = ref('')

onMounted(() => {
  const error = route.query.error
  if (error) {
    errorMessage.value = decodeURIComponent(error)
  }
})

const goToLogin = () => {
  router.push('/login')
}
</script>

<style scoped>
.sso-error-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
}

.sso-error-card {
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

.error-icon {
  font-size: 4rem;
  color: #ef4444;
  margin-bottom: 1rem;
}

.sso-error-card h1 {
  font-size: 2rem;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 1rem 0;
}

.sso-error-card p {
  color: #64748b;
  font-size: 1rem;
  margin: 0 0 2rem 0;
  word-break: break-word;
}

.back-button {
  padding: 0.75rem 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 12px;
  color: white;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.back-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
}
</style>

