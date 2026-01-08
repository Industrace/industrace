<template>
  <div class="asset-vulnerabilities-tab">
    <!-- Banner Warning: These are candidate associations, not confirmed matches -->
    <div class="warning-banner mb-3 p-3 border-round" style="background: var(--yellow-50); border: 1px solid var(--yellow-300);">
      <i class="pi pi-exclamation-triangle mr-2" style="color: var(--yellow-600);"></i>
      <span style="color: var(--yellow-900); font-weight: 500;">{{ t('vulnerabilities.candidateWarning') }}</span>
    </div>

    <!-- Auto-discovery in progress indicator -->
    <div v-if="matchingInProgress" class="matching-indicator mb-3 p-3 border-round" style="background: var(--blue-50); border: 1px solid var(--blue-200);">
      <i class="pi pi-spin pi-spinner mr-2"></i>
      <span>{{ t('vulnerabilities.autoDiscoveryInProgress') }}</span>
    </div>

    <div class="flex justify-content-between align-items-center mb-3">
      <h3 class="m-0">{{ t('vulnerabilities.potentiallyRelevant') }}</h3>
      <Button 
        :label="t('vulnerabilities.matchVulnerabilities')" 
        icon="pi pi-search" 
        :loading="matchingInProgress"
        @click="matchVulnerabilities"
        v-if="canWrite"
      />
    </div>

    <DataTable 
      :value="vulnerabilities" 
      :loading="loading"
      :emptyMessage="t('vulnerabilities.noVulnerabilities')"
      :paginator="true"
      :rows="20"
      class="p-datatable-sm"
    >
      <Column field="vulnerability.cve_id" :header="t('vulnerabilities.cveId')" sortable>
        <template #body="{ data }">
          <div class="cve-cell">
            <div v-if="data.vulnerability.cve_id" class="cve-id-row">
              <a :href="`https://nvd.nist.gov/vuln/detail/${data.vulnerability.cve_id}`" target="_blank" class="cve-link">
                {{ data.vulnerability.cve_id }}
              </a>
            </div>
            <div v-if="data.vulnerability.title" class="cve-title-row">
              <span class="cve-title">{{ data.vulnerability.title }}</span>
            </div>
            <div v-else-if="!data.vulnerability.cve_id" class="cve-title-row">
              <span class="cve-title">{{ t('vulnerabilities.noTitle') }}</span>
            </div>
          </div>
        </template>
      </Column>
      <Column field="vulnerability.severity" :header="t('vulnerabilities.severity')" sortable>
        <template #body="{ data }">
          <Tag 
            :value="data.vulnerability.severity" 
            :severity="getSeveritySeverity(data.vulnerability.severity)" 
          />
        </template>
      </Column>
      <Column field="vulnerability.cvss_v3_score" :header="t('vulnerabilities.cvssScore')" sortable>
        <template #body="{ data }">
          {{ data.vulnerability.cvss_v3_score || '-' }}
        </template>
      </Column>
      <Column field="status" :header="t('vulnerabilities.status')" sortable>
        <template #body="{ data }">
          <Tag 
            :value="getStatusLabel(data.status)" 
            :severity="getStatusSeverity(data.status)" 
          />
        </template>
      </Column>
      <Column field="match_confidence" :header="t('vulnerabilities.relevanceScore')">
        <template #body="{ data }">
          {{ data.match_confidence ? `${(data.match_confidence * 100).toFixed(0)}%` : '-' }}
        </template>
      </Column>
      <Column :header="t('common.strings.actions')">
        <template #body="{ data }">
          <Button 
            icon="pi pi-pencil" 
            class="p-button-rounded p-button-text" 
            @click="editVulnerability(data)" 
            v-if="canWrite"
          />
        </template>
      </Column>
    </DataTable>

    <!-- Edit Vulnerability Dialog -->
    <VulnerabilityEditDialog
      v-model:visible="editDialogVisible"
      :vulnerability="selectedVulnerability"
      :assetId="assetId"
      @saved="handleVulnerabilitySaved"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import api from '@/api/api'
import VulnerabilityEditDialog from '@/components/features/vulnerabilities/VulnerabilityEditDialog.vue'

const props = defineProps({
  assetId: { type: [String, Number], required: true },
  canWrite: { type: Boolean, default: false }
})

const emit = defineEmits(['updated'])
const { t } = useI18n()
const toast = useToast()

const vulnerabilities = ref([])
const loading = ref(false)
const matchingInProgress = ref(false)
const editDialogVisible = ref(false)
const selectedVulnerability = ref(null)

const getSeveritySeverity = (severity) => {
  const severityMap = {
    'critical': 'danger',
    'high': 'warning',
    'medium': 'info',
    'low': 'success'
  }
  return severityMap[severity] || null
}

const getStatusLabel = (status) => {
  const labels = {
    'unreviewed': t('vulnerabilities.statuses.unreviewed'),
    'acknowledged': t('vulnerabilities.statuses.acknowledged'),
    'not_applicable': t('vulnerabilities.statuses.notApplicable'),
    'mitigated': t('vulnerabilities.statuses.mitigated'),
    'patched': t('vulnerabilities.statuses.patched')
  }
  return labels[status] || status
}

const getStatusSeverity = (status) => {
  const severityMap = {
    'unreviewed': 'warning',
    'acknowledged': 'info',
    'not_applicable': 'success',
    'mitigated': 'warning',
    'patched': 'success'
  }
  return severityMap[status] || null
}

async function fetchVulnerabilities() {
  loading.value = true
  try {
    const res = await api.getAssetVulnerabilities(props.assetId)
    vulnerabilities.value = res.data || []
  } catch (error) {
    console.error('Error fetching vulnerabilities:', error)
    toast.add({ severity: 'error', summary: t('common.errors.error'), detail: t('vulnerabilities.errorLoading') })
  } finally {
    loading.value = false
  }
}

async function matchVulnerabilities() {
  matchingInProgress.value = true
  try {
    await api.matchVulnerabilitiesToAsset(props.assetId)
    toast.add({ 
      severity: 'success', 
      summary: t('common.messages.success'), 
      detail: t('vulnerabilities.matchSuccess') 
    })
    // Ricarica le vulnerabilità dopo il matching
    await fetchVulnerabilities()
    emit('updated')
  } catch (error) {
    console.error('Error matching vulnerabilities:', error)
    toast.add({ 
      severity: 'error', 
      summary: t('common.errors.error'), 
      detail: t('vulnerabilities.errorMatching') 
    })
  } finally {
    matchingInProgress.value = false
  }
}

function editVulnerability(vuln) {
  selectedVulnerability.value = vuln
  editDialogVisible.value = true
}

function handleVulnerabilitySaved() {
  fetchVulnerabilities()
  emit('updated')
}

onMounted(async () => {
  await fetchVulnerabilities()
})

watch(() => props.assetId, async (newId, oldId) => {
  if (newId !== oldId) {
    await fetchVulnerabilities()
  }
})
</script>

<style scoped>
.cve-cell {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.cve-id-row {
  font-weight: 600;
}

.cve-link {
  color: var(--primary-color);
  text-decoration: none;
}

.cve-link:hover {
  text-decoration: underline;
}

.cve-title-row {
  font-size: 0.875rem;
  color: var(--text-color-secondary);
}

.cve-title {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
}
</style>

