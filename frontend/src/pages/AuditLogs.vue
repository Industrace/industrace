<!--
  - AuditLogs.vue
  - Componente per la gestione dei log di audit
  - Sistema di change management e timeline
-->
<template>
  <div class="audit-logs-page">
    <div class="page-header">
      <h1>{{ t('auditlog.title') }}</h1>
      <div class="flex gap-2">
        <Button 
          :label="t('common.actions.export')" 
          icon="pi pi-file-excel" 
          severity="secondary"
          @click="exportAuditLogs" 
        />
        <Button 
          :label="t('auditlog.strings.timeline')" 
          icon="pi pi-clock" 
          severity="info"
          @click="showTimelineView = !showTimelineView" 
        />
      </div>
    </div>

    <!-- Filtri Avanzati -->
    <div class="filters-section mb-4">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="field">
          <label class="block text-sm font-medium mb-2">{{ t('auditlog.strings.dateRange') }}</label>
          <Calendar 
            v-model="filters.dateRange" 
            selectionMode="range" 
            :placeholder="t('auditlog.strings.selectDateRange')"
            dateFormat="dd/mm/yy"
            showIcon
            class="w-full"
          />
        </div>
        
        <div class="field">
          <label class="block text-sm font-medium mb-2">{{ t('auditlog.strings.action') }}</label>
          <Dropdown 
            v-model="filters.action" 
            :options="actionOptions" 
            optionLabel="label" 
            optionValue="value" 
            :placeholder="t('auditlog.strings.selectAction')"
            showClear
            class="w-full"
          />
        </div>
        
        <div class="field">
          <label class="block text-sm font-medium mb-2">{{ t('auditlog.strings.entity') }}</label>
          <Dropdown 
            v-model="filters.entity" 
            :options="entityOptions" 
            optionLabel="label" 
            optionValue="value" 
            :placeholder="t('auditlog.strings.selectEntity')"
            showClear
            class="w-full"
          />
        </div>
        
        <div class="field">
          <label class="block text-sm font-medium mb-2">{{ t('auditlog.strings.user') }}</label>
          <Dropdown 
            v-model="filters.user_id" 
            :options="userOptions" 
            optionLabel="label" 
            optionValue="value" 
            :placeholder="t('auditlog.strings.selectUser')"
            showClear
            class="w-full"
          />
        </div>
      </div>
      
      <div class="flex gap-2 mt-4">
        <Button 
          :label="t('common.actions.search')" 
          icon="pi pi-search" 
          @click="fetchAuditLogs" 
        />
        <Button 
          :label="t('common.actions.clear')" 
          icon="pi pi-times" 
          severity="secondary"
          @click="clearFilters" 
        />
      </div>
    </div>

    <!-- Vista Timeline -->
    <div v-if="showTimelineView" class="timeline-view mb-6">
      <h3 class="text-lg font-semibold mb-4">{{ t('auditlog.strings.timelineView') }}</h3>
      <div class="timeline-container">
        <div v-for="log in auditLogs" :key="log.id" class="timeline-item">
          <div class="timeline-marker" :class="getActionClass(log.action)">
            <i :class="getActionIcon(log.action)"></i>
          </div>
          <div class="timeline-content">
            <div class="timeline-header">
              <span class="timeline-time">{{ formatTimestamp(log.timestamp) }}</span>
              <span class="timeline-user">{{ getUserName(log.user_id) }}</span>
              <Tag :value="log.action" :severity="getActionSeverity(log.action)" />
            </div>
            <div class="timeline-body">
              <p class="timeline-description">{{ getFormattedDescription(log) }}</p>
              <div v-if="log.entity_id" class="timeline-entity">
                <Button 
                  :label="t('auditlog.strings.viewEntity')" 
                  icon="pi pi-external-link" 
                  size="small"
                  severity="secondary"
                  @click="viewEntity(log.entity, log.entity_id)"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Vista Tabella -->
    <div v-else>
      <BaseDataTable
        :data="auditLogs"
        :loading="loading"
        :columns="columnOptions"
        :filters="tableFilters"
        :globalFilterFields="['description','entity','action','user_name']"
        :showExport="false"
        @filter-change="updateFilter"
        @refresh="fetchAuditLogs"
      >
        <template #body-timestamp="{ data }">
          <span class="text-sm text-gray-600">{{ formatTimestamp(data.timestamp) }}</span>
        </template>
        
        <template #body-user_name="{ data }">
          <div class="flex items-center gap-2">
            <Avatar :label="getUserInitials(data.user_id)" size="small" />
            <span>{{ getUserName(data.user_id) }}</span>
          </div>
        </template>
        
        <template #body-action="{ data }">
          <Tag :value="data.action" :severity="getActionSeverity(data.action)" />
        </template>
        
        <template #body-entity="{ data }">
          <div class="flex items-center gap-2">
            <i :class="getEntityIcon(data.entity)" class="text-gray-500"></i>
            <span>{{ getEntityLabel(data.entity) }}</span>
          </div>
        </template>
        
        <template #body-description="{ data }">
          <span class="text-sm">{{ getFormattedDescription(data) }}</span>
        </template>
        
        <template #body-actions="{ data }">
          <div class="flex gap-2">
            <Button 
              icon="pi pi-eye" 
              size="small"
              severity="secondary"
              @click="showDetails(data)" 
            />
            <Button 
              v-if="data.entity_id"
              icon="pi pi-external-link" 
              size="small"
              severity="info"
              @click="viewEntity(data.entity, data.entity_id)"
            />
          </div>
        </template>
      </BaseDataTable>
    </div>

    <!-- Dialog Dettagli -->
    <BaseDialog
      v-model:visible="showDialog"
      :title="t('auditlog.strings.details')"
      :showFooter="false"
      @close="closeDialog"
    >
      <div v-if="selectedLog" class="audit-details">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div class="detail-item">
            <label class="text-sm font-medium text-gray-600">{{ t('auditlog.strings.timestamp') }}</label>
            <p>{{ formatTimestamp(selectedLog.timestamp) }}</p>
          </div>
          <div class="detail-item">
            <label class="text-sm font-medium text-gray-600">{{ t('auditlog.strings.user') }}</label>
            <p>{{ getUserName(selectedLog.user_id) }}</p>
          </div>
          <div class="detail-item">
            <label class="text-sm font-medium text-gray-600">{{ t('auditlog.strings.action') }}</label>
            <Tag :value="selectedLog.action" :severity="getActionSeverity(selectedLog.action)" />
          </div>
          <div class="detail-item">
            <label class="text-sm font-medium text-gray-600">{{ t('auditlog.strings.entity') }}</label>
            <p>{{ getEntityLabel(selectedLog.entity) }}</p>
          </div>
          <div class="detail-item">
            <label class="text-sm font-medium text-gray-600">{{ t('auditlog.strings.ip') }}</label>
            <p>{{ selectedLog.ip_address || '-' }}</p>
          </div>
          <div class="detail-item">
            <label class="text-sm font-medium text-gray-600">{{ t('auditlog.strings.description') }}</label>
            <p>{{ selectedLog.description }}</p>
          </div>
        </div>
        
        <div v-if="selectedLog.old_data || selectedLog.new_data" class="data-changes">
          <h4 class="text-lg font-semibold mb-3">{{ t('auditlog.strings.dataChanges') }}</h4>
          
          <div v-if="selectedLog.old_data" class="mb-4">
            <h5 class="text-md font-medium mb-2 text-red-600">{{ t('auditlog.strings.oldData') }}</h5>
            <div class="json-viewer">
              <pre>{{ formatJson(selectedLog.old_data) }}</pre>
            </div>
          </div>
          
          <div v-if="selectedLog.new_data">
            <h5 class="text-md font-medium mb-2 text-green-600">{{ t('auditlog.strings.newData') }}</h5>
            <div class="json-viewer">
              <pre>{{ formatJson(selectedLog.new_data) }}</pre>
            </div>
          </div>
        </div>
        
        <div v-if="selectedLog.entity_id" class="mt-6">
          <Button 
            :label="t('auditlog.strings.viewEntity')" 
            icon="pi pi-external-link"
            @click="viewEntity(selectedLog.entity, selectedLog.entity_id)"
          />
        </div>
      </div>
    </BaseDialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import i18n from '../locales/loader-final.js'
import { useApi } from '../composables/useApi'
import { useFilters } from '../composables/useFilters'
import { useDialog } from '../composables/useDialog'
import api from '../api/api'

import BaseDataTable from '../components/base/BaseDataTable.vue'
import BaseDialog from '../components/base/BaseDialog.vue'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import Calendar from 'primevue/calendar'
import Tag from 'primevue/tag'
import Avatar from 'primevue/avatar'

const { t } = useI18n()
const router = useRouter()

// Composables
const { loading, execute } = useApi()
const { filters: tableFilters, updateFilter } = useFilters({
  global: { value: null, matchMode: 'contains' }
}, 'auditLogs')

const { isVisible: showDialog, data: selectedLog, openEdit, close: closeDialog } = useDialog()

// Data
const auditLogs = ref([])
const users = ref([])
const showTimelineView = ref(false)

// Filtri
const filters = ref({
  dateRange: null,
  action: null,
  entity: null,
  user_id: null
})

const actionOptions = [
  { label: t('auditlog.strings.actionCreate'), value: 'create' },
  { label: t('auditlog.strings.actionUpdate'), value: 'update' },
  { label: t('auditlog.strings.actionDelete'), value: 'delete' },
  { label: t('auditlog.strings.actionLogin'), value: 'login' },
  { label: t('auditlog.strings.actionLogout'), value: 'logout' }
]

const entityOptions = [
  { label: t('auditlog.strings.entityAsset'), value: 'Asset' },
  { label: t('auditlog.strings.entityUser'), value: 'User' },
  { label: t('auditlog.strings.entitySite'), value: 'Site' },
  { label: t('auditlog.strings.entityLocation'), value: 'Location' },
  { label: t('auditlog.strings.entitySupplier'), value: 'Supplier' },
  { label: t('auditlog.strings.entityContact'), value: 'Contact' },
  { label: t('auditlog.strings.entityAssetType'), value: 'AssetType' },
  { label: t('auditlog.strings.entityAssetStatus'), value: 'AssetStatus' },
  { label: t('auditlog.strings.entityManufacturer'), value: 'Manufacturer' }
]

const userOptions = computed(() => {
  return users.value.map(user => ({
    label: user.name || user.email || user.username || user.id,
    value: user.id
  }))
})

const columnOptions = [
  { field: 'timestamp', header: t('auditlog.strings.timestamp'), sortable: true },
  { field: 'user_name', header: t('auditlog.strings.user'), sortable: false },
  { field: 'action', header: t('auditlog.strings.action'), sortable: false },
  { field: 'entity', header: t('auditlog.strings.entity'), sortable: false },
  { field: 'description', header: t('auditlog.strings.description'), sortable: false },
  { field: 'actions', header: t('common.strings.actions'), sortable: false }
]

onMounted(async () => {
  await fetchUsers()
  await fetchAuditLogs()
})

async function fetchUsers() {
  await execute(async () => {
    const response = await api.getUsers()
    users.value = response.data
    return response
  }, {
    errorContext: t('auditlog.strings.fetchUsersError'),
    showToast: false
  })
}

async function fetchAuditLogs() {
  await execute(async () => {
    const params = {
      from: filters.value.dateRange && filters.value.dateRange[0] ? filters.value.dateRange[0].toISOString() : undefined,
      to: filters.value.dateRange && filters.value.dateRange[1] ? filters.value.dateRange[1].toISOString() : undefined,
      action: filters.value.action,
      entity: filters.value.entity,
      user_id: filters.value.user_id,
      skip: 0,
      limit: 100
    }
    
    const response = await api.getAuditLogs(params)
    
    // Aggiungi campi derivati per la visualizzazione
    auditLogs.value = response.data.map(log => ({
      ...log,
      user_name: getUserName(log.user_id),
      entity_label: getEntityLabel(log.entity)
    }))
    
    return response
  }, {
    errorContext: t('auditlog.strings.fetchError'),
    showToast: false
  })
}

function clearFilters() {
  filters.value = {
    dateRange: null,
    action: null,
    entity: null,
    user_id: null
  }
  fetchAuditLogs()
}

function showDetails(log) {
  openEdit(t('auditlog.strings.details'), log)
}

function viewEntity(entity, entityId) {
  // Naviga alla pagina dell'entità specifica
  const routeMap = {
    'Asset': { name: 'AssetDetail', params: { id: entityId } },
    'User': { name: 'UserDetail', params: { id: entityId } },
    'Site': { name: 'SiteDetail', params: { id: entityId } },
    'Location': { name: 'LocationDetail', params: { id: entityId } },
    'Supplier': { name: 'SupplierDetail', params: { id: entityId } },
    'Contact': { name: 'ContactDetail', params: { id: entityId } },
    'AssetType': { name: 'AssetTypeDetail', params: { id: entityId } },
    'AssetStatus': { name: 'AssetStatusDetail', params: { id: entityId } },
    'Manufacturer': { name: 'ManufacturerDetail', params: { id: entityId } }
  }
  
  const route = routeMap[entity]
  if (route) {
    router.push(route)
  }
}

function getUserName(userId) {
  const user = users.value.find(u => u.id === userId)
  return user ? (user.name || user.email || user.username || userId) : userId
}

function getUserInitials(userId) {
  const user = users.value.find(u => u.id === userId)
  if (!user) return '?'
  
  const name = user.name || user.email || user.username || ''
  return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
}

function getEntityLabel(entity) {
  const option = entityOptions.find(e => e.value === entity)
  return option ? option.label : entity
}

function getEntityIcon(entity) {
  const iconMap = {
    'Asset': 'pi pi-desktop',
    'User': 'pi pi-user',
    'Site': 'pi pi-building',
    'Location': 'pi pi-map-marker',
    'Supplier': 'pi pi-briefcase',
    'Contact': 'pi pi-address-book',
    'AssetType': 'pi pi-tag',
    'AssetStatus': 'pi pi-circle-fill',
    'Manufacturer': 'pi pi-cog'
  }
  return iconMap[entity] || 'pi pi-file'
}

function getActionSeverity(action) {
  const severityMap = {
    'create': 'success',
    'update': 'info',
    'delete': 'danger',
    'login': 'warning',
    'logout': 'secondary'
  }
  return severityMap[action] || 'info'
}

function getActionClass(action) {
  const classMap = {
    'create': 'bg-green-500',
    'update': 'bg-blue-500',
    'delete': 'bg-red-500',
    'login': 'bg-yellow-500',
    'logout': 'bg-gray-500'
  }
  return classMap[action] || 'bg-gray-500'
}

function getActionIcon(action) {
  const iconMap = {
    'create': 'pi pi-plus',
    'update': 'pi pi-pencil',
    'delete': 'pi pi-trash',
    'login': 'pi pi-sign-in',
    'logout': 'pi pi-sign-out'
  }
  return iconMap[action] || 'pi pi-info'
}

function getFormattedDescription(log) {
  if (!log.description) return '-'
  
  // Sostituisci l'ID con il nome dell'entità se disponibile
  let description = log.description
  if (log.entity_name) {
    description = description.replace(log.entity_id, log.entity_name)
  }
  
  return description
}

function formatTimestamp(timestamp) {
  if (!timestamp) return '-'
  const date = new Date(timestamp)
  const locale = i18n.global.locale.value;
  const dateLocale = locale === 'it' ? 'it-IT' : 'en-US';
  return date.toLocaleString(dateLocale, {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

function formatJson(data) {
  if (!data) return '-'
  try {
    return JSON.stringify(data, null, 2)
  } catch {
    return data
  }
}

function exportAuditLogs() {
  // TODO: Implementare export CSV dei log di audit
}
</script>

<style scoped>
.audit-logs-page {
  padding: 1rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.filters-section {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.timeline-container {
  position: relative;
  padding-left: 2rem;
}

.timeline-container::before {
  content: '';
  position: absolute;
  left: 1rem;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #e9ecef;
}

.timeline-item {
  position: relative;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: flex-start;
}

.timeline-marker {
  position: absolute;
  left: -1.5rem;
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 0.75rem;
}

.timeline-content {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 1rem;
  flex: 1;
  margin-left: 1rem;
}

.timeline-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.timeline-time {
  font-size: 0.875rem;
  color: #6c757d;
}

.timeline-user {
  font-weight: 500;
}

.timeline-description {
  margin-bottom: 0.5rem;
}

.audit-details {
  max-height: 70vh;
  overflow-y: auto;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.json-viewer {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  padding: 1rem;
  max-height: 200px;
  overflow-y: auto;
}

.json-viewer pre {
  margin: 0;
  font-size: 0.875rem;
  line-height: 1.4;
}
</style> 