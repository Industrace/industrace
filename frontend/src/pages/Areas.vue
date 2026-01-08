<template>
  <div class="areas-page">
    <div class="page-header">
        <h1>{{ t('areas.title') }}</h1> 
      <div class="flex gap-2">
        <!-- Azioni principali -->
        <Button 
          v-if="!trashMode && canWrite('areas')"
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
        :data="areas"
        :loading="loading"
        :columns="columns"
        :filters="filters"
      :globalFilterFields="['name','code','typology','site_name']"
      :selectionMode="!trashMode && canWrite('areas') ? 'multiple' : null"
      :selection="selectedAreas"
      :showExport="false"
      @selection-change="selectedAreas = $event"
        @filter-change="updateFilter"
      @refresh="loadAreas"
    >
      <template #filters>
        <Dropdown 
          v-if="!trashMode"
          v-model="filters['site_id'].value" 
          :options="siteOptions" 
          optionLabel="name" 
          optionValue="id" 
          :placeholder="t('common.fields.site')" 
          showClear 
          style="min-width: 150px" 
          @change="loadAreas"
        />
      </template>
      
        <template #body-actions="{ data }">
        <div class="flex gap-2">
            <Button
            v-if="!trashMode && canWrite('areas')"
              icon="pi pi-pencil"
            size="small"
              @click="editArea(data)"
            />
            <Button
            v-if="!trashMode && canDelete('areas')"
              icon="pi pi-trash"
            size="small"
            severity="danger"
            @click="deleteArea(data.id)" 
          />
          <Button 
            v-if="trashMode && canWrite('areas')"
            icon="pi pi-undo" 
            size="small"
            severity="success"
            @click="restoreArea(data.id)" 
          />
          <Button 
            v-if="trashMode && canDelete('areas')"
            icon="pi pi-times" 
            size="small"
            severity="danger"
            @click="hardDeleteArea(data.id)" 
            />
          </div>
        </template>
      </BaseDataTable>

    <BaseDialog
      v-model:visible="dialogVisible"
      :title="editingArea ? t('common.actions.edit') : t('common.actions.create')"
      :showFooter="false"
      @close="closeDialog"
    >
      <AreaForm
        :area="editingArea"
        :sites="sites"
        @submit="handleFormSubmit"
        @cancel="closeDialog"
      />
    </BaseDialog>

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
import { useI18n } from 'vue-i18n'
import { usePermissions } from '@/composables/usePermissions'
import { useApi } from '@/composables/useApi'
import { useFilters } from '@/composables/useFilters'
import { useDialog } from '@/composables/useDialog'
import { useConfirm } from '@/composables/useConfirm'
import api from '@/api/api'

import BaseDataTable from '@/components/base/BaseDataTable.vue'
import BaseDialog from '@/components/base/BaseDialog.vue'
import BaseConfirmDialog from '@/components/base/BaseConfirmDialog.vue'
import AreaForm from '@/components/forms/AreaForm.vue'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'

const { t } = useI18n()
const { canWrite, canDelete } = usePermissions()

// Composables
const { loading, execute } = useApi()
const { filters, globalSearch, selectedColumns, filterData, getApiParams } = useFilters({
  global: { value: null, matchMode: 'contains' },
  site_id: { value: null, matchMode: 'equals' }
}, 'areas')

const { isVisible: dialogVisible, data: editingArea, openCreate, openEdit, close: closeDialog } = useDialog()
const { 
  showConfirmDialog, 
  confirmData, 
  confirmDelete, 
  executeConfirmedAction,
  closeConfirmDialog 
} = useConfirm()

// Data
const areas = ref([])
const sites = ref([])
const selectedAreas = ref([])
const trashMode = ref(false)

const columns = computed(() => {
  const cols = [
    { field: 'name', header: t('common.fields.name'), sortable: true },
    { field: 'code', header: t('common.fields.code'), sortable: true },
    { field: 'typology', header: t('areas.fields.typology'), sortable: true },
    { field: 'site_name', header: t('common.fields.site'), sortable: true },
    { field: 'created_at', header: t('common.fields.createdAt'), sortable: true }
  ]
  
  // Aggiungi colonna azioni solo se l'utente ha permessi
  if (canWrite('areas') || canDelete('areas')) {
    cols.push({ field: 'actions', header: t('common.strings.actions'), sortable: false })
  }
  
  return cols
})

const siteOptions = computed(() => {
  return sites.value.map(site => ({
    id: site.id,
    name: site.name
  }))
})

onMounted(async () => {
  await Promise.all([loadSites(), loadAreas()])
})

async function loadSites() {
  await execute(async () => {
    const response = await api.getSites()
    sites.value = response.data
    return response
  }, {
    errorContext: t('areas.messages.fetchError'),
    showToast: false
  })
}

async function loadAreas() {
  await execute(async () => {
  const params = getApiParams()
    let response
    if (trashMode.value) {
      response = await api.getAreasTrash(params)
    } else {
  if (filters.value.site_id && filters.value.site_id.value) {
    params.site_id = filters.value.site_id.value
  }
      response = await api.getAreas(params)
    }
    areas.value = response.data
    return response
  }, {
    errorContext: t('areas.messages.fetchError'),
    showToast: false
  })
}

function openCreateDialog() {
  openCreate(t('common.actions.create'), null)
}

function editArea(area) {
  openEdit(t('common.actions.edit'), area)
}

async function handleFormSubmit(formData) {
    if (editingArea.value) {
      // Update
    await execute(async () => {
      await api.updateArea(editingArea.value.id, formData)
      closeDialog()
      await loadAreas()
    }, {
      successMessage: t('areas.messages.updated'),
      errorContext: t('areas.messages.updateError')
    })
    } else {
      // Create
    await execute(async () => {
      await api.createArea(formData)
      closeDialog()
        await loadAreas()
    }, {
      successMessage: t('areas.messages.created'),
      errorContext: t('areas.messages.createError')
    })
  }
}

async function deleteArea(id) {
  await confirmDelete(
    t('common.messages.deleteConfirm'),
    t('common.messages.deleteConfirm'),
    async () => {
      await execute(async () => {
        await api.deleteArea(id)
        await loadAreas()
      }, {
        successMessage: t('areas.messages.deleted'),
        errorContext: t('areas.messages.deleteError')
      })
    }
  )
}

function toggleTrashMode() {
  trashMode.value = !trashMode.value
  selectedAreas.value = []
  areas.value = []
  loadAreas()
}

async function restoreArea(id) {
  await execute(async () => {
    await api.restoreArea(id)
    await loadAreas()
  }, {
    successMessage: t('areas.messages.restored'),
    errorContext: t('areas.messages.restoreError')
  })
}

async function hardDeleteArea(id) {
  await execute(async () => {
    await api.hardDeleteArea(id)
    await loadAreas()
  }, {
    successMessage: t('areas.messages.hardDeleted'),
    errorContext: t('areas.messages.hardDeleteError')
  })
}

function updateFilter(newFilters) {
  Object.assign(filters.value, newFilters)
  loadAreas()
}
</script>

<style scoped>
.areas-page {
  padding: 1rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}
</style> 