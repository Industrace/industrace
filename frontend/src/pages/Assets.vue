
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
      :locations="locations"
    />

    <!-- Active Filters Display -->
    <div v-if="activeFiltersCount > 0" class="active-filters mb-3">
      <div class="flex align-items-center gap-2 flex-wrap">
        <span class="text-sm text-600 font-medium">{{ t('assets.strings.activeFilters') || 'Active Filters' }}:</span>
        
        <!-- Status Filter -->
        <span 
          v-if="filters.status_id.value" 
          class="p-tag p-tag-info active-filter-tag"
          @click="clearFilter('status_id')"
        >
          {{ getStatusFilterLabel() }}
          <i class="pi pi-times ml-2" style="font-size: 0.75rem"></i>
        </span>
        
        <!-- Site Filter -->
        <span 
          v-if="filters.site_id.value" 
          class="p-tag p-tag-info active-filter-tag"
          @click="clearFilter('site_id')"
        >
          {{ getSiteFilterLabel() }}
          <i class="pi pi-times ml-2" style="font-size: 0.75rem"></i>
        </span>
        
        <!-- Area Filter -->
        <span 
          v-if="filters.area_id.value" 
          class="p-tag p-tag-info active-filter-tag"
          @click="clearFilter('area_id')"
        >
          {{ getAreaFilterLabel() }}
          <i class="pi pi-times ml-2" style="font-size: 0.75rem"></i>
        </span>
        
        <!-- Location Filter -->
        <span 
          v-if="filters.location_id.value" 
          class="p-tag p-tag-info active-filter-tag"
          @click="clearFilter('location_id')"
        >
          {{ getLocationFilterLabel() }}
          <i class="pi pi-times ml-2" style="font-size: 0.75rem"></i>
        </span>
        
        <!-- Business Criticality Filter -->
        <span 
          v-if="filters.business_criticality.value" 
          class="p-tag active-filter-tag"
          :style="{ 
            background: getCriticalityColor(filters.business_criticality.value),
            color: '#fff',
            border: 'none'
          }"
          @click="clearFilter('business_criticality')"
        >
          {{ getBusinessCriticalityLabel(filters.business_criticality.value) }}
          <i class="pi pi-times ml-2" style="font-size: 0.75rem"></i>
        </span>
        
        <!-- Risk Score Min Filter -->
        <span 
          v-if="filters.risk_score_min.value !== null && filters.risk_score_min.value !== undefined" 
          class="p-tag p-tag-warning active-filter-tag"
          @click="clearFilter('risk_score_min')"
        >
          {{ t('assets.fields.riskScore') }} ≥ {{ filters.risk_score_min.value }}
          <i class="pi pi-times ml-2" style="font-size: 0.75rem"></i>
        </span>
        
        <!-- Risk Score Max Filter -->
        <span 
          v-if="filters.risk_score_max.value !== null && filters.risk_score_max.value !== undefined" 
          class="p-tag p-tag-warning active-filter-tag"
          @click="clearFilter('risk_score_max')"
        >
          {{ t('assets.fields.riskScore') }} ≤ {{ filters.risk_score_max.value }}
          <i class="pi pi-times ml-2" style="font-size: 0.75rem"></i>
        </span>
        
        <!-- Has Critical Vulns Filter -->
        <span 
          v-if="filters.has_critical_vulns?.value" 
          class="p-tag p-tag-danger active-filter-tag"
          @click="filters.has_critical_vulns.value = false"
        >
          {{ t('assets.filters.hasCriticalVulns') || 'Con Vulnerabilità Critiche' }}
          <i class="pi pi-times ml-2" style="font-size: 0.75rem"></i>
        </span>
        
        <!-- Clear All Button -->
        <Button 
          :label="t('common.actions.clearAll') || 'Clear All'" 
          icon="pi pi-filter-slash" 
          severity="secondary"
          size="small"
          text
          @click="clearAllFilters"
          class="p-button-text"
        />
      </div>
    </div>

    <!-- Indicatore conteggio totale -->
    <div class="flex justify-content-between align-items-center mb-3">
      <div class="text-sm text-600">
        <i class="pi pi-info-circle mr-2"></i>
        {{ $t('assets.strings.totalAssets') }} {{ totalAssetsCount }}
      </div>
      <div class="text-sm text-600" v-if="assets.length !== totalAssetsCount">
        <i class="pi pi-filter mr-2"></i>
        {{ t('assets.strings.filteredAssets', { filtered: assets.length, total: totalAssetsCount }) }}
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
import { useRouter, useRoute } from 'vue-router'
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
import AssetsBulkActions from '../components/features/assets/AssetsBulkActions.vue'
import AssetsTrashActions from '../components/features/assets/AssetsTrashActions.vue'

const router = useRouter()
const route = useRoute()
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
const { filters, globalSearch, selectedColumns, filterData, getApiParams, clearFilter: clearFilterComposable, resetFilters, sortField, sortOrder, setSort } = useFilters({
  global: { value: null, matchMode: 'contains' },
  status_id: { value: null, matchMode: 'equals' },
  site_id: { value: null, matchMode: 'equals' },
  area_id: { value: null, matchMode: 'equals' },
  location_id: { value: null, matchMode: 'equals' },
  business_criticality: { value: null, matchMode: 'equals' },
  risk_score_min: { value: null, matchMode: 'gte' },
  risk_score_max: { value: null, matchMode: 'lte' },
  has_critical_vulns: { value: false, matchMode: 'equals' }
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

// Flag per evitare chiamate API durante l'inizializzazione
const isInitializing = ref(true)

// Debounce timer per evitare troppe chiamate API
let debounceTimer = null

// Debounced fetchAssets per evitare troppe chiamate API
function debouncedFetchAssets() {
  if (debounceTimer) {
    clearTimeout(debounceTimer)
  }
  debounceTimer = setTimeout(() => {
    if (!isInitializing.value) {
      fetchAssets()
    }
  }, 300)
}

// Funzione per sincronizzare i filtri con l'URL
function syncFiltersToUrl() {
  const query = {}
  
  // Aggiorna o rimuove i query params in base ai filtri
  if (filters.value.status_id?.value) {
    query.status_id = filters.value.status_id.value
  }
  
  if (filters.value.site_id?.value) {
    query.site_id = filters.value.site_id.value
  }
  
  if (filters.value.area_id?.value) {
    query.area_id = filters.value.area_id.value
  }
  
  if (filters.value.location_id?.value) {
    query.location_id = filters.value.location_id.value
  }
  
  if (filters.value.business_criticality?.value) {
    // Se c'è un valore originale salvato (da URL con virgole), usalo
    // Altrimenti usa il valore del filtro
    if (filters.value.business_criticality._originalValue) {
      query.business_criticality = filters.value.business_criticality._originalValue
    } else {
      query.business_criticality = filters.value.business_criticality.value
    }
  }
  
  if (filters.value.risk_score_min?.value !== null && filters.value.risk_score_min?.value !== undefined) {
    query.risk_score_min = filters.value.risk_score_min.value.toString()
  }
  
  if (filters.value.risk_score_max?.value !== null && filters.value.risk_score_max?.value !== undefined) {
    query.risk_score_max = filters.value.risk_score_max.value.toString()
  }
  
  if (filters.value.global?.value) {
    query.global_search = filters.value.global.value
  }
  
  if (filters.value.has_critical_vulns?.value) {
    query.has_critical_vulns = 'true'
  }
  
  // Sincronizza sort e order
  if (sortField.value) {
    query.sort = sortField.value
    query.order = sortOrder.value === 1 ? 'asc' : 'desc'
  }
  
  // Aggiorna l'URL solo se è diverso da quello attuale per evitare loop
  const currentQuery = { ...route.query }
  const queryChanged = JSON.stringify(query) !== JSON.stringify(currentQuery)
  
  if (queryChanged) {
    router.replace({ query })
  }
}

// Watch specifico per business_criticality per rimuovere _originalValue quando l'utente cambia manualmente
watch(
  () => filters.value.business_criticality?.value,
  (newValue, oldValue) => {
    // Se l'utente ha cambiato manualmente il valore (non durante l'inizializzazione)
    // e c'era un _originalValue, rimuovilo per usare solo il valore selezionato
    if (!isInitializing.value && oldValue !== undefined && filters.value.business_criticality?._originalValue) {
      // Rimuovi _originalValue solo se il nuovo valore è diverso dal primo valore di _originalValue
      const originalFirstValue = filters.value.business_criticality._originalValue.split(',')[0].trim().toLowerCase()
      if (newValue !== originalFirstValue) {
        delete filters.value.business_criticality._originalValue
      }
    }
  }
)

// Watch reattivo sui filtri per triggerare automaticamente fetchAssets e sincronizzare URL
watch(
  () => [
    filters.value.status_id?.value,
    filters.value.site_id?.value,
    filters.value.area_id?.value,
    filters.value.location_id?.value,
    filters.value.business_criticality?.value,
    filters.value.risk_score_min?.value,
    filters.value.risk_score_max?.value,
    filters.value.global?.value,
    filters.value.has_critical_vulns?.value,
    sortField.value,
    sortOrder.value,
    trashMode.value
  ],
  () => {
    if (!isInitializing.value) {
      syncFiltersToUrl()
      debouncedFetchAssets()
    }
  },
  { deep: true }
)

// Watch per sincronizzare l'URL quando cambia (es. navigazione dalla dashboard)
watch(
  () => route.query,
  (newQuery) => {
    if (!isInitializing.value) {
      // Aggiorna i filtri solo se sono diversi dall'URL
      let filtersChanged = false
      
      if (newQuery.status_id !== filters.value.status_id?.value) {
        filters.value.status_id.value = newQuery.status_id || null
        filtersChanged = true
      }
      
      if (newQuery.site_id !== filters.value.site_id?.value) {
        filters.value.site_id.value = newQuery.site_id || null
        filtersChanged = true
      }
      
      if (newQuery.area_id !== filters.value.area_id?.value) {
        filters.value.area_id.value = newQuery.area_id || null
        filtersChanged = true
      }
      
      if (newQuery.location_id !== filters.value.location_id?.value) {
        filters.value.location_id.value = newQuery.location_id || null
        filtersChanged = true
      }
      
      if (newQuery.business_criticality !== filters.value.business_criticality?.value) {
        const value = newQuery.business_criticality
        const criticalityValues = Array.isArray(value) ? value : value?.split(',')
        const firstValue = criticalityValues?.[0]?.trim().toLowerCase()
        if (firstValue && ['low', 'medium', 'high', 'critical'].includes(firstValue)) {
          filters.value.business_criticality.value = firstValue
          // Salva il valore originale se contiene virgole
          if (value && value.includes && value.includes(',')) {
            filters.value.business_criticality._originalValue = value
          } else {
            delete filters.value.business_criticality._originalValue
          }
        } else {
          filters.value.business_criticality.value = null
          delete filters.value.business_criticality._originalValue
        }
        filtersChanged = true
      }
      
      if (newQuery.risk_score_min !== (filters.value.risk_score_min?.value?.toString() || null)) {
        const value = newQuery.risk_score_min ? parseFloat(newQuery.risk_score_min) : null
        filters.value.risk_score_min.value = !isNaN(value) ? value : null
        filtersChanged = true
      }
      
      if (newQuery.risk_score_max !== (filters.value.risk_score_max?.value?.toString() || null)) {
        const value = newQuery.risk_score_max ? parseFloat(newQuery.risk_score_max) : null
        filters.value.risk_score_max.value = !isNaN(value) ? value : null
        filtersChanged = true
      }
      
      if ((newQuery.global_search || newQuery.search) !== filters.value.global?.value) {
        filters.value.global.value = newQuery.global_search || newQuery.search || null
        filtersChanged = true
      }
      
      if (newQuery.has_critical_vulns === 'true' && !filters.value.has_critical_vulns?.value) {
        filters.value.has_critical_vulns.value = true
        filtersChanged = true
      } else if (newQuery.has_critical_vulns !== 'true' && filters.value.has_critical_vulns?.value) {
        filters.value.has_critical_vulns.value = false
        filtersChanged = true
      }
      
      // Sincronizza sort e order
      const newSortField = newQuery.sort || newQuery.sort_by
      const newSortOrder = newQuery.order || newQuery.sort_order || 'asc'
      if (newSortField !== sortField.value || (newSortField && (newSortOrder === 'desc' ? -1 : 1) !== sortOrder.value)) {
        if (newSortField) {
          setSort(newSortField, newSortOrder === 'desc' ? -1 : 1)
        } else {
          setSort('', 1)
        }
        filtersChanged = true
      }
      
      // Se i filtri sono cambiati, fetchAssets verrà chiamato dal watch sui filtri
      // Non chiamare fetchAssets qui per evitare doppie chiamate
    }
  },
  { immediate: false }
)

// Initialize filters from query params
function initializeFiltersFromQuery() {
  const query = route.query
  
  // Parse status_id
  if (query.status_id) {
    filters.value.status_id.value = query.status_id
  }
  
  // Parse site_id
  if (query.site_id) {
    filters.value.site_id.value = query.site_id
  }
  
  // Parse area_id
  if (query.area_id) {
    filters.value.area_id.value = query.area_id
  }
  
  // Parse location_id
  if (query.location_id) {
    filters.value.location_id.value = query.location_id
  }
  
  // Parse risk_score_min
  if (query.risk_score_min) {
    const value = parseFloat(query.risk_score_min)
    if (!isNaN(value)) {
      filters.value.risk_score_min.value = value
    }
  }
  
  // Parse risk_score_max
  if (query.risk_score_max) {
    const value = parseFloat(query.risk_score_max)
    if (!isNaN(value)) {
      filters.value.risk_score_max.value = value
    }
  }
  
  // Parse business_criticality (support single value or comma-separated values)
  // Quando arriva "critical,high" dalla dashboard, prendiamo il primo valore per il dropdown
  // ma manteniamo il valore completo nell'URL per il backend
  if (query.business_criticality) {
    const value = query.business_criticality
    const criticalityValues = Array.isArray(value) ? value : value.split(',')
    const firstValue = criticalityValues[0]?.trim().toLowerCase()
    if (firstValue && ['low', 'medium', 'high', 'critical'].includes(firstValue)) {
      filters.value.business_criticality.value = firstValue
      // Salva il valore originale se contiene virgole per mantenerlo nell'URL
      if (value.includes(',')) {
        filters.value.business_criticality._originalValue = value
      }
    }
  }
  
  // Parse has_critical_vulns
  if (query.has_critical_vulns === 'true') {
    filters.value.has_critical_vulns.value = true
  }
  
  // Parse global_search
  if (query.global_search || query.search) {
    filters.value.global.value = query.global_search || query.search
  }
  
  // Parse sort and order
  if (query.sort || query.sort_by) {
    const field = query.sort || query.sort_by
    const order = query.order || query.sort_order || 'asc'
    setSort(field, order === 'desc' ? -1 : 1)
  }
}

onMounted(async () => {
  // Initialize filters from query params before fetching
  initializeFiltersFromQuery()
  
  await Promise.all([
    fetchAssets(), 
    fetchSites(), 
    fetchAssetTypes(), 
    fetchLocations(),
    fetchAreas(),
    fetchManufactures(),
    fetchAssetStatuses()
  ])
  
  // Dopo il caricamento iniziale, abilita i watch
  isInitializing.value = false
})

async function fetchAssets() {
  await execute(async () => {
    const params = getApiParams()
    // Sovrascrivi business_criticality se c'è un _originalValue
    if (filters.value.business_criticality?._originalValue) {
      params.business_criticality = filters.value.business_criticality._originalValue
    }
    // Aggiungi has_critical_vulns se è true
    if (filters.value.has_critical_vulns?.value) {
      params.has_critical_vulns = true
    }
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

const assetsWithIP = computed(() =>
  assets.value.map(asset => ({
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
  // fetchAssets verrà chiamato automaticamente dal watch su trashMode
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

// Active filters management
const activeFiltersCount = computed(() => {
  let count = 0
  if (filters.value.status_id?.value) count++
  if (filters.value.site_id?.value) count++
  if (filters.value.area_id?.value) count++
  if (filters.value.location_id?.value) count++
  if (filters.value.business_criticality?.value) count++
  if (filters.value.risk_score_min?.value !== null && filters.value.risk_score_min?.value !== undefined) count++
  if (filters.value.risk_score_max?.value !== null && filters.value.risk_score_max?.value !== undefined) count++
  if (filters.value.global?.value) count++
  if (filters.value.has_critical_vulns?.value) count++
  return count
})

function getStatusFilterLabel() {
  if (!filters.value.status_id?.value) return ''
  const status = assetStatusOptions.value.find(s => s.id === filters.value.status_id.value)
  return status ? status.name : ''
}

function getSiteFilterLabel() {
  if (!filters.value.site_id?.value) return ''
  const site = sites.value.find(s => s.id === filters.value.site_id.value)
  return site ? site.name : ''
}

function getAreaFilterLabel() {
  if (!filters.value.area_id?.value) return ''
  const area = allAreas.value.find(a => a.id === filters.value.area_id.value)
  return area ? area.name : ''
}

function getLocationFilterLabel() {
  if (!filters.value.location_id?.value) return ''
  const location = locations.value.find(l => l.id === filters.value.location_id.value)
  return location ? location.name : ''
}

function clearFilter(filterName) {
  if (filters.value[filterName]) {
    // Per boolean, usa false invece di null
    if (filterName === 'has_critical_vulns') {
      filters.value[filterName].value = false
    } else {
      filters.value[filterName].value = null
    }
  }
  // syncFiltersToUrl e fetchAssets verranno chiamati automaticamente dal watch
}

function clearAllFilters() {
  filters.value.status_id.value = null
  filters.value.site_id.value = null
  filters.value.area_id.value = null
  filters.value.location_id.value = null
  filters.value.business_criticality.value = null
  filters.value.risk_score_min.value = null
  filters.value.risk_score_max.value = null
  filters.value.global.value = null
  filters.value.has_critical_vulns.value = false
  // syncFiltersToUrl e fetchAssets verranno chiamati automaticamente dal watch
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

.active-filters {
  padding: 0.75rem;
  background: #f8f9fa;
  border-radius: 0.5rem;
  border: 1px solid #dee2e6;
}

.active-filter-tag {
  cursor: pointer;
  user-select: none;
  display: inline-flex;
  align-items: center;
  transition: opacity 0.2s ease;
}

.active-filter-tag:hover {
  opacity: 0.8;
}

</style>
