import { useI18n } from 'vue-i18n'

export const RISK_THRESHOLDS = {
  MEDIUM: 4,
  HIGH: 7,
  CRITICAL_ALERT: 8,
  AT_RISK: 5,
}

export function getRiskLevel(score) {
  if (score === null || score === undefined || Number.isNaN(score)) {
    return 'undefined'
  }
  if (score >= RISK_THRESHOLDS.HIGH) return 'high'
  if (score >= RISK_THRESHOLDS.MEDIUM) return 'medium'
  return 'low'
}

export function getRiskSeverity(score) {
  const level = getRiskLevel(score)
  if (level === 'undefined') return 'info'
  if (level === 'high') return 'danger'
  if (level === 'medium') return 'warning'
  return 'success'
}

export function getAlertTier(score) {
  if (score === null || score === undefined || Number.isNaN(score)) {
    return null
  }
  if (score >= RISK_THRESHOLDS.CRITICAL_ALERT) return 'critical'
  if (score >= RISK_THRESHOLDS.HIGH) return 'high'
  if (score >= RISK_THRESHOLDS.MEDIUM) return 'medium'
  return null
}

export function formatRiskScore(score, { suffix = false } = {}) {
  if (score === null || score === undefined || Number.isNaN(score)) {
    return 'N/A'
  }
  const formatted = Number(score).toFixed(2)
  return suffix ? `${formatted} / 10` : formatted
}

export function getNetworkMapRiskColor(score) {
  if (score === null || score === undefined) return '#94a3b8'
  if (score >= RISK_THRESHOLDS.HIGH) return '#ef4444'
  if (score >= RISK_THRESHOLDS.MEDIUM) return '#f97316'
  return '#22c55e'
}

export function getPrintRiskClass(score) {
  if (score === null || score === undefined) return 'risk-minimal'
  if (score >= RISK_THRESHOLDS.CRITICAL_ALERT) return 'risk-critical'
  if (score >= RISK_THRESHOLDS.HIGH) return 'risk-high'
  if (score >= RISK_THRESHOLDS.MEDIUM) return 'risk-medium'
  if (score >= 2) return 'risk-low'
  return 'risk-minimal'
}

export function useRiskLabels() {
  const { t } = useI18n()

  function riskLevelLabel(score) {
    const level = getRiskLevel(score)
    if (level === 'undefined') return t('assets.riskBreakdown.riskLevelUndefined')
    if (level === 'high') return t('assets.riskBreakdown.riskLevelHigh')
    if (level === 'medium') return t('assets.riskBreakdown.riskLevelMedium')
    return t('assets.riskBreakdown.riskLevelLow')
  }

  return {
    RISK_THRESHOLDS,
    getRiskLevel,
    getRiskSeverity,
    getAlertTier,
    formatRiskScore,
    getNetworkMapRiskColor,
    getPrintRiskClass,
    riskLevelLabel,
    riskLevelSeverity: getRiskSeverity,
  }
}
