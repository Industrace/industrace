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

    <!-- 1. EXPOSURE - "Dove sono esposto" -->
    <div class="dashboard-section">
      <SectionHeader
        :title="t('dashboard.exposure.title')"
        :description="t('dashboard.exposure.description')"
        icon="pi pi-exclamation-triangle"
      />
      <div class="cards-grid">
        <DashboardCard
          :value="exposureData.overall_exposure_score || 0"
          :label="t('dashboard.exposure.overallExposure')"
          :subtitle="t('dashboard.exposure.overallExposureSubtitle')"
          icon="pi pi-shield"
          :severity="getExposureSeverity(exposureData.overall_exposure_score)"
          click-action="/assets"
        />
        <DashboardCard
          :value="exposureData.assets_at_risk || 0"
          :label="t('dashboard.exposure.assetsAtRisk')"
          :subtitle="t('dashboard.exposure.assetsAtRiskSubtitle')"
          icon="pi pi-exclamation-triangle"
          severity="warning"
          click-action="/assets?risk_score_min=5"
        />
        <DashboardCard
          :value="exposureData.critical_assets || 0"
          :label="t('dashboard.exposure.criticalAssets')"
          :subtitle="t('dashboard.exposure.criticalAssetsSubtitle')"
          icon="pi pi-exclamation-circle"
          severity="danger"
          click-action="/assets?business_criticality=critical,high"
        />
        <DashboardCard
          :value="exposureData.assets_with_critical_vulns || 0"
          :label="t('dashboard.exposure.assetsWithCriticalVulns')"
          :subtitle="t('dashboard.exposure.assetsWithCriticalVulnsSubtitle')"
          icon="pi pi-exclamation-triangle"
          severity="danger"
          click-action="/assets?has_critical_vulns=true"
        />
      </div>
    </div>

    <!-- 2. ATTENTION - "Cosa devo guardare oggi" -->
    <div class="dashboard-section">
      <SectionHeader
        :title="t('dashboard.attention.title')"
        :description="t('dashboard.attention.description')"
        icon="pi pi-bell"
      />
      <div class="cards-grid">
        <DashboardCard
          :value="reviewsSummary.overdue_count || 0"
          :label="t('dashboard.attention.reviewsOverdue')"
          :subtitle="t('dashboard.attention.reviewsOverdueSubtitle')"
          icon="pi pi-calendar-times"
          :severity="reviewsSummary.overdue_count > 0 ? 'warning' : 'success'"
          click-action="/asset-reviews?status=overdue"
        />
        <DashboardCard
          :value="(complianceSummary.non_compliant_zones || 0) + (complianceSummary.partial_compliant_zones || 0)"
          :label="t('dashboard.attention.complianceGaps')"
          :subtitle="t('dashboard.attention.complianceGapsSubtitle')"
          icon="pi pi-times-circle"
          :severity="(complianceSummary.non_compliant_zones || 0) + (complianceSummary.partial_compliant_zones || 0) > 0 ? 'warning' : 'success'"
          click-action="/compliance"
        />
        <DashboardCard
          :value="dependenciesSummary.missing_dependencies_count || 0"
          :label="t('dashboard.attention.missingDependencies')"
          :subtitle="t('dashboard.attention.missingDependenciesSubtitle')"
          icon="pi pi-sitemap"
          :severity="dependenciesSummary.missing_dependencies_count > 0 ? 'warning' : 'success'"
          click-action="/assets"
        />
        <DashboardCard
          :value="evidenceMissing || 0"
          :label="t('dashboard.attention.evidenceMissing')"
          :subtitle="t('dashboard.attention.evidenceMissingSubtitle')"
          icon="pi pi-file"
          :severity="evidenceMissing > 0 ? 'warning' : 'success'"
          click-action="/compliance"
        />
      </div>
    </div>

    <!-- 3. CHANGE - "Cosa è cambiato di recente" -->
    <div class="dashboard-section">
      <SectionHeader
        :title="t('dashboard.change.title')"
        :description="t('dashboard.change.description')"
        icon="pi pi-clock"
      />
      <div class="change-section">
        <div class="change-card">
          <div class="change-card-header">
            <h3>{{ t('dashboard.change.recentChanges') }}</h3>
            <p class="change-card-subtitle">{{ t('dashboard.change.recentChangesSubtitle') }}</p>
          </div>
          <RecentChangesList
            :changes="recentChanges"
            :loading="loadingRecentChanges"
          />
        </div>
        <DashboardCard
          :value="recentChanges.length || 0"
          :label="t('dashboard.change.newlyAddedAssets')"
          :subtitle="t('dashboard.change.newlyAddedAssetsSubtitle')"
          icon="pi pi-plus-circle"
          severity="info"
          click-action="/assets?sort=created_at&order=desc"
        />
      </div>
    </div>

    <!-- 4. POSTURE - "Sono difendibile?" -->
    <div class="dashboard-section">
      <SectionHeader
        :title="t('dashboard.posture.title')"
        :description="t('dashboard.posture.description')"
        icon="pi pi-check-circle"
      />
      <div class="cards-grid">
        <DashboardCard
          :value="getPostureScore()"
          :label="t('dashboard.posture.securityPosture')"
          :subtitle="t('dashboard.posture.securityPostureSubtitle')"
          icon="pi pi-shield"
          :severity="getPostureSeverity()"
          click-action="/compliance"
        />
        <DashboardCard
          :value="`${complianceSummary.coverage_percentage || 0}%`"
          :label="t('dashboard.posture.iec62443Coverage')"
          :subtitle="t('dashboard.posture.iec62443CoverageSubtitle')"
          icon="pi pi-percentage"
          :severity="(complianceSummary.coverage_percentage || 0) >= 80 ? 'success' : 'warning'"
          click-action="/compliance"
        />
        <DashboardCard
          :value="complianceSummary.non_compliant_zones || 0"
          :label="t('dashboard.posture.nonCompliantZones')"
          :subtitle="t('dashboard.posture.nonCompliantZonesSubtitle')"
          icon="pi pi-times-circle"
          :severity="(complianceSummary.non_compliant_zones || 0) > 0 ? 'danger' : 'success'"
          click-action="/compliance"
        />
        <DashboardCard
          :value="complianceSummary.sl_gap_summary?.zones_with_gap || 0"
          :label="t('dashboard.posture.slGapSummary')"
          :subtitle="t('dashboard.posture.slGapSummarySubtitle')"
          icon="pi pi-chart-line"
          :severity="(complianceSummary.sl_gap_summary?.zones_with_gap || 0) > 0 ? 'warning' : 'success'"
          click-action="/compliance"
        />
      </div>
    </div>

    <!-- Action Center (solo se ci sono problemi) -->
    <div v-if="hasIssues" class="action-center">
      <div class="action-center-card">
        <div class="action-center-header">
          <i class="pi pi-bell"></i>
          <h3>{{ t('dashboard.alerts') }}</h3>
        </div>
        <div class="action-center-content">
          <div v-if="exposureData.assets_at_risk > 0" class="alert-badge warning">
            {{ exposureData.assets_at_risk }} {{ t('dashboard.exposure.assetsAtRisk') }}
          </div>
          <div v-if="exposureData.critical_assets > 0" class="alert-badge danger">
            {{ exposureData.critical_assets }} {{ t('dashboard.exposure.criticalAssets') }}
          </div>
          <div v-if="reviewsSummary.overdue_count > 0" class="alert-badge warning">
            {{ reviewsSummary.overdue_count }} {{ t('dashboard.attention.reviewsOverdue') }}
          </div>
          <div v-if="exposureData.assets_with_critical_vulns > 0" class="alert-badge danger">
            {{ exposureData.assets_with_critical_vulns }} {{ t('dashboard.exposure.assetsWithCriticalVulns') }}
          </div>
        </div>
      </div>
    </div>
    <div v-else class="action-center">
      <div class="action-center-card success">
        <div class="action-center-content">
          <i class="pi pi-check-circle"></i>
          <span>{{ t('dashboard.messages.allSystemsOperational') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import Button from 'primevue/button'
import DashboardCard from '../components/dashboard/DashboardCard.vue'
import SectionHeader from '../components/dashboard/SectionHeader.vue'
import RecentChangesList from '../components/dashboard/RecentChangesList.vue'
import api from '../api/api'

const { t } = useI18n()
const router = useRouter()
const toast = useToast()

// Reactive data
const recalculatingRiskScores = ref(false)
const exposureData = ref({
  overall_exposure_score: 0,
  assets_at_risk: 0,
  critical_assets: 0,
  high_risk_vulnerabilities: 0,
  assets_with_critical_vulns: 0,
  missing_critical_dependencies: 0
})
const reviewsSummary = ref({ overdue_count: 0, due_count: 0 })
const dependenciesSummary = ref({ missing_dependencies_count: 0, critical_missing_count: 0 })
const complianceSummary = ref({
  total_zones: 0,
  non_compliant_zones: 0,
  partial_compliant_zones: 0,
  compliant_zones: 0,
  coverage_percentage: 0,
  sl_gap_summary: { zones_with_gap: 0, average_gap: 0, max_gap: 0 }
})
const recentChanges = ref([])
const loadingRecentChanges = ref(false)
const evidenceMissing = ref(0)

// Computed
const hasIssues = computed(() => {
  return (
    exposureData.value.assets_at_risk > 0 ||
    exposureData.value.critical_assets > 0 ||
    reviewsSummary.value.overdue_count > 0 ||
    exposureData.value.assets_with_critical_vulns > 0
  )
})

// Functions
const getExposureSeverity = (score) => {
  if (score >= 7) return 'danger'
  if (score >= 4) return 'warning'
  return 'info'
}

const getPostureScore = () => {
  const total = complianceSummary.value.total_zones || 1
  const compliant = complianceSummary.value.compliant_zones || 0
  return Math.round((compliant / total) * 10)
}

const getPostureSeverity = () => {
  const score = getPostureScore()
  if (score >= 8) return 'success'
  if (score >= 5) return 'warning'
  return 'danger'
}

const recalculateRiskScores = async () => {
  recalculatingRiskScores.value = true
  try {
    const response = await api.recalculateAllRiskScores()
    await loadDashboardData()
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

const loadDashboardData = async () => {
  try {
    // Load all data in parallel
    const [
      exposureRes,
      reviewsRes,
      depsRes,
      complianceRes,
      changesRes,
      evidenceRes
    ] = await Promise.all([
      api.getExposureSummary().catch(() => ({ data: exposureData.value })),
      api.getReviewsSummary().catch(() => ({ data: { overdue_count: 0, due_count: 0 } })),
      api.getDependenciesSummary().catch(() => ({ data: { missing_dependencies_count: 0, critical_missing_count: 0 } })),
      api.getComplianceSummary().catch(() => ({ data: complianceSummary.value })),
      api.getRecentChanges(10).catch(() => ({ data: [] })),
      api.getEvidenceMissing().catch(() => ({ data: { missing_evidence_count: 0 } }))
    ])
    
    exposureData.value = exposureRes.data
    reviewsSummary.value = reviewsRes.data
    dependenciesSummary.value = depsRes.data
    complianceSummary.value = complianceRes.data
    recentChanges.value = changesRes.data
    evidenceMissing.value = evidenceRes.data.missing_evidence_count || 0
  } catch (error) {
    console.error('Error loading dashboard data:', error)
  }
}

// Load data on mount
onMounted(async () => {
  await loadDashboardData()
})
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

.dashboard-section {
  margin-bottom: 3rem;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
}

.change-section {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.5rem;
}

.change-card {
  background: white;
  border-radius: 0.75rem;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.change-card-header h3 {
  margin: 0 0 0.25rem 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #2c3e50;
}

.change-card-subtitle {
  margin: 0 0 1rem 0;
  font-size: 0.875rem;
  color: #6c757d;
}

.action-center {
  margin-top: 3rem;
}

.action-center-card {
  background: white;
  border-radius: 0.75rem;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.action-center-card.success {
  background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
  border: 1px solid #c3e6cb;
}

.action-center-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.action-center-header i {
  font-size: 1.5rem;
  color: #667eea;
}

.action-center-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #2c3e50;
}

.action-center-content {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.action-center-card.success .action-center-content {
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  color: #155724;
  font-weight: 600;
}

.action-center-card.success .action-center-content i {
  font-size: 1.5rem;
}

.alert-badge {
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  font-weight: 600;
  font-size: 0.875rem;
}

.alert-badge.warning {
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
}

.alert-badge.danger {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

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
  
  .cards-grid {
    grid-template-columns: 1fr;
  }
  
  .change-section {
    grid-template-columns: 1fr;
  }
}
</style>
