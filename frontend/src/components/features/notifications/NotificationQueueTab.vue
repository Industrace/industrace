<template>
  <div class="notification-queue-tab">
    <div class="queue-header mb-3" v-if="canAdmin">
      <Button 
        :label="t('notifications.processQueue')" 
        icon="pi pi-play" 
        @click="$emit('process')"
        class="p-button-sm"
      />
    </div>
    <div v-if="loading" class="text-center p-4">
      <ProgressSpinner />
    </div>
    <div v-else-if="!loading">
      <DataTable 
        :value="safeQueue" 
        :emptyMessage="t('notifications.noQueueItems')"
        :paginator="true"
        :rows="20"
        class="p-datatable-sm"
        :key="`queue-${safeQueue.length}`"
      >
        <Column field="notification_type" :header="t('notifications.type')" sortable>
          <template #body="{ data }">
            <span class="font-semibold" v-if="data">{{ getNotificationTypeLabel(data.notification_type) }}</span>
          </template>
        </Column>
        <Column field="email" :header="t('common.fields.email')" sortable>
          <template #body="{ data }">
            <span v-if="data">{{ data.email }}</span>
          </template>
        </Column>
        <Column field="subject" :header="t('notifications.subject')">
          <template #body="{ data }">
            <span v-if="data">{{ data.subject }}</span>
          </template>
        </Column>
        <Column field="status" :header="t('notifications.status')" sortable>
          <template #body="{ data }">
            <Tag 
              v-if="data"
              :value="getStatusLabel(data.status)" 
              :severity="getStatusSeverity(data.status)" 
            />
          </template>
        </Column>
        <Column field="attempts" :header="t('notifications.attempts')">
          <template #body="{ data }">
            <span v-if="data">{{ data.attempts || 0 }}</span>
          </template>
        </Column>
        <Column :header="t('notifications.scheduledFor')" sortable sortField="scheduled_for">
          <template #body="{ data }">
            <span v-if="data">{{ formatDate(data.scheduled_for) || '-' }}</span>
          </template>
        </Column>
        <Column :header="t('notifications.sentAt')" sortable sortField="sent_at">
          <template #body="{ data }">
            <span v-if="data">{{ formatDate(data.sent_at) || '-' }}</span>
          </template>
        </Column>
        <Column v-if="canAdmin" :header="t('common.strings.actions')">
          <template #body="{ data }">
            <div class="flex gap-2" v-if="data">
              <Button 
                v-if="data.status === 'failed' || data.status === 'pending'"
                icon="pi pi-refresh" 
                class="p-button-rounded p-button-text p-button-success" 
                @click="$emit('retry', data.id)" 
                :title="t('notifications.retry')"
              />
              <Button 
                v-if="data.status === 'pending'"
                icon="pi pi-times" 
                class="p-button-rounded p-button-text p-button-danger" 
                @click="$emit('cancel', data.id)" 
                :title="t('notifications.cancel')"
              />
            </div>
          </template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDateFormatter } from '@/composables/useDateFormatter'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import ProgressSpinner from 'primevue/progressspinner'

const props = defineProps({
  queue: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  canAdmin: { type: Boolean, default: false }
})

const emit = defineEmits(['refresh', 'retry', 'cancel', 'process'])
const { t } = useI18n()
const { formatDate: formatDateUtil } = useDateFormatter()

// Ensure queue is always a safe array
const safeQueue = computed(() => {
  if (!props.queue) return []
  return Array.isArray(props.queue) ? props.queue.filter(item => item !== null && item !== undefined) : []
})

const formatDate = (date) => {
  if (!date) return null
  return formatDateUtil(new Date(date))
}

const getNotificationTypeLabel = (type) => {
  const labels = {
    'asset_review_due': t('notifications.types.assetReviewDue'),
    'asset_review_overdue': t('notifications.types.assetReviewOverdue'),
    'risk_alert': t('notifications.types.riskAlert')
  }
  return labels[type] || type
}

const getStatusLabel = (status) => {
  const labels = {
    'pending': t('notifications.status.pending'),
    'sent': t('notifications.status.sent'),
    'failed': t('notifications.status.failed'),
    'cancelled': t('notifications.status.cancelled')
  }
  return labels[status] || status
}

const getStatusSeverity = (status) => {
  const severityMap = {
    'pending': 'warning',
    'sent': 'success',
    'failed': 'danger',
    'cancelled': 'secondary'
  }
  return severityMap[status] || null
}
</script>

<style scoped>
.queue-header {
  display: flex;
  justify-content: flex-end;
}
</style>

