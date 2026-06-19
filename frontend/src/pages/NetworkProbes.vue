<template>
  <div class="network-probes-page">
    <div class="page-header">
      <h1>{{ t('menu.navigation.networkProbes') }}</h1>
      <div class="flex gap-2 align-items-center">
        <Dropdown
          v-model="selectedSiteId"
          :options="sites"
          optionLabel="name"
          optionValue="id"
          :placeholder="t('common.fields.site')"
          class="w-16rem"
          showClear
          @change="onSiteFilterChange"
        />

        <Button
          icon="pi pi-refresh"
          :label="t('common.actions.refresh')"
          @click="fetchProbes"
          :loading="loading"
          class="p-button-secondary"
        />

        <Button
          v-if="canManageNetworkProbes"
          icon="pi pi-plus"
          :label="t('networkProbes.addProbe')"
          severity="success"
          @click="openCreateDialog"
        />
      </div>
    </div>

    <Message severity="warn" :closable="true" class="mb-3">
      {{ t('networkProbes.legalDisclaimer') }}
    </Message>

    <!-- Overview -->
    <div v-if="loading && !overview" class="overview-loading">
      <ProgressSpinner style="width: 50px; height: 50px" strokeWidth="4" />
      <div class="overview-loading-label">{{ t('common.messages.loading') }}</div>
    </div>

    <div v-else-if="overview" class="overview-section">
      <div class="overview-grid">
        <Card class="overview-card overview-card--total">
          <template #content>
            <div class="overview-item">
              <div class="overview-icon overview-icon--total">
                <i class="pi pi-wifi"></i>
              </div>
              <div class="overview-content">
                <div class="overview-value">{{ overview.total_probes }}</div>
                <div class="overview-label">{{ t('networkProbes.overview.totalProbes') }}</div>
              </div>
            </div>
          </template>
        </Card>

        <Card class="overview-card overview-card--active">
          <template #content>
            <div class="overview-item">
              <div class="overview-icon overview-icon--active">
                <i class="pi pi-check-circle"></i>
              </div>
              <div class="overview-content">
                <div class="overview-value">{{ overview.active_probes }}</div>
                <div class="overview-label">{{ t('networkProbes.overview.active') }}</div>
              </div>
            </div>
          </template>
        </Card>

        <Card class="overview-card overview-card--error">
          <template #content>
            <div class="overview-item">
              <div class="overview-icon overview-icon--error">
                <i class="pi pi-exclamation-triangle"></i>
              </div>
              <div class="overview-content">
                <div class="overview-value">{{ overview.error_probes }}</div>
                <div class="overview-label">{{ t('networkProbes.overview.errors') }}</div>
              </div>
            </div>
          </template>
        </Card>

        <Card class="overview-card overview-card--health">
          <template #content>
            <div class="health-item">
              <div class="health-circle" :class="healthClass">
                <span class="health-value">{{ overview.health_percentage.toFixed(0) }}%</span>
              </div>
              <div class="overview-content">
                <div class="overview-label">{{ t('networkProbes.overview.overallHealth') }}</div>
                <div class="overview-subtitle">
                  {{ t('networkProbes.overview.activeOfTotal', { active: overview.active_probes, total: overview.total_probes }) }}
                </div>
              </div>
            </div>
          </template>
        </Card>
      </div>
    </div>

    <div v-if="!loading && formattedProbes.length === 0" class="empty-probes">
      <i class="pi pi-wifi empty-icon"></i>
      <h3>{{ t('networkProbes.empty.title') }}</h3>
      <p>{{ t('networkProbes.empty.description') }}</p>
      <Button
        v-if="canManageNetworkProbes"
        :label="t('networkProbes.addProbe')"
        icon="pi pi-plus"
        severity="success"
        @click="openCreateDialog"
      />
    </div>

    <BaseDataTable
      v-else
      :data="formattedProbes"
      :loading="loading"
      :columns="columnOptions"
      :showExport="false"
      :showColumnSelector="false"
      :rows="15"
      @refresh="fetchProbes"
    >
      <template #body-actions="{ data }">
        <div class="flex gap-2">
          <Button
            icon="pi pi-eye"
            class="p-button-text p-button-sm"
            :title="t('common.actions.view')"
            @click="openProbeDetails(data)"
          />

          <Button
            v-if="canManageNetworkProbes"
            icon="pi pi-pencil"
            class="p-button-text p-button-sm"
            :title="t('common.actions.edit')"
            @click="openEditProbe(data)"
          />

          <Button
            v-if="canManageNetworkProbes"
            icon="pi pi-ban"
            class="p-button-text p-button-sm p-button-warning"
            :title="t('networkProbes.actions.deauthorize')"
            @click="deauthorizeProbe(data)"
          />

          <Button
            v-if="canManageNetworkProbes"
            icon="pi pi-trash"
            class="p-button-text p-button-sm p-button-danger"
            :title="t('common.actions.delete')"
            @click="deleteProbe(data)"
          />
        </div>
      </template>
    </BaseDataTable>

    <!-- Probe Details -->
    <BaseDialog
      v-model:isVisible="showProbeDetailsDialog"
      :title="probeDetailsTitle"
      :mode="'view'"
      :showFooter="false"
      :showCancel="true"
      :width="'65vw'"
    >
      <template #default>
        <div v-if="selectedProbe" class="probe-details">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="detail-card">
              <div class="detail-label">{{ t('networkProbes.details.status') }}</div>
              <div class="detail-value">
                <Tag
                  :value="statusLabel(probeStatus?.status || selectedProbe.status)"
                  :severity="getProbeStatusSeverity(probeStatus?.status || selectedProbe.status)"
                />
              </div>
            </div>

            <div class="detail-card">
              <div class="detail-label">{{ t('networkProbes.details.healthScore') }}</div>
              <div class="detail-value">
                <span v-if="probeStatus?.health_score !== null && probeStatus?.health_score !== undefined">
                  {{ Math.round(probeStatus.health_score * 10) / 10 }}
                </span>
                <span v-else>—</span>
              </div>
            </div>

            <div class="detail-card">
              <div class="detail-label">{{ t('networkProbes.details.lastHeartbeat') }}</div>
              <div class="detail-value">{{ formatTs(selectedProbe.last_heartbeat) }}</div>
            </div>

            <div class="detail-card">
              <div class="detail-label">{{ t('networkProbes.details.probeId') }}</div>
              <div class="detail-value">{{ selectedProbe.id }}</div>
            </div>

            <div class="detail-card">
              <div class="detail-label">{{ t('networkProbes.details.lastData') }}</div>
              <div class="detail-value">{{ formatTs(selectedProbe.last_data_received) }}</div>
              <div class="detail-sub">
                <span :class="dataFreshnessClass">{{ dataFreshnessText }}</span>
              </div>
            </div>
          </div>

          <div class="mt-4">
            <div class="config-section-title">{{ t('networkProbes.details.configTitle') }}</div>
            <div class="config-hint">
              {{ t('networkProbes.details.configHint') }}
            </div>

            <div class="config-row">
              <InputText
                v-model="probeApiKeyInput"
                type="password"
                class="w-full"
                :placeholder="t('networkProbes.details.apiKeyPlaceholder')"
              />
              <Button
                icon="pi pi-eye"
                :label="loadingConfiguration ? t('common.messages.loading') : t('networkProbes.details.loadConfig')"
                class="p-button-secondary"
                :disabled="!probeApiKeyInput || loadingConfiguration"
                @click="fetchProbeConfiguration"
              />
            </div>

            <pre v-if="probeConfiguration" class="config-pre">{{ configurationJson }}</pre>
            <div v-else class="config-empty">{{ t('networkProbes.details.noConfigLoaded') }}</div>
          </div>
        </div>
      </template>
    </BaseDialog>

    <!-- Probe Edit -->
    <BaseDialog
      v-model:isVisible="showEditDialog"
      :title="t('common.actions.edit')"
      :mode="'edit'"
      :showFooter="true"
      :showCancel="true"
      :showSubmit="true"
      :width="'42vw'"
      @cancel="closeEditDialog"
      @submit="submitEditProbe"
    >
      <template #default>
        <TabView class="probe-edit-tabs">
          <TabPanel :header="t('networkProbes.tabs.identity')">
            <div class="grid grid-cols-1 gap-3">
              <div class="field">
                <label class="block text-sm font-medium mb-2">{{ t('common.fields.name') }}</label>
                <InputText v-model="editForm.name" class="w-full" />
              </div>

              <div class="field">
                <label class="block text-sm font-medium mb-2">{{ t('networkProbes.fields.interface') }}</label>
                <InputText v-model="editForm.interface_name" class="w-full" />
              </div>

              <div class="field">
                <label class="block text-sm font-medium mb-2">{{ t('networkProbes.fields.interfaceIp') }}</label>
                <InputText v-model="editForm.interface_ip" class="w-full" />
              </div>

              <div class="field">
                <label class="block text-sm font-medium mb-2">{{ t('common.fields.description') }}</label>
                <Textarea v-model="editForm.description" rows="3" class="w-full" />
              </div>
            </div>
          </TabPanel>

          <TabPanel :header="t('networkProbes.tabs.sniffing')">
            <div class="grid grid-cols-1 gap-3">
              <div class="field">
                <label class="block text-sm font-medium mb-2">{{ t('networkProbes.fields.captureFilter') }}</label>
                <InputText v-model="editForm.capture_filter" class="w-full" :placeholder="t('networkProbes.fields.captureFilterPlaceholder')" />
              </div>

              <div class="field">
                <label class="block text-sm font-medium mb-2">{{ t('networkProbes.fields.samplingRate') }}</label>
                <InputNumber v-model="editForm.sampling_rate" :min="0.01" :max="1" :step="0.01" mode="decimal" class="w-full" />
              </div>

              <div class="field">
                <label class="block text-sm font-medium mb-2">{{ t('networkProbes.fields.enabledProtocols') }}</label>
                <MultiSelect
                  v-model="editForm.enabled_protocols"
                  :options="protocolOptions"
                  optionLabel="label"
                  optionValue="value"
                  display="chip"
                  class="w-full"
                  :placeholder="t('networkProbes.fields.allProtocolsPlaceholder')"
                />
              </div>

              <div class="field">
                <label class="flex align-items-center gap-2">
                  <Checkbox v-model="editForm.promiscuous_mode" :binary="true" />
                  <span>{{ t('networkProbes.fields.promiscuousMode') }}</span>
                </label>
              </div>

              <div class="field">
                <label class="flex align-items-center gap-2">
                  <Checkbox v-model="editForm.metadata_extraction" :binary="true" />
                  <span>{{ t('networkProbes.fields.metadataExtraction') }}</span>
                </label>
              </div>

              <div class="field">
                <label class="flex align-items-center gap-2">
                  <Checkbox v-model="editForm.payload_analysis" :binary="true" />
                  <span>{{ t('networkProbes.fields.payloadAnalysis') }}</span>
                </label>
              </div>
            </div>
          </TabPanel>

          <TabPanel :header="t('networkProbes.tabs.telecontrol')">
            <div class="grid grid-cols-1 gap-3">
              <div class="field">
                <label class="block text-sm font-medium mb-2">{{ t('networkProbes.fields.heartbeatInterval') }}</label>
                <InputNumber v-model="editForm.heartbeat_interval" :min="10" :max="300" :step="5" class="w-full" />
              </div>

              <div class="field">
                <label class="block text-sm font-medium mb-2">{{ t('networkProbes.fields.dataInterval') }}</label>
                <InputNumber v-model="editForm.data_transmission_interval" :min="60" :max="3600" :step="15" class="w-full" />
              </div>

              <div class="field">
                <label class="block text-sm font-medium mb-2">{{ t('networkProbes.fields.maxRetryAttempts') }}</label>
                <InputNumber v-model="editForm.max_retry_attempts" :min="1" :max="10" :step="1" class="w-full" />
              </div>
            </div>
          </TabPanel>
        </TabView>
      </template>
    </BaseDialog>

    <BaseDialog
      v-model:isVisible="showCreateDialog"
      :title="t('networkProbes.dialogs.createTitle')"
      :mode="'create'"
      :showFooter="true"
      :showCancel="true"
      :showSubmit="true"
      :width="'42vw'"
      @cancel="closeCreateDialog"
      @submit="createProbe"
    >
      <template #default>
        <div class="grid grid-cols-1 gap-3">
          <div class="field">
            <label class="block text-sm font-medium mb-2">{{ t('common.fields.name') }}</label>
            <InputText v-model="form.name" class="w-full" />
          </div>
        </div>
      </template>
    </BaseDialog>

    <!-- API Key dialog (mostrata SOLO al momento della creazione) -->
    <BaseDialog
      v-model:isVisible="showApiKeyDialog"
      :title="t('networkProbes.dialogs.apiKeyTitle')"
      :mode="'view'"
      :width="'55vw'"
      :showFooter="true"
      :showCancel="true"
      :showSubmit="false"
      :cancelLabel="t('common.actions.close')"
      @cancel="showApiKeyDialog = false"
    >
      <template #default>
        <div class="api-key-dialog">
          <p class="mb-3">
            {{ t('networkProbes.apiKey.description') }}
          </p>
          <Textarea
            v-model="createdApiKey"
            :readonly="true"
            rows="3"
            class="w-full api-key-text"
          />
          <div class="flex justify-content-end mt-3 gap-2">
            <Button
              :label="t('networkProbes.apiKey.copy')"
              icon="pi pi-copy"
              class="p-button-sm"
              @click="copyApiKey"
            />
          </div>

          <div class="mt-4">
            <TabView>
              <TabPanel :header="t('networkProbes.tabs.docker')">
                <div class="field">
                  <label class="block text-sm font-medium mb-2">{{ t('networkProbes.apiKey.probeConf') }}</label>
                  <Textarea :value="probeConfText" :readonly="true" rows="12" class="w-full" />
                </div>
                <div class="field mt-3">
                  <label class="block text-sm font-medium mb-2">{{ t('networkProbes.apiKey.dockerStart') }}</label>
                  <Textarea :value="dockerRunCommand" :readonly="true" rows="5" class="w-full" />
                </div>
              </TabPanel>
              <TabPanel :header="t('networkProbes.tabs.host')">
                <div class="field">
                  <label class="block text-sm font-medium mb-2">{{ t('networkProbes.apiKey.probeConf') }}</label>
                  <Textarea :value="probeConfText" :readonly="true" rows="12" class="w-full" />
                </div>
                <div class="field mt-3">
                  <label class="block text-sm font-medium mb-2">{{ t('networkProbes.apiKey.hostStart') }}</label>
                  <Textarea :value="hostRunCommands" :readonly="true" rows="8" class="w-full" />
                </div>
              </TabPanel>
            </TabView>
          </div>
        </div>
      </template>
    </BaseDialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import Card from 'primevue/card'
import ProgressSpinner from 'primevue/progressspinner'
import Tag from 'primevue/tag'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import InputNumber from 'primevue/inputnumber'
import MultiSelect from 'primevue/multiselect'
import Checkbox from 'primevue/checkbox'
import Message from 'primevue/message'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'

import BaseDataTable from '../components/base/BaseDataTable.vue'
import BaseDialog from '../components/base/BaseDialog.vue'

import api from '../api/api'
import { useApi } from '../composables/useApi'
import { usePermissions } from '../composables/usePermissions'

const { t, locale } = useI18n()
const toast = useToast()
const { canDelete } = usePermissions()
const canManageNetworkProbes = computed(() => canDelete('network_probes'))

const showCreateDialog = ref(false)
const sites = ref([])

const probes = ref([])

const selectedSiteId = ref(null)
const overview = ref(null)

const showApiKeyDialog = ref(false)
const createdApiKey = ref('')
const createdProbeId = ref(null)

const serverUrlForProbe = computed(() => {
  // Usa l'origine da cui stai consultando la console come base per la sonda.
  // Nota: dal lato macchina sonda deve essere raggiungibile questo host.
  try {
    return window.location.origin
  } catch (e) {
    return 'https://your-server.com'
  }
})

const probeContainerName = computed(() => {
  const id = createdProbeId.value ? String(createdProbeId.value).slice(0, 8) : 'unknown'
  return `industrace-probe-${id}`
})

const probeConfText = computed(() => {
  if (!createdApiKey.value || !createdProbeId.value) return ''
  // Impostazioni "safe" per far partire subito la sonda (senza payload cifrati e senza verifica SSL).
  // L'utente puo` poi adattarle tramite edit/proxy per produzione.
  return `[main]
probe_id = ${createdProbeId.value}
api_key = ${createdApiKey.value}
server_url = ${serverUrlForProbe.value}

[network]
interface_name = ${'eth0'}
promiscuous_mode = true
capture_filter =
max_packet_size = 1518
buffer_size = 65536

[analysis]
enabled_protocols =
sampling_rate = 1.0
metadata_extraction = true
payload_analysis = false

[telecontrol]
heartbeat_interval = 30
data_transmission_interval = 300
max_retry_attempts = 3

[security]
encryption_enabled = false
ssl_verify = false
`
})

const dockerRunCommand = computed(() => {
  if (!createdApiKey.value || !createdProbeId.value) return ''
  return t('networkProbes.commands.dockerRun', { containerName: probeContainerName.value })
})

const hostRunCommands = computed(() => {
  if (!createdApiKey.value || !createdProbeId.value) return ''
  return t('networkProbes.commands.hostRun')
})

const showProbeDetailsDialog = ref(false)
const selectedProbe = ref(null)
const probeStatus = ref(null)

const showEditDialog = ref(false)
const editForm = reactive({
  name: '',
  description: '',
  interface_name: 'eth0',
  interface_ip: null,
  capture_filter: null,
  sampling_rate: 1.0,
  heartbeat_interval: 30,
  data_transmission_interval: 300,
  max_retry_attempts: 3,
  metadata_extraction: true,
  payload_analysis: false,
  promiscuous_mode: true,
  enabled_protocols: []
})

const probeApiKeyInput = ref('')
const loadingConfiguration = ref(false)
const probeConfiguration = ref(null)

const form = reactive({
  site_id: null,
  name: '',
  description: '',
  interface_name: 'eth0',
  interface_ip: null
})

const protocolOptions = [
  { label: 'Modbus', value: 'Modbus' },
  { label: 'IEC 104', value: 'IEC 104' },
  { label: 'OPC-UA', value: 'OPC-UA' },
  { label: 'EtherNet/IP', value: 'EtherNet/IP' },
  { label: 'BACnet', value: 'BACnet' },
  { label: 'DNP3', value: 'DNP3' },
  { label: 'KNX', value: 'KNX' },
  { label: 'MQTT', value: 'MQTT' },
  { label: 'HTTP', value: 'HTTP' },
  { label: 'HTTPS', value: 'HTTPS' }
]

const columnOptions = computed(() => [
  { field: 'name', header: t('networkProbes.columns.name') },
  { field: 'interface_name', header: t('networkProbes.columns.interface') },
  { field: 'site_name', header: t('networkProbes.columns.site') },
  { field: 'status', header: t('networkProbes.columns.status') },
  { field: 'last_heartbeat_display', header: t('networkProbes.columns.lastHeartbeat') },
  { field: 'last_data_received_display', header: t('networkProbes.columns.lastData') },
  { field: 'actions', header: t('networkProbes.columns.actions'), sortable: false }
])

const probeDetailsTitle = computed(() => {
  if (selectedProbe.value?.name) {
    return t('networkProbes.details.title', { name: selectedProbe.value.name })
  }
  return t('networkProbes.details.titleDefault')
})

const { loading, execute } = useApi()

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

async function fetchOverview() {
  await execute(async () => {
    const response = await api.getNetworkProbesOverview()
    overview.value = response.data || null
    return response
  }, {
    errorContext: t('common.messages.fetchError'),
    showToast: false
  })
}

async function fetchProbes() {
  await execute(async () => {
    const response = await api.getNetworkProbes(
      selectedSiteId.value ? { site_id: selectedSiteId.value } : {}
    )
    probes.value = response.data || []
    return response
  }, {
    errorContext: t('common.messages.fetchError'),
    showToast: false
  })
}

const formattedProbes = computed(() => {
  const map = {}
  for (const s of sites.value || []) {
    map[s.id] = s.name
  }

  // Formattazione date lato client per una visualizzazione pulita
  return probes.value.map(p => ({
    ...p,
    site_name: map[p.site_id] || '—',
    status: statusLabel(p.status),
    last_heartbeat_display: p.last_heartbeat ? new Date(p.last_heartbeat).toLocaleString(locale.value) : null,
    last_data_received_display: p.last_data_received ? new Date(p.last_data_received).toLocaleString(locale.value) : null
  }))
})

function statusLabel(status) {
  const key = `networkProbes.status.${status}`
  const translated = t(key)
  return translated !== key ? translated : status
}

function formatTs(ts) {
  if (!ts) return '—'
  try {
    return new Date(ts).toLocaleString(locale.value)
  } catch (e) {
    return '—'
  }
}

function getProbeStatusSeverity(statusValue) {
  const s = (statusValue || '').toLowerCase()
  if (s === 'active' || s === 'healthy') return 'success'
  if (s === 'warning') return 'warning'
  if (s === 'error') return 'danger'
  if (s === 'maintenance') return 'info'
  return 'info'
}

const configurationJson = computed(() => {
  if (!probeConfiguration.value) return ''
  try {
    return JSON.stringify(probeConfiguration.value, null, 2)
  } catch (e) {
    return String(probeConfiguration.value)
  }
})

const dataFreshnessClass = computed(() => {
  const ts = selectedProbe.value?.last_data_received
  if (!ts) return 'data-freshness--stale'
  const now = Date.now()
  const diffMs = now - new Date(ts).getTime()
  const diffMin = diffMs / 60000
  if (diffMin <= 2) return 'data-freshness--good'
  if (diffMin <= 5) return 'data-freshness--warn'
  return 'data-freshness--stale'
})

const dataFreshnessText = computed(() => {
  const ts = selectedProbe.value?.last_data_received
  if (!ts) return t('networkProbes.freshness.noRecentData')
  const now = Date.now()
  const diffMin = (now - new Date(ts).getTime()) / 60000
  if (diffMin <= 2) return t('networkProbes.freshness.ok')
  if (diffMin <= 5) return t('networkProbes.freshness.delayed')
  return t('networkProbes.freshness.stale')
})

function openCreateDialog() {
  form.site_id = selectedSiteId.value || (sites.value.length ? sites.value[0].id : null)
  form.name = ''
  form.description = null
  form.interface_name = 'eth0'
  form.interface_ip = null
  showCreateDialog.value = true
}

function closeCreateDialog() {
  showCreateDialog.value = false
}

async function createProbe() {
  if (!form.site_id) {
    toast.add({ severity: 'warn', summary: t('common.messages.warning'), detail: t('networkProbes.messages.selectSite'), life: 3000 })
    return
  }

  await execute(async () => {
    const payload = {
      site_id: form.site_id,
      name: form.name,
      description: form.description || null,
      probe_type: 'network',
      interface_name: form.interface_name,
      interface_ip: form.interface_ip || null
    }

    const response = await api.createNetworkProbe(payload)
    const apiKey = response.data?.api_key

    if (apiKey) {
      toast.add({
        severity: 'success',
        summary: t('common.actions.create'),
        detail: apiKey,
        life: 10000
      })

      createdApiKey.value = apiKey
      createdProbeId.value = response.data?.id || null
      showApiKeyDialog.value = true
    }

    showCreateDialog.value = false
    await fetchProbes()
    await fetchOverview()
    return response
  }, {
    successMessage: null,
    errorContext: t('common.messages.createError'),
    showToast: false
  })
}

function onSiteFilterChange() {
  fetchProbes()
}

function openProbeDetails(probe) {
  selectedProbe.value = probe
  probeStatus.value = null
  probeConfiguration.value = null

  // Se è stata appena creata in questa sessione, possiamo precompilare la API key.
  if (createdProbeId.value && createdProbeId.value === probe.id) {
    probeApiKeyInput.value = createdApiKey.value || ''
  } else {
    probeApiKeyInput.value = ''
  }

  showProbeDetailsDialog.value = true
  fetchProbeStatus(probe.id)
}

async function fetchProbeStatus(probeId) {
  try {
    const response = await api.getNetworkProbeStatus(probeId)
    probeStatus.value = response.data || null
  } catch (err) {
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: t('networkProbes.messages.statusLoadError'),
      life: 5000
    })
  }
}

function openEditProbe(probe) {
  selectedProbe.value = probe

  editForm.name = probe.name || ''
  editForm.description = probe.description || ''
  editForm.interface_name = probe.interface_name || ''
  editForm.interface_ip = probe.interface_ip || null
  editForm.capture_filter = probe.capture_filter || null
  editForm.sampling_rate = probe.sampling_rate ?? 1.0
  editForm.heartbeat_interval = probe.heartbeat_interval ?? 30
  editForm.data_transmission_interval = probe.data_transmission_interval ?? 300
  editForm.max_retry_attempts = probe.max_retry_attempts ?? 3
  editForm.metadata_extraction = probe.metadata_extraction ?? true
  editForm.payload_analysis = probe.payload_analysis ?? false
  editForm.promiscuous_mode = probe.promiscuous_mode ?? true
  editForm.enabled_protocols = Array.isArray(probe.enabled_protocols) ? [...probe.enabled_protocols] : []

  showEditDialog.value = true
}

function closeEditDialog() {
  showEditDialog.value = false
}

async function submitEditProbe() {
  if (!selectedProbe.value) return

  const payload = {
    name: editForm.name,
    description: editForm.description || null,
    probe_type: 'network',
    interface_name: editForm.interface_name,
    interface_ip: editForm.interface_ip || null,
    capture_filter: editForm.capture_filter || null,
    sampling_rate: editForm.sampling_rate,
    heartbeat_interval: editForm.heartbeat_interval,
    data_transmission_interval: editForm.data_transmission_interval,
    max_retry_attempts: editForm.max_retry_attempts,
    metadata_extraction: editForm.metadata_extraction,
    payload_analysis: editForm.payload_analysis,
    promiscuous_mode: editForm.promiscuous_mode,
    enabled_protocols: editForm.enabled_protocols
  }

  await execute(async () => {
    const response = await api.updateNetworkProbe(selectedProbe.value.id, payload)
    return response
  }, {
    successMessage: t('networkProbes.messages.updated'),
    errorContext: t('common.messages.updateError'),
    showToast: true
  })

  showEditDialog.value = false
  await fetchProbes()
  await fetchOverview()
}

async function deauthorizeProbe(probe) {
  if (!probe?.id) return
  const ok = window.confirm(t('networkProbes.dialogs.deauthorizeConfirm', { name: probe.name }))
  if (!ok) return

  await execute(async () => {
    const response = await api.deauthorizeNetworkProbe(probe.id)
    return response
  }, {
    successMessage: t('networkProbes.messages.deauthorized'),
    errorContext: t('common.messages.updateError'),
    showToast: true
  })

  // Se stiamo guardando i dettagli della stessa sonda, invalidiamo eventuale config in cache
  if (selectedProbe.value?.id === probe.id) {
    probeConfiguration.value = null
    probeApiKeyInput.value = ''
  }

  await fetchProbes()
  await fetchOverview()
}

async function deleteProbe(probe) {
  if (!probe?.id) return
  const ok = window.confirm(t('networkProbes.dialogs.deleteConfirm', { name: probe.name }))
  if (!ok) return

  await execute(async () => {
    const response = await api.deleteNetworkProbe(probe.id)
    return response
  }, {
    successMessage: t('networkProbes.messages.deleted'),
    errorContext: t('common.messages.deleteError'),
    showToast: true
  })

  if (selectedProbe.value?.id === probe.id) {
    showProbeDetailsDialog.value = false
    selectedProbe.value = null
    probeStatus.value = null
  }

  await fetchProbes()
  await fetchOverview()
}

async function fetchProbeConfiguration() {
  if (!selectedProbe.value) return
  if (!probeApiKeyInput.value) return

  loadingConfiguration.value = true
  probeConfiguration.value = null

  try {
    const response = await api.getNetworkProbeConfiguration(selectedProbe.value.id, probeApiKeyInput.value)
    probeConfiguration.value = response.data || null
  } catch (err) {
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: t('networkProbes.messages.invalidApiKey'),
      life: 7000
    })
  } finally {
    loadingConfiguration.value = false
  }
}

const healthClass = computed(() => {
  const hp = overview.value?.health_percentage ?? 0
  if (hp >= 70) return 'health-circle--good'
  if (hp >= 40) return 'health-circle--warn'
  return 'health-circle--bad'
})

async function copyApiKey() {
  try {
    await navigator.clipboard.writeText(createdApiKey.value || '')
    toast.add({
      severity: 'success',
      summary: t('common.messages.success'),
      detail: t('networkProbes.apiKey.copied'),
      life: 3000
    })
  } catch (e) {
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: t('networkProbes.apiKey.copyFailed'),
      life: 5000
    })
  }
}

onMounted(async () => {
  await fetchSites()
  if (sites.value.length === 1) selectedSiteId.value = sites.value[0].id
  await fetchOverview()
  await fetchProbes()
})
</script>

<style scoped>
.network-probes-page .page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.overview-loading {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin: 1.5rem 0;
  justify-content: center;
  flex-direction: column;
}

.overview-loading-label {
  color: var(--text-color, #6b7280);
}

.overview-section {
  margin-bottom: 1.25rem;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(180px, 1fr));
  gap: 1rem;
}

@media (max-width: 960px) {
  .overview-grid {
    grid-template-columns: repeat(2, minmax(180px, 1fr));
  }
}

.overview-card {
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
}

.overview-item {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.overview-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.overview-icon--total {
  background: #3b82f6;
}

.overview-icon--active {
  background: #22c55e;
}

.overview-icon--error {
  background: #ef4444;
}

.overview-icon--health {
  background: #f59e0b;
}

.overview-value {
  font-size: 1.8rem;
  font-weight: 700;
}

.overview-label {
  margin-top: 0.1rem;
  color: var(--text-color, #6b7280);
  font-size: 0.95rem;
}

.health-item {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.health-circle {
  width: 72px;
  height: 72px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid transparent;
}

.health-circle--good {
  border-color: #22c55e;
  color: #22c55e;
  background: rgba(34, 197, 94, 0.12);
}

.health-circle--warn {
  border-color: #f59e0b;
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.12);
}

.health-circle--bad {
  border-color: #ef4444;
  color: #ef4444;
  background: rgba(239, 68, 68, 0.12);
}

.health-value {
  font-weight: 800;
  font-size: 1.25rem;
}

.overview-subtitle {
  margin-top: 0.15rem;
  font-size: 0.85rem;
  color: var(--text-color, #6b7280);
}

.empty-probes {
  padding: 2rem 1.25rem;
  border: 1px dashed var(--surface-border, #e5e7eb);
  border-radius: 12px;
  text-align: center;
  margin-bottom: 1rem;
}

.empty-icon {
  font-size: 2.5rem;
  color: #94a3b8;
  margin-bottom: 0.75rem;
  display: inline-block;
}

.api-key-dialog {
  line-height: 1.4;
}

.api-key-text {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
}

.probe-details {
  padding: 0.25rem 0;
}

.detail-card {
  border: 1px solid var(--surface-border, #e5e7eb);
  border-radius: 12px;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.02);
}

.detail-label {
  font-size: 0.85rem;
  color: var(--text-color, #6b7280);
  margin-bottom: 0.35rem;
}

.detail-value {
  font-size: 1.05rem;
  font-weight: 600;
}

.detail-sub {
  margin-top: 0.35rem;
  font-size: 0.85rem;
}

.data-freshness--good {
  color: #22c55e;
}

.data-freshness--warn {
  color: #f59e0b;
}

.data-freshness--stale {
  color: #ef4444;
}

.config-section-title {
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.config-hint {
  color: var(--text-color, #6b7280);
  font-size: 0.9rem;
  margin-bottom: 0.75rem;
}

.config-row {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  margin-bottom: 0.75rem;
}

@media (max-width: 900px) {
  .config-row {
    flex-direction: column;
    align-items: stretch;
  }
}

.config-pre {
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--surface-border, #e5e7eb);
  border-radius: 12px;
  padding: 1rem;
  overflow: auto;
  max-height: 420px;
  font-size: 0.85rem;
  line-height: 1.4;
}

.config-empty {
  color: var(--text-color, #6b7280);
  padding: 0.5rem 0;
}
</style>

