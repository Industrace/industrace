<template>
  <div class="risk-tab">
    <!-- Risk Summary Overview -->
    <div class="risk-overview-section">
      <div v-if="loadingRisk || loadingRiskFromDeps" class="p-4 text-center">
        <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
        <p>{{ t('assets.riskBreakdown.loadingRiskData') }}</p>
      </div>
      <div v-else-if="riskBreakdown && riskFromDependenciesData" class="risk-overview-card">
        <div class="overview-main">
          <div class="overview-total">
            <label>{{ t('assets.riskBreakdown.totalRiskScore') }}</label>
            <span class="total-risk-value" :class="getTotalRiskClass()">
              {{ getTotalRiskScore().toFixed(2) }}
            </span>
            <span class="risk-level-badge" :class="getTotalRiskClass()">
              {{ getTotalRiskLabel() }}
            </span>
          </div>
          <div class="overview-breakdown">
            <div class="breakdown-item">
              <label>{{ t('assets.riskBreakdown.baseRiskScore') }}</label>
              <span class="breakdown-value">{{ getBaseRiskScore().toFixed(2) }}</span>
            </div>
            <div class="breakdown-item">
              <label>{{ t('assets.riskBreakdown.riskFromDependencies') }}</label>
              <span class="breakdown-value risk-increase-value">
                +{{ getRiskFromDependencies().toFixed(2) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Risk Base Calculation Section -->
    <div class="risk-section risk-base-section">
      <div class="section-header-collapsible" @click="showBaseBreakdown = !showBaseBreakdown">
        <h3 class="section-title">{{ t('assets.riskBreakdown.baseRiskCalculation') }}</h3>
        <i :class="showBaseBreakdown ? 'pi pi-chevron-up' : 'pi pi-chevron-down'"></i>
      </div>
      <div v-if="showBaseBreakdown" class="section-content">
        <div v-if="loadingRisk" class="p-4 text-center">
          <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
        </div>
        <RiskBreakdown v-else-if="riskBreakdown" :breakdown="riskBreakdown" />
        <div v-else class="p-4 text-center text-muted">{{ t('assets.riskBreakdown.missingData') }}</div>
      </div>
    </div>

    <!-- Risk from Dependencies Section -->
    <div class="risk-section risk-from-dependencies-section">
      <div class="section-header-collapsible" @click="showDependenciesBreakdown = !showDependenciesBreakdown">
        <h3 class="section-title">{{ t('assets.riskBreakdown.riskFromDependencies') }}</h3>
        <i :class="showDependenciesBreakdown ? 'pi pi-chevron-up' : 'pi pi-chevron-down'"></i>
      </div>
      <div v-if="showDependenciesBreakdown" class="section-content">
        <div class="dependencies-risk-info-box">
          <i class="pi pi-info-circle"></i>
          <div>
            <strong>{{ t('assets.riskBreakdown.howItWorks') }}</strong>
            <p>{{ t('assets.riskBreakdown.riskFromDependenciesDescription') }}</p>
          </div>
        </div>

        <div v-if="loadingRiskFromDeps" class="p-4 text-center">
          <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
        </div>
        <div v-else-if="riskFromDependenciesData" class="risk-from-deps-content">
          <div v-if="riskFromDependenciesData.dependencies_risk_breakdown && riskFromDependenciesData.dependencies_risk_breakdown.length > 0" class="dependencies-breakdown">
            <DataTable :value="riskFromDependenciesData.dependencies_risk_breakdown" class="p-datatable-sm" :paginator="true" :rows="10">
              <Column field="dependency_asset_name" :header="t('assetDependencies.dependencyAsset')">
                <template #body="{ data }">
                  <a @click="$router.push(`/assets/${data.dependency_asset_id}`)" class="asset-link">
                    {{ data.dependency_asset_name }}
                  </a>
                </template>
              </Column>
              <Column field="dependency_asset_risk_score" :header="t('assets.riskBreakdown.dependencyAssetRisk')">
                <template #body="{ data }">
                  <span class="risk-score">{{ data.dependency_asset_risk_score?.toFixed(2) || '0.00' }}</span>
                </template>
              </Column>
              <Column field="risk_contribution" :header="t('assets.riskBreakdown.riskContribution')">
                <template #body="{ data }">
                  <span class="risk-increase">+{{ data.risk_contribution?.toFixed(2) || '0.00' }}</span>
                </template>
              </Column>
              <Column field="criticality" :header="t('assetDependencies.dependencyCriticality')">
                <template #body="{ data }">
                  <Tag :value="getCriticalityLabel(data.criticality)" :severity="getCriticalitySeverity(data.criticality)" />
                </template>
              </Column>
              <Column field="dependency_type" :header="t('assetDependencies.dependencyType')">
                <template #body="{ data }">
                  {{ getDependencyTypeLabel(data.dependency_type) }}
                </template>
              </Column>
            </DataTable>
          </div>
          <div v-else class="p-4 text-center text-muted">
            {{ t('assets.riskBreakdown.noDependencies') }}
          </div>
        </div>
        <div v-else class="p-4 text-center text-muted">
          {{ t('assets.riskBreakdown.noRiskFromDepsData') }}
        </div>
      </div>
    </div>

    <!-- Risk Propagation Section -->
    <div class="risk-section risk-propagation-section">
      <div class="section-header-collapsible" @click="showPropagation = !showPropagation">
        <h3 class="section-title">{{ t('assets.riskBreakdown.dependencyRiskPropagation') }}</h3>
        <i :class="showPropagation ? 'pi pi-chevron-up' : 'pi pi-chevron-down'"></i>
      </div>
      <div v-if="showPropagation" class="section-content">
        <div class="propagation-info-box">
          <i class="pi pi-info-circle"></i>
          <div>
            <strong>{{ t('assets.riskBreakdown.howItWorks') }}</strong>
            <p>{{ t('assets.riskBreakdown.dependencyRiskDescription') }}</p>
          </div>
        </div>

        <div v-if="loadingPropagation" class="p-4 text-center">
          <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
        </div>
        <RiskPropagationView 
          v-else-if="riskPropagationData"
          :assetId="assetId"
          :riskData="riskPropagationData"
          :loading="loadingPropagation"
          :maxDepth="propagationDepth"
          @depth-change="handleDepthChange"
        />
        <div v-else class="p-4 text-center text-muted">
          {{ t('assets.riskBreakdown.noPropagationData') }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRiskLabels } from '@/composables/useRiskLabels'
import RiskBreakdown from '../components/RiskBreakdown.vue'
import RiskPropagationView from './components/RiskPropagationView.vue'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import api from '@/api/api'
import { useCriticality } from '@/composables/useCriticality'

const props = defineProps({
  assetId: { type: [String, Number], required: true }
})
const { t } = useI18n()
const { criticalityColors } = useCriticality()
const { riskLevelLabel, riskLevelSeverity } = useRiskLabels()

const riskBreakdown = ref(null)
const loadingRisk = ref(false)
const riskPropagationData = ref(null)
const loadingPropagation = ref(false)
const riskFromDependenciesData = ref(null)
const loadingRiskFromDeps = ref(false)
const propagationDepth = ref(5)

// Collapsible sections state
const showBaseBreakdown = ref(false)
const showDependenciesBreakdown = ref(false)
const showPropagation = ref(false)

async function fetchRiskBreakdown() {
  if (!props.assetId) return
  loadingRisk.value = true
  try {
    const res = await api.calculateAssetRisk(props.assetId)
    riskBreakdown.value = res.data.breakdown
  } catch (e) {
    riskBreakdown.value = null
  } finally {
    loadingRisk.value = false
  }
}

async function fetchRiskPropagation() {
  if (!props.assetId) return
  loadingPropagation.value = true
  try {
    const res = await api.getRiskPropagation(props.assetId, propagationDepth.value)
    riskPropagationData.value = res.data
  } catch (e) {
    riskPropagationData.value = null
  } finally {
    loadingPropagation.value = false
  }
}

function handleDepthChange(newDepth) {
  propagationDepth.value = newDepth
  fetchRiskPropagation()
}

async function fetchRiskFromDependencies() {
  if (!props.assetId) return
  loadingRiskFromDeps.value = true
  try {
    const res = await api.getRiskFromDependencies(props.assetId)
    riskFromDependenciesData.value = res.data
  } catch (e) {
    riskFromDependenciesData.value = null
  } finally {
    loadingRiskFromDeps.value = false
  }
}

function getCriticalityLabel(criticality) {
  return t(`assetDependencies.criticalities.${criticality}`) || criticality
}

function getCriticalitySeverity(criticality) {
  const severityMap = {
    'low': 'success',
    'medium': 'info',
    'high': 'warning',
    'critical': 'danger'
  }
  return severityMap[criticality] || null
}

function getDependencyTypeLabel(type) {
  return t(`assetDependencies.types.${type}`) || type
}

function getBaseRiskScore() {
  if (!riskBreakdown.value) return 0.0
  return riskBreakdown.value.final_score || 0.0
}

function getRiskFromDependencies() {
  if (!riskFromDependenciesData.value) return 0.0
  return riskFromDependenciesData.value.total_risk_from_dependencies || 0.0
}

function getTotalRiskScore() {
  // Cap total risk at 10.0 (risk scale is 0-10)
  const total = getBaseRiskScore() + getRiskFromDependencies()
  return Math.min(10.0, Math.max(0.0, total))
}

function getTotalRiskLabel() {
  const score = getTotalRiskScore()
  return riskLevelLabel(score)
}

function getTotalRiskClass() {
  const score = getTotalRiskScore()
  return riskLevelSeverity(score)
}

onMounted(async () => {
  await Promise.all([fetchRiskBreakdown(), fetchRiskPropagation(), fetchRiskFromDependencies()])
})

watch(() => props.assetId, async (newId, oldId) => {
  if (newId !== oldId) {
    await Promise.all([fetchRiskBreakdown(), fetchRiskPropagation(), fetchRiskFromDependencies()])
  }
})

// Esponi le funzioni e dati per l'header
defineExpose({
  riskBreakdown,
  riskLevelLabel,
  riskLevelSeverity,
  criticalityColors,
  getTotalRiskScore,
  getBaseRiskScore,
  getRiskFromDependencies
})
</script>

<style scoped>
.risk-tab {
  padding: 1rem 0;
}

.risk-overview-section {
  margin-bottom: 2rem;
}

.risk-overview-card {
  background: var(--surface-card);
  border: 2px solid var(--surface-border);
  border-radius: 12px;
  padding: 2rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.overview-main {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.overview-total {
  text-align: center;
  padding-bottom: 1.5rem;
  border-bottom: 2px solid var(--surface-border);
}

.overview-total label {
  display: block;
  font-size: 0.9rem;
  color: var(--text-color-secondary);
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.total-risk-value {
  font-size: 3rem;
  font-weight: bold;
  display: block;
  margin-bottom: 0.5rem;
}

.total-risk-value.risk-high {
  color: #dc3545;
}

.total-risk-value.risk-medium {
  color: #fd7e14;
}

.total-risk-value.risk-low {
  color: #28a745;
}

.total-risk-value.risk-undefined {
  color: #6c757d;
}

.risk-level-badge {
  display: inline-block;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 600;
  text-transform: uppercase;
}

.risk-level-badge.danger {
  background: #dc3545;
  color: white;
}

.risk-level-badge.warning {
  background: #fd7e14;
  color: white;
}

.risk-level-badge.success {
  background: #28a745;
  color: white;
}

.risk-level-badge.info {
  background: #6c757d;
  color: white;
}

.overview-breakdown {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.breakdown-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  background: var(--surface-50);
  border-radius: 8px;
}

.breakdown-item label {
  font-size: 0.85rem;
  color: var(--text-color-secondary);
  font-weight: 600;
}

.breakdown-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: var(--text-color);
}

.risk-increase-value {
  color: var(--orange-600);
}

.risk-section {
  margin-bottom: 1.5rem;
}

.section-header-collapsible {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  background: var(--surface-50);
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  user-select: none;
}

.section-header-collapsible:hover {
  background: var(--surface-100);
}

.section-header-collapsible .section-title {
  margin: 0;
  font-size: 1.1rem;
}

.section-header-collapsible i {
  color: var(--text-color-secondary);
  font-size: 1rem;
}

.section-content {
  margin-top: 1rem;
  padding: 0 1rem;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: var(--text-color);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.risk-propagation-section {
  border-top: 2px solid var(--surface-border);
  padding-top: 2rem;
}

.propagation-info-box {
  background: var(--surface-50);
  border-left: 4px solid var(--primary-color);
  border-radius: 4px;
  padding: 1rem;
  margin-bottom: 1.5rem;
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}

.propagation-info-box i {
  color: var(--primary-color);
  font-size: 1.25rem;
  margin-top: 0.125rem;
}

.propagation-info-box strong {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--text-color);
}

.propagation-info-box p {
  margin: 0;
  color: var(--text-color-secondary);
  line-height: 1.5;
  font-size: 0.9rem;
}

.risk-from-dependencies-section {
  border-top: 2px solid var(--surface-border);
  padding-top: 2rem;
}

.dependencies-risk-info-box {
  background: var(--surface-50);
  border-left: 4px solid var(--orange-500);
  border-radius: 4px;
  padding: 1rem;
  margin-bottom: 1.5rem;
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}

.dependencies-risk-info-box i {
  color: var(--orange-500);
  font-size: 1.25rem;
  margin-top: 0.125rem;
}

.dependencies-risk-info-box strong {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--text-color);
}

.dependencies-risk-info-box p {
  margin: 0;
  color: var(--text-color-secondary);
  line-height: 1.5;
  font-size: 0.9rem;
}

.risk-summary-box {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1.5rem;
  background: var(--surface-50);
  border-radius: 8px;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  background: white;
  border-radius: 4px;
  border: 1px solid var(--surface-border);
}

.summary-item.highlight {
  border: 2px solid var(--orange-500);
  background: var(--orange-50);
}

.summary-item.total {
  border: 2px solid var(--primary-color);
  background: var(--primary-50);
}

.summary-item label {
  font-size: 0.85rem;
  color: var(--text-color-secondary);
  font-weight: 600;
}

.summary-item .risk-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: var(--text-color);
}

.summary-item .risk-value.risk-increase {
  color: var(--orange-600);
}

.summary-item .risk-value.total-risk {
  color: var(--primary-color);
}

.dependencies-breakdown h4 {
  margin-bottom: 1rem;
  color: var(--text-color);
}

.asset-link {
  color: var(--primary-color);
  cursor: pointer;
  text-decoration: none;
  font-weight: 500;
}

.asset-link:hover {
  text-decoration: underline;
}
</style> 