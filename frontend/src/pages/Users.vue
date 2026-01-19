<!--
  - Users.vue
  - Componente per la gestione degli utenti
  - Utilizza i componenti standardizzati e composables
-->
<template>
  <div class="users-page">
    <div class="page-header">
      <h1>{{ t('users.title') }}</h1>
      <div class="flex gap-2">
        <!-- Azioni principali -->
        <Button 
          v-if="!trashMode && canWrite('users')"
          :label="t('common.actions.create')" 
          icon="pi pi-plus" 
          severity="success"
          @click="openCreateDialog" 
        />
        <!-- RIMOSSO: Bottone Import -->
        <!-- RIMOSSO: Bottone Export CSV -->
        <!-- Separatore visivo -->
        <div v-if="canWrite('users')" class="w-px h-8 bg-gray-300 mx-2"></div>
        <!-- Gestione cestino -->
        <Button 
          v-if="canDelete('users')"
          icon="pi pi-trash" 
          :label="trashMode ? t('common.actions.showActive') : t('common.actions.showTrash')" 
          severity="secondary"
          @click="toggleTrashMode"
        />
      </div>
    </div>

    <BaseDataTable
      :data="filteredUsers"
      :loading="loading"
      :columns="columnOptions"
      :filters="filters"
      :globalFilterFields="['name','email','role_name']"
      :selectionMode="!trashMode && canWrite('users') ? 'multiple' : null"
      :selection="selectedUsers"
      :showExport="false"
      :autoHeight="true"
      :heightOffsetTop="150"
      :heightOffsetBottom="100"
      @selection-change="selectedUsers = $event"
      @filter-change="updateFilter"
      @refresh="fetchUsers"
    >
      <template #filters>
        <Dropdown 
          v-model="filters['role_id'].value" 
          :options="roleOptions" 
          optionLabel="label" 
          optionValue="value" 
          :placeholder="t('users.fields.role')" 
          showClear 
          style="min-width: 150px" 
        />
        <Dropdown 
          v-model="filters['is_active'].value" 
          :options="statusOptions" 
          optionLabel="label" 
          optionValue="value" 
          :placeholder="t('users.fields.status')" 
          showClear 
          style="min-width: 150px" 
        />
      </template>

      <template #actions>
        <!-- RIMOSSO: Bottone Bulk Edit -->
      </template>


      
      <template #body-is_active="{ data }">
        <Tag :value="data.is_active ? t('users.strings.active') : t('users.strings.inactive')" :severity="data.is_active ? 'success' : 'danger'" />
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
            v-if="!trashMode && canWrite('users')"
            icon="pi pi-pencil" 
            size="small"
            @click="openEditDialog(data)" 
          />
          <!-- RIMOSSO: Bottone Duplicazione -->
          <Button 
            v-if="!trashMode && canDelete('users')"
            icon="pi pi-trash" 
            size="small"
            severity="danger"
            @click="deleteUser(data.id)" 
          />
          <Button 
            v-if="trashMode && canWrite('users')"
            icon="pi pi-undo" 
            size="small"
            severity="success"
            @click="restoreUser(data.id)" 
          />
          <Button 
            v-if="trashMode && canDelete('users')"
            icon="pi pi-times" 
            size="small"
            severity="danger"
            @click="hardDeleteUser(data.id)" 
          />
        </div>
      </template>
    </BaseDataTable>

    <BaseDialog
      v-model:visible="showDialog"
      :title="dialogTitle"
      :showFooter="false"
      @close="close"
    >
      <UserForm 
        :user="editingUser" 
        :roles="roles" 
        :canResetPassword="canResetUserPassword"
        @submit="saveUser" 
        @cancel="close" 
        @reset-password="handleResetPassword"
      />
    </BaseDialog>

    <BaseDialog
      v-model:visible="showBulkDialog"
      :title="t('common.actions.bulkEdit')"
      @close="closeBulkDialog"
    >
      <!-- RIMOSSO: Form Bulk Edit Utenti -->
    </BaseDialog>

    <!-- TODO: Implementare UserImportDialog -->
    <BaseDialog
      v-model:visible="showImportDialog"
      :title="t('common.actions.import')"
      @close="showImportDialog = false"
    >
      <div class="p-4">
        <p>{{ t('common.messages.importNotImplemented') }}</p>
      </div>
    </BaseDialog>
    
    <BaseConfirmDialog
      v-model:showConfirmDialog="showConfirmDialog"
      :confirmData="confirmData"
      @execute="executeConfirmedAction"
      @close="closeConfirmDialog"
    />
    
    <PasswordResetDialog
      v-model:isVisible="showPasswordResetDialog"
      :temporaryPassword="tempPassword"
      :userEmail="tempUserEmail"
      @ok="handlePasswordResetOk"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useApi } from '../composables/useApi'
import { useFilters } from '../composables/useFilters'
import { useDialog } from '../composables/useDialog'
import { useConfirm } from '../composables/useConfirm'
import { useDuplicate } from '../composables/useDuplicate'
import { usePermissions } from '../composables/usePermissions'
import api from '../api/api'

import BaseDataTable from '../components/base/BaseDataTable.vue'
import BaseDialog from '../components/base/BaseDialog.vue'
import BaseConfirmDialog from '../components/base/BaseConfirmDialog.vue'
import UserForm from '../components/forms/UserForm.vue'
import PasswordResetDialog from '../components/dialogs/PasswordResetDialog.vue'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import Tag from 'primevue/tag'

const { t } = useI18n()
const router = useRouter()

// Composables
const { loading, execute } = useApi()
const { canWrite, canDelete, hasPermission } = usePermissions()
const { filters, globalSearch, selectedColumns, filterData, getApiParams } = useFilters({
  global: { value: null, matchMode: 'contains' },
  role_id: { value: null, matchMode: 'equals' },
  is_active: { value: null, matchMode: 'equals' }
}, 'users')

const { isVisible: showDialog, data: editingUser, title: dialogTitle, openCreate, openEdit, close } = useDialog()
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
const users = ref([])
const roles = ref([])
const selectedUsers = ref([])
const trashMode = ref(false)

// Password reset dialog
const showPasswordResetDialog = ref(false)
const tempPassword = ref('')
const tempUserEmail = ref('')

// Import/Export
const showImportDialog = ref(false)

// Bulk edit
const showBulkDialog = ref(false)
const bulkData = ref({
  role_id: null,
  is_active: null
})

const columnOptions = [
  { field: 'name', header: t('common.fields.name'), sortable: true },
  { field: 'email', header: t('common.fields.email'), sortable: true },
  { field: 'role_name', header: t('users.fields.role'), sortable: false },
  { field: 'is_active', header: t('common.fields.status'), sortable: false, style: 'width: 110px' },
  { field: 'actions', header: t('common.strings.actions'), sortable: false }
]

const roleOptions = computed(() => {
  return roles.value.map(role => ({ label: role.name, value: role.id }))
})

const statusOptions = [
  { label: t('users.strings.active'), value: true },
  { label: t('users.strings.inactive'), value: false }
]

// Computed properties
const canResetUserPassword = computed(() => {
  return hasPermission('reset_user_password', 1)
})

const filteredUsers = computed(() => {
  let filtered = users.value
  
  // Aggiungi il campo role_name per la visualizzazione
  filtered = filtered.map(user => ({
    ...user,
    role_name: user.role && user.role.name ? user.role.name : '-'
  }))
  
  // Filtro per ruolo
  if (filters.value.role_id && filters.value.role_id.value) {
    filtered = filtered.filter(user => user.role_id === filters.value.role_id.value)
  }
  
  // Filtro per stato
  if (filters.value.is_active && filters.value.is_active.value !== null) {
    filtered = filtered.filter(user => user.is_active === filters.value.is_active.value)
  }
  
  // Filtro globale
  if (filters.value.global && filters.value.global.value) {
    const search = filters.value.global.value.toLowerCase()
    filtered = filtered.filter(user =>
      (user.name && user.name.toLowerCase().includes(search)) ||
      (user.email && user.email.toLowerCase().includes(search)) ||
      (user.role && user.role.name && user.role.name.toLowerCase().includes(search))
    )
  }
  
  return filtered
})

onMounted(async () => {
  await fetchRoles()
  await fetchUsers()
})

async function fetchUsers() {
  await execute(async () => {
    const params = getApiParams()
    let response
    if (trashMode.value) {
      response = await api.getUsersTrash(params)
    } else {
      response = await api.getUsers(params)
    }
    users.value = response.data
    return response
  }, {
    errorContext: t('users.messages.fetchError'),
    showToast: false
  })
}

async function fetchRoles() {
  await execute(async () => {
    const response = await api.getRoles()
    roles.value = response.data
    return response
  }, {
    errorContext: t('users.messages.fetchRolesError'),
    showToast: false
  })
}

function openCreateDialog() {
  openCreate(t('common.actions.create'), null)
}

function openEditDialog(user) {
  openEdit(t('common.actions.edit'), user)
}

function openBulkEditDialog() {
  bulkData.value = {
    role_id: null,
    is_active: null
  }
  showBulkDialog.value = true
}

function closeBulkDialog() {
  showBulkDialog.value = false
  selectedUsers.value = []
}

async function saveBulkEdit() {
  const updates = {}
  if (bulkData.value.role_id !== null) updates.role_id = bulkData.value.role_id
  if (bulkData.value.is_active !== null) updates.is_active = bulkData.value.is_active
  
  if (Object.keys(updates).length === 0) {
    closeBulkDialog()
    return
  }
  
  await execute(async () => {
    for (const user of selectedUsers.value) {
      await api.updateUser(user.id, updates)
    }
    closeBulkDialog()
    await fetchUsers()
  }, {
    successMessage: t('common.messages.bulkUpdated'),
    errorContext: t('common.messages.bulkError')
  })
}

async function saveUser(data) {
  if (editingUser.value) {
    // Modalità modifica
    await execute(async () => {
      await api.updateUser(editingUser.value.id, data)
      close()
      await fetchUsers()
    }, {
      successMessage: t('common.messages.updated'),
      errorContext: t('common.messages.updateError')
    })
  } else {
    // Modalità creazione
    await execute(async () => {
      await api.createUser(data)
      close()
      await fetchUsers()
    }, {
      successMessage: t('common.messages.created'),
      errorContext: t('common.messages.createError')
    })
  }
}

async function deleteUser(id) {
  await confirmDelete(
    t('common.messages.deleteConfirm'),
    t('common.messages.deleteWarning'),
    async () => {
      await execute(async () => {
        await api.deleteUser(id)
        await fetchUsers()
      }, {
        successMessage: t('common.messages.deleted'),
        errorContext: t('common.messages.deleteError')
      })
    }
  )
}

async function duplicateUser(user) {
  await duplicateItem(
    user,
    async (data) => {
      const result = await api.createUser(data)
      await fetchUsers()
      return result
    },
    'user',
    excludeFunctions.user
  )
}

async function handleResetPassword(user) {
  await execute(async () => {
    const response = await api.resetUserPassword(user.id)
    
    // Chiudi prima il dialog di modifica
    close()
    
    // Imposta i dati per il dialog di reset password
    // I dati sono dentro response.data
    tempPassword.value = response.data.temporary_password
    tempUserEmail.value = response.data.user_email
    
    // Mostra dialog con password temporanea dopo che il DOM è stato aggiornato
    await nextTick()
    showPasswordResetDialog.value = true
  }, {
    successMessage: t('users.messages.resetPasswordSuccess'),
    errorContext: t('users.messages.resetPasswordError')
  })
}

function handlePasswordResetOk() {
  // Il dialog è già chiuso automaticamente
  // Qui possiamo aggiungere logica aggiuntiva se necessario
}

async function updateUserRole(user) {
  await execute(async () => {
    await api.updateUserRole(user.id, user.role_id)
    await fetchUsers()
  }, {
    successMessage: t('common.messages.updated'),
    errorContext: t('common.messages.updateError')
  })
}

function goToDetail(id) {
  router.push({ name: 'UserDetail', params: { id } })
}

function toggleTrashMode() {
  trashMode.value = !trashMode.value
  selectedUsers.value = []
  fetchUsers()
}

async function restoreUser(id) {
  await execute(async () => {
    await api.restoreUser(id)
    await fetchUsers()
  }, {
    successMessage: t('common.messages.restored'),
    errorContext: t('common.messages.restoreError')
  })
}

async function hardDeleteUser(id) {
  await execute(async () => {
    await api.hardDeleteUser(id)
    await fetchUsers()
  }, {
    successMessage: t('common.messages.hardDeleted'),
    errorContext: t('common.messages.hardDeleteError')
  })
}

async function emptyTrash() {
  await execute(async () => {
    for (const u of users.value) {
      await api.hardDeleteUser(u.id)
    }
    await fetchUsers()
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
function exportCsv() {
  // TODO: Implementare export CSV per utenti
}

// Import
function onUserImport() {
  showImportDialog.value = false
  fetchUsers()
}

function updateFilter(filterName, value) {
  if (filters.value[filterName]) {
    filters.value[filterName].value = value
  }
}
</script>

<style scoped>
.users-page {
  padding: 1rem;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}
</style>

