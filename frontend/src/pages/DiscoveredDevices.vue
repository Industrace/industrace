<template>
  <div class="discovered-devices-page">
    <div class="page-header">
      <h1>{{ t('menu.navigation.discoveredDevices') }}</h1>
      <div class="flex gap-2">
        <Button
          :disabled="loading || !canManageDiscoveredDevices"
          icon="pi pi-trash"
          :label="t('discoveredDevices.actions.clear')"
          severity="danger"
          outlined
          @click="clearDiscoveredDevices"
        />
        <Button
          :disabled="loading"
          icon="pi pi-sync"
          :label="t('common.actions.refresh')"
          severity="secondary"
          @click="fetchDevices"
        />
      </div>
    </div>

    <div class="filters-section mb-4">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div class="field">
          <label class="block text-sm font-medium mb-2">{{ t('discoveredDevices.filters.status') }}</label>
          <Dropdown
            v-model="filters.status"
            :options="statusOptions"
            optionLabel="label"
            optionValue="value"
            :placeholder="t('common.messages.selectOption')"
            class="w-full"
            showClear
          />
        </div>

        <div class="field">
          <label class="block text-sm font-medium mb-2">{{ t('discoveredDevices.filters.probe') }}</label>
          <Dropdown
            v-model="filters.probe_id"
            :options="probes"
            optionLabel="name"
            optionValue="id"
            class="w-full"
            showClear
          />
        </div>

        <div class="field">
          <label class="block text-sm font-medium mb-2">{{ t('discoveredDevices.filters.site') }}</label>
          <Dropdown
            v-model="filters.site_id"
            :options="sites"
            optionLabel="name"
            optionValue="id"
            class="w-full"
            showClear
          />
        </div>

        <div class="field">
          <label class="block text-sm font-medium mb-2">{{ t('common.strings.search') }}</label>
          <InputText
            v-model="filters.search"
            :placeholder="t('discoveredDevices.filters.searchPlaceholder')"
            class="w-full"
          />
        </div>
      </div>
    </div>

    <BaseDataTable
      :data="filteredFormattedDevices"
      :loading="loading"
      :columns="columnOptions"
      :showExport="false"
      :showColumnSelector="false"
      :rows="15"
      @refresh="fetchDevices"
    >
      <template #body-ip_display="{ data }">
        <span>{{ data.ip_display || '-' }}</span>
      </template>

      <template #body-match_indicator="{ data }">
        <Tag
          v-if="data.best_match_type === 'mac'"
          :value="t('discoveredDevices.match.mac')"
          severity="success"
        />
        <Tag
          v-else-if="data.best_match_type === 'ip'"
          :value="t('discoveredDevices.match.ip')"
          severity="warning"
        />
        <Tag
          v-else
          :value="t('discoveredDevices.match.new')"
          severity="info"
        />
      </template>

      <template #body-actions="{ data }">
        <div class="flex gap-2">
          <Button
            v-if="data.best_match_asset_id"
            icon="pi pi-link"
            size="small"
            severity="help"
            :disabled="!canManageDiscoveredDevices"
            @click="assignToMatchedAsset(data)"
            v-tooltip.top="t('discoveredDevices.actions.assignTooltip')"
          />
          <Button
            icon="pi pi-plus"
            size="small"
            severity="success"
            :disabled="!canManageDiscoveredDevices"
            @click="openOnboardDialog(data)"
            v-tooltip.top="t('discoveredDevices.actions.onboardTooltip')"
          />
          <Button
            icon="pi pi-pencil"
            size="small"
            severity="primary"
            :disabled="!canManageDiscoveredDevices"
            @click="openEditDialog(data)"
          />
        </div>
      </template>
    </BaseDataTable>

    <BaseDialog
      v-model:isVisible="showEditDialog"
      :title="t('common.actions.edit')"
      :mode="'edit'"
      :showFooter="true"
      :showCancel="true"
      :showSubmit="true"
      @cancel="closeEditDialog"
      @submit="saveEdit"
    >
      <template #default>
        <div class="grid grid-cols-1 gap-4">
          <div class="field">
            <label class="block text-sm font-medium mb-2">{{ t('discoveredDevices.filters.status') }}</label>
            <Dropdown
              v-model="editForm.status"
              :options="statusOptions"
              optionLabel="label"
              optionValue="value"
              class="w-full"
            />
          </div>

          <div class="field">
            <label class="block text-sm font-medium mb-2">{{ t('common.fields.notes') }}</label>
            <Textarea v-model="editForm.notes" rows="4" class="w-full" />
          </div>
        </div>
      </template>
    </BaseDialog>

    <BaseDialog
      v-model:isVisible="showOnboardDialog"
      :title="t('discoveredDevices.onboard.title')"
      :mode="'create'"
      :showFooter="true"
      :showCancel="true"
      :showSubmit="true"
      :width="'38vw'"
      @cancel="closeOnboardDialog"
      @submit="submitOnboard"
    >
      <template #default>
        <div class="grid grid-cols-1 gap-3">
          <div class="field">
            <label class="block text-sm font-medium mb-2">{{ t('discoveredDevices.onboard.assetName') }}</label>
            <InputText v-model="onboardForm.name" class="w-full" />
          </div>
          <div class="field">
            <label class="block text-sm font-medium mb-2">{{ t('discoveredDevices.onboard.tagOptional') }}</label>
            <InputText v-model="onboardForm.tag" class="w-full" />
          </div>
          <small class="text-color-secondary">
            {{ t('discoveredDevices.onboard.hint') }}
          </small>
        </div>
      </template>
    </BaseDialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useApi } from '../composables/useApi'
import api from '../api/api'
import { useAuthStore } from '@/store/auth'

import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Tag from 'primevue/tag'

import BaseDataTable from '../components/base/BaseDataTable.vue'
import BaseDialog from '../components/base/BaseDialog.vue'

const { t } = useI18n()
const { loading, execute } = useApi()

const authStore = useAuthStore()
const canManageDiscoveredDevices = computed(() => {
  const roleName = authStore.user?.role?.name
  return roleName === 'admin' || roleName === 'super_admin'
})

const devices = ref([])
const probes = ref([])
const sites = ref([])

const filters = reactive({
  status: null,
  probe_id: null,
  site_id: null,
  search: ''
})

const statusOptions = computed(() => [
  { label: t('discoveredDevices.status.discovered'), value: 'discovered' },
  { label: t('discoveredDevices.status.matched'), value: 'matched' },
  { label: t('discoveredDevices.status.imported'), value: 'imported' },
  { label: t('discoveredDevices.status.assigned'), value: 'assigned' },
  { label: t('discoveredDevices.status.ignored'), value: 'ignored' },
  { label: t('discoveredDevices.status.conflict'), value: 'conflict' }
])

function getDeviceStatusValue(device) {
  return device?.status?.value ?? device?.status ?? null
}

const filteredDevices = computed(() => {
  const statusValue = filters.status
  const probeIdValue = filters.probe_id
  const siteIdValue = filters.site_id
  const q = (filters.search || '').trim().toLowerCase()

  return devices.value.filter(d => {
    if (statusValue && getDeviceStatusValue(d) !== statusValue) return false
    if (probeIdValue && d.probe_id !== probeIdValue) return false
    if (siteIdValue && d.site_id !== siteIdValue) return false

    if (q) {
      const ipPart = Array.isArray(d.ip_addresses) ? d.ip_addresses.join(' ') : ''
      const haystack = `${d.mac_address || ''} ${ipPart} ${d.hostname || ''} ${d.vendor || ''}`.toLowerCase()
      if (!haystack.includes(q)) return false
    }

    return true
  })
})

const filteredFormattedDevices = computed(() => {
  const labelByStatus = {}
  for (const s of statusOptions.value) labelByStatus[s.value] = s.label
  return filteredDevices.value.map(d => ({
    ...d,
    status_label: labelByStatus[getDeviceStatusValue(d)] || (d.status ?? ''),
    ip_display: Array.isArray(d.ip_addresses) ? d.ip_addresses.join(', ') : '',
    match_indicator: d.best_match_type || null
  }))
})

const columnOptions = computed(() => [
  { field: 'mac_address', header: t('discoveredDevices.columns.mac') },
  { field: 'ip_display', header: t('discoveredDevices.columns.ip') },
  { field: 'hostname', header: t('discoveredDevices.columns.hostname') },
  { field: 'vendor', header: t('discoveredDevices.columns.vendor') },
  { field: 'match_indicator', header: t('discoveredDevices.columns.match') },
  { field: 'status_label', header: t('discoveredDevices.columns.status') },
  { field: 'last_seen', header: t('discoveredDevices.columns.lastSeen') },
  { field: 'actions', header: t('discoveredDevices.columns.actions') }
])

const showEditDialog = ref(false)
const editingDevice = ref(null)

const editForm = reactive({
  status: null,
  notes: ''
})

const showOnboardDialog = ref(false)
const onboardingDevice = ref(null)
const onboardForm = reactive({
  name: '',
  tag: ''
})

function openEditDialog(device) {
  editingDevice.value = device
  editForm.status = getDeviceStatusValue(device)
  editForm.notes = device.notes || ''
  showEditDialog.value = true
}

function closeEditDialog() {
  showEditDialog.value = false
}

function openOnboardDialog(device) {
  onboardingDevice.value = device
  const firstIp = Array.isArray(device.ip_addresses) && device.ip_addresses.length ? device.ip_addresses[0] : null
  onboardForm.name = device.hostname || (firstIp
    ? t('discoveredDevices.onboard.defaultName', { value: firstIp })
    : t('discoveredDevices.onboard.defaultName', { value: device.mac_address }))
  onboardForm.tag = ''
  showOnboardDialog.value = true
}

function closeOnboardDialog() {
  showOnboardDialog.value = false
}

async function fetchSites() {
  await execute(async () => {
    const response = await api.getSites()
    sites.value = response.data || []
    return response
  }, {
    errorContext: t('common.messages.fetchError'),
    showToast: false
  })
}

async function fetchProbes() {
  await execute(async () => {
    const response = await api.getNetworkProbes()
    probes.value = response.data || []
    return response
  }, {
    errorContext: t('common.messages.fetchError'),
    showToast: false
  })
}

async function fetchDevices() {
  await execute(async () => {
    const response = await api.getDiscoveredDevices({ skip: 0, limit: 1000 })
    devices.value = response.data || []
    return response
  }, {
    errorContext: t('common.messages.fetchError'),
    showToast: false
  })
}

async function saveEdit() {
  if (!editingDevice.value) return
  await execute(async () => {
    await api.updateDiscoveredDevice(editingDevice.value.id, {
      status: editForm.status,
      notes: editForm.notes
    })
    showEditDialog.value = false
    await fetchDevices()
    return true
  }, {
    successMessage: t('common.messages.updated'),
    errorContext: t('common.messages.updateError'),
    showToast: false
  })
}

async function assignToMatchedAsset(device) {
  if (!device?.best_match_asset_id) return
  await execute(async () => {
    await api.updateDiscoveredDevice(device.id, {
      status: 'matched',
      matched_asset_id: device.best_match_asset_id,
      match_confidence: device.best_match_type === 'mac' ? 100 : 75,
      match_reason: `auto-${device.best_match_type}`
    })
    await fetchDevices()
    return true
  }, {
    successMessage: t('discoveredDevices.messages.assigned'),
    errorContext: t('common.messages.updateError'),
    showToast: true
  })
}

async function submitOnboard() {
  if (!onboardingDevice.value) return
  await execute(async () => {
    await api.onboardDiscoveredDevice(onboardingDevice.value.id, {
      name: onboardForm.name || null,
      tag: onboardForm.tag || null
    })
    showOnboardDialog.value = false
    await fetchDevices()
    return true
  }, {
    successMessage: t('discoveredDevices.messages.assetCreated'),
    errorContext: t('common.messages.createError'),
    showToast: true
  })
}

async function clearDiscoveredDevices() {
  const selectedProbe = probes.value.find(p => p.id === filters.probe_id)
  const targetLabel = selectedProbe?.name || t('discoveredDevices.actions.clearAllLabel')
  const confirmed = window.confirm(
    t('discoveredDevices.actions.clearConfirm', { target: targetLabel })
  )
  if (!confirmed) return

  await execute(async () => {
    const params = filters.probe_id ? { probe_id: filters.probe_id } : {}
    await api.clearDiscoveredDevices(params)
    await fetchDevices()
    return true
  }, {
    successMessage: t('discoveredDevices.messages.cleared'),
    errorContext: t('discoveredDevices.messages.clearError'),
    showToast: true
  })
}

onMounted(async () => {
  await fetchSites()
  await fetchProbes()
  await fetchDevices()
})
</script>

<style scoped>
.discovered-devices-page .page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}
</style>

