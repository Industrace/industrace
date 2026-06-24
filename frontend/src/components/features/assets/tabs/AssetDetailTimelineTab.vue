<!--
  - AssetTimeline.vue
  - Componente per visualizzare la timeline delle modifiche di un asset
  - Sistema di change management visivo
-->
<template>
  <div class="asset-timeline">
    <div class="timeline-header">
      <h3 class="text-lg font-semibold">{{ t('assets.timeline.title') }}</h3>
      <div class="flex gap-2">
        <Button 
          :label="t('assets.timeline.refresh')" 
          icon="pi pi-refresh" 
          size="small"
          severity="secondary"
          :loading="loading"
          @click="fetchTimeline" 
        />
        <Button 
          :label="t('assets.timeline.export')" 
          icon="pi pi-file-excel" 
          size="small"
          severity="secondary"
          @click="exportTimeline" 
        />
      </div>
    </div>

    <!-- Filtri Timeline -->
    <div class="timeline-filters mb-4">
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="field">
          <label for="timeline_action" class="block text-sm font-medium mb-2">{{ t('assets.timeline.action') }}</label>
          <Dropdown 
            id="timeline_action"
            v-model="filters.action" 
            :options="actionOptions" 
            optionLabel="label" 
            optionValue="value" 
            :placeholder="t('assets.timeline.selectAction')"
            showClear
            class="w-full"
          />
        </div>
        
        <div class="field">
          <label for="timeline_user" class="block text-sm font-medium mb-2">{{ t('assets.timeline.user') }}</label>
          <Dropdown 
            id="timeline_user"
            v-model="filters.user_id" 
            :options="userOptions" 
            optionLabel="label" 
            optionValue="value" 
            :placeholder="t('assets.timeline.selectUser')"
            showClear
            class="w-full"
          />
        </div>
        
        <div class="field">
          <label for="timeline_date_range" class="block text-sm font-medium mb-2">{{ t('assets.timeline.dateRange') }}</label>
          <Calendar 
            id="timeline_date_range"
            v-model="filters.dateRange" 
            selectionMode="range" 
            :placeholder="t('assets.timeline.selectDateRange')"
            dateFormat="dd/mm/yy"
            showIcon
            class="w-full"
          />
          <div v-if="filters.dateRange && filters.dateRange.length === 2 && filters.dateRange[0] && filters.dateRange[1]" class="date-range-labels mt-2">
            <span>{{ t('assets.timeline.from') }}: {{ formatDate(filters.dateRange[0]) }}</span>
            <span class="ml-2">{{ t('assets.timeline.to') }}: {{ formatDate(filters.dateRange[1]) }}</span>
          </div>
        </div>
      </div>
      
      <div class="flex gap-2 mt-4">
        <Button 
          :label="t('common.actions.search')" 
          icon="pi pi-search" 
          size="small"
          @click="fetchTimeline" 
        />
        <Button 
          :label="t('common.actions.clear')" 
          icon="pi pi-times" 
          size="small"
          severity="secondary"
          @click="clearFilters" 
        />
      </div>
    </div>

    <!-- Timeline -->
    <div v-if="timeline.length === 0 && !loading" class="empty-timeline">
      <div class="text-center py-8">
        <i class="pi pi-clock text-4xl text-gray-400 mb-4"></i>
        <p class="text-gray-500">{{ t('assets.timeline.noChanges') }}</p>
      </div>
    </div>

    <div v-else class="timeline-container">
      <div v-for="(log, index) in timeline" :key="log.id" class="timeline-item">
        <div class="timeline-marker" :class="getActionClass(log.action)">
          <i :class="getActionIcon(log.action)"></i>
        </div>
        
        <div class="timeline-content">
          <div class="timeline-header">
            <div class="timeline-meta">
              <span class="timeline-time">{{ formatTimestamp(log.timestamp) }}</span>
              <span class="timeline-user">{{ getUserName(log.user_id) }}</span>
            </div>
            <Tag :value="getActionLabel(log.action)" :severity="getActionSeverity(log.action)" />
          </div>
          
          <div class="timeline-body">
            <p class="timeline-description">{{ formatDescription(log) }}</p>
            
            <!-- Dettagli delle modifiche -->
            <div v-if="log.old_data || log.new_data" class="timeline-changes">
              <div v-if="log.old_data && log.new_data" class="changes-comparison">
                <div class="change-item old">
                  <h5 class="text-sm font-medium text-red-600 mb-2">{{ t('assets.timeline.before') }}</h5>
                  <div class="change-data">
                    <div v-for="(change, key) in getChangedFields(log.old_data, log.new_data)" :key="key" class="change-field">
                      <span class="field-name">{{ getFieldLabel(key) }}:</span>
                      <span class="field-value old-value">
                        <template v-if="change.isComplex">
                          <Tag severity="info" :value="t('assets.timeline.modified')" />
                        </template>
                        <template v-else>
                          {{ change.old }}
                        </template>
                      </span>
                    </div>
                    <!-- Messaggio se non ci sono modifiche -->
                    <div v-if="Object.keys(getChangedFields(log.old_data, log.new_data)).length === 0" class="no-changes-indicator">
                      <span class="text-sm text-gray-500">{{ t('assets.timeline.noChangesDetected') }}</span>
                    </div>
                  </div>
                </div>
                
                <div class="change-item new">
                  <h5 class="text-sm font-medium text-green-600 mb-2">{{ t('assets.timeline.after') }}</h5>
                  <div class="change-data">
                    <div v-for="(change, key) in getChangedFields(log.old_data, log.new_data)" :key="key" class="change-field">
                      <span class="field-name">{{ getFieldLabel(key) }}:</span>
                      <span class="field-value new-value">
                        <template v-if="change.isComplex">
                          <Tag severity="info" :value="t('assets.timeline.modified')" />
                        </template>
                        <template v-else>
                          {{ change.new }}
                        </template>
                      </span>
                    </div>
                    <!-- Messaggio se non ci sono modifiche -->
                    <div v-if="Object.keys(getChangedFields(log.old_data, log.new_data)).length === 0" class="no-changes-indicator">
                      <span class="text-sm text-gray-500">{{ t('assets.timeline.noChangesDetected') }}</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div v-else-if="log.old_data" class="change-item old">
                <h5 class="text-sm font-medium text-red-600 mb-2">{{ t('assets.timeline.removed') }}</h5>
                <div class="change-data">
                  <div v-for="(value, key) in parseJsonSafely(log.old_data)" :key="key" class="change-field">
                    <span class="field-name">{{ getFieldLabel(key) }}:</span>
                    <span class="field-value">{{ formatFieldValueWithName(parseJsonSafely(log.old_data), key, value) }}</span>
                  </div>
                </div>
              </div>
              
              <div v-else-if="log.new_data" class="change-item new">
                <h5 class="text-sm font-medium text-green-600 mb-2">{{ t('assets.timeline.added') }}</h5>
                <div class="change-data">
                  <div v-for="(value, key) in parseJsonSafely(log.new_data)" :key="key" class="change-field">
                    <span class="field-name">{{ getFieldLabel(key) }}:</span>
                    <span class="field-value">{{ formatFieldValueWithName(parseJsonSafely(log.new_data), key, value) }}</span>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Dettagli aggiuntivi -->
            <div class="timeline-details">
              <span v-if="log.ip_address" class="detail-item">
                <i class="pi pi-globe text-xs"></i>
                {{ log.ip_address }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Paginazione -->
    <div v-if="total > 0" class="timeline-pagination mt-6">
      <Paginator 
        v-model:first="first" 
        :rows="pageSize" 
        :totalRecords="total"
        :rowsPerPageOptions="[10, 25, 50]"
        @page="onPage"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import i18n from '@/locales/loader-final.js'
import api from '@/api/api'
import { useApi } from '@/composables/useApi'
import { useAuditLogLabels, ASSET_TIMELINE_ACTIONS } from '@/composables/useAuditLogLabels'

import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import Calendar from 'primevue/calendar'
import Tag from 'primevue/tag'
import Paginator from 'primevue/paginator'

const { t } = useI18n()

// Props
const props = defineProps({
  assetId: {
    type: String,
    required: true
  }
})

// Composables
const { loading, execute } = useApi()

const {
  actionOptions,
  getActionLabel,
  getActionSeverity,
  getActionClass,
  getActionIcon,
  formatDescription,
} = useAuditLogLabels(ASSET_TIMELINE_ACTIONS, ['Asset'])

const timeline = ref([])
const users = ref([])
const total = ref(0)
const first = ref(0)
const pageSize = ref(25)

const filters = ref({
  action: null,
  user_id: null,
  dateRange: null
})

const userOptions = computed(() => {
  return users.value.map(user => ({
    label: user.name || user.email || user.username || user.id,
    value: user.id
  }))
})

onMounted(async () => {
  await fetchUsers()
  await fetchTimeline()
})

watch(() => props.assetId, () => {
  if (props.assetId) {
    fetchTimeline()
  }
})

async function fetchUsers() {
  await execute(async () => {
    const response = await api.getUsers()
    users.value = response.data
    return response
  }, {
    errorContext: t('assets.timeline.fetchUsersError'),
    showToast: false
  })
}

async function fetchTimeline() {
  if (!props.assetId) return
  
  await execute(async () => {
    const params = {
      entity: 'Asset',
      entity_id: props.assetId,
      action: filters.value.action,
      user_id: filters.value.user_id,
      from: filters.value.dateRange && filters.value.dateRange[0] ? filters.value.dateRange[0].toISOString() : undefined,
      to: filters.value.dateRange && filters.value.dateRange[1] ? filters.value.dateRange[1].toISOString() : undefined,
      skip: first.value,
      limit: pageSize.value
    }
    
    const response = await api.getAuditLogs(params)
    timeline.value = response.data
    total.value = response.data.length // TODO: backend dovrebbe restituire il totale
    return response
  }, {
    errorContext: t('assets.timeline.fetchError'),
    showToast: false
  })
}

function clearFilters() {
  filters.value = {
    action: null,
    user_id: null,
    dateRange: null
  }
  first.value = 0
  fetchTimeline()
}

function onPage(e) {
  first.value = e.first
  pageSize.value = e.rows
  fetchTimeline()
}

function getUserName(userId) {
  const user = users.value.find(u => u.id === userId)
  return user ? (user.name || user.email || user.username || userId) : userId
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

function formatDate(date) {
  if (!date) return '-';
  const locale = i18n.global.locale.value;
  const dateLocale = locale === 'it' ? 'it-IT' : 'en-US';
  if (typeof date === 'string') return new Date(date).toLocaleDateString(dateLocale);
  return date.toLocaleDateString(dateLocale);
}

function parseJsonSafely(data) {
  if (!data) return null
  if (typeof data === 'object') return data
  if (typeof data === 'string') {
    try {
      return JSON.parse(data)
    } catch {
      return data
    }
  }
  return data
}

function formatFieldValueWithName(data, key, value) {
  if (key.endsWith('_id')) {
    const nameKey = `${key}_name`
    if (data && data[nameKey]) {
      return data[nameKey]
    }
  }
  return formatFieldValue(key, value)
}

function getChangedFields(oldData, newData) {
  if (!oldData && !newData) return {}
  
  // Parsa i dati JSON se sono stringhe
  const oldParsed = parseJsonSafely(oldData)
  const newParsed = parseJsonSafely(newData)
  
  const changed = {}
  
  // Confronta tutti i campi rilevanti da entrambi gli oggetti
  const allKeys = new Set([
    ...Object.keys(oldParsed || {}),
    ...Object.keys(newParsed || {})
  ])
  
  for (const key of allKeys) {
    // Ignora i campi di sistema e metadati
    if (key.startsWith('_') || key === 'id' || key === 'tenant_id' || key === 'created_at' || key === 'updated_at') {
      continue
    }
    
    const oldVal = oldParsed ? oldParsed[key] : undefined
    const newVal = newParsed ? newParsed[key] : undefined
    
    // Normalizza i valori per il confronto
    const normalizeValue = (val) => {
      if (val === null || val === undefined || val === '') return null
      if (typeof val === 'string') return val.trim()
      return val
    }
    
    const normalizedOld = normalizeValue(oldVal)
    const normalizedNew = normalizeValue(newVal)
    
    // Confronta i valori normalizzati
    const oldStr = JSON.stringify(normalizedOld)
    const newStr = JSON.stringify(normalizedNew)
    
    // Mostra solo se c'è una differenza reale
    if (oldStr !== newStr) {
      // Se array o oggetto complesso, mostra solo badge "modificato"
      if (Array.isArray(oldVal) || Array.isArray(newVal) || 
          (typeof oldVal === 'object' && oldVal !== null) || 
          (typeof newVal === 'object' && newVal !== null)) {
        changed[key] = { old: t('assets.timeline.modified'), new: t('assets.timeline.modified'), isComplex: true }
      } else {
        // Per i campi ID, prova a usare il nome se disponibile
        let oldDisplay = oldVal
        let newDisplay = newVal
        
        if (key.endsWith('_id')) {
          const nameKey = `${key}_name`
          if (oldParsed && oldParsed[nameKey]) {
            oldDisplay = oldParsed[nameKey]
          }
          if (newParsed && newParsed[nameKey]) {
            newDisplay = newParsed[nameKey]
          }
        }
        
        // Formatta i valori per la visualizzazione
        oldDisplay = formatFieldValue(key, oldDisplay)
        newDisplay = formatFieldValue(key, newDisplay)
        
        changed[key] = { 
          old: oldDisplay, 
          new: newDisplay, 
          isComplex: false,
          oldName: oldParsed ? oldParsed[`${key}_name`] : null,
          newName: newParsed ? newParsed[`${key}_name`] : null
        }
      }
    }
  }
  
  return changed
}

function getFieldLabel(field) {
  const fieldMap = {
    'name': t('common.fields.name'),
    'ip_address': t('assets.fields.ipAddress'),
    'site_id': t('assets.fields.site'),
    'location_id': t('assets.fields.location'),
    'asset_type_id': t('assets.fields.type'),
    'asset_status_id': t('assets.fields.status'),
    'manufacturer_id': t('assets.fields.manufacturer'),
    'tag': t('assets.fields.tag'),
    'firmware_version': t('assets.fields.firmware'),
    'serial_number': t('assets.fields.serialNumber'),
    'risk_score': t('assets.fields.riskScore'),
    'purdue_level': t('assets.fields.purdueLevel'),
    'impact_value': t('assets.fields.impactValue'),
    'access_ease': t('assets.fields.accessEase'),
    'exposure_level': t('assets.fields.exposureLevel'),
    'update_status': t('assets.fields.updateStatus'),
    // Campi con nomi degli oggetti
    'site_id_name': t('assets.fields.site'),
    'location_id_name': t('assets.fields.location'),
    'asset_type_id_name': t('common.fields.type'),
    'asset_status_id_name': t('common.fields.status'),
    'manufacturer_id_name': t('common.fields.manufacturer'),
    'status_id': t('common.fields.status'),
    'status_id_name': t('common.fields.status')
  }
  return fieldMap[field] || field
}

function formatFieldValue(field, value) {
  if (value === null || value === undefined) return '-'
  
  if (typeof value === 'string' && (value.startsWith('{') || value.startsWith('['))) {
    try {
      const parsed = JSON.parse(value)
      if (typeof parsed === 'object') {
        return t('assets.timeline.objectValue')
      }
    } catch {
    }
  }
  
  // Formattazione speciale per alcuni campi
  switch (field) {
    case 'risk_score':
      return `${value}%`
    case 'purdue_level':
      return t('assets.timeline.purdueLevelValue', { level: value })
    case 'impact_value':
    case 'access_ease':
    case 'exposure_level':
    case 'update_status':
      return value
    case 'site_id':
    case 'location_id':
    case 'asset_type_id':
    case 'asset_status_id':
    case 'manufacturer_id':
      return typeof value === 'string' ? value : String(value)
    case 'site_id_name':
      return value || '-'
    case 'location_id_name':
      return value || '-'
    case 'asset_type_id_name':
      return value || '-'
    case 'asset_status_id_name':
      return value || '-'
    case 'manufacturer_id_name':
      return value || '-'
    case 'status_id':
      return typeof value === 'string' ? value : String(value)
    case 'status_id_name':
      return value || '-'
    case 'created_at':
    case 'updated_at':
      if (value) {
        const date = new Date(value)
        const locale = i18n.global.locale.value;
        const dateLocale = locale === 'it' ? 'it-IT' : 'en-US';
        return date.toLocaleString(dateLocale)
      }
      return value
    default:
      return value
  }
}

async function exportTimeline() {
  try {
    const params = {
      entity: 'Asset',
      entity_id: props.assetId,
      action: filters.value.action,
      user_id: filters.value.user_id,
      from: filters.value.dateRange && filters.value.dateRange[0] ? filters.value.dateRange[0].toISOString() : undefined,
      to: filters.value.dateRange && filters.value.dateRange[1] ? filters.value.dateRange[1].toISOString() : undefined
    }
    const response = await api.exportAuditLogs(params)
    const url = window.URL.createObjectURL(new Blob([response.data], { type: 'text/csv' }))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'audit_logs.csv')
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch {
    // export failed silently
  }
}
</script>

<style scoped>
.asset-timeline {
  padding: 1rem;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.timeline-filters {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.empty-timeline {
  text-align: center;
  padding: 2rem;
  background: #f8f9fa;
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
  z-index: 1;
}

.timeline-content {
  background: white;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 1rem;
  flex: 1;
  margin-left: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.timeline-meta {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.timeline-time {
  font-size: 0.875rem;
  color: #6c757d;
}

.timeline-user {
  font-weight: 500;
  color: #495057;
}

.timeline-description {
  margin-bottom: 1rem;
  color: #495057;
}

.timeline-changes {
  margin-bottom: 1rem;
}

.changes-comparison {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.change-item {
  padding: 0.75rem;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

.change-item.old {
  background: #fff5f5;
  border-color: #fed7d7;
}

.change-item.new {
  background: #f0fff4;
  border-color: #c6f6d5;
}

.change-data {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.change-field {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.25rem 0;
  border-bottom: 1px solid #f1f3f4;
}

.change-field:last-child {
  border-bottom: none;
}

.field-name {
  font-weight: 500;
  color: #495057;
  font-size: 0.875rem;
}

.field-value {
  font-size: 0.875rem;
  color: #6c757d;
}

.old-value {
  color: #dc3545;
  text-decoration: line-through;
}

.new-value {
  color: #28a745;
  font-weight: 500;
}

.no-changes-message {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  padding: 1rem;
}

.no-changes-indicator {
  text-align: center;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 4px;
  border: 1px dashed #dee2e6;
}

.timeline-details {
  display: flex;
  gap: 1rem;
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid #e9ecef;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  color: #6c757d;
}

.timeline-pagination {
  display: flex;
  justify-content: center;
}
</style> 