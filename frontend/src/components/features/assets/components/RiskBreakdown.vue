<template>
  <div class="risk-breakdown">
    <div class="risk-score-summary" :class="riskClass">
      <span class="score">{{ breakdown.final_score !== null ? breakdown.final_score : 'N/A' }}</span>
      <span class="label">{{ riskLabel }}</span>
    </div>
    <div v-if="breakdown.missing_data && breakdown.missing_data.length" class="risk-warning">
      <i class="pi pi-exclamation-triangle"></i>
      <span>{{ t('assets.riskBreakdown.missingData') }}: {{ breakdown.missing_data.join(', ') }}</span>
    </div>
    <div class="risk-table">
      <div class="risk-row" v-for="(item, key) in partials" :key="key">
        <span class="risk-title">{{ keyLabel(key) }}</span>
        <span class="risk-value">{{ item.score !== null ? item.score : 'N/A' }}</span>
        <span class="risk-breakdown-list">
          <ul>
            <li v-for="b in item.breakdown" :key="b">{{ b }}</li>
          </ul>
        </span>
      </div>
      <div class="risk-row risk-weights">
        <span>{{ t('assets.riskBreakdown.weights') }}:</span>
        <span class="risk-weights-list">
          <span v-for="(w, k) in breakdown.weights" :key="k">{{ keyLabel(k) }}: {{ (w*100).toFixed(0) }}%</span>
        </span>
      </div>
    </div>
    <div v-if="breakdown.suggestions && breakdown.suggestions.length" class="risk-suggestions">
      <h4>{{ t('assets.riskBreakdown.suggestionsTitle') }}</h4>
      <ul>
        <li v-for="s in breakdown.suggestions" :key="s">
          <span class="suggestion-badge">⚠️</span> {{ s }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { getRiskLevel } from '@/composables/useRiskLabels'

const { t } = useI18n()
const props = defineProps({
  breakdown: { type: Object, required: true }
})
const partials = computed(() => ({
  'vulnerability': props.breakdown.vulnerability,
  'impact': props.breakdown.impact,
  'operational': props.breakdown.operational
}))
const riskLabel = computed(() => {
  const level = getRiskLevel(props.breakdown.final_score)
  if (level === 'undefined') return t('assets.riskBreakdown.undefined')
  if (level === 'high') return t('assets.riskBreakdown.high')
  if (level === 'medium') return t('assets.riskBreakdown.medium')
  return t('assets.riskBreakdown.low')
})
const riskClass = computed(() => {
  const level = getRiskLevel(props.breakdown.final_score)
  if (level === 'undefined') return 'risk-undefined'
  if (level === 'high') return 'risk-high'
  if (level === 'medium') return 'risk-medium'
  return 'risk-low'
})
function keyLabel(key) {
  // Usa direttamente la chiave come chiave di traduzione
  // Il backend dovrebbe inviare chiavi standardizzate (es: 'vulnerability', 'impact', 'operational')
  return t(`assets.riskBreakdown.${key}`)
}
</script>

<style scoped>
.risk-breakdown {
  border: 1px solid var(--surface-border);
  border-radius: 8px;
  padding: 1.5rem;
  background: var(--surface-card);
  margin-bottom: 1.5rem;
}
.risk-score-summary {
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 1.5rem;
  font-weight: bold;
  margin-bottom: 1rem;
}
.risk-high { color: #dc3545; }
.risk-medium { color: #fd7e14; }
.risk-low { color: #28a745; }
.risk-undefined { color: #6c757d; }
.risk-warning {
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffeeba;
  border-radius: 6px;
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.risk-table {
  margin-bottom: 1rem;
}
.risk-row {
  display: flex;
  align-items: flex-start;
  gap: 1.5rem;
  margin-bottom: 0.5rem;
}
.risk-title {
  min-width: 120px;
  font-weight: bold;
}
.risk-value {
  min-width: 40px;
}
.risk-breakdown-list ul {
  margin: 0;
  padding-left: 1.2em;
  font-size: 0.95em;
}
.risk-weights {
  font-size: 0.95em;
  color: #888;
}
.risk-weights-list span {
  margin-right: 1.2em;
}
.risk-suggestions {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 1rem;
}
.suggestion-badge {
  color: #dc3545;
  margin-right: 0.5em;
}
</style> 