<template>
  <div class="asset-reviews-page">
    <div class="page-header">
      <h1>{{ t('assetReviews.title') }}</h1>
      <div class="header-actions">
        <Button 
          :label="t('assetReviews.recalculateDates')" 
          icon="pi pi-refresh" 
          @click="recalculateDates"
          :loading="recalculating"
        />
      </div>
    </div>

    <!-- Stat Cards -->
    <div class="stats-grid">
      <Card class="stat-card">
        <template #content>
          <div class="stat-content">
            <div class="stat-icon overdue">
              <i class="pi pi-exclamation-triangle"></i>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ overdueCount ?? 0 }}</div>
              <div class="stat-label">{{ t('assetReviews.overdue') }}</div>
            </div>
          </div>
        </template>
      </Card>
      <Card class="stat-card">
        <template #content>
          <div class="stat-content">
            <div class="stat-icon due">
              <i class="pi pi-calendar-times"></i>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ dueCount ?? 0 }}</div>
              <div class="stat-label">{{ t('assetReviews.due') }}</div>
            </div>
          </div>
        </template>
      </Card>
      <Card class="stat-card">
        <template #content>
          <div class="stat-content">
            <div class="stat-icon upcoming">
              <i class="pi pi-calendar"></i>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ upcomingCount ?? 0 }}</div>
              <div class="stat-label">{{ t('assetReviews.upcoming') }}</div>
            </div>
          </div>
        </template>
      </Card>
    </div>

    <!-- Upcoming Review Days Selector -->
    <Card class="mb-4">
      <template #content>
        <div class="flex align-items-center gap-3">
          <label for="upcoming-days" class="font-medium">{{ t('assetReviews.upcomingDaysLabel') }}:</label>
          <Dropdown 
            id="upcoming-days"
            v-model="upcomingDays" 
            :options="upcomingDaysOptions" 
            optionLabel="label"
            optionValue="value"
            :placeholder="t('assetReviews.selectDays')"
            @change="onUpcomingDaysChange"
            class="w-12rem"
          />
          <span class="text-sm text-600">{{ t('assetReviews.upcomingDaysHint') }}</span>
        </div>
      </template>
    </Card>

    <!-- Tabs -->
    <TabView class="mt-4">
      <TabPanel>
        <template #header>
          <span style="display: flex; align-items: center; gap: 0.4em;">
            <i class="pi pi-exclamation-triangle"></i> {{ t('assetReviews.overdue') }} ({{ overdueAssets.length }})
          </span>
        </template>
        <AssetReviewTable 
          :assets="overdueAssets" 
          :loading="loadingOverdue"
          @review="handleReview"
          @skip="handleSkip"
          @refresh="fetchOverdue"
        />
      </TabPanel>
      <TabPanel>
        <template #header>
          <span style="display: flex; align-items: center; gap: 0.4em;">
            <i class="pi pi-calendar-times"></i> {{ t('assetReviews.due') }} ({{ dueAssets.length }})
          </span>
        </template>
        <AssetReviewTable 
          :assets="dueAssets" 
          :loading="loadingDue"
          @review="handleReview"
          @skip="handleSkip"
          @refresh="fetchDue"
        />
      </TabPanel>
      <TabPanel>
        <template #header>
          <span style="display: flex; align-items: center; gap: 0.4em;">
            <i class="pi pi-calendar"></i> {{ t('assetReviews.upcoming') }} ({{ upcomingAssets.length }}) - {{ upcomingDays }} {{ upcomingDays === 1 ? t('assetReviews.day') : t('assetReviews.days') }}
          </span>
        </template>
        <AssetReviewTable 
          :assets="upcomingAssets" 
          :loading="loadingUpcoming"
          @review="handleReview"
          @skip="handleSkip"
          @refresh="fetchUpcoming"
        />
      </TabPanel>
    </TabView>

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
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import { useRouter } from 'vue-router'
import Button from 'primevue/button'
import Card from 'primevue/card'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import Dialog from 'primevue/dialog'
import Textarea from 'primevue/textarea'
import Calendar from 'primevue/calendar'
import Dropdown from 'primevue/dropdown'
import AssetReviewTable from '../components/features/assets/AssetReviewTable.vue'
import api from '@/api/api'

const { t } = useI18n()
const toast = useToast()
const router = useRouter()

const overdueAssets = ref([])
const dueAssets = ref([])
const upcomingAssets = ref([])
const loadingOverdue = ref(false)
const loadingDue = ref(false)
const loadingUpcoming = ref(false)
const recalculating = ref(false)
const reviewing = ref(false)
const skipping = ref(false)

// Upcoming days selector
const upcomingDays = ref(30) // Default: 30 days
const upcomingDaysOptions = [
  { label: '7 giorni', value: 7 },
  { label: '14 giorni', value: 14 },
  { label: '30 giorni', value: 30 },
  { label: '60 giorni', value: 60 },
  { label: '90 giorni', value: 90 },
  { label: '180 giorni', value: 180 },
  { label: '365 giorni', value: 365 }
]

const showReviewDialog = ref(false)
const showSkipDialog = ref(false)
const selectedAsset = ref(null)
const reviewNotes = ref('')
const nextReviewDate = ref(null)
const skipReason = ref('')
const skipNextReviewDate = ref(null)

const overdueCount = computed(() => {
  return overdueAssets.value.length
})
const dueCount = computed(() => {
  return dueAssets.value.length
})
const upcomingCount = computed(() => {
  return upcomingAssets.value.length
})

async function fetchOverdue() {
  loadingOverdue.value = true
  try {
    const res = await api.getOverdueAssets()
    // Handle both direct array and wrapped response
    if (Array.isArray(res.data)) {
      overdueAssets.value = res.data
    } else if (res.data?.data && Array.isArray(res.data.data)) {
      overdueAssets.value = res.data.data
    } else {
      overdueAssets.value = []
    }
  } catch (error) {
    console.error('Error fetching overdue assets:', error)
    toast.add({ severity: 'error', summary: t('common.messages.error'), detail: t('assetReviews.errorLoading') })
    overdueAssets.value = []
  } finally {
    loadingOverdue.value = false
  }
}

async function fetchDue() {
  loadingDue.value = true
  try {
    const res = await api.getDueAssets()
    // Handle both direct array and wrapped response
    if (Array.isArray(res.data)) {
      dueAssets.value = res.data
    } else if (res.data?.data && Array.isArray(res.data.data)) {
      dueAssets.value = res.data.data
    } else {
      dueAssets.value = []
    }
  } catch (error) {
    console.error('Error fetching due assets:', error)
    toast.add({ severity: 'error', summary: t('common.messages.error'), detail: t('assetReviews.errorLoading') })
    dueAssets.value = []
  } finally {
    loadingDue.value = false
  }
}

async function fetchUpcoming() {
  loadingUpcoming.value = true
  try {
    const res = await api.getUpcomingAssets({ days: upcomingDays.value })
    // Handle both direct array and wrapped response
    if (Array.isArray(res.data)) {
      upcomingAssets.value = res.data
    } else if (res.data?.data && Array.isArray(res.data.data)) {
      upcomingAssets.value = res.data.data
    } else {
      upcomingAssets.value = []
    }
  } catch (error) {
    console.error('Error fetching upcoming assets:', error)
    toast.add({ severity: 'error', summary: t('common.messages.error'), detail: t('assetReviews.errorLoading') })
    upcomingAssets.value = []
  } finally {
    loadingUpcoming.value = false
  }
}

function onUpcomingDaysChange() {
  fetchUpcoming()
}

async function recalculateDates() {
  recalculating.value = true
  try {
    await api.recalculateReviewDates()
    toast.add({ severity: 'success', summary: t('common.messages.success'), detail: t('assetReviews.datesRecalculated') })
    await Promise.all([fetchOverdue(), fetchDue(), fetchUpcoming()])
  } catch (error) {
    console.error('Error recalculating dates:', error)
    toast.add({ severity: 'error', summary: t('common.messages.error'), detail: error.response?.data?.detail || t('assetReviews.errorRecalculating') })
  } finally {
    recalculating.value = false
  }
}

function handleReview(asset) {
  selectedAsset.value = asset
  reviewNotes.value = ''
  nextReviewDate.value = null
  showReviewDialog.value = true
}

async function confirmReview() {
  if (!selectedAsset.value) return

  reviewing.value = true
  try {
    await api.markAssetAsReviewed(selectedAsset.value.id, {
      notes: reviewNotes.value || null,
      next_review_override: nextReviewDate.value ? new Date(nextReviewDate.value).toISOString() : null
    })
    toast.add({ severity: 'success', summary: t('common.messages.success'), detail: t('assetReviews.assetReviewed') })
    showReviewDialog.value = false
    selectedAsset.value = null
    
    // Refresh all lists
    await Promise.all([fetchOverdue(), fetchDue(), fetchUpcoming()])
  } catch (error) {
    console.error('Error reviewing asset:', error)
    toast.add({ severity: 'error', summary: t('common.messages.error'), detail: error.response?.data?.detail || t('assetReviews.errorReviewing') })
  } finally {
    reviewing.value = false
  }
}

function handleSkip(asset) {
  selectedAsset.value = asset
  skipReason.value = ''
  skipNextReviewDate.value = null
  showSkipDialog.value = true
}

async function confirmSkip() {
  if (!selectedAsset.value || !skipReason.value || !skipNextReviewDate.value) return

  skipping.value = true
  try {
    await api.skipAssetReview(selectedAsset.value.id, {
      reason: skipReason.value,
      next_review_date: new Date(skipNextReviewDate.value).toISOString()
    })
    toast.add({ severity: 'success', summary: t('common.messages.success'), detail: t('assetReviews.reviewSkipped') })
    showSkipDialog.value = false
    selectedAsset.value = null
    
    // Refresh all lists
    await Promise.all([fetchOverdue(), fetchDue(), fetchUpcoming()])
  } catch (error) {
    console.error('Error skipping review:', error)
    toast.add({ severity: 'error', summary: t('common.messages.error'), detail: error.response?.data?.detail || t('assetReviews.errorSkipping') })
  } finally {
    skipping.value = false
  }
}

onMounted(async () => {
  await Promise.all([fetchOverdue(), fetchDue(), fetchUpcoming()])
})
</script>

<style scoped>
.asset-reviews-page {
  padding: 1.5rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  height: 100%;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: white;
}

.stat-icon.overdue {
  background: linear-gradient(135deg, #f56565 0%, #c53030 100%);
}

.stat-icon.due {
  background: linear-gradient(135deg, #ed8936 0%, #c05621 100%);
}

.stat-icon.upcoming {
  background: linear-gradient(135deg, #4299e1 0%, #2b6cb0 100%);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  color: var(--text-color);
}

.stat-label {
  font-size: 0.9rem;
  color: var(--text-color-secondary);
  margin-top: 0.25rem;
}
</style>

