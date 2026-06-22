<template>
  <div class="asset-review-table">
    <DataTable 
      v-model:selection="selectionModel"
      :value="assets" 
      :loading="loading"
      :emptyMessage="t('assetReviews.noAssets')"
      :paginator="true"
      :rows="20"
      dataKey="id"
      class="p-datatable-sm"
    >
      <Column v-if="selectable" selectionMode="multiple" headerStyle="width: 3rem" />
      <Column field="name" :header="t('common.fields.name')" sortable>
        <template #body="{ data }">
          <a 
            @click="goToAsset(data.id)" 
            class="asset-link"
          >
            {{ data.name }}
          </a>
        </template>
      </Column>
      <Column field="tag" :header="t('assets.fields.tag')" sortable />
      <Column :header="t('assetReviews.reviewStatus')" sortable sortField="review_status">
        <template #body="{ data }">
          <Tag 
            :value="getStatusLabel(data.review_status)" 
            :severity="getStatusSeverity(data.review_status)" 
          />
        </template>
      </Column>
      <Column :header="t('assetReviews.lastReview')" sortable sortField="last_review_date">
        <template #body="{ data }">
          {{ formatDate(data.last_review_date) }}
        </template>
      </Column>
      <Column :header="t('assetReviews.nextReview')" sortable sortField="next_review_date">
        <template #body="{ data }">
          <div class="flex align-items-center gap-2">
            <span :class="getDateClass(data.next_review_date)">
              {{ formatDate(data.next_review_date) }}
            </span>
            <Tag 
              v-if="getDaysUntil(data.next_review_date) !== null"
              :value="getDaysLabel(data.next_review_date)"
              :severity="getDaysSeverity(data.next_review_date)"
              class="ml-2"
            />
          </div>
        </template>
      </Column>
      <Column :header="t('assetReviews.interval')">
        <template #body="{ data }">
          {{ data.review_interval_months || 6 }} {{ t('assetReviews.months') }}
        </template>
      </Column>
      <Column v-if="canWrite" :header="t('common.strings.actions')">
        <template #body="{ data }">
          <div class="flex gap-2">
            <Button 
              icon="pi pi-check" 
              class="p-button-rounded p-button-text p-button-success" 
              @click="$emit('review', data)" 
              :title="t('assetReviews.markAsReviewed')"
              v-tooltip.top="t('assetReviews.markAsReviewed')"
            />
            <Button 
              icon="pi pi-forward" 
              class="p-button-rounded p-button-text p-button-warning" 
              @click="$emit('skip', data)" 
              :title="t('assetReviews.skipReview')"
              v-tooltip.top="t('assetReviews.skipReview')"
            />
          </div>
        </template>
      </Column>
    </DataTable>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useDateFormatter } from '@/composables/useDateFormatter'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Tooltip from 'primevue/tooltip'

const props = defineProps({
  assets: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  canWrite: { type: Boolean, default: false },
  selectable: { type: Boolean, default: false },
  selectedAssets: { type: Array, default: () => [] }
})

const emit = defineEmits(['review', 'skip', 'refresh', 'update:selectedAssets'])
const { t } = useI18n()
const router = useRouter()
const { formatDate: formatDateUtil } = useDateFormatter()

const selectionModel = computed({
  get: () => props.selectedAssets,
  set: (value) => emit('update:selectedAssets', value || [])
})

const goToAsset = (assetId) => {
  router.push(`/assets/${assetId}`)
}

const formatDate = (date) => {
  if (!date) return '-'
  return formatDateUtil(new Date(date))
}

const getStatusLabel = (status) => {
  const labels = {
    'pending': t('assetReviews.status.pending'),
    'reviewed': t('assetReviews.status.reviewed'),
    'skipped': t('assetReviews.status.skipped'),
    'overdue': t('assetReviews.status.overdue')
  }
  return labels[status] || status
}

const getStatusSeverity = (status) => {
  const severityMap = {
    'pending': 'warning',
    'reviewed': 'success',
    'skipped': 'info',
    'overdue': 'danger'
  }
  return severityMap[status] || null
}

const getDaysUntil = (nextReviewDate) => {
  if (!nextReviewDate) return null
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const next = new Date(nextReviewDate)
  next.setHours(0, 0, 0, 0)
  const diff = Math.floor((next - today) / (1000 * 60 * 60 * 24))
  return diff
}

const getDaysLabel = (nextReviewDate) => {
  const days = getDaysUntil(nextReviewDate)
  if (days === null) return null
  if (days < 0) {
    return `${Math.abs(days)} ${t('assetReviews.daysOverdue')}`
  } else if (days === 0) {
    return t('assetReviews.dueToday')
  } else {
    return `${days} ${t('assetReviews.daysUntil')}`
  }
}

const getDaysSeverity = (nextReviewDate) => {
  const days = getDaysUntil(nextReviewDate)
  if (days === null) return null
  if (days < 0) return 'danger'
  if (days <= 7) return 'warning'
  return 'info'
}

const getDateClass = (nextReviewDate) => {
  const days = getDaysUntil(nextReviewDate)
  if (days === null) return ''
  if (days < 0) return 'text-red-500 font-bold'
  if (days <= 7) return 'text-orange-500 font-semibold'
  return ''
}
</script>

<style scoped>
.asset-review-table {
  padding: 1rem 0;
}

.asset-link {
  color: var(--primary-color);
  cursor: pointer;
  text-decoration: none;
}

.asset-link:hover {
  text-decoration: underline;
}
</style>
