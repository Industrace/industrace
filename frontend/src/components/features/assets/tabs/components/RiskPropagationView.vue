<template>
  <div class="risk-propagation-view">
    <div v-if="loading" class="text-center p-4">
      <ProgressSpinner />
    </div>
    <div v-else-if="riskData" class="risk-content">
      <Card class="mb-4">
        <template #title>{{ t('assetDependencies.riskPropagation') }}</template>
        <template #content>
          <div class="risk-info mb-4">
            <div class="info-row">
              <label>{{ t('assetDependencies.thisAsset') }}:</label>
              <span class="asset-name">{{ riskData.source_asset_name || '-' }}</span>
            </div>
            <div class="info-row">
              <label>{{ t('assetDependencies.thisAssetRiskScore') }}:</label>
              <div class="risk-score-container">
                <span class="risk-score">{{ riskData.source_risk_score?.toFixed(2) || '0.00' }}</span>
                <small class="risk-scale-info">{{ t('assetDependencies.riskScoreScale') }}</small>
              </div>
            </div>
            <div class="info-row info-description">
              <div class="risk-explanation">
                <strong>{{ t('assetDependencies.propagationExplanationTitle') }}</strong>
                <p>{{ t('assetDependencies.propagationExplanation') }}</p>
              </div>
            </div>
          </div>
          <div class="depth-control mb-4">
            <div class="depth-control-row">
              <label for="depth-select">{{ t('assetDependencies.propagationDepth') }}:</label>
              <SelectButton 
                v-model="selectedDepth" 
                :options="depthOptions" 
                optionLabel="label"
                optionValue="value"
                @update:modelValue="onDepthChange"
                class="depth-selector"
              />
            </div>
          </div>
          <div class="risk-stats">
            <div class="stat-item highlight">
              <label>{{ t('assetDependencies.affectedAssets') }}</label>
              <span class="stat-value">{{ riskData.total_affected_assets || 0 }}</span>
            </div>
            <div class="stat-item">
              <label>{{ t('assetDependencies.maxPropagationDepth') }}</label>
              <span class="stat-value">{{ riskData.max_propagation_depth || 0 }}</span>
            </div>
            <div class="stat-item" v-if="maxRiskIncrease > 0">
              <label>{{ t('assetDependencies.maxRiskIncrease') }}</label>
              <span class="stat-value">{{ maxRiskIncrease.toFixed(2) }}</span>
            </div>
          </div>
          <div v-if="riskData.propagated_risks && riskData.propagated_risks.length > 0" class="propagated-risks mt-4">
            <h4>{{ t('assetDependencies.affectedAssets') }}</h4>
            <p class="table-description">{{ t('assetDependencies.affectedAssetsDescription') }}</p>
            <div class="formula-explanation mb-3">
              <strong>{{ t('assetDependencies.formulaTitle') }}:</strong>
              <code class="formula-code">{{ t('assetDependencies.formula') }}</code>
              <div class="formula-details mt-2">
                <small>
                  <strong>{{ t('assetDependencies.sourceRisk') }}:</strong> {{ riskData.source_risk_score?.toFixed(2) || '0.00' }} × 
                  <strong>{{ t('assetDependencies.criticalityWeight') }}:</strong> {{ getCriticalityWeightLabel() }} × 
                  <strong>{{ t('assetDependencies.dependencyWeight') }}:</strong> {{ getDependencyWeightLabel() }} × 
                  <strong>{{ t('assetDependencies.depthDecay') }}:</strong> {{ t('assetDependencies.depthDecayFormula') }}
                </small>
              </div>
            </div>
            <DataTable :value="riskData.propagated_risks" class="p-datatable-sm" :paginator="true" :rows="10">
              <Column field="asset_name" :header="t('assetDependencies.dependentAsset')">
                <template #body="{ data }">
                  <a @click="$router.push(`/assets/${data.asset_id}`)" class="asset-link">
                    {{ data.asset_name }}
                  </a>
                </template>
              </Column>
              <Column field="current_risk_score" :header="t('assetDependencies.riskBeforePropagation')">
                <template #body="{ data }">
                  {{ data.current_risk_score?.toFixed(2) || '0.00' }}
                </template>
              </Column>
              <Column field="propagated_risk_adjustment" :header="t('assetDependencies.riskIncrease')">
                <template #body="{ data }">
                  <span class="risk-increase" v-tooltip.top="getCalculationTooltip(data)">
                    +{{ data.propagated_risk_adjustment?.toFixed(2) || '0.00' }}
                  </span>
                </template>
              </Column>
              <Column field="adjusted_risk_score" :header="t('assetDependencies.riskAfterPropagation')">
                <template #body="{ data }">
                  <span class="risk-score">{{ data.adjusted_risk_score?.toFixed(2) || '0.00' }}</span>
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
              <Column field="depth" :header="t('assetDependencies.dependencyDepth')">
                <template #body="{ data }">
                  <span class="depth-badge">{{ data.depth }}</span>
                </template>
              </Column>
            </DataTable>
          </div>
          <div v-else class="no-data mt-4">
            <p>{{ t('assetDependencies.noPropagatedRisks') }}</p>
          </div>
        </template>
      </Card>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import Card from 'primevue/card'
import ProgressSpinner from 'primevue/progressspinner'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import SelectButton from 'primevue/selectbutton'

const props = defineProps({
  assetId: { type: [String, Number], required: true },
  riskData: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  maxDepth: { type: Number, default: 5 }
})

const emit = defineEmits(['depth-change'])

const { t } = useI18n()

const depthOptions = [
  { label: '1', value: 1 },
  { label: '2', value: 2 },
  { label: '3', value: 3 },
  { label: '4', value: 4 },
  { label: '5', value: 5 },
  { label: '6', value: 6 },
  { label: '7', value: 7 },
  { label: '8', value: 8 },
  { label: '9', value: 9 },
  { label: '10', value: 10 }
]

const selectedDepth = ref(props.maxDepth || 5)

watch(() => props.maxDepth, (newDepth) => {
  selectedDepth.value = newDepth || 5
})

const onDepthChange = (newDepth) => {
  emit('depth-change', newDepth)
}

const maxRiskIncrease = computed(() => {
  if (!props.riskData?.propagated_risks || props.riskData.propagated_risks.length === 0) {
    return 0
  }
  return Math.max(...props.riskData.propagated_risks.map(r => r.propagated_risk_adjustment || 0))
})

const getCriticalityLabel = (criticality) => {
  return t(`assetDependencies.criticalities.${criticality}`) || criticality
}

const getCriticalitySeverity = (criticality) => {
  const severityMap = {
    'low': 'success',
    'medium': 'info',
    'high': 'warning',
    'critical': 'danger'
  }
  return severityMap[criticality] || null
}

const getCriticalityWeight = (criticality) => {
  const weights = {
    'low': 0.25,
    'medium': 0.50,
    'high': 0.75,
    'critical': 1.0
  }
  return weights[criticality] || 0.5
}

const getDependencyWeight = (dependencyType) => {
  const weights = {
    'logical': 0.3,
    'functional': 0.5,
    'data_flow': 0.7,
    'control_flow': 0.9
  }
  return weights[dependencyType] || 0.5
}

const getDepthDecay = (depth) => {
  if (depth === 1) return 1.0
  return 1.0 / (1.0 + (depth - 1) * 0.2)
}

const getCalculationTooltip = (data) => {
  const sourceRisk = props.riskData.source_risk_score || 0.0
  const critWeight = getCriticalityWeight(data.criticality)
  const depWeight = getDependencyWeight(data.dependency_type)
  const depthDecay = getDepthDecay(data.depth)
  const calculation = sourceRisk * critWeight * depWeight * depthDecay
  
  return `${sourceRisk.toFixed(2)} × ${critWeight} × ${depWeight} × ${depthDecay.toFixed(2)} = ${calculation.toFixed(2)}`
}

const getCriticalityWeightLabel = () => {
  return t('assetDependencies.criticalityWeights')
}

const getDependencyWeightLabel = () => {
  return t('assetDependencies.dependencyWeights')
}

const getDependencyTypeLabel = (type) => {
  return t(`assetDependencies.types.${type}`) || type
}
</script>

<style scoped>
.risk-info {
  padding: 1rem;
  background: var(--surface-50);
  border-radius: 4px;
  margin-bottom: 1rem;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--surface-200);
}

.info-row:last-child {
  border-bottom: none;
}

.info-row label {
  font-weight: 600;
  color: var(--text-color-secondary);
}

.risk-score-container {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.25rem;
}

.risk-score {
  font-weight: bold;
  color: var(--primary-color);
  font-size: 1.1rem;
}

.risk-scale-info {
  color: var(--text-color-secondary);
  font-size: 0.75rem;
}

.info-description {
  margin-top: 0.5rem;
  padding-top: 0.75rem;
  border-top: 1px solid var(--surface-200);
}

.risk-description {
  color: var(--text-color-secondary);
  font-size: 0.85rem;
  line-height: 1.4;
  font-style: italic;
}

.asset-name {
  font-weight: 600;
  color: var(--text-color);
}

.risk-explanation {
  background: var(--surface-50);
  padding: 1rem;
  border-radius: 4px;
  border-left: 3px solid var(--primary-color);
}

.risk-explanation strong {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--text-color);
}

.risk-explanation p {
  margin: 0;
  color: var(--text-color-secondary);
  line-height: 1.5;
  font-size: 0.9rem;
}

.table-description {
  color: var(--text-color-secondary);
  font-size: 0.9rem;
  margin-bottom: 1rem;
  padding: 0.75rem;
  background: var(--surface-50);
  border-radius: 4px;
}

.depth-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  background: var(--surface-200);
  border-radius: 4px;
  font-size: 0.85rem;
  font-weight: 600;
}

.risk-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  background: var(--surface-50);
  border-radius: 4px;
}

.stat-item label {
  font-size: 0.9rem;
  color: var(--text-color-secondary);
}

.stat-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: var(--primary-color);
}

.propagated-risks {
  margin-top: 2rem;
}

.propagated-risks h4 {
  margin-bottom: 1rem;
  color: var(--text-color);
}

.risk-increase {
  color: var(--red-500);
  font-weight: bold;
}

.risk-decrease {
  color: var(--green-500);
  font-weight: bold;
}

.no-data {
  text-align: center;
  padding: 2rem;
  color: var(--text-color-secondary);
}

.depth-control {
  padding: 1rem;
  background: var(--surface-50);
  border-radius: 4px;
  border: 1px solid var(--surface-border);
}

.depth-control-row {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.depth-control-row label {
  font-weight: 600;
  color: var(--text-color);
  min-width: 150px;
}

.depth-selector {
  flex: 1;
}

.stat-item.highlight {
  border: 2px solid var(--primary-color);
  background: var(--primary-50);
}

.stat-item.highlight .stat-value {
  color: var(--primary-color);
}

.formula-explanation {
  background: var(--surface-50);
  border-left: 3px solid var(--primary-color);
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.formula-code {
  display: block;
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: var(--surface-0);
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  color: var(--primary-color);
  font-weight: bold;
}

.formula-details {
  color: var(--text-color-secondary);
  font-size: 0.85rem;
  line-height: 1.6;
}

.formula-details strong {
  color: var(--text-color);
}
</style>

