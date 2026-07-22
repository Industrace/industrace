<template>
  <div class="mfa-enroll-page">
    <div class="mfa-card">
      <h1>{{ t('mfa.setupTitle') }}</h1>
      <p>{{ t('mfa.setupRequired') }}</p>
      <MfaSetupWizard @done="onDone" @cancel="onCancel" />
    </div>
    <Toast position="top-right" />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import Toast from 'primevue/toast'
import MfaSetupWizard from '@/components/mfa/MfaSetupWizard.vue'

const { t } = useI18n()
const router = useRouter()

onMounted(() => {
  if (!sessionStorage.getItem('mfa_setup_token')) {
    router.replace('/login')
  }
})

function onDone() {
  sessionStorage.removeItem('mfa_setup_token')
  router.push('/login')
}

function onCancel() {
  sessionStorage.removeItem('mfa_setup_token')
  router.push('/login')
}
</script>

<style scoped>
.mfa-enroll-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(160deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
  padding: 1.5rem;
}
.mfa-card {
  width: 100%;
  max-width: 480px;
  background: #fff;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.25);
}
.mfa-card h1 {
  margin: 0 0 0.5rem;
  font-size: 1.4rem;
}
.mfa-card > p {
  color: #64748b;
  margin: 0 0 1.25rem;
}
</style>
