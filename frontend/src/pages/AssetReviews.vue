<template>
  <div class="asset-reviews-page">
    <div class="page-header">
      <h1>{{ t('assetReviews.title') }}</h1>
      <div class="header-actions">
        <Button 
          v-if="canDelete('asset_reviews')"
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

    <!-- Tenant Review Settings -->
    <Card v-if="canDelete('asset_reviews')" class="mb-4">
      <template #title>
        <div class="flex align-items-center gap-2">
          <i class="pi pi-cog"></i>
          {{ t('assetReviews.settings.title') }}
        </div>
      </template>
      <template #content>
        <div v-if="loadingSettings" class="text-center p-3">
          <ProgressSpinner style="width: 2rem; height: 2rem" />
        </div>
        <div v-else class="settings-grid">
          <div class="field">
            <label for="default-interval">{{ t('assetReviews.settings.defaultInterval') }}</label>
            <InputNumber
              id="default-interval"
              v-model="reviewSettings.default_review_interval_months"
              :min="1"
              :max="120"
              showButtons
              class="w-full"
            />
            <small class="text-600">{{ t('assetReviews.settings.defaultIntervalHint') }}</small>
          </div>
          <div class="field">
            <label for="due-days">{{ t('assetReviews.settings.dueDaysAhead') }}</label>
            <InputNumber
              id="due-days"
              v-model="reviewSettings.review_due_days_ahead"
              :min="1"
              :max="365"
              showButtons
              class="w-full"
            />
            <small class="text-600">{{ t('assetReviews.settings.dueDaysAheadHint') }}</small>
          </div>
          <div class="field">
            <label for="upcoming-days-setting">{{ t('assetReviews.settings.upcomingDaysAhead') }}</label>
            <InputNumber
              id="upcoming-days-setting"
              v-model="reviewSettings.review_upcoming_days_ahead"
              :min="1"
              :max="365"
              showButtons
              class="w-full"
            />
            <small class="text-600">{{ t('assetReviews.settings.upcomingDaysAheadHint') }}</small>
          </div>
          <div class="field settings-actions">
            <Button
              :label="t('common.actions.save')"
              icon="pi pi-check"
              @click="saveReviewSettings"
              :loading="savingSettings"
            />
          </div>
        </div>
      </template>
    </Card>

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

    <!-- Bulk action bar -->
    <div v-if="canDelete('asset_reviews') && selectedAssets.length > 0" class="bulk-bar mb-3">
      <span>{{ t('assetReviews.bulk.selected', { count: selectedAssets.length }) }}</span>
      <Button
        :label="t('assetReviews.bulk.markReviewed', { count: selectedAssets.length })"
        icon="pi pi-check"
        class="p-button-success"
        @click="openBulkReviewDialog"
      />
      <Button
        :label="t('common.actions.cancel')"
        icon="pi pi-times"
        class="p-button-text"
        @click="selectedAssets = []"
      />
    </div>

    <!-- Tabs -->
    <TabView v-model:activeIndex="activeTabIndex" class="mt-4">
      <TabPanel>
        <template #header>
          <span style="display: flex; align-items: center; gap: 0.4em;">
            <i class="pi pi-exclamation-triangle"></i> {{ t('assetReviews.overdue') }} ({{ overdueAssets.length }})
          </span>
        </template>
        <AssetReviewTable 
          :assets="overdueAssets" 
          :loading="loadingOverdue"
          :canWrite="canWrite('asset_reviews')"
          :selectable="canDelete('asset_reviews')"
          v-model:selectedAssets="selectedAssets"
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
          :canWrite="canWrite('asset_reviews')"
          :selectable="canDelete('asset_reviews')"
          v-model:selectedAssets="selectedAssets"
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
          :canWrite="canWrite('asset_reviews')"
          :selectable="canDelete('asset_reviews')"
          v-model:selectedAssets="selectedAssets"
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

    <!-- Bulk Review Dialog -->
    <Dialog
      v-model:visible="showBulkReviewDialog"
      :header="t('assetReviews.bulk.title')"
      modal
      :closable="true"
      :dismissableMask="true"
      style="width: 600px"
    >
      <div class="p-fluid">
        <p class="mb-3">{{ t('assetReviews.bulk.description', { count: selectedAssets.length }) }}</p>
        <div class="field">
          <label>{{ t('assetReviews.reviewNotes') }}</label>
          <Textarea
            v-model="bulkReviewNotes"
            :rows="4"
            :placeholder="t('assetReviews.reviewNotesPlaceholder')"
          />
        </div>
        <div class="flex justify-content-end gap-2 mt-3">
          <Button
            :label="t('assetReviews.bulk.confirm')"
            icon="pi pi-check"
            class="p-button-success"
            @click="confirmBulkReview"
            :loading="bulkReviewing"
          />
          <Button
            :label="t('common.actions.cancel')"
            icon="pi pi-times"
            class="p-button-secondary"
            @click="showBulkReviewDialog = false"
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
import { useRoute } from 'vue-router'
import { usePermissions } from '@/composables/usePermissions'
import Button from 'primevue/button'
import Card from 'primevue/card'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import Dialog from 'primevue/dialog'
import Textarea from 'primevue/textarea'
import Calendar from 'primevue/calendar'
import Dropdown from 'primevue/dropdown'
import InputNumber from 'primevue/inputnumber'
import ProgressSpinner from 'primevue/progressspinner'
import AssetReviewTable from '../components/features/assets/AssetReviewTable.vue'
import api from '@/api/api'

const { t } = useI18n()
const toast = useToast()
const route = useRoute()
const { canWrite, canDelete } = usePermissions()

const overdueAssets = ref([])
const dueAssets = ref([])
const upcomingAssets = ref([])
const loadingOverdue = ref(false)
const loadingDue = ref(false)
const loadingUpcoming = ref(false)
const recalculating = ref(false)
const reviewing = ref(false)
const skipping = ref(false)
const bulkReviewing = ref(false)
const loadingSettings = ref(false)
const savingSettings = ref(false)

const upcomingDays = ref(30)
const upcomingDayValues = [7, 14, 30, 60, 90, 180, 365]
const upcomingDaysOptions = computed(() =>
  upcomingDayValues.map((value) => ({
    label: t('assetReviews.upcomingDaysOption', { count: value }),
    value
  }))
)

const activeTabIndex = ref(0)
const selectedAssets = ref([])

const reviewSettings = ref({
  default_review_interval_months: 6,
  review_due_days_ahead: 30,
  review_upcoming_days_ahead: 30
})

const showReviewDialog = ref(false)
const showSkipDialog = ref(false)
const showBulkReviewDialog = ref(false)
const selectedAsset = ref(null)
const reviewNotes = ref('')
const nextReviewDate = ref(null)
const skipReason = ref('')
const skipNextReviewDate = ref(null)
const bulkReviewNotes = ref('')

const overdueCount = computed(() => overdueAssets.value.length)
const dueCount = computed(() => dueAssets.value.length)
const upcomingCount = computed(() => upcomingAssets.value.length)

function statusToTabIndex(status) {
  const map = { overdue: 0, due: 1, upcoming: 2 }
  return map[status] ?? 0
}

function parseAssetsResponse(res) {
  if (Array.isArray(res.data)) return res.data
  if (res.data?.data && Array.isArray(res.data.data)) return res.data.data
  return []
}

async function fetchOverdue() {
  loadingOverdue.value = true
  try {
    const res = await api.getOverdueAssets()
    overdueAssets.value = parseAssetsResponse(res)
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
    dueAssets.value = parseAssetsResponse(res)
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
    upcomingAssets.value = parseAssetsResponse(res)
  } catch (error) {
    console.error('Error fetching upcoming assets:', error)
    toast.add({ severity: 'error', summary: t('common.messages.error'), detail: t('assetReviews.errorLoading') })
    upcomingAssets.value = []
  } finally {
    loadingUpcoming.value = false
  }
}

async function fetchReviewSettings() {
  if (!canDelete('asset_reviews')) return
  loadingSettings.value = true
  try {
    const res = await api.getTenantReviewSettings()
    reviewSettings.value = { ...reviewSettings.value, ...res.data }
    if (res.data.review_upcoming_days_ahead) {
      upcomingDays.value = res.data.review_upcoming_days_ahead
    }
  } catch (error) {
    console.error('Error loading review settings:', error)
  } finally {
    loadingSettings.value = false
  }
}

async function saveReviewSettings() {
  savingSettings.value = true
  try {
    const res = await api.updateTenantReviewSettings(reviewSettings.value)
    reviewSettings.value = { ...reviewSettings.value, ...res.data }
    if (res.data.review_upcoming_days_ahead) {
      upcomingDays.value = res.data.review_upcoming_days_ahead
    }
    toast.add({ severity: 'success', summary: t('common.messages.success'), detail: t('assetReviews.settings.saved') })
    await Promise.all([fetchDue(), fetchUpcoming()])
  } catch (error) {
    console.error('Error saving review settings:', error)
    toast.add({ severity: 'error', summary: t('common.messages.error'), detail: error.response?.data?.detail || t('assetReviews.settings.errorSaving') })
  } finally {
    savingSettings.value = false
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
    selectedAssets.value = []
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
    selectedAssets.value = []
    await Promise.all([fetchOverdue(), fetchDue(), fetchUpcoming()])
  } catch (error) {
    console.error('Error skipping review:', error)
    toast.add({ severity: 'error', summary: t('common.messages.error'), detail: error.response?.data?.detail || t('assetReviews.errorSkipping') })
  } finally {
    skipping.value = false
  }
}

function openBulkReviewDialog() {
  bulkReviewNotes.value = ''
  showBulkReviewDialog.value = true
}

async function confirmBulkReview() {
  if (selectedAssets.value.length === 0) return

  bulkReviewing.value = true
  try {
    await api.bulkReviewAssets({
      asset_ids: selectedAssets.value.map((a) => a.id),
      notes: bulkReviewNotes.value || null
    })
    toast.add({ severity: 'success', summary: t('common.messages.success'), detail: t('assetReviews.bulk.success') })
    showBulkReviewDialog.value = false
    selectedAssets.value = []
    await Promise.all([fetchOverdue(), fetchDue(), fetchUpcoming()])
  } catch (error) {
    console.error('Error bulk reviewing assets:', error)
    toast.add({ severity: 'error', summary: t('common.messages.error'), detail: error.response?.data?.detail || t('assetReviews.bulk.error') })
  } finally {
    bulkReviewing.value = false
  }
}

watch(
  () => route.query.status,
  (status) => {
    if (status) {
      activeTabIndex.value = statusToTabIndex(status)
    }
  },
  { immediate: true }
)

watch(activeTabIndex, () => {
  selectedAssets.value = []
})

onMounted(async () => {
  await Promise.all([fetchOverdue(), fetchDue(), fetchUpcoming(), fetchReviewSettings()])
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

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1.5rem;
  align-items: end;
}

.settings-actions {
  display: flex;
  align-items: flex-end;
}

.bulk-bar {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1rem;
  background: var(--surface-100);
  border-radius: 8px;
  border: 1px solid var(--surface-border);
}
</style>
