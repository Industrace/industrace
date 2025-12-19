<!--
  - AssetDetail.vue
  - Pagina di dettaglio asset con layout a tab per migliore organizzazione
  - Sistema di change management integrato
-->
<template>
  <div class="asset-detail" v-if="asset">
    <AssetDetailHeader
      :asset="asset"
      :riskBreakdown="riskTabRef?.riskBreakdown"
      :totalRiskScore="riskTabRef?.getTotalRiskScore ? riskTabRef.getTotalRiskScore() : null"
      :canWrite="canWrite"
      @edit="showEditDialog = true"
      @print="openPrintDialog"
      @position-saved="onAssetPositionSaved"
      @back="router.push('/assets')"
    />

    <!-- SEZIONI PRINCIPALI: Due colonne -->
    <div class="asset-main-sections">
      <!-- Colonna sinistra: Info principali e rete -->
      <div class="asset-col">
        <AssetDetailMainInfo :asset="asset" />
      </div>
      <div class="asset-col">
        <AssetDetailTechnicalInfo
          :asset="asset"
          :getRemoteAccessTypeLabel="getRemoteAccessTypeLabel"
          :getPhysicalAccessLabel="getPhysicalAccessLabel"
          :getBusinessCriticalityLabel="getBusinessCriticalityLabel"
        />
      </div>
    </div>

    <!-- TABS: Rischio, Documenti, Contatti, Timeline -->
    <TabView class="modern-tabs">
      <TabPanel>
        <template #header>
          <span :title="t('assets.tabs.riskTooltip')" style="display: flex; align-items: center; gap: 0.4em; white-space: nowrap;">
            <i class="pi pi-exclamation-triangle"></i> {{ t('assets.tabs.risk') }}
          </span>
        </template>
        <AssetDetailRiskTab ref="riskTabRef" :assetId="asset.id" />
      </TabPanel>
      <TabPanel>
        <template #header>
          <span :title="t('assets.tabs.documentsTooltip')" style="display: flex; align-items: center; gap: 0.4em; white-space: nowrap;">
            <i class="pi pi-file"></i> {{ t('assets.tabs.documents') }}
          </span>
        </template>
        <AssetDetailDocumentsTab :assetId="asset.id" :readOnly="!canWrite('assets')" />
      </TabPanel>
      <TabPanel>
        <template #header>
          <span :title="t('assets.tabs.contactsTooltip')" style="display: flex; align-items: center; gap: 0.4em; white-space: nowrap;">
            <i class="pi pi-users"></i> {{ t('assets.tabs.contacts') }}
          </span>
        </template>
        <AssetDetailContactsTab
          :assetId="asset.id"
          :canWrite="canWrite('assets')"
        />
      </TabPanel>
      <TabPanel>
        <template #header>
          <span :title="t('assets.tabs.notesTooltip')" style="display: flex; align-items: center; gap: 0.4em; white-space: nowrap;">
            <i class="pi pi-sticky-note"></i> {{ t('assets.tabs.notes') }}
          </span>
        </template>
        <div class="asset-notes" v-if="asset.description" v-html="sanitizedDescription"></div>
        <div v-else class="asset-notes-empty">{{ t('assets.notes.noNotes') }}</div>
        <Button class="mt-3" icon="pi pi-pencil" :label="asset.description ? t('assets.notes.editNote') : t('assets.notes.addNote')" @click="showNoteDialog = true" v-if="canWrite('assets')" />
        <Dialog v-model:visible="showNoteDialog" :header="t('assets.notes.editNote')" modal style="width: 600px" :closable="true" :dismissableMask="true">
          <template #default>
            <QuillEditor v-model:content="noteDraft" contentType="html" style="min-height:200px" />
            <div class="flex justify-content-end gap-2 mt-3">
              <Button :label="t('common.actions.save')" icon="pi pi-check" class="p-button-sm" @click="saveNote" />
              <Button :label="t('common.actions.cancel')" icon="pi pi-times" class="p-button-secondary p-button-sm" @click="showNoteDialog = false" />
            </div>
          </template>
        </Dialog>
      </TabPanel>
      <!-- NUOVA TAB CONNESSIONI -->
      <TabPanel>
        <template #header>
          <span :title="t('assets.tabs.connectionsTooltip')" style="display: flex; align-items: center; gap: 0.4em; white-space: nowrap;">
            <i class="pi pi-link"></i> {{ t('assets.tabs.connections') }}
          </span>
        </template>
        <AssetDetailConnectionsTab :assetId="asset.id" :assetInterfaces="asset.interfaces || []" />
      </TabPanel>
      <!-- NUOVA TAB COMUNICAZIONI -->
      <TabPanel>
        <template #header>
          <span :title="t('assets.tabs.communicationsTooltip')" style="display: flex; align-items: center; gap: 0.4em; white-space: nowrap;">
            <i class="pi pi-share-alt"></i> {{ t('assets.tabs.communications') }}
          </span>
        </template>
        <AssetDetailCommunicationsTab :assetId="asset.id" />
      </TabPanel>
      <TabPanel>
        <template #header>
          <span :title="t('assets.tabs.suppliersTooltip')" style="display: flex; align-items: center; gap: 0.4em; white-space: nowrap;">
            <i class="pi pi-briefcase"></i> {{ t('assets.tabs.suppliers') }}
          </span>
        </template>
        <AssetSuppliersTab :assetId="asset.id" :readOnly="!canWrite('assets')" />
      </TabPanel>
      <TabPanel>
        <template #header>
          <span :title="t('assets.tabs.customFieldsTooltip')" style="display: flex; align-items: center; gap: 0.4em; white-space: nowrap;">
            <i class="pi pi-list"></i> {{ t('assets.tabs.customFields') }}
          </span>
        </template>
        <AssetCustomFields :assetId="asset.id" :customFields="asset.custom_fields" :readOnly="!canWrite('assets')" @saved="onCustomFieldsSaved" />
      </TabPanel>
      <TabPanel>
        <template #header>
          <span :title="t('assets.tabs.reviewTooltip')" style="display: flex; align-items: center; gap: 0.4em; white-space: nowrap;">
            <i class="pi pi-calendar-check"></i> {{ t('assets.tabs.review') }}
          </span>
        </template>
        <AssetDetailReviewTab :assetId="asset.id" :canWrite="canWrite('assets')" @updated="fetchAsset" />
      </TabPanel>
      <TabPanel>
        <template #header>
          <span :title="t('assets.tabs.dependenciesTooltip')" style="display: flex; align-items: center; gap: 0.4em; white-space: nowrap;">
            <i class="pi pi-sitemap"></i> {{ t('assets.tabs.dependencies') }}
          </span>
        </template>
        <AssetDetailDependenciesTab :assetId="asset.id" :canWrite="canWrite('assets')" @updated="fetchAsset" />
      </TabPanel>
      <TabPanel>
        <template #header>
          <span :title="t('assets.tabs.vulnerabilitiesTooltip')" style="display: flex; align-items: center; gap: 0.4em; white-space: nowrap;">
            <i class="pi pi-shield"></i> {{ t('assets.tabs.vulnerabilities') }}
          </span>
        </template>
        <AssetDetailVulnerabilitiesTab :assetId="asset.id" :canWrite="canWrite('assets')" @updated="fetchAsset" />
      </TabPanel>
      <TabPanel>
        <template #header>
          <span :title="t('assets.tabs.timelineTooltip')" style="display: flex; align-items: center; gap: 0.4em; white-space: nowrap;">
            <i class="pi pi-clock"></i> {{ t('assets.tabs.timeline') }}
          </span>
        </template>
        <AssetDetailTimelineTab :assetId="asset.id" />
      </TabPanel>
      <TabPanel>
        <template #header>
          <span :title="t('assets.tabs.iec62443Tooltip')" style="display: flex; align-items: center; gap: 0.4em; white-space: nowrap;">
            <i class="pi pi-shield"></i> {{ t('assets.tabs.iec62443') }}
          </span>
        </template>
        <AssetDetailIEC62443Tab 
          :assetId="asset.id" 
          :asset="asset"
          :canWrite="canWrite('assets')"
          @updated="fetchAsset"
        />
      </TabPanel>
    </TabView>

    <!-- Dialogs -->
    <Dialog v-model:visible="showEditDialog" :header="t('common.actions.edit') + ' ' + asset?.name" modal style="width: 60vw; max-width: 700px" :closable="true" :dismissableMask="true">
      <AssetForm v-if="asset" :asset="asset" :sites="sites" :assetTypes="assetTypes" :allLocations="allLocations" :allAreas="allAreas" :manufacturers="manufacturers" :assetStatusOptions="assetStatusOptions" :securityZones="securityZones" @submit="onAssetEditSubmit" @cancel="showEditDialog = false" />
    </Dialog>
    <PrintDialog v-model:visible="showPrintDialog" :data="asset" />

    <ConfirmDialog />
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import { useI18n } from 'vue-i18n'

// Componenti
import AssetCustomFields from '../components/features/assets/components/AssetCustomFields.vue'
import PrintDialog from '../components/print/PrintDialog.vue'
import AssetForm from '../components/forms/AssetForm.vue'
import { usePermissions } from '../composables/usePermissions'
import { useDateFormatter } from '../composables/useDateFormatter'
import api from '../api/api'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import Button from 'primevue/button'
import ConfirmDialog from 'primevue/confirmdialog'

import { QuillEditor } from '@vueup/vue-quill'  
import { usePrint } from '../composables/usePrint'
import AssetSuppliersTab from '../components/features/assets/components/AssetSuppliersTab.vue'
import AssetDetailHeader from '../components/features/assets/AssetDetailHeader.vue'
import AssetDetailMainInfo from '../components/features/assets/AssetDetailMainInfo.vue'
import AssetDetailTechnicalInfo from '../components/features/assets/AssetDetailTechnicalInfo.vue'
import AssetDetailRiskTab from '../components/features/assets/tabs/AssetDetailRiskTab.vue'
import AssetDetailDocumentsTab from '../components/features/assets/tabs/AssetDetailDocumentsTab.vue'
import AssetDetailContactsTab from '../components/features/assets/tabs/AssetDetailContactsTab.vue'
import AssetDetailReviewTab from '../components/features/assets/tabs/AssetDetailReviewTab.vue'
import AssetDetailDependenciesTab from '../components/features/assets/tabs/AssetDetailDependenciesTab.vue'
import AssetDetailVulnerabilitiesTab from '../components/features/assets/tabs/AssetDetailVulnerabilitiesTab.vue'
import AssetDetailTimelineTab from '../components/features/assets/tabs/AssetDetailTimelineTab.vue'
import AssetDetailConnectionsTab from '../components/features/assets/tabs/AssetDetailConnectionsTab.vue'
import AssetDetailCommunicationsTab from '../components/features/assets/tabs/AssetDetailCommunicationsTab.vue'
import AssetDetailIEC62443Tab from '../components/features/assets/tabs/AssetDetailIEC62443Tab.vue'
import DOMPurify from 'dompurify'
const { loadTemplates } = usePrint()

const route = useRoute()
const router = useRouter()
const toast = useToast()
const confirm = useConfirm()
const { t } = useI18n()
const { canWrite, canDelete } = usePermissions()

const { formatDate } = useDateFormatter()
// Rimuovo tutte le funzioni, ref e computed relativi al floorplan

const interfacesExpanded = ref(false)
// Data
const asset = ref(null)
const loading = ref(false)
const activeTab = ref(0)
const riskTabRef = ref(null)
// Dialog states
const showContactDialog = ref(false)
const showPrintDialog = ref(false)
const showEditDialog = ref(false)
const sites = ref([])
const assetTypes = ref([])
const allLocations = ref([])
const allAreas = ref([])
const manufacturers = ref([])
const assetStatusOptions = ref([])
const securityZones = ref([])

async function fetchAssetStatuses() {
  try {
    const res = await api.getAssetStatuses()
    assetStatusOptions.value = res.data.filter(s => s.active)
  } catch (e) {
    assetStatusOptions.value = []
  }
}

// Contacts
const assetContacts = ref([])

async function fetchSites() {
  try {
    const response = await api.getSites()
    sites.value = response.data
  } catch (e) {
    console.error('Error fetching sites:', e)
    sites.value = []
  }
}
async function fetchAssetTypes() {
  try {
    const response = await api.getAssetTypes()
    assetTypes.value = response.data
  } catch (e) {
    console.error('Error fetching asset types:', e)
    assetTypes.value = []
  }
}
async function fetchLocations() {
  try {
    const response = await api.getLocations()
    allLocations.value = response.data
  } catch (e) {
    console.error('Error fetching locations:', e)
    allLocations.value = []
  }
}

async function fetchAreas() {
  try {
    const response = await api.getAreas()
    allAreas.value = response.data
  } catch (e) {
    console.error('Error fetching areas:', e)
    allAreas.value = []
  }
}
async function fetchManufacturers() {
  try {
    const response = await api.getManufacturers()
    manufacturers.value = response.data
  } catch (e) {
    console.error('Error fetching manufacturers:', e)
    manufacturers.value = []
  }
}

async function fetchSecurityZones() {
  try {
    const response = await api.getSecurityZones()
    securityZones.value = response.data || []
  } catch (e) {
    console.error('Error fetching security zones:', e)
    securityZones.value = []
  }
}


// Lifecycle
onMounted(() => {
  initializeAsset()
})

async function initializeAsset() {
  loading.value = true
  try {
    const res = await api.getAsset(route.params.id)
    asset.value = res.data
    await fetchAssetStatuses()
    await fetchAssetTypes()
    await fetchManufacturers()
    await fetchLocations()
    await fetchAreas()
    await fetchSites()
    await fetchSecurityZones()
  } finally {
    loading.value = false
  }
}

watch(() => route.params.id, async () => {
  await fetchAsset()
  await fetchAssetStatuses()
  await fetchAssetTypes()
  await fetchManufacturers()
  await fetchLocations()
  await fetchAreas()
  await fetchSites()
})

// Methods
async function fetchAsset() {
  loading.value = true
  try {
    const response = await api.getAsset(route.params.id)
    asset.value = response.data
  } catch {
    toast.add({ 
      severity: 'error', 
      summary: t('common.messages.error'), 
      detail: t('assets.messages.fetchError'), 
      life: 3000 
    })
    router.push('/assets')
  } finally {
    loading.value = false
  }
}



async function fetchAssetContacts() {
  const response = await api.getAssetContacts(asset.value.id)
  assetContacts.value = response.data.map(mapContact)
}

function mapContact(contact) {
  return { ...contact, fullName: `${contact.first_name} ${contact.last_name}` }
}



// Print
async function openPrintDialog() {
  if (!asset.value) {
    toast.add({ 
      severity: 'warn', 
      summary: t('common.messages.warning'), 
      detail: t('assets.messages.notLoaded') 
    })
    return
  }
  await loadTemplates()
  showPrintDialog.value = true
}



// Floorplan
function onAssetPositionSaved({ id, map_x, map_y }) {
  if (asset.value && asset.value.id === id) {
    asset.value.map_x = map_x
    asset.value.map_y = map_y
  }
}

// Custom fields
function onCustomFieldsSaved(updatedFields) {
  const newCustomFields = {}
  updatedFields.forEach(({ key, value }) => {
    newCustomFields[key] = value
  })
  asset.value = { 
    ...asset.value, 
    custom_fields: { ...newCustomFields }
  }
  toast.add({ 
    severity: 'success', 
    summary: t('common.messages.success'), 
    detail: t('assets.messages.customFieldsUpdated') 
  })
}

// Edit asset
function editAsset() {
  router.push(`/assets/${asset.value.id}/edit`)
}

async function onAssetEditSubmit(updatedAsset) {
  try {
    await api.updateAsset(asset.value.id, updatedAsset)
    toast.add({ severity: 'success', summary: t('common.messages.success'), detail: t('assets.messages.updated') })
    showEditDialog.value = false
    await fetchAsset()
  } catch (err) {
    toast.add({ severity: 'error', summary: t('common.messages.error'), detail: t('assets.messages.updateError') })
  }
}

// Watch asset changes
watch(asset, (newVal) => {
  if (newVal) {
    // currentAssetMarker.value = {
    //   id: newVal.id,
    //   x: newVal.map_x || 0,
    //   y: newVal.map_y || 0,
    //   name: newVal.name
    // }
  }
}, { immediate: true })

watch(asset, (newAsset) => {
  if (newAsset) {
    // currentAssetMarker.value = {
    //   id: newAsset.id,
    //   x: newAsset.map_x || 0,
    //   y: newAsset.map_y || 0,
    //   name: newAsset.name
    // }
  }
}, { immediate: true })

// Helper functions
function getEntityName(entity) {
  if (!entity) return null
  return typeof entity === 'string' ? entity : entity.name
}

function getManufacturerName(manufacturer) {
  if (!manufacturer) return null
  return typeof manufacturer === 'string' ? manufacturer : manufacturer.name
}

function getPhysicalAccessLabel(value) {
  switch (value) {
    case 'internal': return t('assets.strings.physicalAccessInternal')
    case 'dmz': return t('assets.strings.physicalAccessDMZ')
    case 'external': return t('assets.strings.physicalAccessExternal')
    default: return value || '-'
  }
}
function getBusinessCriticalityLabel(value) {
  switch (value) {
    case 'low': return t('assets.strings.businessCriticalityLow')
    case 'medium': return t('assets.strings.businessCriticalityMedium')
    case 'high': return t('assets.strings.businessCriticalityHigh')
    case 'critical': return t('assets.strings.businessCriticalityCritical')
    default: return t('common.strings.na')
  }
}
function getRemoteAccessTypeLabel(value) {
  switch (value) {
    case 'none': return t('assets.strings.remoteAccessTypeNone')
    case 'attended': return t('assets.strings.remoteAccessTypeAttended')
    case 'unattended': return t('assets.strings.remoteAccessTypeUnattended')
    default: return value || '-'
  }
}

// --- CONNESSIONI E GRAFO ---
const showNoteDialog = ref(false)
const noteDraft = ref('')
watch(showNoteDialog, (val) => {
  if (val) noteDraft.value = asset.value?.description || ''
})
async function saveNote() {
  try {
    await api.updateAsset(asset.value.id, { description: noteDraft.value })
    asset.value.description = noteDraft.value
    showNoteDialog.value = false
    toast.add({ severity: 'success', summary: t('common.messages.success'), detail: t('assets.messages.noteSaved'), life: 2000 })
  } catch (e) {
    toast.add({ severity: 'error', summary: t('common.messages.error'), detail: t('assets.messages.noteSaveError'), life: 3000 })
  }
}

const sanitizedDescription = computed(() => asset.value?.description ? DOMPurify.sanitize(asset.value.description) : '')

</script>

<style scoped>
.asset-detail {
  padding: 1rem;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
  gap: 1rem;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex: 1;
}

.asset-title h1 {
  margin: 0 0 0.5rem 0;
  font-size: 1.75rem;
  font-weight: 600;
}

.asset-meta {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.asset-type,
.asset-site {
  font-size: 0.875rem;
  color: #6c757d;
  background: #f8f9fa;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
}

.main-info-card {
  background: #fff;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.info-section h4 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  font-weight: 600;
  color: #495057;
  border-bottom: 2px solid #e9ecef;
  padding-bottom: 0.5rem;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f8f9fa;
}

.info-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.label {
  font-weight: 500;
  color: #495057;
  font-size: 0.875rem;
}

.value {
  color: #6c757d;
  font-size: 0.875rem;
  text-align: right;
  max-width: 60%;
  word-break: break-word;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.asset-tabs {
  background: #fff;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.contacts-section,
.documents-section,
.communications-section {
  padding: 1rem 0;
}

.contacts-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.contacts-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

:deep(.p-tabview-nav) {
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

:deep(.p-tabview-nav-link) {
  padding: 1rem 1.5rem;
  font-weight: 500;
}

:deep(.p-tabview-panels) {
  padding: 1.5rem;
}

:deep(.p-card) {
  background: #fff !important;
  color: #495057 !important;
  border: 1px solid #e9ecef !important;
}

.asset-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f8f9fa;
  border-radius: 12px;
  padding: 1.5rem 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.asset-header .meta {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-top: 0.5rem;
}
.asset-header .actions {
  display: flex;
  gap: 0.5rem;
}
.modern-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  padding: 2rem;
  margin-bottom: 2rem;
}
.modern-tabs :deep(.p-tabview-nav) {
  background: #f4f6fa;
  border-radius: 8px 8px 0 0;
  border-bottom: 2px solid #b0b8c1;
  box-shadow: 0 2px 6px rgba(180, 190, 200, 0.07);
}
.modern-tabs :deep(.p-tabview-nav-link) {
  font-weight: 500;
  font-size: 1rem;
  padding: 0.5rem 1rem;
}
.modern-tabs :deep(.p-tabview-panels) {
  background: #fff;
  border-radius: 0 0 8px 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.03);
  padding: 2rem;
}
.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.2rem 2rem;
  margin-bottom: 1.5rem;
}
.label {
  color: #888;
  font-size: 0.95rem;
}
.value {
  font-weight: 500;
  color: #222;
  margin-left: 0.5rem;
}
.value:empty, .value.na {
  color: #bbb;
  font-style: italic;
}
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: flex-start;
  }
  
  .contacts-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .contacts-actions {
    justify-content: flex-start;
  }
  .asset-header { flex-direction: column; align-items: stretch; }
  .info-grid { grid-template-columns: 1fr; }
}
.asset-header-flex {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
}
.asset-header-main {
  flex: 1;
}
.asset-title {
  margin: 0 0 0.5rem 0;
  font-size: 2rem;
  font-weight: 600;
}
.asset-meta {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 0.5rem;
}
.asset-header-actions {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
}
.asset-main-sections {
  display: flex;
  gap: 2rem;
  margin-bottom: 2rem;
}
.asset-col {
  flex: 1;
  min-width: 250px;
}
.section-title {
  font-weight: 600;
  color: #495057;
  margin-bottom: 0.5rem;
  margin-top: 1.5rem;
}
.info-list {
  margin-bottom: 1rem;
}
.info-list .label {
  color: #888;
  font-size: 0.95rem;
  min-width: 120px;
  display: inline-block;
}
.info-list .value {
  font-weight: 500;
  color: #222;
  margin-left: 0.5rem;
}
@media (max-width: 900px) {
  .asset-main-sections { flex-direction: column; gap: 1rem; }
}
.criticality-badge {
  font-weight: 600;
  letter-spacing: 0.03em;
  text-transform: uppercase;
}
.asset-header-top {
  margin-bottom: 0.5rem;
}
.back-btn {
  margin-bottom: 0.5rem;
}

.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}

/* Scroll orizzontale sulle tab */
.modern-tabs .p-tabview-nav {
  flex-wrap: nowrap !important;
  overflow-x: auto;
  overflow-y: hidden;
  white-space: nowrap;
  scrollbar-width: thin;
}
.modern-tabs .p-tabview-nav li {
  flex: 0 0 auto;
}
.modern-tabs .p-tabview-nav::-webkit-scrollbar {
  height: 6px;
}
</style>
