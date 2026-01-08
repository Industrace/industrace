<template>
  <div class="contacts-page">
    <div class="page-header">
      <h1>{{ t('contacts.title') }}</h1>
      <div class="flex gap-2">
        <!-- Azioni principali -->
        <Button 
          v-if="!trashMode && canWrite('contacts')"
          :label="t('common.actions.create')" 
          icon="pi pi-plus" 
          severity="success"
          @click="openCreateDialog" 
        />
        <Button 
          v-if="!trashMode && canWrite('contacts')"
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
      :data="[...filteredContacts]"
      :loading="loading"
      :columns="columnOptions"
      :filters="filters"
      :global-search="globalSearch"
      :selected-columns="selectedColumns"
      :selectionMode="!trashMode && canWrite('contacts') ? 'multiple' : null"
      :selection="selectedContacts"
      :showExport="false"
      @selection-change="selectedContacts = $event"
      @filter-change="updateFilter"
      @refresh="fetchContacts"
    >
      <template #actions>
        <Button 
          v-if="!trashMode && canWrite('contacts')"
          :label="t('common.actions.bulkEdit')" 
          icon="pi pi-pencil" 
          severity="warning"
          :disabled="!selectedContacts.length" 
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
            v-if="!trashMode && canWrite('contacts')"
            icon="pi pi-pencil" 
            size="small"
            @click="openEditDialog(data)" 
          />
          <Button 
            v-if="!trashMode && canWrite('contacts')"
            icon="pi pi-copy" 
            size="small"
            severity="info"
            :loading="duplicating"
            @click="duplicateContact(data)" 
          />
          <Button 
            v-if="!trashMode && canDelete('contacts')"
            icon="pi pi-trash" 
            size="small"
            severity="danger"
            @click="deleteContact(data.id)" 
          />
          <Button 
            v-if="trashMode && canWrite('contacts')"
            icon="pi pi-undo" 
            size="small"
            severity="success"
            @click="restoreContact(data.id)" 
          />
          <Button 
            v-if="trashMode && canDelete('contacts')"
            icon="pi pi-times" 
            size="small"
            severity="danger"
            @click="hardDeleteContact(data.id)" 
          />
        </div>
      </template>
    </BaseDataTable>
    
    <BaseDialog
      v-model:visible="showDialog"
      :title="editingContact ? t('common.actions.edit') : t('common.actions.create')"
      :showFooter="false"
      @close="close"
    >
      <ContactForm 
        :contact="editingContact" 
        @submit="saveContact" 
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
            {{ t('common.actions.bulkEditInfo', { count: selectedContacts.length }) }}
          </p>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="field">
            <label class="block text-sm font-medium mb-2">{{ t('common.fields.type') }}</label>
            <Dropdown
              v-model="bulkData.type"
              :options="typeOptions"
              option-label="label"
              option-value="value"
              :placeholder="t('common.strings.select')"
              class="w-full"
            />
          </div>
          
          <div class="field">
            <label class="block text-sm font-medium mb-2">{{ t('common.fields.notes') }}</label>
            <InputText
              v-model="bulkData.notes"
              :placeholder="t('contacts.strings.notes_placeholder')"
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
    
    <div v-if="trashMode && canDelete('contacts')" class="mt-4 flex justify-content-end">
      <Button 
        icon="pi pi-times" 
        :label="t('common.actions.emptyTrash')" 
        severity="danger"
        @click="handleEmptyTrash"
      />
    </div>
    
    <BaseConfirmDialog
      v-model:showConfirmDialog="showConfirmDialog"
      :confirmData="confirmData"
      @execute="executeConfirmedAction"
      @close="closeConfirmDialog"
    />
    
    <!-- Sostituisco il BaseDialog placeholder con il nuovo dialog -->
    <ContactImportDialog
      :visible="showImportDialog"
      @close="showImportDialog = false"
      @imported="onContactImportResult"
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
import ContactForm from '../components/forms/ContactForm.vue'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import ContactImportDialog from '../components/dialogs/ContactImportDialog.vue'

const { t } = useI18n()
const router = useRouter()
const { canWrite, canDelete } = usePermissions()

// Composables
const { loading, execute } = useApi()
const { filters, globalSearch, selectedColumns, filterData, getApiParams } = useFilters({
  global: { value: null, matchMode: 'contains' },
  type: { value: null, matchMode: 'equals' }
}, 'contacts')

const { isVisible: showDialog, data: editingContact, openCreate, openEdit, close } = useDialog()
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
const contacts = ref([])
const selectedContacts = ref([])
const trashMode = ref(false)

// Import/Export
const showImportDialog = ref(false)
const importResult = ref(null)

// Bulk edit
const showBulkDialog = ref(false)
const bulkData = ref({
  type: null,
  notes: ''
})

const columnOptions = computed(() => {
  const columns = [
    { field: 'fullName', header: t('contacts.fields.fullName'), sortable: true },
    { field: 'email', header: t('common.fields.email'), sortable: true },
    { field: 'phone1', header: t('contacts.fields.phone1'), sortable: false },
    { field: 'phone2', header: t('contacts.fields.phone2'), sortable: false },
    { field: 'type', header: t('contacts.fields.type'), sortable: true },
    { field: 'notes', header: t('contacts.fields.notes'), sortable: false }
  ]
  
  // Aggiungi colonna azioni sempre, perché il pulsante "Visualizza" è sempre disponibile
  columns.push({ field: 'actions', header: t('common.strings.actions'), sortable: false })
  
  return columns
})

const typeOptions = [
  { label: t('contacts.fields.internal'), value: 'interno' },
  { label: t('contacts.fields.supplier'), value: 'fornitore' },
  { label: t('contacts.fields.other'), value: 'altro' }
]

const filteredContacts = computed(() => {
  let filtered = contacts.value
  
  // Filtro per tipo
  if (filters.value.type && filters.value.type.value) {
    filtered = filtered.filter(contact => contact.type === filters.value.type.value)
  }
  
  // Filtro globale
  if (filters.value.global && filters.value.global.value) {
    const search = filters.value.global.value.toLowerCase()
    filtered = filtered.filter(contact =>
      (contact.fullName && contact.fullName.toLowerCase().includes(search)) ||
      (contact.email && contact.email.toLowerCase().includes(search)) ||
      (contact.phone1 && contact.phone1.toLowerCase().includes(search)) ||
      (contact.phone2 && contact.phone2.toLowerCase().includes(search)) ||
      (contact.type && contact.type.toLowerCase().includes(search)) ||
      (contact.notes && contact.notes.toLowerCase().includes(search))
    )
  }
  
  return filtered
})



function mapContact(contact) {
  return { ...contact, fullName: `${contact.first_name} ${contact.last_name}` }
}

onMounted(fetchContacts)

async function fetchContacts() {
  await execute(async () => {
    const params = getApiParams()
    let response
    if (trashMode.value) {
      response = await api.getContactsTrash(params)
    } else {
      response = await api.getContacts(params)
    }
    contacts.value = response.data.map(mapContact)
    return response
  }, {
    errorContext: t('contacts.messages.fetchError'),
    showToast: false
  })
}

function openCreateDialog() {
  openCreate(t('common.actions.create'), null)
}

function openEditDialog(contact) {
  openEdit(t('common.actions.edit'), contact)
}

function openBulkEditDialog() {
  bulkData.value = {
    type: null,
    notes: ''
  }
  showBulkDialog.value = true
}

function closeBulkDialog() {
  showBulkDialog.value = false
  selectedContacts.value = []
}

async function saveBulkEdit() {
  const updates = {}
  if (bulkData.value.type !== null) updates.type = bulkData.value.type
  if (bulkData.value.notes !== '') updates.notes = bulkData.value.notes
  
  if (Object.keys(updates).length === 0) {
    closeBulkDialog()
    return
  }
  
  await execute(async () => {
    for (const contact of selectedContacts.value) {
      await api.updateContact(contact.id, updates)
    }
    closeBulkDialog()
    await fetchContacts()
  }, {
    successMessage: t('common.messages.bulkupdated'),
    errorContext: t('contacts.messages.bulkUpdateError')
  })
}

async function saveContact(data) {
  if (editingContact.value) {
    // Modalità modifica
    await execute(async () => {
      await api.updateContact(editingContact.value.id, data)
      close()
      await fetchContacts()
    }, {
      successMessage: t('common.messages.updated'),
      errorContext: t('contacts.messages.updateError')
    })
  } else {
    // Modalità creazione
    await execute(async () => {
      await api.createContact(data)
      close()
      await fetchContacts()
    }, {
      successMessage: t('common.messages.created'),
      errorContext: t('contacts.messages.createError')
    })
  }
}

async function deleteContact(id) {
  await confirmDelete(
    t('common.messages.deleteConfirm'),
    t('common.messages.deleteWarning'),
    async () => {
      await execute(async () => {
        await api.deleteContact(id)
        await fetchContacts()
      }, {
        successMessage: t('common.messages.deleted'),
        errorContext: t('contacts.messages.deleteError')
      })
    }
  )
}

async function duplicateContact(contact) {
  await duplicateItem(
    contact,
    async (data) => {
      const result = await api.createContact(data)
      await fetchContacts()
      return result
    },
    'contact',
    excludeFunctions.contact
  )
}

function goToDetail(id) {
  router.push({ name: 'ContactDetail', params: { id } })
}

function toggleTrashMode() {
  trashMode.value = !trashMode.value
  selectedContacts.value = []
  fetchContacts()
}

async function restoreContact(id) {
  await execute(async () => {
    await api.restoreContact(id)
    await fetchContacts()
  }, {
    successMessage: t('common.messages.restored'),
    errorContext: t('contacts.messages.restoreError')
  })
}

async function hardDeleteContact(id) {
  await execute(async () => {
    await api.hardDeleteContact(id)
    await fetchContacts()
  }, {
    successMessage: t('common.messages.hardDeleted'),
    errorContext: t('contacts.messages.hardDeleteError')
  })
}

async function emptyTrash() {
  await execute(async () => {
    for (const c of contacts.value) {
      await api.hardDeleteContact(c.id)
    }
    await fetchContacts()
  }, {
    successMessage: t('common.messages.trashEmptied'),
    errorContext: t('contacts.messages.emptyTrashError')
  })
}

async function handleEmptyTrash() {
  await confirmEmptyTrash(
    t('common.messages.emptyTrashConfirm'),
    t('common.messages.emptyTrashWarning'),
    emptyTrash
  )
}

function updateFilter(newFilters) {
  Object.assign(filters, newFilters)
}

// Export CSV
async function exportCsv() {
  try {
    const response = await api.exportContactsCsv();
    const blob = new Blob([response.data], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'contacts.csv');
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  } catch (e) {
    alert('Errore durante l\'esportazione CSV');
  }
}

function onContactImportResult(result) {
  importResult.value = result
  showImportDialog.value = false
  fetchContacts()
}
</script>

<style scoped>
.contacts-page {
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
.bulk-edit-form {
  min-width: 400px;
}
</style> 