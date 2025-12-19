<!--
  - Manufacturers.vue
  - Componente per la gestione dei produttori
  - Utilizza i componenti standardizzati e composables
-->
<template>
  <div class="manufacturers-page">
    <div class="page-header">
      <h1>{{ t('manufacturers.title') }}</h1>
      <div class="flex gap-2">
        <!-- Azioni principali -->
        <Button 
          v-if="!trashMode && canWrite('manufacturers')"
          :label="t('common.actions.create')" 
          icon="pi pi-plus" 
          severity="success"
          @click="openCreateDialog" 
        />
        <Button 
          v-if="!trashMode && canWrite('manufacturers')"
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
        
        <!-- Separatore visivo -->
        <div class="w-px h-8 bg-gray-300 mx-2"></div>
        
        <!-- Gestione cestino -->
        <Button 
          icon="pi pi-trash" 
          :label="trashMode ? t('common.actions.showActive') : t('common.actions.showTrash')" 
          severity="secondary"
          @click="toggleTrashMode"
        />
      </div>
    </div>

    <BaseDataTable
      :data="filteredManufacturers"
      :loading="loading"
      :columns="columnOptions"
      :filters="filters"
      :globalFilterFields="['name','description','website','email','phone']"
      :selectionMode="!trashMode && canWrite('manufacturers') ? 'multiple' : null"
      :selection="selectedManufacturers"
      :showExport="false"
      @selection-change="selectedManufacturers = $event"
      @filter-change="updateFilter"
      @refresh="fetchManufacturers"
    >
      <template #actions>
        <Button 
          v-if="!trashMode && canWrite('manufacturers')"
          :label="t('common.actions.bulkEdit')" 
          icon="pi pi-pencil" 
          severity="warning"
          :disabled="!selectedManufacturers.length" 
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
            @click="goToDetail(data.id)" 
          />
          <Button 
            v-if="!trashMode && canWrite('manufacturers')"
            icon="pi pi-pencil" 
            size="small"
            @click="openEditDialog(data)" 
          />
          <Button 
            v-if="!trashMode && canWrite('manufacturers')"
            icon="pi pi-copy" 
            size="small"
            severity="info"
            :loading="duplicating"
            @click="duplicateManufacturer(data)" 
          />
          <Button 
            v-if="!trashMode && canDelete('manufacturers')"
            icon="pi pi-trash" 
            size="small"
            severity="danger"
            @click="deleteManufacturer(data.id)" 
          />
          <Button 
            v-if="trashMode && canWrite('manufacturers')"
            icon="pi pi-undo" 
            size="small"
            severity="success"
            @click="restoreManufacturer(data.id)" 
          />
          <Button 
            v-if="trashMode && canDelete('manufacturers')"
            icon="pi pi-times" 
            size="small"
            severity="danger"
            @click="hardDeleteManufacturer(data.id)" 
          />
        </div>
      </template>
    </BaseDataTable>

    <BaseDialog
      v-model:visible="showDialog"
      :title="editingManufacturer ? t('common.actions.edit') : t('common.actions.create')"
      :showFooter="false"
      @close="close"
    >
      <ManufacturerForm 
        :manufacturer="editingManufacturer" 
        @submit="saveManufacturer" 
        @cancel="close" 
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
            {{ t('common.actions.bulkEditInfo', { count: selectedManufacturers.length }) }}
          </p>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="field">
            <label class="block text-sm font-medium mb-2">{{ t('common.fields.website') }}</label>
            <InputText
              v-model="bulkData.website"
              :placeholder="t('common.enter')"
              class="w-full"
            />
          </div>
          
          <div class="field">
            <label class="block text-sm font-medium mb-2">{{ t('common.fields.email') }}</label>
            <InputText
              v-model="bulkData.email"
              :placeholder="t('common.enter')"
              class="w-full"
            />
          </div>
          
          <div class="field">
            <label class="block text-sm font-medium mb-2">{{ t('common.fields.phone') }}</label>
            <InputText
              v-model="bulkData.phone"
              :placeholder="t('common.enter')"
              class="w-full"
            />
          </div>
          
          <div class="field">
            <label class="block text-sm font-medium mb-2">{{ t('common.fields.description') }}</label>
            <Textarea
              v-model="bulkData.description"
              :placeholder="t('common.fields.description')"
              class="w-full"
              rows="3"
            />
          </div>
        </div>
        
        <div class="flex justify-end gap-2 mt-6">
          <Button 
            :label="t('common.actionscancel')" 
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

    <ManufacturerImportDialog
      :visible="showImportDialog"
      @close="showImportDialog = false"
      @imported="onManufacturerImportResult"
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
import ManufacturerForm from '../components/forms/ManufacturerForm.vue'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import ManufacturerImportDialog from '../components/dialogs/ManufacturerImportDialog.vue'

const { t } = useI18n()
const router = useRouter()
const { canWrite, canDelete } = usePermissions()

// Composables
const { loading, execute } = useApi()
const { filters, globalSearch, selectedColumns, filterData, getApiParams } = useFilters({
  global: { value: null, matchMode: 'contains' }
}, 'manufacturers')

const { isVisible: showDialog, data: editingManufacturer, openCreate, openEdit, close } = useDialog()
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
const manufacturers = ref([])
const selectedManufacturers = ref([])
const trashMode = ref(false)

// Import/Export
const showImportDialog = ref(false)
const importResult = ref(null)

// Bulk edit
const showBulkDialog = ref(false)
const bulkData = ref({
  website: '',
  email: '',
  phone: '',
  description: ''
})

const columnOptions = computed(() => {
  const columns = [
    { field: 'name', header: t('common.fields.name'), sortable: true },
    { field: 'description', header: t('common.fields.description'), sortable: false },
    { field: 'website', header: t('common.fields.website'), sortable: false },
    { field: 'email', header: t('common.fields.email'), sortable: false },
    { field: 'phone', header: t('common.fields.phone'), sortable: false }
  ]
  
  // Aggiungi colonna azioni sempre, perché il pulsante "Visualizza" è sempre disponibile
  columns.push({ field: 'actions', header: t('common.strings.actions'), sortable: false })
  
  return columns
})

const filteredManufacturers = computed(() => {
  let filtered = manufacturers.value
  
  // Filtro globale
  if (filters.value.global && filters.value.global.value) {
    const search = filters.value.global.value.toLowerCase()
    filtered = filtered.filter(manufacturer =>
      (manufacturer.name && manufacturer.name.toLowerCase().includes(search)) ||
      (manufacturer.description && manufacturer.description.toLowerCase().includes(search)) ||
      (manufacturer.website && manufacturer.website.toLowerCase().includes(search)) ||
      (manufacturer.email && manufacturer.email.toLowerCase().includes(search)) ||
      (manufacturer.phone && manufacturer.phone.toLowerCase().includes(search))
    )
  }
  
  return filtered
})

onMounted(fetchManufacturers)

async function fetchManufacturers() {
  await execute(async () => {
    const params = getApiParams()
    let response
    if (trashMode.value) {
      response = await api.getManufacturersTrash(params)
    } else {
      response = await api.getManufacturers(params)
    }
    manufacturers.value = response.data
    return response
  }, {
    errorContext: t('common.messages.fetchError'),
    showToast: false
  })
}

function openCreateDialog() {
  openCreate(t('common.new'), null)
}

function openEditDialog(manufacturer) {
  openEdit(t('common.actions.edit'), manufacturer)
}

function openBulkEditDialog() {
  bulkData.value = {
    website: '',
    email: '',
    phone: '',
    description: ''
  }
  showBulkDialog.value = true
}

function closeBulkDialog() {
  showBulkDialog.value = false
  selectedManufacturers.value = []
}

async function saveBulkEdit() {
  const updates = {}
  if (bulkData.value.website !== '') updates.website = bulkData.value.website
  if (bulkData.value.email !== '') updates.email = bulkData.value.email
  if (bulkData.value.phone !== '') updates.phone = bulkData.value.phone
  if (bulkData.value.description !== '') updates.description = bulkData.value.description
  
  if (Object.keys(updates).length === 0) {
    closeBulkDialog()
    return
  }
  
  await execute(async () => {
    for (const manufacturer of selectedManufacturers.value) {
      await api.updateManufacturer(manufacturer.id, updates)
    }
    closeBulkDialog()
    await fetchManufacturers()
  }, {
    successMessage: t('common.bulkUpdated'),
    errorContext: t('common.bulkUpdateError')
  })
}

async function saveManufacturer(data) {
  if (editingManufacturer.value) {
    // Modalità modifica
    await execute(async () => {
      await api.updateManufacturer(editingManufacturer.value.id, data)
      close()
      await fetchManufacturers()
    }, {
      successMessage: t('common.messages.updated'),
      errorContext: t('common.messages.updateError')
    })
  } else {
    // Modalità creazione
    await execute(async () => {
      await api.createManufacturer(data)
      close()
      await fetchManufacturers()
    }, {
      successMessage: t('common.messages.created'),
      errorContext: t('common.messages.createError')
    })
  }
}

async function deleteManufacturer(id) {
  await confirmDelete(
    t('common.messages.deleteConfirm'),
    t('common.messages.deleteWarning'),
    async () => {
      await execute(async () => {
        await api.deleteManufacturer(id)
        await fetchManufacturers()
      }, {
        errorContext: t('common.messages.deleteError')
      })
    },
    {
      successMessage: t('common.messages.deleted')
    }
  )
}

async function duplicateManufacturer(manufacturer) {
  await duplicateItem(
    manufacturer,
    async (data) => {
      const result = await api.createManufacturer(data)
      await fetchManufacturers()
      return result
    },
    'manufacturer',
    excludeFunctions.manufacturer
  )
}

function goToDetail(id) {
  router.push({ name: 'ManufacturerDetail', params: { id } })
}

function toggleTrashMode() {
  trashMode.value = !trashMode.value
  selectedManufacturers.value = []
  fetchManufacturers()
}

async function restoreManufacturer(id) {
  await execute(async () => {
    await api.restoreManufacturer(id)
    await fetchManufacturers()
  }, {
    successMessage: t('common.messages.restored'),
    errorContext: t('common.messages.restoreError')
  })
}

async function hardDeleteManufacturer(id) {
  await execute(async () => {
    await api.hardDeleteManufacturer(id)
    await fetchManufacturers()
  }, {
    successMessage: t('common.messages.hardDeleted'),
    errorContext: t('common.messages.hardDeleteError')
  })
}

async function emptyTrash() {
  await execute(async () => {
    for (const m of manufacturers.value) {
      await api.hardDeleteManufacturer(m.id)
    }
    await fetchManufacturers()
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
    const response = await api.exportManufacturersCsv();
    const blob = new Blob([response.data], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'manufacturers.csv');
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  } catch (e) {
    alert('Errore durante l\'esportazione CSV');
  }
}

function onManufacturerImportResult(result) {
  importResult.value = result
  showImportDialog.value = false
  fetchManufacturers()
}

function updateFilter(filterName, value) {
  if (filters.value[filterName]) {
    filters.value[filterName].value = value
  }
}
</script>

<style scoped>
.manufacturers-page {
  padding: 1rem;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}
</style>
