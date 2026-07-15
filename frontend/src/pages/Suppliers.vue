<!--
  - Suppliers.vue
  - Componente per la gestione dei fornitori
  - Utilizza i componenti PrimeVue per la gestione del form
-->
<template>
  <div class="suppliers-page">
    <div class="page-header">
      <h1>{{ t('suppliers.title') }}</h1>
      <div class="flex gap-2">
        <!-- Azioni principali -->
        <Button 
          v-if="!trashMode && canWrite('suppliers')"
          :label="t('common.actions.create')" 
          icon="pi pi-plus" 
          severity="success"
          @click="openCreateDialog" 
        />
        <Button 
          v-if="!trashMode && canWrite('suppliers')"
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
      :data="filteredSuppliers"
      :loading="loading"
      :columns="columnOptions"
      :filters="filters"
      :globalFilterFields="['name','description','vat_number','city','country','email','phone']"
      :selectionMode="!trashMode && canWrite('suppliers') ? 'multiple' : null"
      :selection="selectedSuppliers"
      :showExport="false"
      @selection-change="selectedSuppliers = $event"
      @filter-change="updateFilter"
      @refresh="fetchSuppliers"
    >
      <template #filters>
        <Dropdown 
          v-model="filters['country'].value" 
          :options="countryOptions" 
          optionLabel="label" 
          optionValue="value" 
          :placeholder="t('common.fields.country')" 
          showClear 
          style="min-width: 150px" 
        />
        <Dropdown 
          v-model="filters['city'].value" 
          :options="cityOptions" 
          optionLabel="label" 
          optionValue="value" 
          :placeholder="t('common.fields.city')" 
          showClear 
          style="min-width: 150px" 
        />
      </template>

      <template #actions>
        <Button 
          v-if="!trashMode && canWrite('suppliers')"
          :label="t('common.actions.bulkEdit')" 
          icon="pi pi-pencil" 
          severity="warning"
          :disabled="!selectedSuppliers.length" 
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
            v-if="!trashMode && canWrite('suppliers')"
            icon="pi pi-pencil" 
            size="small"
            @click="openEditDialog(data)" 
          />
          <Button 
            v-if="!trashMode && canWrite('suppliers')"
            icon="pi pi-copy" 
            size="small"
            severity="info"
            :loading="duplicating"
            @click="duplicateSupplier(data)" 
          />
          <Button 
            v-if="!trashMode && canDelete('suppliers')"
            icon="pi pi-trash" 
            size="small"
            severity="danger"
            @click="deleteSupplier(data.id)" 
          />
          <Button 
            v-if="trashMode && canWrite('suppliers')"
            icon="pi pi-undo" 
            size="small"
            severity="success"
            @click="restoreSupplier(data.id)" 
          />
          <Button 
            v-if="trashMode && canDelete('suppliers')"
            icon="pi pi-times" 
            size="small"
            severity="danger"
            @click="hardDeleteSupplier(data.id)" 
          />
        </div>
      </template>
    </BaseDataTable>

    <BaseDialog
      v-model:visible="showDialog"
      :title="editingSupplier ? t('common.actions.edit') : t('common.actions.create')"
      :showFooter="false"
      @close="close"
    >
      <SupplierForm 
        :supplier="editingSupplier" 
        @submit="saveSupplier" 
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
            {{ t('common.actions.bulkEditInfo', { count: selectedSuppliers.length }) }}
          </p>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="field">
            <label class="block text-sm font-medium mb-2">{{ t('common.fields.country') }}</label>
            <Dropdown
              v-model="bulkData.country"
              :options="countryOptions"
              option-label="label"
              option-value="value"
              :placeholder="t('common.strings.select')"
              class="w-full"
            />
          </div>
          
          <div class="field">
            <label class="block text-sm font-medium mb-2">{{ t('common.fields.city') }}</label>
            <Dropdown
              v-model="bulkData.city"
              :options="cityOptions"
              option-label="label"
              option-value="value"
              :placeholder="t('common.strings.select')"
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

    <SupplierImportDialog
      :visible="showImportDialog"
      @close="showImportDialog = false"
      @imported="onSupplierImportResult"
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
import SupplierForm from '../components/forms/SupplierForm.vue'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import SupplierImportDialog from '../components/dialogs/SupplierImportDialog.vue'

const { t } = useI18n()
const router = useRouter()
const { canWrite, canDelete } = usePermissions()

// Composables
const { loading, execute } = useApi()
const { filters, globalSearch, selectedColumns, filterData, getApiParams } = useFilters({
  global: { value: null, matchMode: 'contains' },
  country: { value: null, matchMode: 'equals' },
  city: { value: null, matchMode: 'equals' }
}, 'suppliers')

const { isVisible: showDialog, data: editingSupplier, openCreate, openEdit, close } = useDialog()
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
const suppliers = ref([])
const selectedSuppliers = ref([])
const trashMode = ref(false)

// Import/Export
const showImportDialog = ref(false)
const importResult = ref(null)

// Bulk edit
const showBulkDialog = ref(false)
const bulkData = ref({
  country: null,
  city: null
})

const columnOptions = computed(() => {
  const columns = [
    { field: 'name', header: t('common.fields.name'), sortable: true },
    { field: 'description', header: t('common.fields.description'), sortable: false },
    { field: 'vat_number', header: t('suppliers.fields.vatNumber'), sortable: false },
    { field: 'city', header: t('common.fields.city'), sortable: true },
    { field: 'country', header: t('common.fields.country'), sortable: true },
    { field: 'email', header: t('common.fields.email'), sortable: false },
    { field: 'phone', header: t('common.fields.phone'), sortable: false }
  ]
  
  // Aggiungi colonna azioni sempre, perché il pulsante "Visualizza" è sempre disponibile
  columns.push({ field: 'actions', header: t('common.strings.actions'), sortable: false })
  
  return columns
})

const countryOptions = computed(() => {
  const unique = [...new Set(suppliers.value.map(s => s.country).filter(Boolean))]
  return unique.map(c => ({ label: c, value: c }))
})

const cityOptions = computed(() => {
  const unique = [...new Set(suppliers.value.map(s => s.city).filter(Boolean))]
  return unique.map(c => ({ label: c, value: c }))
})

const filteredSuppliers = computed(() => {
  let filtered = suppliers.value
  
  // Filtro per paese
  if (filters.value.country && filters.value.country.value) {
    filtered = filtered.filter(supplier => supplier.country === filters.value.country.value)
  }
  
  // Filtro per città
  if (filters.value.city && filters.value.city.value) {
    filtered = filtered.filter(supplier => supplier.city === filters.value.city.value)
  }
  
  // Filtro globale
  if (filters.value.global && filters.value.global.value) {
    const search = filters.value.global.value.toLowerCase()
    filtered = filtered.filter(supplier =>
      (supplier.name && supplier.name.toLowerCase().includes(search)) ||
      (supplier.description && supplier.description.toLowerCase().includes(search)) ||
      (supplier.vat_number && supplier.vat_number.toLowerCase().includes(search)) ||
      (supplier.city && supplier.city.toLowerCase().includes(search)) ||
      (supplier.country && supplier.country.toLowerCase().includes(search)) ||
      (supplier.email && supplier.email.toLowerCase().includes(search)) ||
      (supplier.phone && supplier.phone.toLowerCase().includes(search))
    )
  }
  
  return filtered
})

onMounted(fetchSuppliers)

async function fetchSuppliers() {
  await execute(async () => {
    const params = getApiParams()
    let response
    if (trashMode.value) {
      response = await api.getSuppliersTrash(params)
    } else {
      response = await api.getSuppliers(params)
    }
    suppliers.value = response.data
    return response
  }, {
    errorContext: t('suppliers.messages.fetchError'),
    showToast: false
  })
}

function openCreateDialog() {
  openCreate(t('common.actions.create'), null)
}

function openEditDialog(supplier) {
  openEdit(t('common.actions.edit'), supplier)
}

function openBulkEditDialog() {
  bulkData.value = {
    country: null,
    city: null
  }
  showBulkDialog.value = true
}

function closeBulkDialog() {
  showBulkDialog.value = false
  selectedSuppliers.value = []
}

async function saveBulkEdit() {
  const updates = {}
  if (bulkData.value.country !== null) updates.country = bulkData.value.country
  if (bulkData.value.city !== null) updates.city = bulkData.value.city
  
  if (Object.keys(updates).length === 0) {
    closeBulkDialog()
    return
  }
  
  await execute(async () => {
    for (const supplier of selectedSuppliers.value) {
      await api.updateSupplier(supplier.id, updates)
    }
    closeBulkDialog()
    await fetchSuppliers()
  }, {
    successMessage: t('common.messages.bulkUpdated'),
    errorContext: t('common.messages.bulkError')
  })
}

async function saveSupplier(data) {
  if (editingSupplier.value) {
    // Modalità modifica
    await execute(async () => {
      await api.updateSupplier(editingSupplier.value.id, data)
      close()
      await fetchSuppliers()
    }, {
      successMessage: t('common.messages.updated'),
      errorContext: t('common.messages.updateError')
    })
  } else {
    // Modalità creazione
    await execute(async () => {
      await api.createSupplier(data)
      close()
      await fetchSuppliers()
    }, {
      successMessage: t('common.messages.created'),
      errorContext: t('common.messages.createError')
    })
  }
}

async function deleteSupplier(id) {
  await confirmDelete(
    t('common.messages.deleteConfirm'),
    t('common.messages.deleteWarning'),
    async () => {
      await execute(async () => {
        await api.deleteSupplier(id)
        await fetchSuppliers()
      }, {
        errorContext: t('common.messages.deleteError')
      })
    },
    {
      successMessage: t('common.messages.deleted')
    }
  )
}

async function duplicateSupplier(supplier) {
  await duplicateItem(
    supplier,
    async (data) => {
      const result = await api.createSupplier(data)
      await fetchSuppliers()
      return result
    },
    'supplier',
    excludeFunctions.supplier
  )
}

function goToDetail(id) {
  router.push({ name: 'SupplierDetail', params: { id } })
}

function toggleTrashMode() {
  trashMode.value = !trashMode.value
  selectedSuppliers.value = []
  fetchSuppliers()
}

async function restoreSupplier(id) {
  await execute(async () => {
    await api.restoreSupplier(id)
    await fetchSuppliers()
  }, {
    successMessage: t('common.messages.restored'),
    errorContext: t('common.messages.restoreError')
  })
}

async function hardDeleteSupplier(id) {
  await execute(async () => {
    await api.hardDeleteSupplier(id)
    await fetchSuppliers()
  }, {
    successMessage: t('common.messages.hardDeleted'),
    errorContext: t('common.messages.hardDeleteError')
  })
}

async function emptyTrash() {
  await execute(async () => {
    for (const s of suppliers.value) {
      await api.hardDeleteSupplier(s.id)
    }
    await fetchSuppliers()
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
    const response = await api.exportSuppliersCsv();
    const blob = new Blob([response.data], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'suppliers.csv');
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  } catch (e) {
    // Mostra errore
    alert(t('common.messages.exportError'));
  }
}

function onSupplierImportResult(result) {
  importResult.value = result
  showImportDialog.value = false
  fetchSuppliers()
}

function updateFilter(newFilters) {
  Object.assign(filters.value, newFilters)
}


</script>

<style scoped>
.suppliers-page {
  padding: 1rem;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}
</style>
