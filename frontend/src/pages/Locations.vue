<template>
  <div class="locations-page">
    <div class="page-header">
      <h1>{{ t('locations.title') }}</h1>
      <div class="flex gap-2">
        <Button 
          v-if="!trashMode && canWrite('locations')"
          :label="t('common.actions.create')" 
          icon="pi pi-plus" 
          severity="success"
          @click="openCreateDialog" 
        />

        <div class="w-px h-8 bg-gray-300 mx-2"></div>

        <Button 
          icon="pi pi-trash" 
          :label="trashMode ? t('common.actions.showActive') : t('common.actions.showTrash')" 
          severity="secondary"
          @click="toggleTrashMode"
        />
      </div>
    </div>
    
    <BaseDataTable
      :data="filteredLocations"
      :loading="loading"
      :columns="columnOptions"
      :filters="filters"
      :globalFilterFields="['name','code','description','area','site.name']"
      :selectionMode="!trashMode && canWrite('locations') ? 'multiple' : null"
      :selection="selectedLocations"
      :showExport="false"
      @selection-change="selectedLocations = $event"
      @filter-change="updateFilter"
      @refresh="fetchLocations"
    >
      <template #filters>
        <Dropdown 
          v-model="filters['site_id'].value" 
          :options="siteOptions" 
          optionLabel="name" 
          optionValue="id" 
          :placeholder="t('locations.messages.filterBySite')" 
          showClear 
          style="min-width: 150px" 
        />
        <Dropdown 
          v-model="filters['floorplan_status'].value" 
          :options="floorplanOptions" 
          optionLabel="label" 
          optionValue="value" 
          :placeholder="t('locations.messages.filterByFloorplan')" 
          showClear 
          style="min-width: 150px" 
        />
      </template>

      <template #actions>
        <Button 
          v-if="!trashMode && canWrite('locations')"
          :label="t('common.actions.bulkEdit')" 
          icon="pi pi-pencil" 
          severity="warning"
          :disabled="!selectedLocations.length" 
          @click="openBulkEditDialog" 
        />
      </template>
      
      <template #body-actions="{ data }">
        <div class="flex gap-2">
          <Button 
            v-if="!trashMode"
            icon="pi pi-eye" 
            size="small"
            severity="secondary"
            @click="viewLocation(data.id)" 
          />
          <Button 
            v-if="!trashMode && canWrite('locations')"
            icon="pi pi-pencil" 
            size="small"
            @click="openEditDialog(data)" 
          />
          <Button 
            v-if="!trashMode && canWrite('locations')"
            icon="pi pi-copy" 
            size="small"
            severity="info"
            :loading="duplicating"
            @click="duplicateLocation(data)" 
          />
          <Button 
            v-if="!trashMode && canDelete('locations')"
            icon="pi pi-trash" 
            size="small"
            severity="danger"
            @click="deleteLocation(data.id)" 
          />
          <Button 
            v-if="trashMode && canWrite('locations')"
            icon="pi pi-undo" 
            size="small"
            severity="success"
            @click="restoreLocation(data.id)" 
          />
          <Button 
            v-if="trashMode && canDelete('locations')"
            icon="pi pi-times" 
            size="small"
            severity="danger"
            @click="hardDeleteLocation(data.id)" 
          />
        </div>
      </template>


    </BaseDataTable>
    
    <BaseDialog
      v-model:visible="showDialog"
      :title="editingLocation ? t('common.actions.edit') : t('common.actions.create')"
      :showFooter="false"
      @close="close"
    >
      <LocationForm 
        :location="editingLocation" 
        :sites="sites"
        :areas="areas"
        @submit="saveLocation" 
        @cancel="close"
        @site-changed="handleSiteChanged"
      />
      <FloorplanUploader
        v-if="editingLocation && editingLocation.id"
        :locationId="editingLocation.id"
        :floorplan="editingLocation.floorplan"
        @uploaded="fetchLocations"
      />
    </BaseDialog>

    <BaseDialog
      v-model:visible="showBulkDialog"
      :title="t('common.actions.bulkEdit')"
      :showFooter="false"
      @close="closeBulkDialog"
    >
      <div class="bulk-edit-form">
        <div class="mb-4">
          <p class="text-sm text-gray-600">
            {{ t('common.actions.bulkEditInfo', { count: selectedLocations.length }) }}
          </p>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="field">
            <label class="block text-sm font-medium mb-2">{{ t('common.fields.site') }}</label>
            <Dropdown
              v-model="bulkData.site_id"
              :options="siteOptions"
              option-label="name"
              option-value="id"
              :placeholder="t('common.strings.select')"
              class="w-full"
            />
          </div>
          
          <div class="field">
            <label class="block text-sm font-medium mb-2">{{ t('locations.fields.area') }}</label>
            <InputText
              v-model="bulkData.area"
              :placeholder="t('locations.fields.area')"
              class="w-full"
            />
          </div>
        </div>
        
        <div class="flex justify-end gap-2 mt-6">
          <Button 
            :label="t('common.actions.cancel')" 
            severity="secondary"
            @click="closeBulkDialog" 
          />
          <Button 
            :label="t('common.actions.save')" 
            @click="saveBulkEdit" 
          />
        </div>
      </div>
    </BaseDialog>

    <!-- TODO: Implementare LocationImportDialog -->
    <BaseDialog
      v-model:visible="showFloorplanDialog"
      :title="t('locations.fields.floorplan')"
      @close="showFloorplanDialog = false"
    >
      <Image 
        v-if="selectedFloorplan" 
        :src="getFloorplanThumbnailUrl(selectedFloorplan)" 
        alt="t('locations.fields.floorplan')" 
        width="100%" 
        preview 
      />
    </BaseDialog>
    
    <BaseConfirmDialog
      v-model:showConfirmDialog="showConfirmDialog"
      :confirmData="confirmData"
      @execute="executeConfirmedAction"
      @close="closeConfirmDialog"
    />

    <BaseDialog
      v-model:visible="showViewDialog"
      :title="t('locations.title') + ' - ' + (viewingLocation?.name || '')"
      :showFooter="false"
      :style="{ width: '800px' }"
      @close="showViewDialog = false"
    >
      <div v-if="viewingLocation" class="location-detail">
        <!-- Informazioni base della posizione -->
        <div class="location-info mb-4">
          <h3 class="text-lg font-semibold mb-3">{{ t('common.strings.info') }}</h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div><b>{{ t('common.fields.name') }}:</b> {{ viewingLocation.name }}</div>
            <div><b>{{ t('common.fields.code') }}:</b> {{ viewingLocation.code || '-' }}</div>
            <div><b>{{ t('common.fields.description') }}:</b> {{ viewingLocation.description || '-' }}</div>
            <div><b>{{ t('locations.fields.area') }}:</b> {{ viewingLocation.area || '-' }}</div>
            <div><b>{{ t('common.fields.site') }}:</b> {{ viewingLocation.site?.name || '-' }}</div>
            <div><b>{{ t('locations.fields.floorplan') }}:</b> {{ viewingLocation.floorplan ? t('locations.strings.floorplanPresent') : t('locations.strings.floorplanAbsent') }}</div>
          </div>
          <div v-if="viewingLocation.notes" class="mt-3">
            <b>{{ t('common.fields.notes') }}:</b> {{ viewingLocation.notes }}
          </div>
        </div>

        <!-- Sezione Asset -->
        <div class="assets-section">
          <h3 class="text-lg font-semibold mb-3">{{ t('assets.title') }}</h3>
          <div v-if="loadingAssets" class="text-center py-4">
            <i class="pi pi-spinner pi-spin" style="font-size: 1.5rem;"></i>
            <p class="mt-2">{{ t('common.messages.loading') }}</p>
          </div>
          <div v-else-if="locationAssets.length === 0" class="text-center py-4 text-gray-500">
            <i class="pi pi-info-circle" style="font-size: 1.5rem;"></i>
            <p class="mt-2">{{ t('common.messages.noData') }}</p>
          </div>
          <div v-else class="assets-grid">
            <div 
              v-for="asset in locationAssets" 
              :key="asset.id" 
              class="asset-card"
              @click="viewAsset(asset.id)"
            >
              <div class="asset-header">
                <div class="asset-name">{{ asset.name }}</div>
                <Tag 
                  :value="asset.status?.name || '-'" 
                  :severity="getStatusSeverity(asset.status)"
                />
              </div>
              <div class="asset-details">
                <div class="asset-type">{{ asset.asset_type?.name || '-' }}</div>
                <div class="asset-manufacturer">{{ asset.manufacturer?.name || '-' }}</div>
                <div v-if="asset.risk_score !== null" class="asset-risk">
                  <i class="pi pi-shield"></i>
                  {{ t('assets.fields.riskScore') }}: {{ asset.risk_score.toFixed(1) }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </BaseDialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { usePermissions } from '../composables/usePermissions'
import { useApi } from '../composables/useApi'
import { useFilters } from '../composables/useFilters'
import { useDialog } from '../composables/useDialog'
import { useConfirm } from '../composables/useConfirm'
import { useDuplicate } from '../composables/useDuplicate'
import { useStatus } from '../composables/useStatus'
import api from '../api/api'

import BaseDataTable from '../components/base/BaseDataTable.vue'
import BaseDialog from '../components/base/BaseDialog.vue'
import BaseConfirmDialog from '../components/base/BaseConfirmDialog.vue'
import LocationForm from '../components/forms/LocationForm.vue'
import FloorplanUploader from '../components/features/assets/widgets/FloorplanUploader.vue'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import Image from 'primevue/image'
import Tag from 'primevue/tag'

const { t } = useI18n()
const router = useRouter()
const { canWrite, canDelete } = usePermissions()
const { getStatusSeverity } = useStatus()

// Composables
const { loading, execute } = useApi()
const { filters, globalSearch, selectedColumns, filterData, getApiParams } = useFilters({
  global: { value: null, matchMode: 'contains' },
  site_id: { value: null, matchMode: 'equals' },
  floorplan_status: { value: null, matchMode: 'equals' }
}, 'locations')

const { isVisible: showDialog, data: editingLocation, openCreate, openEdit, close } = useDialog()
const { 
  showConfirmDialog, 
  confirmData, 
  confirmDelete, 
  confirmBulkAction, 
  confirmEmptyTrash,
  executeConfirmedAction,
  closeConfirmDialog 
} = useConfirm()

const { duplicating, duplicateItem, excludeFunctions } = useDuplicate()

const showViewDialog = ref(false)
const viewingLocation = ref(null)
const locationAssets = ref([])
const loadingAssets = ref(false)


// Data
const locations = ref([])
const sites = ref([])
const areas = ref([])
const selectedLocations = ref([])
const trashMode = ref(false)

// Import/Export

// Bulk edit
const showBulkDialog = ref(false)
const bulkData = ref({
  site_id: null,
  area: ''
})

// Floorplan
const showFloorplanDialog = ref(false)
const selectedFloorplan = ref(null)

const columnOptions = computed(() => {
  const columns = [
    { field: 'name', header: t('common.fields.name'), sortable: true },
    { field: 'code', header: t('common.fields.code'), sortable: true },
    { field: 'description', header: t('common.fields.description'), sortable: false },
    { field: 'area_name', header: t('locations.fields.area'), sortable: false },
    { field: 'site.name', header: t('common.fields.site'), sortable: false },
    { field: 'floorplan_status', header: t('locations.fields.floorplan'), sortable: false }
  ]
  
  // Aggiungi colonna azioni sempre, perché il pulsante "Visualizza" è sempre disponibile
  columns.push({ field: 'actions', header: t('common.strings.actions'), sortable: false })
  
  return columns
})

const siteOptions = computed(() => sites.value)

const floorplanOptions = computed(() => [
  { label: t('locations.strings.floorplanPresent'), value: 'present' },
  { label: t('locations.strings.floorplanAbsent'), value: 'absent' }
])

const filteredLocations = computed(() => {
  let filtered = locations.value
  
  // Aggiungi il campo floorplan_status per la visualizzazione
  filtered = filtered.map(location => ({
    ...location,
    floorplan_status: location.floorplan ? 'present' : 'absent'
  }))
  
  // Filtro per sito
  if (filters.value.site_id && filters.value.site_id.value) {
    filtered = filtered.filter(l => l.site_id === filters.value.site_id.value)
  }
  
  // Filtro per planimetria
  if (filters.value.floorplan_status && filters.value.floorplan_status.value) {
    filtered = filtered.filter(l => l.floorplan_status === filters.value.floorplan_status.value)
  }
  
  // Filtro globale
  if (filters.value.global && filters.value.global.value) {
    const search = filters.value.global.value.toLowerCase()
    filtered = filtered.filter(l =>
      (l.name && l.name.toLowerCase().includes(search)) ||
      (l.code && l.code.toLowerCase().includes(search)) ||
      (l.description && l.description.toLowerCase().includes(search)) ||
      (l.area_name && l.area_name.toLowerCase().includes(search)) ||
      (l.site && l.site.name && l.site.name.toLowerCase().includes(search))
    )
  }
  
  return filtered
})

onMounted(async () => {
  await Promise.all([fetchSites(), fetchAreas(), fetchLocations()])
})

async function fetchSites() {
  await execute(async () => {
    const response = await api.getSites()
    sites.value = response.data
    return response
  }, {
    errorContext: t('common.messages.fetchError'),
    showToast: false
  })
}

async function fetchAreas(siteId = null) {
  await execute(async () => {
    const params = siteId ? { site_id: siteId } : {}
    const response = await api.getAreas(params)
    areas.value = response.data
    return response
  }, {
    errorContext: t('common.messages.fetchError'),
    showToast: false
  })
}

async function handleSiteChanged(siteId) {
  // Areas are filtered by computed in LocationForm, no need to reload
  // This is just for potential future use if we need to do something else
}

async function fetchLocations() {
  await execute(async () => {
    const params = getApiParams()
    let response
    if (trashMode.value) {
      response = await api.getLocationsTrash(params)
    } else {
      response = await api.getLocations(params)
    }
    locations.value = response.data
    return response
  }, {
    errorContext: t('common.messages.fetchError'),
    showToast: false
  })
}

function openCreateDialog() {
  // Load all areas when opening create dialog
  fetchAreas()
  openCreate(t('common.actions.create'), null)
}

function openEditDialog(location) {
  // Load all areas when opening edit dialog
  fetchAreas()
  openEdit(t('common.actions.edit'), location)
}

function openBulkEditDialog() {
  bulkData.value = {
    site_id: null,
    area: ''
  }
  showBulkDialog.value = true
}

function closeBulkDialog() {
  showBulkDialog.value = false
  selectedLocations.value = []
}

async function saveBulkEdit() {
  const updates = {}
  if (bulkData.value.site_id !== null) updates.site_id = bulkData.value.site_id
  if (bulkData.value.area !== '') updates.area = bulkData.value.area
  
  if (Object.keys(updates).length === 0) {
    closeBulkDialog()
    return
  }
  
  await execute(async () => {
    for (const location of selectedLocations.value) {
      await api.updateLocation(location.id, updates)
    }
    closeBulkDialog()
    await fetchLocations()
  }, {
    successMessage: t('common.messages.bulkUpdated'),
    errorContext: t('common.messages.bulkError')
  })
}

async function saveLocation(data) {
  const formData = { ...data }
  
  if (editingLocation.value) {
    // Modalità modifica
    await execute(async () => {
      await api.updateLocation(editingLocation.value.id, formData)
      close()
      await fetchLocations()
    }, {
      successMessage: t('common.messages.updated'),
      errorContext: t('common.messages.updateError')
    })
  } else {
    // Modalità creazione
    await execute(async () => {
      await api.createLocation(formData)
      close()
      await fetchLocations()
    }, {
      successMessage: t('common.messages.created'),
      errorContext: t('common.messages.createError')
    })
  }
}

async function deleteLocation(id) {
  await confirmDelete(
    t('common.actions.confirmDelete'),
    t('common.actions.warningDelete'),
    async () => {
      await execute(async () => {
        await api.deleteLocation(id)
        await fetchLocations()
      }, {
        successMessage: t('common.messages.deleted'),
        errorContext: t('common.messages.deleteError')
      })
    }
  )
}

async function duplicateLocation(location) {
  await duplicateItem(
    location,
    async (data) => {
      const result = await api.createLocation(data)
      await fetchLocations()
      return result
    },
    'location',
    excludeFunctions.location
  )
}

async function viewLocation(id) {
  const loc = locations.value.find(l => l.id === id)
  if (loc) {
    viewingLocation.value = loc
    showViewDialog.value = true
    await loadLocationAssets(id)
  }
}

async function loadLocationAssets(locationId) {
  loadingAssets.value = true
  try {
    const response = await api.getAssetsByLocation(locationId)
    locationAssets.value = response.data
  } catch (error) {
    console.error('Error loading location assets:', error)
    locationAssets.value = []
  } finally {
    loadingAssets.value = false
  }
}

function viewAsset(assetId) {
  router.push(`/assets/${assetId}`)
}



function openFloorplanDialog(location) {
  selectedFloorplan.value = location.floorplan
  showFloorplanDialog.value = true
}

function getFloorplanThumbnailUrl(floorplan) {
  if (!floorplan || !floorplan.location_id || !floorplan.id) return ''
  const baseUrl = '/api'
  return `${baseUrl}/locations/${floorplan.location_id}/floorplan/${floorplan.id}`
}

function toggleTrashMode() {
  trashMode.value = !trashMode.value
  selectedLocations.value = []
  fetchLocations()
}

async function restoreLocation(id) {
  await execute(async () => {
    await api.restoreLocation(id)
    await fetchLocations()
  }, {
    successMessage: t('common.messages.restored'),
    errorContext: t('common.messages.restoreError')
  })
}

async function hardDeleteLocation(id) {
  await execute(async () => {
    await api.hardDeleteLocation(id)
    await fetchLocations()
  }, {
    successMessage: t('common.messages.hardDeleted'),
    errorContext: t('common.messages.hardDeleteError')
  })
}

async function emptyTrash() {
  await execute(async () => {
    for (const loc of locations.value) {
      await api.hardDeleteLocation(loc.id)
    }
    await fetchLocations()
  }, {
    successMessage: t('common.messages.trashEmptied'),
    errorContext: t('common.messages.emptyTrashError')
  })
}

async function handleEmptyTrash() {
  await confirmEmptyTrash(
    t('common.messages.emptyTrashConfirm'),
    t('common.messages.emptyTrashWarning'),
    emptyTrash
  )
}

// Export CSV
async function exportCsv() {
  try {
    const response = await api.exportLocationsCsv();
    const blob = new Blob([response.data], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'locations.csv');
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  } catch (e) {
    alert('Errore durante l\'esportazione CSV');
  }
}

// Import
function onLocationImport() {
  showImportDialog.value = false
  fetchLocations()
}

function updateFilter(newFilters) {
  Object.assign(filters, newFilters)
}
</script>

<style scoped>
.locations-page {
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

/* Location Detail Dialog Styles */
.location-detail {
  max-height: 70vh;
  overflow-y: auto;
}

.location-info {
  border-bottom: 1px solid var(--surface-border);
  padding-bottom: 1rem;
}

.assets-section {
  margin-top: 1rem;
}

.assets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.asset-card {
  background: var(--surface-card);
  border: 1px solid var(--surface-border);
  border-radius: 8px;
  padding: 1rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.asset-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: var(--primary-color);
}

.asset-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.75rem;
}

.asset-name {
  font-weight: 600;
  color: var(--text-color);
  flex: 1;
  margin-right: 0.5rem;
}

.asset-details {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.asset-type {
  font-size: 0.875rem;
  color: var(--text-color-secondary);
}

.asset-manufacturer {
  font-size: 0.875rem;
  color: var(--text-color-secondary);
}

.asset-risk {
  font-size: 0.875rem;
  color: var(--primary-color);
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.asset-risk i {
  font-size: 0.75rem;
}
</style> 