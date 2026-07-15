<!--
  - Sites.vue
  - Componente per la gestione dei siti
  - Utilizza i componenti PrimeVue per la gestione del form
-->
<template>
  <div class="sites-page">
    <div class="page-header">
      <h1>{{ t('sites.title') }}</h1>
      <div class="flex gap-2">
        <!-- Azioni principali -->
        <Button 
          v-if="!trashMode && canWrite('sites')"
          :label="t('common.actions.create')" 
          icon="pi pi-plus" 
          severity="success"
          @click="openCreateDialog" 
        />
        <Button 
          v-if="!trashMode && canWrite('sites')"
          :label="t('common.actions.import')" 
          icon="pi pi-upload" 
          severity="info"
          @click="showImportDialog = true" 
        />
        <Button 
          v-if="!trashMode"
          :label="t('common.actions.exportCsv')" 
          icon="pi pi-file-excel" 
          severity="secondary"
          @click="exportCsv" 
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

    <div v-if="!trashMode" class="mb-4">
      <Tree :value="siteTree" :selectionMode="null" :filter="true" :filterPlaceholder="t('sites.messages.filterTree')" />
    </div>
    
    <BaseDataTable
      :data="filteredSites"
      :loading="loading"
      :columns="columnOptions"
      :filters="filters"
      :globalFilterFields="['name','code','address','description']"
      :selectionMode="!trashMode && canWrite('sites') ? 'multiple' : null"
      :selection="selectedSites"
      :showExport="false"
      @selection-change="selectedSites = $event"
      @filter-change="updateFilter"
      @refresh="fetchSites"
    >
      <template #filters>
        <Dropdown 
          v-model="filters['parent_id'].value" 
          :options="parentSiteOptions" 
          optionLabel="name" 
          optionValue="id" 
          :placeholder="t('sites.messages.filterByParent')" 
          showClear 
          style="min-width: 150px" 
        />
      </template>

      <template #actions>
        <!-- RIMOSSO: Bottone Bulk Edit -->
      </template>
      
      <template #body-actions="{ data }">
        <div class="flex gap-2">
          <Button 
            v-if="!trashMode"
            icon="pi pi-eye" 
            size="small"
            severity="secondary"
            @click="viewSite(data.id)" 
          />
          <Button 
            v-if="!trashMode && canWrite('sites')"
            icon="pi pi-pencil" 
            size="small"
            @click="openEditDialog(data)" 
          />
          <!-- RIMOSSO: Bottone Duplicazione -->
          <Button 
            v-if="!trashMode && canDelete('sites')"
            icon="pi pi-trash" 
            size="small"
            severity="danger"
            @click="deleteSite(data.id)" 
          />
          <Button 
            v-if="trashMode && canWrite('sites')"
            icon="pi pi-undo" 
            size="small"
            severity="success"
            @click="restoreSite(data.id)" 
          />
          <Button 
            v-if="trashMode && canDelete('sites')"
            icon="pi pi-times" 
            size="small"
            severity="danger"
            @click="hardDeleteSite(data.id)" 
          />
        </div>
      </template>
    </BaseDataTable>
    
    <BaseDialog
      v-model:visible="showDialog"
      :title="editingSite ? t('common.actions.edit') : t('common.actions.create')"
      :showFooter="false"
      @close="close"
    >
      <SiteForm 
        :site="editingSite" 
        :sites="sites"
        @submit="saveSite" 
        @cancel="close" 
      />
    </BaseDialog>

    <BaseDialog
      v-model:visible="showBulkDialog"
      :title="t('common.actions.bulkEdit')"
      @close="closeBulkDialog"
    >
      <div class="bulk-edit-form">
        <div class="mb-4">
          <p class="text-sm text-gray-600">
            {{ t('common.actions.bulkEditInfo', { count: selectedSites.length }) }}
          </p>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="field">
            <label class="block text-sm font-medium mb-2">{{ t('sites.fields.parent') }}</label>
            <Dropdown
              v-model="bulkData.parent_id"
              :options="parentSiteOptions"
              option-label="name"
              option-value="id"
              :placeholder="t('common.strings.select')"
              class="w-full"
            />
          </div>
          
          <div class="field">
            <label class="block text-sm font-medium mb-2">{{ t('common.fields.address') }}</label>
            <InputText
              v-model="bulkData.address"
              :placeholder="t('common.fields.address')"
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

    <SiteImportDialog
      :visible="showImportDialog"
      @close="showImportDialog = false"
      @imported="onSiteImport"
    />
    
    <BaseConfirmDialog
      v-model:showConfirmDialog="showConfirmDialog"
      :confirmData="confirmData"
      @execute="executeConfirmedAction"
      @close="closeConfirmDialog"
    />
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
import api from '../api/api'

import BaseDataTable from '../components/base/BaseDataTable.vue'
import BaseDialog from '../components/base/BaseDialog.vue'
import BaseConfirmDialog from '../components/base/BaseConfirmDialog.vue'
import SiteForm from '../components/forms/SiteForm.vue'
import Tree from 'primevue/tree'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import SiteImportDialog from '../components/dialogs/SiteImportDialog.vue'

const { t } = useI18n()
const router = useRouter()
const { canWrite, canDelete } = usePermissions()

// Composables
const { loading, execute } = useApi()
const { filters, globalSearch, selectedColumns, filterData, getApiParams } = useFilters({
  global: { value: null, matchMode: 'contains' },
  parent_id: { value: null, matchMode: 'equals' }
}, 'sites')

const { isVisible: showDialog, data: editingSite, openCreate, openEdit, close } = useDialog()
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

// Data
const sites = ref([])
const selectedSites = ref([])
const trashMode = ref(false)

// Import/Export
const showImportDialog = ref(false)

// Bulk edit
const showBulkDialog = ref(false)
const bulkData = ref({
  parent_id: null,
  address: ''
})

const columnOptions = computed(() => {
  const columns = [
    { field: 'name', header: t('common.fields.name'), sortable: true },
    { field: 'code', header: t('common.fields.code'), sortable: true },
    { field: 'address', header: t('common.fields.address'), sortable: true },
    { field: 'description', header: t('common.fields.description'), sortable: false }
  ]
  
  // Aggiungi colonna azioni solo se l'utente ha permessi di scrittura o eliminazione
  if (canWrite('sites') || canDelete('sites')) {
    columns.push({ field: 'actions', header: t('common.strings.actions'), sortable: false })
  }
  
  return columns
})

const siteTree = computed(() => buildSiteTree(sites.value))

const parentSiteOptions = computed(() => {
  return sites.value.map(site => ({
    id: site.id,
    name: site.name
  }))
})

const filteredSites = computed(() => {
  let filtered = sites.value
  
  // Filtro per sito padre
  if (filters.value.parent_id && filters.value.parent_id.value) {
    filtered = filtered.filter(site => site.parent_id === filters.value.parent_id.value)
  }
  
  // Filtro globale
  if (filters.value.global && filters.value.global.value) {
    const search = filters.value.global.value.toLowerCase()
    filtered = filtered.filter(site =>
      (site.name && site.name.toLowerCase().includes(search)) ||
      (site.code && site.code.toLowerCase().includes(search)) ||
      (site.address && site.address.toLowerCase().includes(search)) ||
      (site.description && site.description.toLowerCase().includes(search))
    )
  }
  
  return filtered
})

onMounted(fetchSites)

async function fetchSites() {
  await execute(async () => {
    const params = getApiParams()
    let response
    if (trashMode.value) {
      response = await api.getSitesTrash(params)
    } else {
      response = await api.getSites(params)
    }
    sites.value = response.data
    return response
  }, {
    errorContext: t('common.messages.fetchError'),
    showToast: false
  })
}

function openCreateDialog() {
  openCreate(t('common.actions.create'), null)
}

function openEditDialog(site) {
  openEdit(t('common.actions.edit'), site)
}

function openBulkEditDialog() {
  bulkData.value = {
    parent_id: null,
    address: ''
  }
  showBulkDialog.value = true
}

function closeBulkDialog() {
  showBulkDialog.value = false
  selectedSites.value = []
}

async function saveBulkEdit() {
  const updates = {}
  if (bulkData.value.parent_id !== null) updates.parent_id = bulkData.value.parent_id
  if (bulkData.value.address !== '') updates.address = bulkData.value.address
  
  if (Object.keys(updates).length === 0) {
    closeBulkDialog()
    return
  }
  
  await execute(async () => {
    for (const site of selectedSites.value) {
      await api.updateSite(site.id, updates)
    }
    closeBulkDialog()
    await fetchSites()
  }, {
    successMessage: t('common.messages.bulkUpdated'),
    errorContext: t('common.messages.bulkError')
  })
}

async function saveSite(data) {
  if (editingSite.value) {
    // Modalità modifica
    await execute(async () => {
      await api.updateSite(editingSite.value.id, data)
      close()
      await fetchSites()
    }, {
      successMessage: t('common.messages.updated'),
      errorContext: t('common.messages.updateError')
    })
  } else {
    // Modalità creazione
    await execute(async () => {
      await api.createSite(data)
      close()
      await fetchSites()
    }, {
      successMessage: t('common.messages.created'),
      errorContext: t('common.messages.createError')
    })
  }
}

async function deleteSite(id) {
  await confirmDelete(
    t('common.messages.deleteConfirm'),
    t('common.messages.deleteConfirm'),
    async () => {
      await execute(async () => {
        await api.deleteSite(id)
        await fetchSites()
      }, {
        successMessage: t('common.messages.deleted'),
        errorContext: t('common.messages.deleteError')
      })
    }
  )
}

async function duplicateSite(site) {
  await duplicateItem(
    site,
    async (data) => {
      const result = await api.createSite(data)
      await fetchSites()
      return result
    },
    'site',
    excludeFunctions.site
  )
}

function viewSite(id) {
  router.push({ name: 'SiteDetail', params: { id } })
}

function toggleTrashMode() {
  trashMode.value = !trashMode.value
  selectedSites.value = []
  // Forza refresh della lista
  sites.value = []
  fetchSites()
}

async function restoreSite(id) {
  await execute(async () => {
    await api.restoreSite(id)
    await fetchSites()
  }, {
    successMessage: t('common.messages.restored'),
    errorContext: t('common.messages.restoreError')
  })
}

async function hardDeleteSite(id) {
  await execute(async () => {
    await api.hardDeleteSite(id)
    await fetchSites()
  }, {
    successMessage: t('common.messages.hardDeleted'),
    errorContext: t('common.messages.hardDeleteError')
  })
}

async function emptyTrash() {
  await execute(async () => {
    await api.emptySitesTrash()
    await fetchSites()
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
    const response = await api.exportSitesCsv()
    const blob = new Blob([response.data], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'sites.csv')
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (e) {
    alert(t('common.messages.exportError'))
  }
}

// Import
function onSiteImport() {
  showImportDialog.value = false
  fetchSites()
}

function updateFilter(newFilters) {
  Object.assign(filters, newFilters)
}

function buildSiteTree(sites) {
  const map = new Map()
  sites.forEach(site => map.set(site.id, { key: site.id, label: site.name, data: site, children: [] }))
  const tree = []
  map.forEach(node => {
    if (node.data.parent_id && map.has(node.data.parent_id)) {
      map.get(node.data.parent_id).children.push(node)
    } else {
      tree.push(node)
    }
  })
  return tree
}
</script>

<style scoped>
.sites-page {
  padding: 1rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.bulk-edit-form {
  min-width: 400px;
}
</style>
