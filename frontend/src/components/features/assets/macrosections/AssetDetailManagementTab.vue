<template>
  <div class="asset-management-tab">
    <!-- Riepilogo Gestione -->
    <div class="management-summary card p-4 mb-4">
      <div class="grid">
        <div class="col-12 md:col-3">
          <div class="summary-card">
            <label class="text-600 text-sm">{{ t('assets.management.documents') }}</label>
            <div class="summary-value">{{ documentsCount }}</div>
          </div>
        </div>
        <div class="col-12 md:col-3">
          <div class="summary-card">
            <label class="text-600 text-sm">{{ t('assets.management.contacts') }}</label>
            <div class="summary-value">{{ contactsCount }}</div>
          </div>
        </div>
        <div class="col-12 md:col-3">
          <div class="summary-card">
            <label class="text-600 text-sm">{{ t('assets.management.suppliers') }}</label>
            <div class="summary-value">{{ suppliersCount }}</div>
          </div>
        </div>
        <div class="col-12 md:col-3">
          <div class="summary-card">
            <label class="text-600 text-sm">{{ t('assets.management.nextReview') }}</label>
            <div class="summary-value">
              <Tag :value="reviewStatusLabel" :severity="reviewStatusSeverity" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Documenti (default espanso) -->
    <Accordion :activeIndex="[0]" class="mb-4">
      <AccordionTab :header="t('assets.tabs.documents')">
        <AssetDetailDocumentsTab :assetId="assetId" :readOnly="!canWrite('assets')" />
      </AccordionTab>
    </Accordion>

    <!-- Contatti e Responsabili (default espanso) -->
    <Accordion :activeIndex="[1]" class="mb-4">
      <AccordionTab :header="t('assets.tabs.contacts')">
        <AssetDetailContactsTab :assetId="assetId" :canWrite="canWrite('assets')" />
      </AccordionTab>
    </Accordion>

    <!-- Review e Audit (default espanso) -->
    <Accordion v-if="canReadReview" :activeIndex="[2]" class="mb-4">
      <AccordionTab :header="t('assets.tabs.review')">
        <AssetDetailReviewTab :assetId="assetId" :canWrite="canWrite('asset_reviews')" @updated="onReviewUpdated" />
      </AccordionTab>
    </Accordion>

    <!-- Fornitori (collassabile) -->
    <Accordion class="mb-4">
      <AccordionTab :header="t('assets.tabs.suppliers')">
        <AssetSuppliersTab :assetId="assetId" :readOnly="!canWrite('assets')" />
      </AccordionTab>
    </Accordion>

    <!-- Note e Campi Personalizzati (collassabile) -->
    <Accordion class="mb-4">
      <AccordionTab :header="t('assets.management.notesAndCustomFields')">
        <div class="subsection mb-4">
          <h4 class="subsection-title">{{ t('assets.tabs.notes') }}</h4>
          <div class="asset-notes" v-if="asset?.description" v-html="sanitizedDescription"></div>
          <div v-else class="asset-notes-empty">{{ t('assets.notes.noNotes') }}</div>
          <Button class="mt-3" icon="pi pi-pencil" :label="asset?.description ? t('assets.notes.editNote') : t('assets.notes.addNote')" @click="$emit('edit-note')" v-if="canWrite('assets')" />
        </div>
        <div class="subsection">
          <h4 class="subsection-title">{{ t('assets.tabs.customFields') }}</h4>
          <AssetCustomFields :assetId="assetId" :customFields="asset?.custom_fields" :readOnly="!canWrite('assets')" @saved="$emit('updated')" />
        </div>
      </AccordionTab>
    </Accordion>

    <!-- Timeline (collassabile) -->
    <Accordion>
      <AccordionTab :header="t('assets.tabs.timeline')">
        <AssetDetailTimelineTab :assetId="assetId" />
      </AccordionTab>
    </Accordion>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Tag from 'primevue/tag'
import Button from 'primevue/button'
import Accordion from 'primevue/accordion'
import AccordionTab from 'primevue/accordiontab'
import AssetDetailDocumentsTab from '../tabs/AssetDetailDocumentsTab.vue'
import AssetDetailContactsTab from '../tabs/AssetDetailContactsTab.vue'
import AssetDetailReviewTab from '../tabs/AssetDetailReviewTab.vue'
import AssetSuppliersTab from '../components/AssetSuppliersTab.vue'
import AssetCustomFields from '../components/AssetCustomFields.vue'
import AssetDetailTimelineTab from '../tabs/AssetDetailTimelineTab.vue'
import api from '../../../../api/api'
import DOMPurify from 'dompurify'

const props = defineProps({
  asset: { type: Object, required: true },
  assetId: { type: [String, Number], required: true },
  canWrite: { type: Function, required: true },
  canRead: { type: Function, default: () => () => true }
})

const emit = defineEmits(['updated', 'edit-note'])

const { t } = useI18n()

const canReadReview = computed(() => props.canRead('asset_reviews'))

const documentsCount = ref(0)
const contactsCount = ref(0)
const suppliersCount = ref(0)
const reviewData = ref(null)

const sanitizedDescription = computed(() => {
  if (!props.asset?.description) return ''
  return DOMPurify.sanitize(props.asset.description)
})

const reviewStatusLabel = computed(() => {
  if (!reviewData.value) return t('assets.management.noReviewScheduled')
  const status = reviewData.value.review_status
  if (status === 'overdue') return t('assets.management.reviewOverdue')
  if (status === 'pending' || status === 'due') return t('assets.management.reviewDue')
  if (reviewData.value.next_review_date) {
    return new Date(reviewData.value.next_review_date).toLocaleDateString()
  }
  return t('assets.management.noReviewScheduled')
})

const reviewStatusSeverity = computed(() => {
  if (!reviewData.value) return 'info'
  const status = reviewData.value.review_status
  if (status === 'overdue') return 'danger'
  if (status === 'pending') return 'warning'
  if (status === 'reviewed') return 'success'
  return 'info'
})

async function loadReviewStatus() {
  if (!canReadReview.value) return
  try {
    const res = await api.getAssetReviewStatus(props.assetId)
    reviewData.value = res.data
  } catch (e) {
    console.error('Error loading review status:', e)
    reviewData.value = null
  }
}

function onReviewUpdated() {
  loadReviewStatus()
  emit('updated')
}

async function loadCounts() {
  try {
    // TODO: Caricare conteggi reali
    documentsCount.value = 0
    contactsCount.value = 0
    suppliersCount.value = 0
  } catch (e) {
    console.error('Error loading management counts:', e)
  }
}

onMounted(() => {
  loadCounts()
  loadReviewStatus()
})

watch(() => props.assetId, () => {
  loadReviewStatus()
})
</script>

<style scoped>
.asset-management-tab {
  max-width: 1200px;
}

.summary-card {
  text-align: center;
  padding: 1rem;
}

.summary-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--primary-color);
  margin-top: 0.5rem;
}

.subsection {
  margin-bottom: 2rem;
  padding-bottom: 2rem;
  border-bottom: 1px solid var(--surface-border);
}

.subsection:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.subsection-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--text-color);
  margin: 0 0 1rem 0;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--surface-200);
}

.asset-notes {
  padding: 1rem;
  background: var(--surface-50);
  border-radius: 8px;
  min-height: 100px;
}

.asset-notes-empty {
  padding: 2rem;
  text-align: center;
  color: var(--text-color-secondary);
  font-style: italic;
}
</style>

