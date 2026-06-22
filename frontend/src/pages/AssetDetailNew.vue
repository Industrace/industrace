<!--
  - AssetDetailNew.vue
  - Nuovo layout con 4 macro-sezioni: Panoramica, Relazioni, Sicurezza e Rischi, Gestione
  - Design ottimizzato per rispondere: "Questa risorsa rappresenta un problema?"
-->
<template>
  <div class="asset-detail-new" v-if="asset">
    <!-- Skip to main content link per accessibilità -->
    <a href="#main-content" class="skip-link">{{ t('common.accessibility.skipToContent') }}</a>
    
    <AssetDetailHeader
      :asset="asset"
      :riskBreakdown="riskTabRef?.riskBreakdown"
      :totalRiskScore="riskTabRef?.totalRiskScore"
      :canWrite="canWrite"
      @edit="showEditDialog = true"
      @print="openPrintDialog"
      @position-saved="onAssetPositionSaved"
      @back="router.push('/assets')"
    />

    <!-- 4 Macro-Sezioni (Tab di primo livello) -->
    <TabView 
      v-model:activeIndex="activeTabIndex" 
      class="asset-macro-tabs"
      @tab-change="onTabChange"
    >
      <!-- 1. PANORAMICA -->
      <TabPanel>
        <template #header>
          <span class="tab-header">
            <i class="pi pi-info-circle"></i>
            {{ t('assets.macroSections.overview') }}
            <Badge v-if="alertLevel" :value="alertLevel" :severity="alertSeverity" class="tab-badge" />
          </span>
        </template>
        <AssetDetailOverviewTab
          :asset="asset"
          :riskBreakdown="riskTabRef?.riskBreakdown"
          :totalRiskScore="riskTabRef?.totalRiskScore"
          :riskFromDependencies="riskTabRef?.riskFromDependencies"
          :getRemoteAccessTypeLabel="getRemoteAccessTypeLabel"
          :getPhysicalAccessLabel="getPhysicalAccessLabel"
          :getBusinessCriticalityLabel="getBusinessCriticalityLabel"
          :canWrite="canWrite"
          @edit="showEditDialog = true"
          @add-note="showNoteDialog = true"
        />
      </TabPanel>

      <!-- 2. RELAZIONI -->
      <TabPanel>
        <template #header>
          <span class="tab-header">
            <i class="pi pi-sitemap"></i>
            {{ t('assets.macroSections.relationships') }}
            <Badge v-if="relationshipsCount > 0" :value="relationshipsCount" severity="info" class="tab-badge" />
          </span>
        </template>
        <AssetDetailRelationsTab
          :asset="asset"
          :assetId="asset.id"
          :canWrite="canWrite"
          @updated="fetchAsset"
        />
      </TabPanel>

      <!-- 3. SICUREZZA E RISCHI -->
      <TabPanel>
        <template #header>
          <span class="tab-header">
            <i class="pi pi-shield"></i>
            {{ t('assets.macroSections.security') }}
            <Badge 
              v-if="criticalVulnerabilitiesCount > 0" 
              :value="criticalVulnerabilitiesCount" 
              severity="danger" 
              class="tab-badge" 
            />
          </span>
        </template>
        <AssetDetailSecurityTab
          :assetId="asset.id"
          ref="riskTabRef"
        />
      </TabPanel>

      <!-- 4. GESTIONE -->
      <TabPanel>
        <template #header>
          <span class="tab-header">
            <i class="pi pi-cog"></i>
            {{ t('assets.macroSections.management') }}
            <Badge 
              v-if="reviewStatus === 'overdue'" 
              value="!" 
              severity="danger" 
              class="tab-badge" 
            />
          </span>
        </template>
        <AssetDetailManagementTab
          :asset="asset"
          :assetId="asset.id"
          :canWrite="canWrite"
          :canRead="canRead"
          @updated="onManagementUpdated"
        />
      </TabPanel>
    </TabView>

    <!-- Dialogs -->
    <Dialog v-model:visible="showEditDialog" :header="t('common.actions.edit') + ' ' + asset?.name" modal style="width: 60vw; max-width: 700px" :closable="true" :dismissableMask="true">
      <AssetForm v-if="asset" :asset="asset" :sites="sites" :assetTypes="assetTypes" :allLocations="allLocations" :allAreas="allAreas" :manufacturers="manufacturers" :assetStatusOptions="assetStatusOptions" :securityZones="securityZones" @submit="onAssetEditSubmit" @cancel="showEditDialog = false" />
    </Dialog>
    <PrintDialog v-model:visible="showPrintDialog" :data="asset" />
    <Dialog v-model:visible="showNoteDialog" :header="t('assets.notes.editNote')" modal style="width: 600px" :closable="true" :dismissableMask="true">
      <template #default>
        <QuillEditor v-model:content="noteDraft" contentType="html" style="min-height:200px" />
        <div class="flex justify-content-end gap-2 mt-3">
          <Button :label="t('common.actions.save')" icon="pi pi-check" class="p-button-sm" @click="saveNote" />
          <Button :label="t('common.actions.cancel')" icon="pi pi-times" class="p-button-secondary p-button-sm" @click="showNoteDialog = false" />
        </div>
      </template>
    </Dialog>
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
import PrintDialog from '../components/print/PrintDialog.vue'
import AssetForm from '../components/forms/AssetForm.vue'
import { usePermissions } from '../composables/usePermissions'
import api from '../api/api'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import Badge from 'primevue/badge'
import ConfirmDialog from 'primevue/confirmdialog'

import { QuillEditor } from '@vueup/vue-quill'  
import { usePrint } from '../composables/usePrint'
import AssetDetailHeader from '../components/features/assets/AssetDetailHeader.vue'
import AssetDetailRiskTab from '../components/features/assets/tabs/AssetDetailRiskTab.vue'

// Nuovi componenti macro-sezioni
import AssetDetailOverviewTab from '../components/features/assets/macrosections/AssetDetailOverviewTab.vue'
import AssetDetailRelationsTab from '../components/features/assets/macrosections/AssetDetailRelationsTab.vue'
import AssetDetailSecurityTab from '../components/features/assets/macrosections/AssetDetailSecurityTab.vue'
import AssetDetailManagementTab from '../components/features/assets/macrosections/AssetDetailManagementTab.vue'

const { loadTemplates } = usePrint()

const route = useRoute()
const router = useRouter()
const toast = useToast()
const confirm = useConfirm()
const { t } = useI18n()
const { canWrite, canDelete, canRead } = usePermissions()

// State
const asset = ref(null)
const loading = ref(true)
const showEditDialog = ref(false)
const showPrintDialog = ref(false)
const showNoteDialog = ref(false)
const noteDraft = ref('')
const riskTabRef = ref(null)
const activeTabIndex = ref(0)
const assetReviewStatus = ref(null)

// Data
const sites = ref([])
const assetTypes = ref([])
const allLocations = ref([])
const allAreas = ref([])
const manufacturers = ref([])
const assetStatusOptions = ref([])
const securityZones = ref([])

// Computed per alert e badge
const alertLevel = computed(() => {
  if (!riskTabRef.value?.totalRiskScore) return null
  const risk = riskTabRef.value.totalRiskScore
  if (risk >= 8) return t('assets.alerts.critical')
  if (risk >= 6) return t('assets.alerts.high')
  if (risk >= 4) return t('assets.alerts.medium')
  return null
})

const alertSeverity = computed(() => {
  if (!riskTabRef.value?.totalRiskScore) return 'info'
  const risk = riskTabRef.value.totalRiskScore
  if (risk >= 8) return 'danger'
  if (risk >= 6) return 'warning'
  if (risk >= 4) return 'info'
  return 'success'
})

const relationshipsCount = computed(() => {
  // TODO: Calcolare da dipendenze + connessioni + comunicazioni
  return 0
})

const criticalVulnerabilitiesCount = computed(() => {
  // TODO: Calcolare da vulnerabilità critiche
  return 0
})

const reviewStatus = computed(() => {
  if (!assetReviewStatus.value) return null
  return assetReviewStatus.value.review_status || null
})

async function loadAssetReviewStatus() {
  if (!canRead('asset_reviews') || !route.params.id) return
  try {
    const res = await api.getAssetReviewStatus(route.params.id)
    assetReviewStatus.value = res.data
  } catch (e) {
    assetReviewStatus.value = null
  }
}

function onManagementUpdated() {
  fetchAsset()
  loadAssetReviewStatus()
}

// Methods
function onTabChange(event) {
  // Salva ultima tab visitata
  localStorage.setItem('assetDetailLastTab', event.index)
}

async function fetchAsset() {
  if (!route.params.id) return
  loading.value = true
  try {
    const res = await api.getAsset(route.params.id)
    asset.value = res.data
    noteDraft.value = asset.value.description || ''
    
    // Ripristina ultima tab visitata
    const lastTab = localStorage.getItem('assetDetailLastTab')
    if (lastTab) {
      activeTabIndex.value = parseInt(lastTab)
    }
    await loadAssetReviewStatus()
  } catch (e) {
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: t('assets.messages.errorLoadingAsset'),
      life: 3000
    })
    router.push('/assets')
  } finally {
    loading.value = false
  }
}

async function loadInitialData() {
  try {
    const [sitesRes, typesRes, locationsRes, areasRes, manufacturersRes, statusRes, zonesRes] = await Promise.all([
      api.getSites(),
      api.getAssetTypes(),
      api.getLocations(),
      api.getAreas(),
      api.getManufacturers(),
      api.getAssetStatuses(),
      api.getSecurityZones()
    ])
    sites.value = sitesRes.data
    assetTypes.value = typesRes.data
    allLocations.value = locationsRes.data
    allAreas.value = areasRes.data
    manufacturers.value = manufacturersRes.data
    assetStatusOptions.value = statusRes.data
    securityZones.value = zonesRes.data
  } catch (e) {
    console.error('Error loading initial data:', e)
  }
}

function onAssetEditSubmit(updatedAsset) {
  asset.value = updatedAsset
  showEditDialog.value = false
  toast.add({
    severity: 'success',
    summary: t('common.messages.success'),
    detail: t('assets.messages.assetUpdated'),
    life: 3000
  })
}

function onAssetPositionSaved({ id, map_x, map_y }) {
  if (asset.value && asset.value.id === id) {
    asset.value.map_x = map_x
    asset.value.map_y = map_y
  }
}

function openPrintDialog() {
  loadTemplates()
  showPrintDialog.value = true
}

async function saveNote() {
  try {
    await api.updateAsset(asset.value.id, { description: noteDraft.value })
    asset.value.description = noteDraft.value
    showNoteDialog.value = false
    toast.add({
      severity: 'success',
      summary: t('common.messages.success'),
      detail: t('assets.notes.editNote') + ' ' + t('common.messages.success'),
      life: 3000
    })
  } catch (e) {
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: t('assets.messages.errorUpdatingAsset'),
      life: 3000
    })
  }
}

// Labels
function getRemoteAccessTypeLabel(value) {
  return t(`assets.remoteAccessType${value?.charAt(0).toUpperCase() + value?.slice(1)}`) || value
}

function getPhysicalAccessLabel(value) {
  return t(`assets.physicalAccess${value?.charAt(0).toUpperCase() + value?.slice(1)}`) || value
}

function getBusinessCriticalityLabel(value) {
  return t(`assets.businessCriticality${value?.charAt(0).toUpperCase() + value?.slice(1)}`) || value
}

onMounted(async () => {
  await Promise.all([fetchAsset(), loadInitialData()])
})

watch(() => route.params.id, async (newId) => {
  if (newId) {
    await fetchAsset()
  }
})
</script>

<style scoped>
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  background: var(--primary-color);
  color: white;
  padding: 0.5rem 1rem;
  text-decoration: none;
  z-index: 1000;
  border-radius: 0 0 4px 0;
}

.skip-link:focus {
  top: 0;
}

.asset-detail-new {
  padding: 1rem;
  max-width: 1600px;
  margin: 0 auto;
}

.asset-macro-tabs {
  margin-top: 2rem;
}

.tab-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.tab-badge {
  margin-left: 0.25rem;
}

:deep(.p-tabview-nav) {
  background: var(--surface-card);
  border-bottom: 2px solid var(--surface-border);
}

:deep(.p-tabview-nav li .p-tabview-nav-link) {
  padding: 1rem 1.5rem;
  font-weight: 500;
}

:deep(.p-tabview-nav li.p-highlight .p-tabview-nav-link) {
  border-bottom: 3px solid var(--primary-color);
  color: var(--primary-color);
}

:deep(.p-tabview-panels) {
  padding: 2rem 0;
  background: var(--surface-ground);
}
</style>
