<template>
  <div class="compliance-page">
    <div class="page-header">
      <h1>{{ t('isa62443.compliance.title') }}</h1>
      <p class="text-muted">{{ t('isa62443.compliance.description') }}</p>
    </div>

    <Message severity="info" class="mb-4" :closable="true">
      {{ t('isa62443.compliance.scopeBanner') }}
    </Message>

    <!-- Overview Cards -->
    <div class="grid mb-4">
      <div class="col-12 md:col-3">
        <Card>
          <template #content>
            <div class="stat-card">
              <div class="stat-value">{{ zonesSummary.total }}</div>
              <div class="stat-label">{{ t('isa62443.compliance.totalZones') }}</div>
            </div>
          </template>
        </Card>
      </div>
      <div class="col-12 md:col-3">
        <Card>
          <template #content>
            <div class="stat-card">
              <div class="stat-value text-green-500">{{ zonesSummary.compliant }}</div>
              <div class="stat-label">{{ t('isa62443.compliance.compliantZones') }}</div>
            </div>
          </template>
        </Card>
      </div>
      <div class="col-12 md:col-3">
        <Card>
          <template #content>
            <div class="stat-card">
              <div class="stat-value text-orange-500">{{ zonesSummary.partial }}</div>
              <div class="stat-label">{{ t('isa62443.compliance.partialZones') }}</div>
            </div>
          </template>
        </Card>
      </div>
      <div class="col-12 md:col-3">
        <Card>
          <template #content>
            <div class="stat-card">
              <div class="stat-value text-red-500">{{ zonesSummary.nonCompliant }}</div>
              <div class="stat-label">{{ t('isa62443.compliance.nonCompliantZones') }}</div>
            </div>
          </template>
        </Card>
      </div>
    </div>

    <TabView class="mt-4">
      <!-- Gap Analysis Tab -->
      <TabPanel>
        <template #header>
          <span style="display: flex; align-items: center; gap: 0.4em;">
            <i class="pi pi-chart-line"></i> {{ t('isa62443.compliance.gapAnalysis') }}
          </span>
        </template>
        
        <div v-if="gapAnalysisLoading" class="text-center p-4">
          <ProgressSpinner />
        </div>
        
        <div v-else-if="gapAnalysis.length === 0" class="text-center p-4">
          <p>{{ t('isa62443.compliance.noZones') }}</p>
        </div>
        
        <DataTable 
          v-else
          :value="gapAnalysis" 
          :loading="gapAnalysisLoading"
          :paginator="true"
          :rows="20"
          class="p-datatable-sm"
        >
          <Column field="zone_name" :header="t('isa62443.securityZones.title')" sortable>
            <template #body="{ data }">
              <a 
                v-if="data.zone_id"
                @click="goToZoneDetail(data.zone_id)" 
                class="zone-link"
                :title="t('isa62443.securityZones.viewDetails')"
              >
                {{ data.zone_name }}
              </a>
              <span v-else>{{ data.zone_name }}</span>
            </template>
          </Column>
          <Column :header="t('isa62443.compliance.securityLevelTarget')">
            <template #body="{ data }">
              <span v-if="data.security_level_target">SL-{{ data.security_level_target }}</span>
              <span v-else class="text-muted">-</span>
            </template>
          </Column>
          <Column :header="t('isa62443.compliance.securityLevelAchieved')">
            <template #body="{ data }">
              <span v-if="data.security_level_achieved">SL-{{ data.security_level_achieved }}</span>
              <span v-else class="text-muted">-</span>
            </template>
          </Column>
          <Column :header="t('isa62443.compliance.gap')">
            <template #body="{ data }">
              <Badge 
                v-if="data.gap !== null && data.gap !== undefined"
                :value="data.gap > 0 ? `-${data.gap}` : '0'"
                :severity="data.gap > 0 ? 'danger' : 'success'"
              />
              <span v-else class="text-muted">-</span>
            </template>
          </Column>
          <Column field="compliance_status" :header="t('isa62443.compliance.status')">
            <template #body="{ data }">
              <Badge 
                :value="getComplianceStatusLabel(data.compliance_status)"
                :severity="getComplianceSeverity(data.compliance_status)"
              />
            </template>
          </Column>
          <Column :header="t('isa62443.compliance.nonCompliantCount')">
            <template #body="{ data }">
              <span v-if="data.non_compliant_count > 0" class="text-red-500 font-bold">
                {{ data.non_compliant_count }}
              </span>
              <span v-else class="text-green-500">0</span>
            </template>
          </Column>
          <Column :header="t('isa62443.compliance.missingRequirements')">
            <template #body="{ data }">
              <span v-if="data.missing_requirements_count > 0" class="text-orange-500 font-bold">
                {{ data.missing_requirements_count }}
              </span>
              <span v-else class="text-green-500">0</span>
            </template>
          </Column>
        </DataTable>
      </TabPanel>

      <!-- Security Requirements Reference Tab -->
      <TabPanel>
        <template #header>
          <span style="display: flex; align-items: center; gap: 0.4em;">
            <i class="pi pi-list"></i> {{ t('isa62443.compliance.requirements') }}
          </span>
        </template>
        
        <div class="mb-3">
          <InputText 
            v-model="requirementsFilter"
            :placeholder="t('common.actions.search')"
            class="w-full"
          />
        </div>

        <DataTable 
          :value="filteredRequirements" 
          :loading="loading"
          :emptyMessage="t('isa62443.compliance.noRequirements')"
          :paginator="true"
          :rows="20"
          class="p-datatable-sm"
        >
          <Column field="requirement_id" :header="t('isa62443.compliance.requirementId')" sortable />
          <Column field="title" :header="t('common.fields.name')" sortable />
          <Column field="requirement_category" :header="t('isa62443.compliance.category')" sortable />
          <Column :header="t('isa62443.compliance.appliesTo')">
            <template #body="{ data }">
              <div class="flex gap-2">
                <Badge v-if="data.applies_to_zones" value="Zones" severity="info" />
                <Badge v-if="data.applies_to_conduits" value="Conduits" severity="info" />
                <Badge v-if="data.applies_to_assets" value="Assets" severity="info" />
              </div>
            </template>
          </Column>
          <Column :header="t('isa62443.compliance.securityLevel')">
            <template #body="{ data }">
              <span v-if="data.min_security_level">
                SL-{{ data.min_security_level }}
                <span v-if="data.max_security_level"> - SL-{{ data.max_security_level }}</span>
                <span v-else>+</span>
              </span>
              <span v-else class="text-muted">-</span>
            </template>
          </Column>
        </DataTable>
      </TabPanel>
    </TabView>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Card from 'primevue/card'
import Badge from 'primevue/badge'
import InputText from 'primevue/inputtext'
import ProgressSpinner from 'primevue/progressspinner'
import Message from 'primevue/message'
import api from '@/api/api'

const { t } = useI18n()
const router = useRouter()
const toast = useToast()

// Data
const requirements = ref([])
const gapAnalysis = ref([])
const loading = ref(false)
const gapAnalysisLoading = ref(false)
const requirementsFilter = ref('')

// Computed
const filteredRequirements = computed(() => {
  if (!requirementsFilter.value) return requirements.value
  const filter = requirementsFilter.value.toLowerCase()
  return requirements.value.filter(req => 
    req.requirement_id?.toLowerCase().includes(filter) ||
    req.title?.toLowerCase().includes(filter) ||
    req.requirement_category?.toLowerCase().includes(filter)
  )
})

const zonesSummary = computed(() => {
  const total = gapAnalysis.value.length
  const compliant = gapAnalysis.value.filter(z => z.compliance_status === 'compliant').length
  const partial = gapAnalysis.value.filter(z => z.compliance_status === 'partial').length
  const nonCompliant = gapAnalysis.value.filter(z => z.compliance_status === 'non_compliant').length
  
  return { total, compliant, partial, nonCompliant }
})

// Methods
function getComplianceStatusLabel(status) {
  const labels = {
    'compliant': t('isa62443.compliance.compliant'),
    'non_compliant': t('isa62443.compliance.nonCompliant'),
    'partial': t('isa62443.compliance.partial'),
    'not_assessed': t('isa62443.compliance.notAssessed'),
    'not_applicable': t('isa62443.compliance.notApplicable')
  }
  return labels[status] || status
}

function getComplianceSeverity(status) {
  const severities = {
    'compliant': 'success',
    'non_compliant': 'danger',
    'partial': 'warning',
    'not_assessed': 'info',
    'not_applicable': 'secondary'
  }
  return severities[status] || 'info'
}

async function fetchRequirements() {
  loading.value = true
  try {
    const res = await api.getSecurityRequirements()
    requirements.value = res.data || []
  } catch (error) {
    console.error('Error fetching requirements:', error)
    console.error('Error details:', error.response?.data)
    toast.add({ 
      severity: 'error', 
      summary: t('common.messages.error'), 
      detail: error.response?.data?.detail || t('isa62443.compliance.errorLoading') 
    })
  } finally {
    loading.value = false
  }
}

async function fetchGapAnalysis() {
  gapAnalysisLoading.value = true
  try {
    const res = await api.getGapAnalysis()
    // Backend returns { zones: [...], summary: {...} }
    if (res.data?.zones) {
      gapAnalysis.value = res.data.zones
    } else if (Array.isArray(res.data)) {
      gapAnalysis.value = res.data
    } else {
      gapAnalysis.value = []
    }
  } catch (error) {
    console.error('Error fetching gap analysis:', error)
    // Se non ci sono zone, non è un errore critico
    if (error.response?.status === 404 || error.response?.status === 400) {
      gapAnalysis.value = []
    } else {
      toast.add({ 
        severity: 'error', 
        summary: t('common.messages.error'), 
        detail: error.response?.data?.detail || error.message || t('isa62443.compliance.errorLoading') 
      })
    }
  } finally {
    gapAnalysisLoading.value = false
  }
}

function goToZoneDetail(zoneId) {
  router.push(`/security-zones/${zoneId}`)
}

onMounted(async () => {
  try {
    // Fetch requirements and gap analysis in parallel
    await Promise.all([
      fetchRequirements(),
      fetchGapAnalysis()
    ])
  } catch (error) {
    console.error('Error during page initialization:', error)
  }
})
</script>

<style scoped>
.compliance-page {
  padding: 1.5rem;
}

.page-header {
  margin-bottom: 1.5rem;
}

.text-muted {
  color: var(--text-color-secondary);
}

.stat-card {
  text-align: center;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.stat-label {
  color: var(--text-color-secondary);
  font-size: 0.9rem;
}

.zone-link {
  color: var(--primary-color);
  text-decoration: none;
  cursor: pointer;
  font-weight: 500;
}

.zone-link:hover {
  text-decoration: underline;
}

</style>
