<template>
  <div class="notification-logs-tab">
    <div class="logs-filters mb-3">
      <div class="flex gap-2 align-items-end">
        <div class="field">
          <label>{{ t('notifications.filterByType') }}</label>
          <Dropdown
            v-model="selectedType"
            :options="typeOptions"
            optionLabel="label"
            optionValue="value"
            :placeholder="t('notifications.allTypes')"
            class="w-12rem"
            @change="fetchLogs"
          />
        </div>
        <div class="field">
          <label>{{ t('notifications.fromDate') }}</label>
          <Calendar 
            v-model="fromDate" 
            :showTime="false"
            dateFormat="yy-mm-dd"
            @date-select="fetchLogs"
            class="w-12rem"
          />
        </div>
        <div class="field">
          <label>{{ t('notifications.toDate') }}</label>
          <Calendar 
            v-model="toDate" 
            :showTime="false"
            dateFormat="yy-mm-dd"
            @date-select="fetchLogs"
            class="w-12rem"
          />
        </div>
        <Button 
          :label="t('common.actions.refresh')" 
          icon="pi pi-refresh" 
          @click="fetchLogs"
          class="p-button-sm"
        />
      </div>
    </div>
    <div v-if="loading" class="text-center p-4">
      <ProgressSpinner />
    </div>
    <div v-else>
      <DataTable 
        :value="logs" 
        :emptyMessage="t('notifications.noLogs')"
        :paginator="true"
        :rows="20"
        class="p-datatable-sm"
      >
        <Column field="notification_type" :header="t('notifications.type')" sortable>
          <template #body="{ data }">
            <span class="font-semibold">{{ getNotificationTypeLabel(data.notification_type) }}</span>
          </template>
        </Column>
        <Column field="status" :header="t('notifications.status')" sortable>
          <template #body="{ data }">
            <Tag 
              :value="getStatusLabel(data.status)" 
              :severity="getStatusSeverity(data.status)" 
            />
          </template>
        </Column>
        <Column :header="t('notifications.sentAt')" sortable sortField="sent_at">
          <template #body="{ data }">
            {{ formatDate(data.sent_at) || '-' }}
          </template>
        </Column>
        <Column :header="t('notifications.createdAt')" sortable sortField="created_at">
          <template #body="{ data }">
            {{ formatDate(data.created_at) }}
          </template>
        </Column>
        <Column field="error_message" :header="t('notifications.error')">
          <template #body="{ data }">
            <span v-if="data.error_message" class="text-red-500">{{ data.error_message }}</span>
            <span v-else>-</span>
          </template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useDateFormatter } from '@/composables/useDateFormatter'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Dropdown from 'primevue/dropdown'
import Calendar from 'primevue/calendar'
import ProgressSpinner from 'primevue/progressspinner'
import api from '@/api/api'

const props = defineProps({
  logs: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
})

const emit = defineEmits(['refresh'])
const { t } = useI18n()
const { formatDate: formatDateUtil } = useDateFormatter()

const selectedType = ref(null)
const fromDate = ref(null)
const toDate = ref(null)

const typeOptions = computed(() => [
  { label: t('notifications.allTypes'), value: null },
  { label: t('notifications.types.assetReviewDue'), value: 'asset_review_due' },
  { label: t('notifications.types.assetReviewOverdue'), value: 'asset_review_overdue' },
  { label: t('notifications.types.riskAlert'), value: 'risk_alert' }
])

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
    'sent': t('notifications.status.sent'),
    'failed': t('notifications.status.failed')
  }
  return labels[status] || status
}

const getStatusSeverity = (status) => {
  const severityMap = {
    'sent': 'success',
    'failed': 'danger'
  }
  return severityMap[status] || null
}

function fetchLogs() {
  const params = {}
  if (selectedType.value) params.notification_type = selectedType.value
  if (fromDate.value) params.from_date = new Date(fromDate.value).toISOString()
  if (toDate.value) params.to_date = new Date(toDate.value).toISOString()
  emit('refresh', params)
}
</script>

<style scoped>
.logs-filters {
  padding: 1rem;
  background: var(--surface-ground);
  border-radius: 4px;
}

.w-12rem {
  width: 12rem;
}
</style>

