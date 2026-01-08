<template>
  <div class="asset-review-tab">
    <div v-if="loading" class="text-center p-4">
      <ProgressSpinner />
    </div>
    <div v-else-if="reviewStatus" class="review-content">
      <!-- Status Card -->
      <Card class="mb-4">
        <template #title>
          <div class="flex align-items-center gap-2">
            <i class="pi pi-calendar"></i>
            {{ t('assetReviews.reviewStatus') }}
          </div>
        </template>
        <template #content>
          <div class="review-status-grid">
            <div class="status-item">
              <label>{{ t('assetReviews.reviewStatus') }}</label>
              <Tag 
                :value="getStatusLabel(reviewStatus.review_status)" 
                :severity="getStatusSeverity(reviewStatus.review_status)" 
              />
            </div>
            <div class="status-item">
              <label>{{ t('assetReviews.lastReview') }}</label>
              <span>{{ formatDate(reviewStatus.last_review_date) || '-' }}</span>
            </div>
            <div class="status-item">
              <label>{{ t('assetReviews.nextReview') }}</label>
              <div class="flex align-items-center gap-2">
                <span :class="getDateClass(reviewStatus.next_review_date)">
                  {{ formatDate(reviewStatus.next_review_date) || '-' }}
                </span>
                <Tag 
                  v-if="reviewStatus.days_until_review !== null || reviewStatus.days_overdue !== null"
                  :value="getDaysLabel()"
                  :severity="getDaysSeverity()"
                />
              </div>
            </div>
            <div class="status-item">
              <label>{{ t('assetReviews.interval') }}</label>
              <span>{{ reviewStatus.review_interval_months || 6 }} {{ t('assetReviews.months') }}</span>
            </div>
          </div>
        </template>
      </Card>

      <!-- Review Notes -->
      <Card v-if="reviewStatus.review_notes" class="mb-4">
        <template #title>
          <div class="flex align-items-center gap-2">
            <i class="pi pi-file-edit"></i>
            {{ t('assetReviews.reviewNotes') }}
          </div>
        </template>
        <template #content>
          <p class="review-notes">{{ reviewStatus.review_notes }}</p>
        </template>
      </Card>

      <!-- Actions -->
      <div v-if="canWrite" class="review-actions">
        <Button 
          :label="t('assetReviews.markAsReviewed')" 
          icon="pi pi-check" 
          class="p-button-success"
          @click="showReviewDialog = true"
        />
        <Button 
          :label="t('assetReviews.skipReview')" 
          icon="pi pi-forward" 
          class="p-button-warning"
          @click="showSkipDialog = true"
        />
      </div>
    </div>

    <!-- Review Dialog -->
    <Dialog 
      v-model:visible="showReviewDialog" 
      :header="t('assetReviews.markAsReviewed')" 
      modal 
      :closable="true" 
      :dismissableMask="true"
      style="width: 600px"
    >
      <div class="p-fluid">
        <div class="field">
          <label>{{ t('assetReviews.reviewNotes') }}</label>
          <Textarea 
            v-model="reviewNotes" 
            :rows="5" 
            :placeholder="t('assetReviews.reviewNotesPlaceholder')"
          />
        </div>
        <div class="field">
          <label>{{ t('assetReviews.nextReviewDate') }}</label>
          <Calendar 
            v-model="nextReviewDate" 
            :minDate="new Date()"
            :showTime="false"
            dateFormat="yy-mm-dd"
            :placeholder="t('assetReviews.nextReviewDatePlaceholder')"
          />
        </div>
        <div class="flex justify-content-end gap-2 mt-3">
          <Button 
            :label="t('common.actions.save')" 
            icon="pi pi-check" 
            @click="confirmReview"
            :loading="reviewing"
          />
          <Button 
            :label="t('common.actions.cancel')" 
            icon="pi pi-times" 
            class="p-button-secondary" 
            @click="showReviewDialog = false" 
          />
        </div>
      </div>
    </Dialog>

    <!-- Skip Dialog -->
    <Dialog 
      v-model:visible="showSkipDialog" 
      :header="t('assetReviews.skipReview')" 
      modal 
      :closable="true" 
      :dismissableMask="true"
      style="width: 600px"
    >
      <div class="p-fluid">
        <div class="field">
          <label>{{ t('assetReviews.skipReason') }} *</label>
          <Textarea 
            v-model="skipReason" 
            :rows="3" 
            :placeholder="t('assetReviews.skipReasonPlaceholder')"
            required
          />
        </div>
        <div class="field">
          <label>{{ t('assetReviews.nextReviewDate') }} *</label>
          <Calendar 
            v-model="skipNextReviewDate" 
            :minDate="new Date()"
            :showTime="false"
            dateFormat="yy-mm-dd"
            :placeholder="t('assetReviews.nextReviewDatePlaceholder')"
            required
          />
        </div>
        <div class="flex justify-content-end gap-2 mt-3">
          <Button 
            :label="t('common.actions.save')" 
            icon="pi pi-check" 
            @click="confirmSkip"
            :loading="skipping"
            :disabled="!skipReason || !skipNextReviewDate"
          />
          <Button 
            :label="t('common.actions.cancel')" 
            icon="pi pi-times" 
            class="p-button-secondary" 
            @click="showSkipDialog = false" 
          />
        </div>
      </div>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import { useDateFormatter } from '@/composables/useDateFormatter'
import Card from 'primevue/card'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Dialog from 'primevue/dialog'
import Textarea from 'primevue/textarea'
import Calendar from 'primevue/calendar'
import ProgressSpinner from 'primevue/progressspinner'
import api from '@/api/api'

const props = defineProps({
  assetId: { type: [String, Number], required: true },
  canWrite: { type: Boolean, default: false }
})

const emit = defineEmits(['updated'])
const { t } = useI18n()
const toast = useToast()
const { formatDate: formatDateUtil } = useDateFormatter()

const reviewStatus = ref(null)
const loading = ref(false)
const reviewing = ref(false)
const skipping = ref(false)
const showReviewDialog = ref(false)
const showSkipDialog = ref(false)
const reviewNotes = ref('')
const nextReviewDate = ref(null)
const skipReason = ref('')
const skipNextReviewDate = ref(null)

const formatDate = (date) => {
  if (!date) return null
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

const getDaysLabel = () => {
  if (reviewStatus.value.days_overdue !== null && reviewStatus.value.days_overdue > 0) {
    return `${reviewStatus.value.days_overdue} ${t('assetReviews.daysOverdue')}`
  } else if (reviewStatus.value.days_until_review !== null) {
    if (reviewStatus.value.days_until_review === 0) {
      return t('assetReviews.dueToday')
    }
    return `${reviewStatus.value.days_until_review} ${t('assetReviews.daysUntil')}`
  }
  return null
}

const getDaysSeverity = () => {
  if (reviewStatus.value.days_overdue !== null && reviewStatus.value.days_overdue > 0) {
    return 'danger'
  } else if (reviewStatus.value.days_until_review !== null) {
    if (reviewStatus.value.days_until_review <= 7) {
      return 'warning'
    }
    return 'info'
  }
  return null
}

const getDateClass = (nextReviewDate) => {
  if (!nextReviewDate || !reviewStatus.value) return ''
  const days = reviewStatus.value.days_overdue !== null && reviewStatus.value.days_overdue > 0 
    ? -reviewStatus.value.days_overdue 
    : reviewStatus.value.days_until_review
  if (days === null) return ''
  if (days < 0) return 'text-red-500 font-bold'
  if (days <= 7) return 'text-orange-500 font-semibold'
  return ''
}

async function fetchReviewStatus() {
  loading.value = true
  try {
    const res = await api.getAssetReviewStatus(props.assetId)
    reviewStatus.value = res.data
  } catch (error) {
    console.error('Error fetching review status:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: t('assetReviews.errorLoading') })
  } finally {
    loading.value = false
  }
}

async function confirmReview() {
  reviewing.value = true
  try {
    await api.markAssetAsReviewed(props.assetId, {
      notes: reviewNotes.value || null,
      next_review_override: nextReviewDate.value ? new Date(nextReviewDate.value).toISOString() : null
    })
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('assetReviews.assetReviewed') })
    showReviewDialog.value = false
    reviewNotes.value = ''
    nextReviewDate.value = null
    await fetchReviewStatus()
    emit('updated')
  } catch (error) {
    console.error('Error reviewing asset:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: error.response?.data?.detail || t('assetReviews.errorReviewing') })
  } finally {
    reviewing.value = false
  }
}

async function confirmSkip() {
  if (!skipReason.value || !skipNextReviewDate.value) return

  skipping.value = true
  try {
    await api.skipAssetReview(props.assetId, {
      reason: skipReason.value,
      next_review_date: new Date(skipNextReviewDate.value).toISOString()
    })
    toast.add({ severity: 'success', summary: t('common.success'), detail: t('assetReviews.reviewSkipped') })
    showSkipDialog.value = false
    skipReason.value = ''
    skipNextReviewDate.value = null
    await fetchReviewStatus()
    emit('updated')
  } catch (error) {
    console.error('Error skipping review:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: error.response?.data?.detail || t('assetReviews.errorSkipping') })
  } finally {
    skipping.value = false
  }
}

onMounted(async () => {
  await fetchReviewStatus()
})

watch(() => props.assetId, async (newId, oldId) => {
  if (newId !== oldId) {
    await fetchReviewStatus()
  }
})
</script>

<style scoped>
.asset-review-tab {
  padding: 1rem 0;
}

.review-content {
  max-width: 800px;
}

.review-status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
}

.status-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.status-item label {
  font-weight: 600;
  color: var(--text-color-secondary);
  font-size: 0.9rem;
}

.review-notes {
  white-space: pre-wrap;
  line-height: 1.6;
}

.review-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}
</style>

