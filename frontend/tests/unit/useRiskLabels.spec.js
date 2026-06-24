import { describe, it, expect } from 'vitest'
import {
  RISK_THRESHOLDS,
  getRiskLevel,
  getRiskSeverity,
  getAlertTier,
  formatRiskScore,
  getNetworkMapRiskColor,
  getPrintRiskClass,
} from '@/composables/useRiskLabels'

describe('useRiskLabels', () => {
  it('uses backend-aligned risk levels', () => {
    expect(getRiskLevel(null)).toBe('undefined')
    expect(getRiskLevel(3.9)).toBe('low')
    expect(getRiskLevel(4)).toBe('medium')
    expect(getRiskLevel(6.99)).toBe('medium')
    expect(getRiskLevel(7)).toBe('high')
  })

  it('maps severity for PrimeVue tags', () => {
    expect(getRiskSeverity(3)).toBe('success')
    expect(getRiskSeverity(5)).toBe('warning')
    expect(getRiskSeverity(8)).toBe('danger')
  })

  it('uses alert tiers with critical at 8+', () => {
    expect(getAlertTier(6.99)).toBe('medium')
    expect(getAlertTier(7)).toBe('high')
    expect(getAlertTier(8)).toBe('critical')
  })

  it('formats score on 0-10 scale', () => {
    expect(formatRiskScore(4.256)).toBe('4.26')
    expect(formatRiskScore(4.256, { suffix: true })).toBe('4.26 / 10')
    expect(formatRiskScore(null)).toBe('N/A')
  })

  it('exposes shared thresholds', () => {
    expect(RISK_THRESHOLDS.MEDIUM).toBe(4)
    expect(RISK_THRESHOLDS.HIGH).toBe(7)
    expect(RISK_THRESHOLDS.CRITICAL_ALERT).toBe(8)
  })

  it('colors network map nodes by risk', () => {
    expect(getNetworkMapRiskColor(3)).toBe('#22c55e')
    expect(getNetworkMapRiskColor(5)).toBe('#f97316')
    expect(getNetworkMapRiskColor(8)).toBe('#ef4444')
  })

  it('maps print risk classes on 0-10 scale', () => {
    expect(getPrintRiskClass(8)).toBe('risk-critical')
    expect(getPrintRiskClass(7)).toBe('risk-high')
    expect(getPrintRiskClass(4)).toBe('risk-medium')
  })
})
