<template>
  <div class="dashboard">
    <!-- Header con benvenuto e azioni rapide -->
    <div class="dashboard-header">
      <div class="header-content">
        <h1>{{ t('dashboard.title') }}</h1>
        <p class="welcome-text">{{ t('dashboard.welcome') }}</p>
      </div>
      <div class="quick-actions">
        <Button 
          :label="t('dashboard.actions.viewAllAssets')" 
          icon="pi pi-list" 
          @click="$router.push('/assets')"
          class="p-button-outlined"
        />
        <Button 
          :label="t('dashboard.actions.recalculateRiskScores')" 
          icon="pi pi-refresh" 
          @click="recalculateRiskScores"
          :loading="recalculatingRiskScores"
          class="p-button-outlined p-button-secondary"
        />
      </div>
    </div>

    <!-- Metriche principali -->
    <div class="metrics-grid">
      <div class="metric-card total-assets">
        <div class="metric-icon">
          <i class="pi pi-database"></i>
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ stats.total_assets || 0 }}</div>
          <div class="metric-label">{{ t('dashboard.stats.totalAssets') }}</div>
        </div>
      </div>

      <div class="metric-card critical-assets">
        <div class="metric-icon">
          <i class="pi pi-exclamation-triangle"></i>
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ stats.critical_assets || 0 }}</div>
          <div class="metric-label">{{ t('dashboard.stats.criticalAssets') }}</div>
        </div>
      </div>

      <div class="metric-card risky-assets">
        <div class="metric-icon">
          <i class="pi pi-shield"></i>
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ stats.assets_at_risk || 0 }}</div>
          <div class="metric-label">{{ t('dashboard.stats.assetsAtRisk') }}</div>
        </div>
      </div>

      <div class="metric-card recent-changes">
        <div class="metric-icon">
          <i class="pi pi-clock"></i>
        </div>
        <div class="metric-content">
          <div class="metric-value">{{ stats.recent_changes || 0 }}</div>
          <div class="metric-label">{{ t('dashboard.stats.recentChanges') }}</div>
        </div>
      </div>
    </div>

    <!-- Grafici e analisi -->
    <div class="charts-section">
      <div class="chart-row">
        <!-- Distribuzione per tipo -->
        <div class="simple-card">
          <div class="card-title">
            <i class="pi pi-chart-pie"></i>
            {{ t('dashboard.charts.assetsByType') }}
          </div>
          <div class="chart-container" v-if="assetTypeChartData.labels.length > 0">
            <Doughnut 
              :key="`asset-type-${chartKey}`"
              :data="assetTypeChartData" 
              :options="doughnutOptions" 
              class="chart"
            />
          </div>
          <div v-else class="no-data">
            {{ t('common.messages.noData') }}
          </div>
        </div>

        <!-- Distribuzione per stato -->
        <div class="simple-card">
          <div class="card-title">
            <i class="pi pi-chart-bar"></i>
            {{ t('dashboard.charts.assetsByStatus') }}
          </div>
          <div class="chart-container" v-if="statusChartData.labels.length > 0">
            <Bar 
              :key="`status-${chartKey}`"
              :data="statusChartData" 
              :options="barOptions" 
              class="chart"
            />
          </div>
          <div v-else class="no-data">
            {{ t('common.messages.noData') }}
          </div>
        </div>
      </div>
    </div>

    <!-- Tabelle informative -->
    <div class="tables-section">
      <div class="table-row">
        <!-- Asset più a rischio -->
        <div class="simple-card">
          <div class="card-title">
            <i class="pi pi-exclamation-triangle"></i>
            {{ t('dashboard.tables.topRiskyAssets') }}
          </div>
          <div v-if="riskyAssets.length === 0" class="no-data">
            {{ t('common.messages.noData') }}
          </div>
          <DataTable 
            v-else
            :value="riskyAssets" 
            :rows="5" 
            responsiveLayout="scroll"
            class="dashboard-table"
          >
            <Column field="name" :header="t('common.fields.name')" sortable>
              <template #body="{ data }">
                <router-link :to="`/assets/${data.id}`" class="asset-link">
                  {{ data.name }}
                </router-link>
              </template>
            </Column>
            <Column field="risk_score" :header="t('common.fields.riskScore')" sortable>
              <template #body="{ data }">
                <Tag 
                  :value="data.risk_score" 
                  :severity="getRiskSeverity(data.risk_score)"
                />
              </template>
            </Column>
            <Column field="business_criticality" :header="t('common.fields.businessCriticality')" sortable>
              <template #body="{ data }">
                <CriticalityBadge :value="data.business_criticality" />
              </template>
            </Column>
            <Column field="asset_type_name" :header="t('common.fields.type')" />
            <Column field="status_name" :header="t('common.fields.status')" />
            <Column field="site_name" :header="t('common.fields.site')" />
          </DataTable>
        </div>

        <!-- Ultimi asset -->
        <div class="simple-card">
          <div class="card-title">
            <i class="pi pi-clock"></i>
            {{ t('dashboard.tables.latestAssets') }}
          </div>
          <div v-if="recentAssets.length === 0" class="no-data">
            {{ t('common.messages.noData') }}
          </div>
          <DataTable 
            v-else
            :value="recentAssets" 
            :rows="5" 
            responsiveLayout="scroll"
            class="dashboard-table"
          >
            <Column field="name" :header="t('common.fields.name')" sortable>
              <template #body="{ data }">
                <router-link :to="`/assets/${data.id}`" class="asset-link">
                  {{ data.name }}
                </router-link>
              </template>
            </Column>
            <Column field="asset_type.name" :header="t('common.fields.type')" />
            <Column field="status.name" :header="t('common.fields.status')" />
            <Column field="site.name" :header="t('common.fields.site')" />
            <Column field="created_at" :header="t('common.fields.createdAt')" sortable>
              <template #body="{ data }">
                {{ formatDate(data.created_at) }}
              </template>
            </Column>
          </DataTable>
        </div>
      </div>
    </div>

    <!-- Widget Feature Integrate -->
    <div class="feature-widgets-section">
      <div class="widget-row">
        <!-- Asset Reviews Widget -->
        <div class="simple-card">
          <div class="card-title">
            <i class="pi pi-calendar-check"></i>
            {{ t('dashboard.widgets.assetReviews') }}
            <Button 
              v-if="reviewsSummary.overdue_count > 0 || reviewsSummary.due_count > 0"
              :label="t('dashboard.actions.viewAll')" 
              icon="pi pi-external-link" 
              class="p-button-text p-button-sm ml-auto"
              @click="$router.push('/asset-reviews')"
            />
          </div>
          <div class="widget-content" v-if="!loadingSummaries">
            <div class="widget-metrics">
              <div class="widget-metric" :class="{ 'has-issues': reviewsSummary.overdue_count > 0 }">
                <div class="widget-metric-value">{{ reviewsSummary.overdue_count || 0 }}</div>
                <div class="widget-metric-label">{{ t('dashboard.widgets.overdueReviews') }}</div>
              </div>
              <div class="widget-metric" :class="{ 'has-issues': reviewsSummary.due_count > 0 }">
                <div class="widget-metric-value">{{ reviewsSummary.due_count || 0 }}</div>
                <div class="widget-metric-label">{{ t('dashboard.widgets.dueReviews') }}</div>
              </div>
            </div>
            <div v-if="reviewsSummary.overdue_assets && reviewsSummary.overdue_assets.length > 0" class="widget-list">
              <div class="widget-list-title">{{ t('dashboard.widgets.recentOverdue') }}</div>
              <div v-for="asset in reviewsSummary.overdue_assets.slice(0, 3)" :key="asset.id" class="widget-list-item">
                <router-link :to="`/assets/${asset.id}`" class="asset-link">{{ asset.name }}</router-link>
              </div>
            </div>
          </div>
          <div v-else class="widget-loading">
            <i class="pi pi-spin pi-spinner"></i>
          </div>
        </div>

        <!-- Missing Dependencies Widget -->
        <div class="simple-card">
          <div class="card-title">
            <i class="pi pi-sitemap"></i>
            {{ t('dashboard.widgets.missingDependencies') }}
          </div>
          <div class="widget-content" v-if="!loadingSummaries">
            <div class="widget-metrics">
              <div class="widget-metric" :class="{ 'has-issues': dependenciesSummary.missing_dependencies_count > 0 }">
                <div class="widget-metric-value">{{ dependenciesSummary.missing_dependencies_count || 0 }}</div>
                <div class="widget-metric-label">{{ t('dashboard.widgets.missingDeps') }}</div>
              </div>
              <div class="widget-metric" :class="{ 'has-issues': dependenciesSummary.critical_missing_count > 0 }">
                <div class="widget-metric-value">{{ dependenciesSummary.critical_missing_count || 0 }}</div>
                <div class="widget-metric-label">{{ t('dashboard.widgets.criticalMissing') }}</div>
              </div>
            </div>
            <div class="widget-info">
              <small>{{ t('dashboard.widgets.totalConnections') }}: {{ dependenciesSummary.total_connections || 0 }}</small>
            </div>
          </div>
          <div v-else class="widget-loading">
            <i class="pi pi-spin pi-spinner"></i>
          </div>
        </div>

        <!-- Vulnerabilities Widget -->
        <div class="simple-card">
          <div class="card-title">
            <i class="pi pi-shield"></i>
            {{ t('dashboard.widgets.vulnerabilities') }}
            <Button 
              v-if="vulnerabilitiesSummary.critical_unpatched > 0 || vulnerabilitiesSummary.high_unpatched > 0"
              :label="t('dashboard.actions.viewAll')" 
              icon="pi pi-external-link" 
              class="p-button-text p-button-sm ml-auto"
              @click="$router.push('/vulnerabilities')"
            />
          </div>
          <div class="widget-content" v-if="!loadingSummaries">
            <div class="widget-metrics">
              <div class="widget-metric critical" :class="{ 'has-issues': vulnerabilitiesSummary.critical_unpatched > 0 }">
                <div class="widget-metric-value">{{ vulnerabilitiesSummary.critical_unpatched || 0 }}</div>
                <div class="widget-metric-label">{{ t('dashboard.widgets.criticalUnpatched') }}</div>
              </div>
              <div class="widget-metric warning" :class="{ 'has-issues': vulnerabilitiesSummary.high_unpatched > 0 }">
                <div class="widget-metric-value">{{ vulnerabilitiesSummary.high_unpatched || 0 }}</div>
                <div class="widget-metric-label">{{ t('dashboard.widgets.highUnpatched') }}</div>
              </div>
            </div>
            <div class="widget-info">
              <small>{{ t('dashboard.widgets.totalUnpatched') }}: {{ vulnerabilitiesSummary.total_unpatched || 0 }}</small>
            </div>
          </div>
          <div v-else class="widget-loading">
            <i class="pi pi-spin pi-spinner"></i>
          </div>
        </div>

        <!-- Compliance Widget -->
        <div class="simple-card">
          <div class="card-title">
            <i class="pi pi-check-circle"></i>
            {{ t('dashboard.widgets.compliance') }}
            <Button 
              v-if="complianceSummary.non_compliant_zones > 0 || complianceSummary.partial_compliant_zones > 0"
              :label="t('dashboard.actions.viewAll')" 
              icon="pi pi-external-link" 
              class="p-button-text p-button-sm ml-auto"
              @click="$router.push('/compliance')"
            />
          </div>
          <div class="widget-content" v-if="!loadingSummaries">
            <div class="widget-metrics">
              <div class="widget-metric" :class="{ 'has-issues': complianceSummary.non_compliant_zones > 0 }">
                <div class="widget-metric-value">{{ complianceSummary.non_compliant_zones || 0 }}</div>
                <div class="widget-metric-label">{{ t('dashboard.widgets.nonCompliantZones') }}</div>
              </div>
              <div class="widget-metric" :class="{ 'has-issues': complianceSummary.partial_compliant_zones > 0 }">
                <div class="widget-metric-value">{{ complianceSummary.partial_compliant_zones || 0 }}</div>
                <div class="widget-metric-label">{{ t('dashboard.widgets.partialCompliantZones') }}</div>
              </div>
            </div>
            <div class="widget-info">
              <small>{{ t('dashboard.widgets.totalZones') }}: {{ complianceSummary.total_zones || 0 }} | 
              {{ t('dashboard.widgets.compliantZones') }}: {{ complianceSummary.compliant_zones || 0 }}</small>
            </div>
          </div>
          <div v-else class="widget-loading">
            <i class="pi pi-spin pi-spinner"></i>
          </div>
        </div>
      </div>
    </div>

    <!-- Sezione avvisi e notifiche -->
    <div class="alerts-section">
      <div class="simple-card">
        <div class="card-title">
          <i class="pi pi-bell"></i>
          {{ t('dashboard.alerts') }}
        </div>
        <div class="alerts-content">
          <div v-if="stats.assets_at_risk > 0" class="alert-item warning">
            <i class="pi pi-exclamation-triangle"></i>
            <span>{{ stats.assets_at_risk }} {{ t('dashboard.stats.assetsAtRisk') }}</span>
          </div>
          <div v-if="stats.critical_assets > 0" class="alert-item critical">
            <i class="pi pi-exclamation-circle"></i>
            <span>{{ stats.critical_assets }} {{ t('dashboard.stats.criticalAssets') }}</span>
          </div>
          <div v-if="reviewsSummary.overdue_count > 0" class="alert-item warning">
            <i class="pi pi-calendar-times"></i>
            <span>{{ reviewsSummary.overdue_count }} {{ t('dashboard.widgets.overdueReviews') }}</span>
          </div>
          <div v-if="vulnerabilitiesSummary.critical_unpatched > 0" class="alert-item critical">
            <i class="pi pi-shield"></i>
            <span>{{ vulnerabilitiesSummary.critical_unpatched }} {{ t('dashboard.widgets.criticalUnpatched') }}</span>
          </div>
          <div v-if="stats.assets_at_risk === 0 && stats.critical_assets === 0 && reviewsSummary.overdue_count === 0 && vulnerabilitiesSummary.critical_unpatched === 0" class="alert-item success">
            <i class="pi pi-check-circle"></i>
            <span>{{ t('dashboard.messages.allSystemsOperational') }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import { Doughnut, Bar } from 'vue-chartjs'
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement } from 'chart.js'

// Registra i componenti necessari per Chart.js
ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement)
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Tag from 'primevue/tag'
import Card from 'primevue/card'
import CriticalityBadge from '../components/common/CriticalityBadge.vue'
import api from '../api/api'

const { t } = useI18n()
const router = useRouter()
const toast = useToast()

// Reactive data
const stats = ref({})
const assetTypes = ref([])
const recentAssets = ref([])
const riskyAssets = ref([])
const recalculatingRiskScores = ref(false)
const reviewsSummary = ref({ overdue_count: 0, due_count: 0, overdue_assets: [], due_assets: [] })
const dependenciesSummary = ref({ total_connections: 0, missing_dependencies_count: 0, critical_missing_count: 0 })
const vulnerabilitiesSummary = ref({ critical_unpatched: 0, high_unpatched: 0, total_unpatched: 0 })
const complianceSummary = ref({ total_zones: 0, non_compliant_zones: 0, partial_compliant_zones: 0, compliant_zones: 0 })
const loadingSummaries = ref(false)

// Chart data
const assetTypeChartData = ref({ labels: [], datasets: [] })
const statusChartData = ref({ labels: [], datasets: [] })
const chartKey = ref(0) // Per forzare il re-render dei grafici

// Chart options
const doughnutOptions = ref({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { 
      display: true,
      position: 'bottom'
    }
  }
})

const barOptions = ref({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false }
  },
  scales: {
    y: {
      beginAtZero: true
    }
  }
})

// Computed functions
const getRiskSeverity = (score) => {
  if (score >= 8) return 'danger'
  if (score >= 6) return 'warning'
  return 'info'
}

const getCriticalitySeverity = (level) => {
  if (level >= 4) return 'danger'
  if (level >= 3) return 'warning'
  return 'info'
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  return new Date(dateString).toLocaleDateString()
}

// Funzione per ricalcolare i risk score
const recalculateRiskScores = async () => {
  recalculatingRiskScores.value = true
  try {
    const response = await api.recalculateAllRiskScores()
    console.log('Risk scores ricalcolati:', response.data)
    
    // Ricarica i dati della dashboard
    await loadDashboardData()
    
    // Mostra messaggio di successo
    toast.add({
      severity: 'success',
      summary: t('common.messages.success'),
      detail: response.data.message || 'Risk scores aggiornati con successo!',
      life: 3000
    })
  } catch (error) {
    console.error('Errore durante il ricalcolo dei risk score:', error)
    toast.add({
      severity: 'error',
      summary: t('common.messages.error'),
      detail: 'Errore durante il ricalcolo dei risk score',
      life: 3000
    })
  } finally {
    recalculatingRiskScores.value = false
  }
}

// Watcher per reagire ai cambiamenti dei dati
watch(() => stats.value, (newStats) => {
  if (newStats && (newStats.type_stats || newStats.status_stats)) {
    prepareChartData()
  }
}, { deep: true })

// Funzione per caricare i dati della dashboard
const loadDashboardData = async () => {
  try {
    // Carica statistiche
    const statsRes = await api.getDashboardStats()
    stats.value = statsRes.data

    // Carica asset a rischio
    const riskyRes = await api.getRiskyAssets(5)
    riskyAssets.value = Array.isArray(riskyRes.data) ? riskyRes.data : []

    // Carica ultimi asset
    const recentRes = await api.getAssets({ limit: 5 })
    recentAssets.value = Array.isArray(recentRes.data) ? recentRes.data : []

    // Prepara dati per i grafici
    prepareChartData()
    
    // Carica summary per nuove feature
    await loadSummaries()
  } catch (error) {
    console.error('Error loading dashboard data:', error.response?.data || error  )
  }
}

// Funzione per caricare i summary
const loadSummaries = async () => {
  loadingSummaries.value = true
  try {
    const [reviewsRes, depsRes, vulnsRes, complianceRes] = await Promise.all([
      api.getReviewsSummary().catch(() => ({ data: { overdue_count: 0, due_count: 0, overdue_assets: [], due_assets: [] } })),
      api.getDependenciesSummary().catch(() => ({ data: { total_connections: 0, missing_dependencies_count: 0, critical_missing_count: 0 } })),
      api.getVulnerabilitiesSummary().catch(() => ({ data: { critical_unpatched: 0, high_unpatched: 0, total_unpatched: 0 } })),
      api.getComplianceSummary().catch(() => ({ data: { total_zones: 0, non_compliant_zones: 0, partial_compliant_zones: 0, compliant_zones: 0 } }))
    ])
    
    reviewsSummary.value = reviewsRes.data
    dependenciesSummary.value = depsRes.data
    vulnerabilitiesSummary.value = vulnsRes.data
    complianceSummary.value = complianceRes.data
  } catch (error) {
    console.error('Error loading summaries:', error)
  } finally {
    loadingSummaries.value = false
  }
}

// Load data
onMounted(async () => {
  await loadDashboardData()
})

const prepareChartData = () => {
  // Incrementa la key per forzare il re-render
  chartKey.value++
  
  // Grafico asset per tipo
  if (stats.value.type_stats && Array.isArray(stats.value.type_stats) && stats.value.type_stats.length > 0) {
    // Filtra solo i tipi con asset_count > 0
    const validTypes = stats.value.type_stats.filter(t => t.asset_count > 0)
    
    if (validTypes.length > 0) {
      assetTypeChartData.value = {
        labels: validTypes.map(t => t.name),
        datasets: [{
          label: 'Asset per tipo',
          data: validTypes.map(t => t.asset_count),
          backgroundColor: [
            '#42A5F5', '#66BB6A', '#FFA726', '#AB47BC', '#FF7043', 
            '#26A69A', '#D4E157', '#FFCA28', '#8D6E63', '#789262'
          ],
          borderWidth: 2,
          borderColor: '#fff'
        }]
      }
    } else {
      assetTypeChartData.value = { labels: [], datasets: [] }
    }
  } else {
    assetTypeChartData.value = { labels: [], datasets: [] }
  }

  // Grafico asset per stato
  if (stats.value.status_stats && Array.isArray(stats.value.status_stats) && stats.value.status_stats.length > 0) {
    statusChartData.value = {
      labels: stats.value.status_stats.map(s => s.name),
      datasets: [{
        label: t('dashboard.stats.totalAssets'),
        data: stats.value.status_stats.map(s => s.count),
        backgroundColor: stats.value.status_stats.map(s => s.color || '#42A5F5'),
        borderWidth: 1,
        borderColor: '#fff'
      }]
    }
  } else {
    statusChartData.value = { labels: [], datasets: [] }
  }
}
</script>

<style scoped>
.dashboard {
  padding: 2rem;
  background: #f8f9fa;
  min-height: 100vh;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  background: white;
  padding: 2rem;
  border-radius: 1rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.header-content h1 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
  font-size: 2.5rem;
  font-weight: 700;
}

.welcome-text {
  margin: 0;
  color: #6c757d;
  font-size: 1.1rem;
}

.quick-actions {
  display: flex;
  gap: 1rem;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.metric-card {
  background: white;
  border-radius: 1rem;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  display: flex;
  align-items: center;
  gap: 1.5rem;
  transition: transform 0.2s, box-shadow 0.2s;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.1);
}

.metric-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: white;
}

.total-assets .metric-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.critical-assets .metric-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.risky-assets .metric-icon {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.recent-changes .metric-icon {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.metric-content {
  flex: 1;
}

.metric-value {
  font-size: 2.5rem;
  font-weight: 700;
  color: #2c3e50;
  line-height: 1;
  margin-bottom: 0.5rem;
}

.metric-label {
  color: #6c757d;
  font-size: 0.9rem;
  font-weight: 500;
}

.charts-section {
  margin-bottom: 2rem;
}

.chart-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
}

.simple-card {
  flex: 1;
  min-width: 0;
  background: white;
  border-radius: 1rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  overflow: hidden;
}

.card-title {
  padding: 1.5rem 1.5rem 1rem 1.5rem;
  font-size: 1.2rem;
  font-weight: 600;
  color: #2c3e50;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.chart-container {
  padding: 1rem;
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart {
  width: 100%;
  height: 300px;
  min-height: 300px;
}



.no-data {
  text-align: center;
  padding: 2rem;
  color: #6c757d;
  font-style: italic;
}

.tables-section {
  margin-bottom: 2rem;
}

.table-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
  gap: 1.5rem;
}

.table-card {
  background: white;
  border-radius: 1rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.table-card :deep(.p-card-title) {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #2c3e50;
  font-weight: 600;
}

.dashboard-table {
  font-size: 0.9rem;
}

.asset-link {
  color: #007bff;
  text-decoration: none;
  font-weight: 500;
}

.asset-link:hover {
  text-decoration: underline;
}

.alerts-section {
  margin-bottom: 2rem;
}

.alerts-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.alert-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  border-radius: 0.5rem;
  font-weight: 500;
}

.alert-item.warning {
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}

.alert-item.critical {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.alert-item.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.alert-item i {
  font-size: 1.2rem;
}

/* Feature Widgets Section */
.feature-widgets-section {
  margin-bottom: 2rem;
}

.widget-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}

.widget-content {
  padding: 1.5rem;
}

.widget-metrics {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-bottom: 1rem;
}

.widget-metric {
  text-align: center;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 0.5rem;
  transition: all 0.2s;
}

.widget-metric.has-issues {
  background: #fff3cd;
  border: 1px solid #ffc107;
}

.widget-metric.critical.has-issues {
  background: #f8d7da;
  border: 1px solid #dc3545;
}

.widget-metric.warning.has-issues {
  background: #fff3cd;
  border: 1px solid #ffc107;
}

.widget-metric-value {
  font-size: 2rem;
  font-weight: 700;
  color: #2c3e50;
  line-height: 1;
  margin-bottom: 0.5rem;
}

.widget-metric.has-issues .widget-metric-value {
  color: #856404;
}

.widget-metric.critical.has-issues .widget-metric-value {
  color: #721c24;
}

.widget-metric-label {
  font-size: 0.85rem;
  color: #6c757d;
  font-weight: 500;
}

.widget-list {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #f0f0f0;
}

.widget-list-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.widget-list-item {
  padding: 0.5rem 0;
  font-size: 0.9rem;
}

.widget-info {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #f0f0f0;
  text-align: center;
  color: #6c757d;
}

.widget-loading {
  padding: 2rem;
  text-align: center;
  color: #6c757d;
}

.widget-loading i {
  font-size: 2rem;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.ml-auto {
  margin-left: auto;
}

/* Responsive design */
@media (max-width: 768px) {
  .dashboard {
    padding: 1rem;
  }
  
  .dashboard-header {
    flex-direction: column;
    gap: 1rem;
    text-align: center;
  }
  
  .quick-actions {
    justify-content: center;
  }
  
  .metrics-grid {
    grid-template-columns: 1fr;
  }
  
  .chart-row,
  .table-row {
    grid-template-columns: 1fr;
  }
  
  .metric-card {
    padding: 1.5rem;
  }
  
  .metric-value {
    font-size: 2rem;
  }
}
</style>
