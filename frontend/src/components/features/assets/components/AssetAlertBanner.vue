<template>
  <div v-if="alertMessage" class="alert-banner" :class="alertClass">
    <div class="alert-content">
      <i :class="alertIcon" class="alert-icon"></i>
      <div class="alert-text">
        <strong>{{ alertTitle }}</strong>
        <p class="m-0">{{ alertMessage }}</p>
      </div>
    </div>
  </div>
  <div v-else class="alert-banner alert-success">
    <div class="alert-content">
      <i class="pi pi-check-circle alert-icon"></i>
      <div class="alert-text">
        <strong>{{ t('assets.alerts.allOk') }}</strong>
        <p class="m-0">{{ t('assets.alerts.noIssues') }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps({
  totalRiskScore: { type: Number, default: null },
  baseRiskScore: { type: Number, default: null },
  riskFromDependencies: { type: Number, default: null }
})

const { t } = useI18n()

const alertLevel = computed(() => {
  if (!props.totalRiskScore) return null
  const risk = props.totalRiskScore
  if (risk >= 8) return 'critical'
  if (risk >= 6) return 'high'
  if (risk >= 4) return 'medium'
  return null
})

const alertClass = computed(() => {
  const level = alertLevel.value
  if (level === 'critical') return 'alert-critical'
  if (level === 'high') return 'alert-high'
  if (level === 'medium') return 'alert-medium'
  return 'alert-success'
})

const alertIcon = computed(() => {
  const level = alertLevel.value
  if (level === 'critical') return 'pi pi-exclamation-triangle'
  if (level === 'high') return 'pi pi-exclamation-circle'
  if (level === 'medium') return 'pi pi-info-circle'
  return 'pi pi-check-circle'
})

const alertTitle = computed(() => {
  const level = alertLevel.value
  if (level === 'critical') return t('assets.alerts.criticalTitle')
  if (level === 'high') return t('assets.alerts.highTitle')
  if (level === 'medium') return t('assets.alerts.mediumTitle')
  return t('assets.alerts.allOk')
})

const alertMessage = computed(() => {
  const level = alertLevel.value
  if (level === 'critical') {
    return t('assets.alerts.criticalMessage', { score: props.totalRiskScore?.toFixed(2) })
  }
  if (level === 'high') {
    return t('assets.alerts.highMessage', { score: props.totalRiskScore?.toFixed(2) })
  }
  if (level === 'medium') {
    return t('assets.alerts.mediumMessage', { score: props.totalRiskScore?.toFixed(2) })
  }
  return null
})
</script>

<style scoped>
.alert-banner {
  padding: 1rem 1.5rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
  border-left: 4px solid;
}

.alert-critical {
  background: #fee;
  border-left-color: #dc3545;
  color: #721c24;
}

.alert-high {
  background: #fff3cd;
  border-left-color: #ffc107;
  color: #856404;
}

.alert-medium {
  background: #d1ecf1;
  border-left-color: #17a2b8;
  color: #0c5460;
}

.alert-success {
  background: #d4edda;
  border-left-color: #28a745;
  color: #155724;
}

.alert-content {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.alert-icon {
  font-size: 1.5rem;
  margin-top: 0.25rem;
}

.alert-text {
  flex: 1;
}

.alert-text strong {
  display: block;
  margin-bottom: 0.25rem;
  font-size: 1.1rem;
}
</style>

