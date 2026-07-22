<template>
  <div class="mfa-verify-page">
    <div class="mfa-card">
      <h1>{{ t('mfa.verifyTitle') }}</h1>
      <p>{{ t('mfa.verifySubtitle') }}</p>

      <form @submit.prevent="submit" class="mfa-form">
        <div v-if="!useBackup" class="field">
          <label>{{ t('mfa.code') }}</label>
          <InputText
            v-model="code"
            maxlength="6"
            inputmode="numeric"
            autocomplete="one-time-code"
            class="code-input"
            :placeholder="t('mfa.codePlaceholder')"
            autofocus
          />
        </div>
        <div v-else class="field">
          <label>{{ t('mfa.backupCode') }}</label>
          <InputText
            v-model="code"
            class="code-input backup"
            :placeholder="t('mfa.backupCodePlaceholder')"
            autofocus
          />
        </div>

        <Button
          type="submit"
          :label="t('mfa.verify')"
          :loading="loading"
          :disabled="!canSubmit"
          class="w-full"
        />

        <Button
          type="button"
          class="w-full mt-2"
          text
          :label="useBackup ? t('mfa.useTotpCode') : t('mfa.useBackupCode')"
          @click="toggleMode"
        />
        <Button
          type="button"
          class="w-full"
          text
          severity="secondary"
          :label="t('mfa.backToLogin')"
          @click="goLogin"
        />
      </form>
    </div>
    <Toast position="top-right" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Toast from 'primevue/toast'
import { useAuthStore } from '@/store/auth'

const { t } = useI18n()
const toast = useToast()
const router = useRouter()
const authStore = useAuthStore()

const code = ref('')
const useBackup = ref(false)
const loading = ref(false)
const mfaToken = ref('')

const canSubmit = computed(() => {
  if (useBackup.value) return code.value.replace(/-/g, '').length >= 8
  return code.value.length === 6
})

onMounted(() => {
  mfaToken.value = sessionStorage.getItem('mfa_token') || ''
  if (!mfaToken.value) {
    router.replace('/login')
  }
})

watch(code, (val) => {
  if (!useBackup.value && val.length === 6) {
    submit()
  }
})

function toggleMode() {
  useBackup.value = !useBackup.value
  code.value = ''
}

function goLogin() {
  sessionStorage.removeItem('mfa_token')
  router.push('/login')
}

async function submit() {
  if (!canSubmit.value || loading.value) return
  loading.value = true
  try {
    await authStore.verifyMfa(mfaToken.value, code.value.trim())
    sessionStorage.removeItem('mfa_token')
    toast.add({
      severity: 'success',
      summary: t('common.messages.success'),
      detail: t('mfa.messages.verifySuccess'),
      life: 2500
    })
    router.push('/')
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: error.response?.data?.detail || t('mfa.messages.verifyError'),
      life: 4000
    })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.mfa-verify-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(160deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
  padding: 1.5rem;
}
.mfa-card {
  width: 100%;
  max-width: 420px;
  background: #fff;
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.25);
}
.mfa-card h1 {
  margin: 0 0 0.5rem;
  font-size: 1.5rem;
}
.mfa-card p {
  color: #64748b;
  margin: 0 0 1.5rem;
}
.field {
  margin-bottom: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.code-input {
  letter-spacing: 0.35em;
  font-size: 1.4rem;
  text-align: center;
}
.code-input.backup {
  letter-spacing: 0.1em;
  font-size: 1.1rem;
}
.mt-2 {
  margin-top: 0.5rem;
}
.w-full {
  width: 100%;
}
</style>
