
<template>
  <div class="assets-page">
    <AssetsHeader 
      :trashMode="trashMode"
      @create="openCreate(t('common.actions.create'))"
      @import="showImportDialog = true"
      @toggleTrash="toggleTrashMode"
    />

    <AssetsFilters 
      :filters="filters"
      :assetStatusOptions="assetStatusOptions"
      :sites="sites"
      :areas="allAreas"
      @showAdvancedFilters="showAdvancedFilters = true"
    />

    <!-- Indicatore conteggio totale -->
    <div class="flex justify-content-between align-items-center mb-3">
      <div class="text-sm text-600">
        <i class="pi pi-info-circle mr-2"></i>
        {{ $t('assets.strings.totalAssets') }} {{ totalAssetsCount }}
      </div>
      <div class="text-sm text-600" v-if="filteredAssets.length !== totalAssetsCount">
        <i class="pi pi-filter mr-2"></i>
        {{ t('assets.strings.filteredAssets', { filtered: filteredAssets.length, total: totalAssetsCount }) }}
      </div>
    </div>

    <BaseDataTable
      :data="assetsWithIP"
      :loading="loading"
      :columns="allColumns"
      :filters="filters"
      :globalFilterFields="['name','site.name','location.name','status.name','manufacturer.name','asset_type.name']"
      :selectionMode="canWrite('assets') ? 'multiple' : null"
      :storageKey="'assets'"
      :showExport="false"
      :autoHeight="true"
      :heightOffsetTop="300"
      :heightOffsetBottom="120"
      @selection-change="selectedAssets = $event"
      @sort="onSort"
    >


      <template #actions>
        <Button 
          v-if="!trashMode && canWrite('assets')"
          :label="t('common.actions.bulkEdit')" 
          icon="pi pi-pencil" 
          severity="warning"
          :disabled="!selectedAssets.length" 
          @click="showBulkDialog = true" 
        />
        <Button 
          v-if="!trashMode && canDelete('assets')"
          :label="t('common.actions.moveToTrash')" 
          icon="pi pi-trash" 
          severity="danger"
          :disabled="!selectedAssets.length" 
          @click="confirmBulkSoftDelete" 
        />
      </template>

      <template #body-status.name="{ data }">
        <span v-if="data.status">
          <span :style="{ background: data.status.color, color: '#fff', padding: '0.2rem 0.5rem', borderRadius: '4px' }">
            {{ data.status.name }}
          </span>
        </span>
        <span v-else>-</span>
      </template>

      <template #body-business_criticality="{ data }">
        <span v-if="data.business_criticality" :style="{ 
          background: getCriticalityColor(data.business_criticality), 
          color: '#fff', 
          padding: '0.2rem 0.5rem', 
          borderRadius: '4px',
          fontSize: '0.875rem',
          fontWeight: '500'
        }">
          {{ getBusinessCriticalityLabel(data.business_criticality) }}
        </span>
        <span v-else>-</span>
      </template>

      <template #body-risk_score="{ data }">
        <span v-if="data.total_risk_score !== null && data.total_risk_score !== undefined">
          <Tag 
            :value="data.total_risk_score.toFixed(2)" 
            :severity="riskLevelSeverity(data.total_risk_score)"
            v-tooltip.top="data.risk_score !== data.total_risk_score ? `${t('assets.riskBreakdown.baseRiskScore')}: ${data.risk_score?.toFixed(2) || '0.00'} + ${t('assets.riskBreakdown.riskFromDependencies')}: ${(data.total_risk_score - (data.risk_score || 0)).toFixed(2)}` : ''"
          />
        </span>
        <span v-else-if="data.risk_score !== null && data.risk_score !== undefined">
          <Tag :value="data.risk_score.toFixed(2)" :severity="riskLevelSeverity(data.risk_score)" />
        </span>
        <span v-else>-</span>
      </template>

      <template #body-name="{ data }">
        <router-link :to="`/assets/${data.id}`" class="asset-link">
          {{ data.name }}
        </router-link>
      </template>

      <template #body-actions="{ data }">
        <div class="flex gap-2">
          <Button 
            v-if="!trashMode"
            icon="pi pi-eye" 
            size="small"
            @click="viewAsset(data.id)" 
          />
          <Button
            v-if="!trashMode && canWrite('assets')"
            icon="pi pi-pencil"
            size="small"
            @click="openEdit(t('assets.edit'), data)"
          />
          <Button 
            v-if="!trashMode && canWrite('assets')"
            icon="pi pi-copy" 
            size="small"
            severity="info"
            :loading="duplicating"
            @click="duplicateAsset(data)" 
          />
          <Button 
            v-if="!trashMode && canDelete('assets')"
            icon="pi pi-trash" 
            size="small"
            severity="danger"
            @click="deleteAsset(data.id)" 
          />
          <Button 
            v-if="trashMode && canWrite('assets')" 
            icon="pi pi-undo" 
            size="small"
            severity="success"
            @click="restoreAsset(data.id)" 
          />
          <Button 
            v-if="trashMode && canDelete('assets')" 
            icon="pi pi-times" 
            size="small"
            severity="danger"
            @click="hardDeleteAsset(data.id)" 
          />
        </div>
      </template>
    </BaseDataTable>

    <BaseDialog
      v-model:isVisible="showDialog"
      :title="dialogTitle"
      :mode="dialogMode"
      :data="editingAsset"
      :showFooter="false"
      @cancel="close"
    >
      <template #default="{ data }">
        <AssetForm 
          :asset="data" 
          :sites="sites" 
          :allLocations="locations"
          :allAreas="allAreas"
          :assetTypes="assetTypes" 
          :manufacturers="manufacturers"
          :assetStatusOptions="assetStatusOptions"
          @submit="handleSubmit" 
          @cancel="close" 
        />
      </template>
    </BaseDialog>

    <AssetImportDialog :visible="showImportDialog" @close="showImportDialog = false" @imported="onAssetImport" />
    
    <BaseConfirmDialog
      v-model:showConfirmDialog="showConfirmDialog"
      :confirmData="confirmData"
      @execute="executeConfirmedAction"
      @close="closeConfirmDialog"
    />
    
    <AssetsAdvancedFilters 
      v-model:visible="showAdvancedFilters"
      :filters="filters"
      @apply="applyAdvancedFilters"
      @clear="clearAdvancedFilters"
    />

    <AssetsBulkActions 
      v-model:visible="showBulkDialog"
      :assetStatusOptions="assetStatusOptions"
      :sites="sites"
      :assetTypes="assetTypes"
      :areas="allAreas"
      :locations="locations"
      :manufacturers="manufacturers"
      @bulkUpdate="onBulkUpdate"
    />

    <AssetsTrashActions 
      :trashMode="trashMode"
      @emptyTrash="confirmEmptyTrash"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch, computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import { useApi } from '../composables/useApi'
import { useFilters } from '../composables/useFilters'
import { useDialog } from '../composables/useDialog'
import { useConfirm } from '../composables/useConfirm'
import { useDuplicate } from '../composables/useDuplicate'
import { usePermissions } from '../composables/usePermissions'
import { useStatus } from '../composables/useStatus'
import api from '../api/api'

import Tag from 'primevue/tag'
import AssetForm from '../components/forms/AssetForm.vue'
import BaseDataTable from '../components/base/BaseDataTable.vue'
import BaseDialog from '../components/base/BaseDialog.vue'

import BaseConfirmDialog from '../components/base/BaseConfirmDialog.vue'
import AssetImportDialog from '../components/dialogs/AssetImportDialog.vue'
import AssetsHeader from '../components/features/assets/AssetsHeader.vue'
import AssetsFilters from '../components/features/assets/AssetsFilters.vue'
import AssetsAdvancedFilters from '../components/features/assets/AssetsAdvancedFilters.vue'
import AssetsBulkActions from '../components/features/assets/AssetsBulkActions.vue'
import AssetsTrashActions from '../components/features/assets/AssetsTrashActions.vue'

const router = useRouter()
const { t } = useI18n()
const toast = useToast()

// Definizione delle colonne PRIMA di useFilters
const allColumns = [
  { field: 'name', header: t('common.fields.name') },
  { field: 'ip_address', header: t('assets.fields.ipAddress') },
  { field: 'vlan', header: t('assets.fields.vlan') },
  { field: 'logical_port', header: t('assets.fields.logicalPort') },
  { field: 'site.name', header: t('common.fields.site') },
  { field: 'area_name', header: t('areas.fields.name') },
  { field: 'location.name', header: t('locations.fields.name') },
  { field: 'status.name', header: t('common.fields.status') },
  { field: 'manufacturer.name', header: t('manufacturers.fields.name') },
  { field: 'asset_type.name', header: t('common.fields.type') },
  { field: 'business_criticality', header: t('assets.fields.businessCriticality'), sortable: true },
  { field: 'risk_score', header: t('assets.fields.riskScore'), sortable: true },
  { field: 'actions', header: t('common.strings.actions') }
]

// Composables
const { loading, execute } = useApi()
const { filters, globalSearch, selectedColumns, filterData, getApiParams } = useFilters({
  global: { value: null, matchMode: 'contains' },
  status_id: { value: null, matchMode: 'equals' },
  site_id: { value: null, matchMode: 'equals' },
  area_id: { value: null, matchMode: 'equals' },
  business_criticality: { value: null, matchMode: 'equals' },
  risk_score_min: { value: null, matchMode: 'gte' },
  risk_score_max: { value: null, matchMode: 'lte' }
}, 'assets')

const { isVisible: showDialog, data: editingAsset, openCreate, openEdit, close } = useDialog()
// Importa il composable useConfirm e rinomina la funzione per evitare conflitti
const { 
  showConfirmDialog, 
  confirmData, 
  confirmDelete, 
  confirmBulkAction, 
  confirmEmptyTrash: confirmEmptyTrashFn, // rinominato
  executeConfirmedAction,
  closeConfirmDialog 
} = useConfirm()

const { duplicating, duplicateItem, excludeFunctions } = useDuplicate()
const { canRead, canWrite, canDelete } = usePermissions()
const { getStatusSeverity } = useStatus()

// Computed properties per il dialog
const dialogTitle = computed(() => {
  return editingAsset.value ? t('common.actions.edit') : t('common.actions.create')
})

const dialogMode = computed(() => {
  return editingAsset.value ? 'edit' : 'create'
})

// Data
const assets = ref([])
const totalAssets = ref(0)


// Computed per il conteggio totale degli asset
const totalAssetsCount = computed(() => {
  // Se totalAssets è stato impostato dall'API, usalo
  if (totalAssets.value > 0) {
    return totalAssets.value
  }
  // Altrimenti usa il conteggio degli asset caricati
  return assets.value.length
})

// Watcher per aggiornare totalAssets quando assets cambia
watch(assets, (newAssets) => {
  if (newAssets && newAssets.length > 0 && totalAssets.value === 0) {
    totalAssets.value = newAssets.length
  }
}, { immediate: true })
const sites = ref([])
const manufacturers = ref([])
const assetTypes = ref([])
const locations = ref([])
const allAreas = ref([])
const assetStatusOptions = ref([])
const showImportDialog = ref(false)
const selectedAssets = ref([])
const showBulkDialog = ref(false)
const trashMode = ref(false)



const showAdvancedFilters = ref(false)
function applyAdvancedFilters(advancedFiltersData) {
  filters.value.business_criticality.value = advancedFiltersData.business_criticality
  filters.value.risk_score_min.value = advancedFiltersData.risk_score_min
  filters.value.risk_score_max.value = advancedFiltersData.risk_score_max
}
function clearAdvancedFilters() {
  advancedFilters.business_criticality = null
  advancedFilters.risk_score_min = null
  advancedFilters.risk_score_max = null
  filters.value.business_criticality.value = null
  filters.value.risk_score_min.value = null
  filters.value.risk_score_max.value = null
}

function onEditCancel() {
  close()
}

function onSort(event) {
  // Gestione ordinamento se necessario
}


function cleanAssetData(assetData) {
  const cleaned = { ...assetData }
  
  const optionalFieldsToClean = ['ip_address', 'vlan', 'logical_port', 'physical_plug_label', 'firmware_version', 'serial_number', 'tag', 'model', 'description']
  optionalFieldsToClean.forEach(field => {
    if (cleaned[field] === '') {
      cleaned[field] = null
    }
  })
  
  return cleaned
}

// Funzione unificata per gestire submit (creazione e modifica)
async function handleSubmit(assetData) {
  
  const cleanedData = cleanAssetData(assetData)
  
  if (editingAsset.value) {
    // Modalità modifica
    await updateAsset(cleanedData)
  } else {
    // Modalità creazione
    await createAsset(cleanedData)
  }
}

// Debug per verificare i dati
watch(() => editingAsset.value, (newAsset) => {
})

onMounted(async () => {
  await Promise.all([
    fetchAssets(), 
    fetchSites(), 
    fetchAssetTypes(), 
    fetchLocations(),
    fetchAreas(),
    fetchManufactures(),
    fetchAssetStatuses()
  ])
})

async function fetchAssets() {
  await execute(async () => {
    const params = getApiParams()
    let response
    if (trashMode.value) {
      response = await api.getAssetsTrash(params)
    } else {
      response = await api.getAssets(params)
    }
    // Gestisci la nuova struttura della risposta con paginazione
    if (response.data && response.data.data) {
      assets.value = response.data.data
      // Aggiungi informazioni di paginazione se disponibili
      if (response.data.total !== undefined && response.data.total !== null) {
        totalAssets.value = response.data.total
      } else {
        // Fallback: usa il conteggio degli asset caricati
        totalAssets.value = response.data.data.length
      }
    } else {
      // Fallback per la vecchia struttura
      assets.value = response.data || []
      totalAssets.value = assets.value.length
    }
    return response
  }, {
    errorContext: t('assets.messages.fetchError'),
    showToast: false
  })
}

async function fetchSites() {
  await execute(async () => {
    const response = await api.getSites()
    sites.value = response.data
    return response
  }, {
    errorContext: t('assets.messages.fetchSitesError'),
    showToast: false
  })
}

async function fetchLocations() {
  try {
    const response = await api.getLocations()
    locations.value = response.data
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: t('assets.messages.fetchLocationsError'),
      life: 3000
    })
  }
}

async function fetchAreas() {
  try {
    const response = await api.getAreas()
    allAreas.value = response.data
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: t('assets.messages.fetchAreasError'),
      life: 3000
    })
  }
}

async function fetchManufactures() {
  try {
    const response = await api.getManufacturers()
    manufacturers.value = response.data
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: t('assets.messages.fetchManufacturersError'),
      life: 3000
    })
  }
}

async function fetchAssetTypes() {
  try {
    const response = await api.getAssetTypes()
    assetTypes.value = response.data
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: t('assets.messages.fetchAssetTypesError'),
      life: 3000
    })
  }
}

async function fetchAssetStatuses() {
  try {
    const res = await api.getAssetStatuses()
    assetStatusOptions.value = res.data.filter(s => s.active)
  } catch (e) {
    assetStatusOptions.value = []
  }
}



function viewAsset(id) {
  router.push(`/assets/${id}`)
}

async function createAsset(assetData) {
  try {
    const result = await api.createAsset(assetData)
    close()
    await fetchAssets()
  } catch (error) {
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: t('assets.messages.createError'),
      life: 3000
    })
  }
}

async function updateAsset(assetData) {
  try {
    await api.updateAsset(editingAsset.value.id, assetData)
    close()
    await fetchAssets()
  } catch (error) {
    toast.add({ severity: 'error', summary: t('common.messages.error'), detail: t('assets.messages.updateError'), life: 3000 })
  }
}

async function deleteAsset(id) {
  const asset = assets.value.find(a => a.id === id)
  const assetName = asset ? asset.name : 'Asset'
  
  confirmDelete(asset, assetName, async () => {
    await api.deleteAsset(id)
    await fetchAssets()
  }, {
    successMessage: t('assets.messages.deleteSuccess'),
    errorContext: t('assets.messages.deleteError')
  })
}

async function duplicateAsset(asset) {
  await duplicateItem(
    asset,
    async (data) => {
      const result = await api.createAsset(data)
      await fetchAssets()
      return result
    },
    'asset',
    excludeFunctions.asset
  )
}

const filteredAssets = computed(() => {
  let filtered = assets.value
  if (filters.value.status_id.value) {
    filtered = filtered.filter(a => a.status_id === filters.value.status_id.value)
  }
  if (filters.value.site_id.value) {
    filtered = filtered.filter(a => a.site_id === filters.value.site_id.value)
  }
  if (filters.value.area_id.value) {
    filtered = filtered.filter(a => a.area_id === filters.value.area_id.value)
  }
  if (filters.value.business_criticality.value) {
    filtered = filtered.filter(a => (a.business_criticality || '').toLowerCase() === filters.value.business_criticality.value)
  }
  if (filters.value.risk_score_min.value !== null) {
    filtered = filtered.filter(a => (a.risk_score ?? 0) >= filters.value.risk_score_min.value)
  }
  if (filters.value.risk_score_max.value !== null) {
    filtered = filtered.filter(a => (a.risk_score ?? 0) <= filters.value.risk_score_max.value)
  }
  if (filters.value.global.value) {
    const search = filters.value.global.value.toLowerCase()
    filtered = filtered.filter(a =>
      (a.name && a.name.toLowerCase().includes(search)) ||
      (a.interfaces && a.interfaces.some(i => i.ip_address && i.ip_address.toLowerCase().includes(search))) ||
      (a.site && a.site.name && a.site.name.toLowerCase().includes(search)) ||
      (a.area_name && a.area_name.toLowerCase().includes(search)) ||
      (a.location && a.location.name && a.location.name.toLowerCase().includes(search)) ||
      (a.status && a.status.name && a.status.name.toLowerCase().includes(search)) ||
      (a.manufacturer && a.manufacturer.name && a.manufacturer.name.toLowerCase().includes(search)) ||
      (a.asset_type && a.asset_type.name && a.asset_type.name.toLowerCase().includes(search))
    )
  }
  return filtered
})

const assetsWithIP = computed(() =>
  filteredAssets.value.map(asset => ({
    ...asset,
    ip_address: asset.interfaces && asset.interfaces.length
      ? asset.interfaces.map(i => i.ip_address).filter(Boolean).join(', ')
      : '-'
  }))
)

function onAssetImport(result) {
  showImportDialog.value = false
  if (result && (result.created || result.updated)) {
    toast.add({
      severity: 'success',
      summary: t('common.messages.success'),
      detail: t('assets.messages.imported', { created: result.created?.length || 0, updated: result.updated?.length || 0, errors: result.errors?.length || 0 }),
      life: 4000
    })
    fetchAssets()
  } else if (result && result.errors && result.errors.length) {
    toast.add({
      severity: 'warn',
      summary: t('common.messages.warning'),
      detail: t('assets.messages.importErrors', { errors: result.errors.length }),
      life: 4000
    })
  } else {
    toast.add({
      severity: 'info',
      summary: t('common.actions.import'),
      detail: t('assets.messages.importedInfo'),
      life: 4000
    })
  }
}

async function onBulkUpdate(bulkData) {
  try {
    const assetIds = selectedAssets.value.map(asset => asset.id)
    await api.bulkUpdateAssets(assetIds, { [bulkData.field]: bulkData.value })
    toast.add({ severity: 'success', summary: t('common.messages.success'), detail: t('assets.messages.bulkUpdated'), life: 3000 })
    selectedAssets.value = []
    await fetchAssets()
  } catch (error) {
    toast.add({ severity: 'error', summary: t('common.messages.error'), detail: t('assets.messages.bulkUpdateError'), life: 4000 })
  }
}

function confirmBulkSoftDelete() {
  const assetNames = selectedAssets.value.map(asset => asset.name).join(', ')
  confirmBulkAction(
    selectedAssets.value,
    'soft_delete',
    () => bulkSoftDelete(selectedAssets.value), // Passa i parametri correttamente
    t('assets.messages.confirmBulkSoftDelete'),
    t('assets.messages.confirmBulkSoftDeleteMessage', { count: selectedAssets.value.length, names: assetNames })
  )
}

async function bulkSoftDelete(assets) {
  try {
    const assetIds = assets.map(asset => asset.id)
    // console.log('Bulk soft delete - Asset IDs:', assetIds)
    
    const response = await api.bulkSoftDeleteAssets(assetIds)
          // console.log('Bulk soft delete - Response:', response.data)
    
    const deletedCount = response.data.deleted ? response.data.deleted.length : 0
    const errorCount = response.data.errors ? response.data.errors.length : 0
    
          // console.log('Bulk soft delete - Deleted count:', deletedCount, 'Error count:', errorCount)
    
    // Mostra toast di successo solo se ci sono asset eliminati
    if (deletedCount > 0) {
      toast.add({ 
        severity: 'success', 
        summary: t('common.messages.success'), 
        detail: t('assets.messages.bulkSoftDeleted', { count: deletedCount }), 
        life: 3000 
      })
    }
    
    // Mostra toast di warning solo se ci sono errori
    if (errorCount > 0) {
      toast.add({ 
        severity: 'warn', 
        summary: t('common.messages.warning'), 
        detail: t('assets.messages.bulkSoftDeleteErrors', { count: errorCount }), 
        life: 4000 
      })
    }
    
    // Mostra toast di errore se non è stato eliminato nessun asset
    if (deletedCount === 0 && errorCount === 0) {
      toast.add({ 
        severity: 'error', 
        summary: t('common.messages.error'), 
        detail: t('assets.messages.bulkSoftDeleteError'), 
        life: 4000 
      })
    }
    
    selectedAssets.value = []
    await fetchAssets()
  } catch (error) {
    console.error('Bulk soft delete error:', error)
    toast.add({ 
      severity: 'error', 
      summary: t('common.messages.error'), 
      detail: t('assets.messages.bulkSoftDeleteError'), 
      life: 4000 
    })
  }
}

function toggleTrashMode() {
  trashMode.value = !trashMode.value
  fetchAssets()
}

async function restoreAsset(id) {
  try {
    await api.restoreAsset(id)
    toast.add({ severity: 'success', summary: t('common.messages.success'), detail: t('assets.messages.restored'), life: 3000 })
    fetchAssets()
  } catch {
    toast.add({ severity: 'error', summary: t('common.messages.error'), detail: t('assets.messages.restoreError'), life: 3000 })
  }
}

async function hardDeleteAsset(id) {
  try {
    await api.hardDeleteAsset(id)
    toast.add({ severity: 'success', summary: t('common.messages.success'), detail: t('assets.messages.hardDeleted'), life: 3000 })
    fetchAssets()
  } catch {
    toast.add({ severity: 'error', summary: t('common.messages.error'), detail: t('assets.messages.hardDeleteError'), life: 3000 })
  }
}

async function emptyTrash() {
  try {
    await api.emptyAssetsTrash()
    toast.add({ severity: 'success', summary: t('common.messages.success'), detail: t('assets.messages.trashEmptied'), life: 3000 })
    fetchAssets()
  } catch (err) {
    // console.log(err)
    toast.add({ severity: 'error', summary: t('common.messages.error'), detail: t('assets.messages.trashEmptyError'), life: 3000 })
  }
}

function riskLevelSeverity(score) {
  if (score === null || score === undefined) return 'info'
  if (score >= 7) return 'danger'
  if (score >= 4) return 'warning'
  return 'success'
}

function getBusinessCriticalityLabel(value) {
  switch ((value || '').toLowerCase()) {
    case 'low': return t('assets.strings.businessCriticalityLow')
    case 'medium': return t('assets.strings.businessCriticalityMedium')
    case 'high': return t('assets.strings.businessCriticalityHigh')
    case 'critical': return t('assets.strings.businessCriticalityCritical')
    default: return t('common.strings.na')
  }
}

function getCriticalityColor(value) {
  switch ((value || '').toLowerCase()) {
    case 'low': return '#28a745'      // Verde
    case 'medium': return '#ffc107'   // Giallo
    case 'high': return '#fd7e14'     // Arancione
    case 'critical': return '#dc3545' // Rosso
    default: return '#6c757d'         // Grigio
  }
}






// Funzione locale per mostrare il dialog di conferma svuota cestino
function confirmEmptyTrash() {
  confirmEmptyTrashFn(emptyTrash)
}

</script>

<style scoped>
.assets-page {
  padding: 1rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.filters {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.asset-link {
  color: #007bff;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.2s ease;
}

.asset-link:hover {
  color: #0056b3;
  text-decoration: underline;
}

</style>
