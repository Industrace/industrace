<!--
  - UserDetail.vue
  - Componente per la visualizzazione dei dettagli di un utente
  - Utilizza i componenti PrimeVue per la gestione del form
-->
<template>
  <div class="user-detail-page">
    <div class="page-header">
      <Button icon="pi pi-arrow-left" :label="t('common.actions.back')" class="mb-3" @click="goBack" />
      <h1>{{ t('users.title') }}</h1>
    </div>

    <Card v-if="user" class="mb-4">
      <template #title>{{ user.name }}</template>
      <template #content>
        <div class="grid">
          <div class="col-12 md:col-6">
            <p><strong>{{ t('common.fields.name') }}:</strong> {{ user.name }}</p>
            <p><strong>{{ t('common.fields.email') }}:</strong> {{ user.email }}</p>
            <p><strong>{{ t('users.fields.role') }}:</strong> {{ user.role?.name || t('common.strings.na') }}</p>
            <p><strong>{{ t('common.fields.status') }}:</strong> 
              <Tag :value="user.is_active ? t('users.strings.active') : t('users.strings.inactive')" 
                   :severity="user.is_active ? 'success' : 'danger'" />
            </p>
            <p><strong>{{ t('common.fields.createdAt') }}:</strong> {{ formatDate(user.created_at) }}</p>
            <p><strong>{{ t('users.fields.lastLogin') }}:</strong> {{ user.last_login ? formatDate(user.last_login) : t('common.strings.na') }}</p>
            <p v-if="mfaInfo">
              <strong>{{ t('mfa.title') }}:</strong>
              {{ mfaInfo.totp_enabled ? t('mfa.statusEnabled') : t('mfa.statusDisabled') }}
            </p>
          </div>
        </div>
        <div class="mt-3" v-if="mfaInfo?.totp_enabled">
          <Button
            :label="t('mfa.resetAdmin')"
            icon="pi pi-refresh"
            severity="danger"
            outlined
            :loading="resettingMfa"
            @click="resetMfa"
          />
        </div>
      </template>
    </Card>

    <div v-if="!user && !loading" class="text-center">
      <p>{{ t('users.messages.userNotFound') }}</p>
    </div>

    <div v-if="loading" class="text-center">
      <ProgressSpinner />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import { useI18n } from 'vue-i18n'
import api from '../api/api'

import Button from 'primevue/button'
import Card from 'primevue/card'
import Tag from 'primevue/tag'
import ProgressSpinner from 'primevue/progressspinner'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const toast = useToast()

const user = ref(null)
const loading = ref(false)
const mfaInfo = ref(null)
const resettingMfa = ref(false)
const userId = route.params.id

function goBack() {
  router.push({ name: 'Users' })
}

function formatDate(dateString) {
  if (!dateString) return t('common.strings.na')
  return new Date(dateString).toLocaleDateString('it-IT', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function fetchMfa() {
  try {
    const res = await api.getUserMfaStatus(userId)
    mfaInfo.value = res.data
  } catch (e) {
    mfaInfo.value = null
  }
}

async function resetMfa() {
  if (!confirm(t('mfa.resetAdminConfirm'))) return
  resettingMfa.value = true
  try {
    await api.resetUserMfa(userId)
    toast.add({
      severity: 'success',
      summary: t('common.messages.success'),
      detail: t('mfa.resetSuccess'),
      life: 3000
    })
    await fetchMfa()
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: error.response?.data?.detail || t('common.messages.error'),
      life: 4000
    })
  } finally {
    resettingMfa.value = false
  }
}

async function fetchUser() {
  loading.value = true
  try {
    const response = await api.getUser(userId)
    user.value = response.data
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: t('users.messages.fetchError'),
      life: 3000
    })
    user.value = null
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  await fetchUser()
  await fetchMfa()
})
</script>

<style scoped>
.user-detail-page {
  padding: 1rem;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.page-header h1 {
  margin: 0;
}
</style> 