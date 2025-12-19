<template>
  <div class="notifications-page">
    <div class="page-header">
      <h1>{{ t('notifications.title') }}</h1>
    </div>

    <TabView class="mt-4">
      <!-- Preferences Tab -->
      <TabPanel>
        <template #header>
          <span style="display: flex; align-items: center; gap: 0.4em;">
            <i class="pi pi-cog"></i> {{ t('notifications.preferences') }}
          </span>
        </template>
        <NotificationPreferencesTab 
          :preferences="preferences"
          :loading="loadingPreferences"
          @refresh="fetchPreferences"
        />
      </TabPanel>

      <!-- Queue Tab -->
      <TabPanel>
        <template #header>
          <span style="display: flex; align-items: center; gap: 0.4em;">
            <i class="pi pi-inbox"></i> {{ t('notifications.queue') }}
            <Badge v-if="queueStats.pending > 0" :value="queueStats.pending" severity="warning" />
          </span>
        </template>
        <NotificationQueueTab 
          :queue="queue"
          :loading="loadingQueue"
          :canAdmin="canAdmin"
          @refresh="fetchQueue"
          @retry="handleRetry"
          @cancel="handleCancel"
          @process="handleProcessQueue"
        />
      </TabPanel>

      <!-- Logs Tab -->
      <TabPanel>
        <template #header>
          <span style="display: flex; align-items: center; gap: 0.4em;">
            <i class="pi pi-history"></i> {{ t('notifications.logs') }}
          </span>
        </template>
        <NotificationLogsTab 
          :logs="logs"
          :loading="loadingLogs"
          @refresh="fetchLogs"
        />
      </TabPanel>

      <!-- Test Tab (Admin only) -->
      <TabPanel v-if="canAdmin">
        <template #header>
          <span style="display: flex; align-items: center; gap: 0.4em;">
            <i class="pi pi-send"></i> {{ t('notifications.test') }}
          </span>
        </template>
        <NotificationTestTab 
          @test="handleTest"
        />
      </TabPanel>
    </TabView>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import { usePermissions } from '@/composables/usePermissions'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import Badge from 'primevue/badge'
import NotificationPreferencesTab from '../components/features/notifications/NotificationPreferencesTab.vue'
import NotificationQueueTab from '../components/features/notifications/NotificationQueueTab.vue'
import NotificationLogsTab from '../components/features/notifications/NotificationLogsTab.vue'
import NotificationTestTab from '../components/features/notifications/NotificationTestTab.vue'
import api from '@/api/api'

const { t } = useI18n()
const toast = useToast()
const { canRead } = usePermissions()

const preferences = ref([])
const queue = ref([])
const logs = ref([])
const loadingPreferences = ref(false)
const loadingQueue = ref(false)
const loadingLogs = ref(false)

const canAdmin = computed(() => canRead('users')) // Admin check

const queueStats = computed(() => {
  const pending = queue.value.filter(q => q.status === 'pending').length
  const failed = queue.value.filter(q => q.status === 'failed').length
  const sent = queue.value.filter(q => q.status === 'sent').length
  return { pending, failed, sent }
})

async function fetchPreferences() {
  loadingPreferences.value = true
  try {
    const res = await api.getNotificationPreferences()
    preferences.value = res.data || []
  } catch (error) {
    console.error('Error fetching preferences:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: t('notifications.errorLoadingPreferences') })
  } finally {
    loadingPreferences.value = false
  }
}

async function fetchQueue() {
  loadingQueue.value = true
  try {
    const res = await api.getNotificationQueue({ limit: 100 })
    queue.value = res.data || []
  } catch (error) {
    console.error('Error fetching queue:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: t('notifications.errorLoadingQueue') })
  } finally {
    loadingQueue.value = false
  }
}

async function fetchLogs(params = {}) {
  loadingLogs.value = true
  try {
    const res = await api.getNotificationLogs({ limit: 100, ...params })
    logs.value = res.data || []
  } catch (error) {
    console.error('Error fetching logs:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: t('notifications.errorLoadingLogs') })
  } finally {
    loadingLogs.value = false
  }
}

async function handleRetry(queueId) {
  try {
    await api.retryNotification(queueId)
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('notifications.retrySuccess') })
    await fetchQueue()
  } catch (error) {
    console.error('Error retrying notification:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: error.response?.data?.detail || t('notifications.errorRetry') })
  }
}

async function handleCancel(queueId) {
  try {
    await api.cancelNotification(queueId)
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('notifications.cancelSuccess') })
    await fetchQueue()
  } catch (error) {
    console.error('Error cancelling notification:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: error.response?.data?.detail || t('notifications.errorCancel') })
  }
}

async function handleProcessQueue() {
  try {
    const res = await api.processNotificationQueue(50)
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('notifications.queueProcessed', res.data?.stats) })
    await fetchQueue()
  } catch (error) {
    console.error('Error processing queue:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: error.response?.data?.detail || t('notifications.errorProcessing') })
  }
}

async function handleTest(testData) {
  try {
    await api.testNotification(testData)
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('notifications.testSent') })
  } catch (error) {
    console.error('Error sending test:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: error.response?.data?.detail || t('notifications.errorTest') })
  }
}

onMounted(async () => {
  await Promise.all([fetchPreferences(), fetchQueue(), fetchLogs()])
})
</script>

<style scoped>
.notifications-page {
  padding: 1.5rem;
}

.page-header {
  margin-bottom: 1.5rem;
}
</style>

