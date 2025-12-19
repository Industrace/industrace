<template>
  <div class="vulnerabilities-page">
    <div class="page-header mb-4">
      <h1>{{ t('vulnerabilities.title') }}</h1>
      <p class="page-description">
        {{ t('vulnerabilities.pageDescription') }}
      </p>
    </div>

    <!-- Filters -->
    <Card class="mb-4">
      <template #content>
        <div class="filters-grid">
          <div class="filter-item">
            <label>{{ t('vulnerabilities.severity') }}</label>
            <Dropdown
              v-model="filters.severity"
              :options="severityOptions"
              optionLabel="label"
              optionValue="value"
              :placeholder="t('vulnerabilities.allSeverities')"
              showClear
              class="w-full"
            />
          </div>
          <div class="filter-item">
            <label>{{ t('vulnerabilities.source') }}</label>
            <Dropdown
              v-model="filters.source"
              :options="sourceOptions"
              optionLabel="label"
              optionValue="value"
              :placeholder="t('vulnerabilities.allSources')"
              showClear
              class="w-full"
            />
          </div>
          <div class="filter-item">
            <label>{{ t('vulnerabilities.publishedFrom') }}</label>
            <Calendar
              v-model="filters.publishedFrom"
              :showIcon="true"
              dateFormat="yy-mm-dd"
              :maxDate="filters.publishedTo || new Date()"
              class="w-full"
            />
          </div>
          <div class="filter-item">
            <label>{{ t('vulnerabilities.publishedTo') }}</label>
            <Calendar
              v-model="filters.publishedTo"
              :showIcon="true"
              dateFormat="yy-mm-dd"
              :minDate="filters.publishedFrom"
              :maxDate="new Date()"
              class="w-full"
            />
          </div>
          <div class="filter-item">
            <label>{{ t('vulnerabilities.cvssMin') }}</label>
            <InputNumber
              v-model="filters.cvssMin"
              :min="0"
              :max="10"
              :step="0.1"
              :placeholder="t('vulnerabilities.min')"
              class="w-full"
            />
          </div>
          <div class="filter-item">
            <label>{{ t('vulnerabilities.cvssMax') }}</label>
            <InputNumber
              v-model="filters.cvssMax"
              :min="0"
              :max="10"
              :step="0.1"
              :placeholder="t('vulnerabilities.max')"
              class="w-full"
            />
          </div>
        </div>
        <div class="filter-actions mt-3">
          <Button 
            :label="t('common.actions.search')" 
            icon="pi pi-search" 
            @click="applyFilters"
          />
          <Button 
            :label="t('common.actions.clear')" 
            icon="pi pi-times" 
            @click="clearFilters"
            class="p-button-text"
          />
        </div>
      </template>
    </Card>

    <!-- Statistics Cards -->
    <div class="stats-grid mb-4">
      <Card>
        <template #content>
          <div class="stat-card">
            <div class="stat-value">{{ stats.total_vulnerabilities || 0 }}</div>
            <div class="stat-label">{{ t('vulnerabilities.total') }}</div>
          </div>
        </template>
      </Card>
      <Card>
        <template #content>
          <div class="stat-card">
            <div class="stat-value text-red-500">{{ stats.by_severity?.critical || 0 }}</div>
            <div class="stat-label">{{ t('vulnerabilities.critical') }}</div>
          </div>
        </template>
      </Card>
      <Card>
        <template #content>
          <div class="stat-card">
            <div class="stat-value text-orange-500">{{ stats.by_severity?.high || 0 }}</div>
            <div class="stat-label">{{ t('vulnerabilities.high') }}</div>
          </div>
        </template>
      </Card>
      <Card>
        <template #content>
          <div class="stat-card">
            <div class="stat-value text-blue-500">{{ stats.by_severity?.medium || 0 }}</div>
            <div class="stat-label">{{ t('vulnerabilities.medium') }}</div>
          </div>
        </template>
      </Card>
      <Card>
        <template #content>
          <div class="stat-card">
            <div class="stat-value text-green-500">{{ stats.by_severity?.low || 0 }}</div>
            <div class="stat-label">{{ t('vulnerabilities.low') }}</div>
          </div>
        </template>
      </Card>
    </div>

    <!-- Vulnerabilities Table -->
    <Card>
      <template #content>
        <DataTable 
          :value="vulnerabilities" 
          :loading="loading"
          :paginator="true"
          :rows="rowsPerPage"
          :totalRecords="totalRecords"
          :rowsPerPageOptions="[50, 100, 200, 500]"
          :lazy="true"
          @page="onPage"
          @sort="onSort"
          :emptyMessage="t('vulnerabilities.noVulnerabilities')"
          :sortField="sortField"
          :sortOrder="sortOrder"
          class="p-datatable-sm"
        >
          <template #header>
            <div class="table-header">
              <span class="p-input-icon-left">
                <i class="pi pi-search" />
                <InputText 
                  v-model="globalFilter" 
                  :placeholder="t('common.actions.search')"
                  @input="onGlobalFilter"
                />
              </span>
            </div>
          </template>

          <Column field="cve_id" :header="t('vulnerabilities.cveId')" sortable>
            <template #body="{ data }">
              <a 
                v-if="data.cve_id" 
                :href="`https://nvd.nist.gov/vuln/detail/${data.cve_id}`" 
                target="_blank" 
                class="cve-link"
              >
                {{ data.cve_id }}
              </a>
              <span v-else>{{ data.title }}</span>
            </template>
          </Column>

          <Column field="title" :header="t('vulnerabilities.title')" sortable>
            <template #body="{ data }">
              <div class="vuln-title">
                {{ data.title }}
                <Button 
                  icon="pi pi-external-link" 
                  class="p-button-text p-button-sm ml-2"
                  @click="viewDetail(data.id)"
                  v-tooltip.top="t('vulnerabilities.viewDetail')"
                />
              </div>
            </template>
          </Column>

          <Column field="severity" :header="t('vulnerabilities.severity')" sortable>
            <template #body="{ data }">
              <Tag 
                :value="data.severity" 
                :severity="getSeveritySeverity(data.severity)" 
              />
            </template>
          </Column>

          <Column field="cvss_v3_score" :header="t('vulnerabilities.cvssScore')" sortable>
            <template #body="{ data }">
              {{ data.cvss_v3_score || data.cvss_v2_score || '-' }}
            </template>
          </Column>

          <Column field="source" :header="t('vulnerabilities.source')" sortable>
            <template #body="{ data }">
              <Tag :value="data.source.toUpperCase()" severity="secondary" />
            </template>
          </Column>

          <Column field="published_date" :header="t('vulnerabilities.publishedDate')" sortable>
            <template #body="{ data }">
              {{ formatDate(data.published_date) }}
            </template>
          </Column>

          <Column field="affected_assets_count" :header="t('vulnerabilities.affectedAssets')" sortable>
            <template #body="{ data }">
              <Button 
                :label="(data.affected_assets_count || 0).toString()" 
                icon="pi pi-link"
                class="p-button-text p-button-sm"
                @click="viewAffectedAssets(data.id)"
                :disabled="(data.affected_assets_count || 0) === 0"
              />
            </template>
          </Column>

          <Column :header="t('common.strings.actions')">
            <template #body="{ data }">
              <Button 
                icon="pi pi-eye" 
                class="p-button-rounded p-button-text" 
                @click="viewDetail(data.id)"
                v-tooltip.top="t('vulnerabilities.viewDetail')"
              />
            </template>
          </Column>
        </DataTable>
      </template>
    </Card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useToast } from 'primevue/usetoast'
import Card from 'primevue/card'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Dropdown from 'primevue/dropdown'
import Calendar from 'primevue/calendar'
import InputNumber from 'primevue/inputnumber'
import InputText from 'primevue/inputtext'
import api from '@/api/api'

const { t } = useI18n()
const router = useRouter()
const toast = useToast()

const vulnerabilities = ref([])
const loading = ref(false)
const stats = ref({})
const globalFilter = ref('')
const totalRecords = ref(0)
const currentPage = ref(0)
const rowsPerPage = ref(100)
const sortField = ref(null)
const sortOrder = ref(null)
let searchTimeout = null

const filters = ref({
  severity: null,
  source: null,
  publishedFrom: null,
  publishedTo: null,
  cvssMin: null,
  cvssMax: null
})

const severityOptions = [
  { label: t('vulnerabilities.critical'), value: 'critical' },
  { label: t('vulnerabilities.high'), value: 'high' },
  { label: t('vulnerabilities.medium'), value: 'medium' },
  { label: t('vulnerabilities.low'), value: 'low' }
]

const sourceOptions = [
  { label: 'NVD', value: 'nvd' },
  { label: 'ICS-CERT', value: 'ics-cert' },
  { label: 'CISA', value: 'cisa' },
  { label: t('vulnerabilities.vendor'), value: 'vendor' },
  { label: t('vulnerabilities.custom'), value: 'custom' }
]


async function fetchVulnerabilities() {
  loading.value = true
  try {
    const params = {
      skip: currentPage.value * rowsPerPage.value,
      limit: rowsPerPage.value
    }
    if (filters.value.severity) params.severity = filters.value.severity
    if (filters.value.source) params.source = filters.value.source
    if (globalFilter.value && globalFilter.value.trim()) {
      params.search = globalFilter.value.trim()
    }
    if (sortField.value) {
      params.sort_field = sortField.value
      params.sort_order = sortOrder.value === 1 ? 'asc' : 'desc'
    }
    
    const res = await api.getVulnerabilities(params)
    
    // Handle both old format (array) and new format (object with items and total)
    if (Array.isArray(res.data)) {
      vulnerabilities.value = res.data
      // Estimate total if not provided
      if (vulnerabilities.value.length < rowsPerPage.value) {
        totalRecords.value = currentPage.value * rowsPerPage.value + vulnerabilities.value.length
      } else {
        totalRecords.value = (currentPage.value + 1) * rowsPerPage.value + 1
      }
    } else if (res.data && res.data.items) {
      vulnerabilities.value = res.data.items || []
      totalRecords.value = res.data.total || 0
    } else {
      vulnerabilities.value = []
      totalRecords.value = 0
    }
  } catch (error) {
    console.error('Error fetching vulnerabilities:', error)
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: t('vulnerabilities.errorLoading'),
      life: 3000
    })
  } finally {
    loading.value = false
  }
}

async function fetchStats() {
  try {
    const res = await api.getVulnerabilityStats()
    stats.value = res.data || {}
  } catch (error) {
    console.error('Error fetching stats:', error)
  }
}

function onPage(event) {
  currentPage.value = event.page
  rowsPerPage.value = event.rows
  fetchVulnerabilities()
}

function onSort(event) {
  // Handle server-side sorting
  // PrimeVue passes: { sortField: string, sortOrder: number (1=asc, -1=desc) }
  if (event && event.sortField) {
    sortField.value = event.sortField
    sortOrder.value = event.sortOrder // 1 for asc, -1 for desc
  } else {
    sortField.value = null
    sortOrder.value = null
  }
  // Reset to first page when sorting changes
  currentPage.value = 0
  fetchVulnerabilities()
}

function applyFilters() {
  fetchVulnerabilities()
}

function clearFilters() {
  filters.value = {
    severity: null,
    source: null,
    publishedFrom: null,
    publishedTo: null,
    cvssMin: null,
    cvssMax: null
  }
  globalFilter.value = ''
  fetchVulnerabilities()
}

function onGlobalFilter() {
  // Debounce search to avoid too many API calls
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = setTimeout(() => {
    // Reset to first page when searching
    currentPage.value = 0
    fetchVulnerabilities()
  }, 500) // 500ms debounce
}

function viewDetail(vulnerabilityId) {
  router.push(`/vulnerabilities/${vulnerabilityId}`)
}

function viewAffectedAssets(vulnerabilityId) {
  // Navigate to vulnerability detail with assets tab
  router.push(`/vulnerabilities/${vulnerabilityId}?tab=assets`)
}

function formatDate(dateString) {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString()
}

function getSeveritySeverity(severity) {
  const severityMap = {
    'critical': 'danger',
    'high': 'warning',
    'medium': 'info',
    'low': 'success'
  }
  return severityMap[severity] || null
}

onMounted(() => {
  fetchVulnerabilities()
  fetchStats()
})
</script>

<style scoped>
.vulnerabilities-page {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header h1 {
  margin: 0 0 0.5rem 0;
}

.page-description {
  color: var(--text-color-secondary);
  margin: 0;
}

.filters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-item label {
  font-weight: 600;
  font-size: 0.875rem;
}

.filter-actions {
  display: flex;
  gap: 0.5rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.stat-card {
  text-align: center;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
}

.stat-label {
  color: var(--text-color-secondary);
  margin-top: 0.5rem;
  font-size: 0.875rem;
}

.table-header {
  display: flex;
  justify-content: flex-end;
}

.cve-link {
  color: var(--primary-color);
  text-decoration: none;
}

.cve-link:hover {
  text-decoration: underline;
}

.vuln-title {
  display: flex;
  align-items: center;
}
</style>

